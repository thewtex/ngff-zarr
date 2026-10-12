# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""Utility functions for ngff-zarr MCP server."""

import asyncio
import contextlib
import ipaddress
import json
import zipfile
from collections.abc import Iterator, Mapping, MutableMapping
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiofiles
import httpx
from ngff_zarr import (  # type: ignore[import-untyped]
    config,
    from_ome_zarr,
)
from ngff_zarr.v04.zarr_metadata import (  # type: ignore[import-untyped]
    is_unit_supported,
)

from .models import StoreInfo, SupportedFormats


async def _refuse_local_host(request: httpx.Request) -> None:
    """Refuse loopback and link-local hosts, such as cloud metadata endpoints.

    shortcut: the address is resolved again on connect, so DNS rebinding can
    slip past; bind the connection to the checked address if that matters.
    """
    host = request.url.host
    for *_, sockaddr in await asyncio.get_running_loop().getaddrinfo(host, None):
        address = ipaddress.ip_address(sockaddr[0])
        if address.is_loopback or address.is_link_local:
            raise ValueError(f"Refusing to download from {host}: a local address.")


async def download_file(url: str, destination: Path) -> None:
    """Download a file from URL to destination."""
    async with httpx.AsyncClient(
        follow_redirects=True, event_hooks={"request": [_refuse_local_host]}
    ) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            async with aiofiles.open(destination, "wb") as f:
                async for chunk in response.aiter_bytes():
                    await f.write(chunk)


def is_url(path: str) -> bool:
    """Check if path is a URL."""
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_s3_url(path: str) -> bool:
    """Check if path is an S3 URL."""
    return path.startswith("s3://")


def is_zarr_store(path: str) -> bool:
    """Check if path points to a Zarr store."""
    if is_url(path):
        # For URLs, we'd need to check remotely - simplified for now
        return path.endswith(".zarr") or path.endswith(".ome.zarr")

    path_obj = Path(path)
    if path_obj.suffix == ".ozx":
        return path_obj.is_file()
    return (
        (path_obj / "zarr.json").exists()
        or (path_obj / ".zgroup").exists()
        or (path_obj / ".zarray").exists()
    )


def check_output_path(output_path: str, overwrite: bool) -> None:
    """Refuse an output path whose contents the write would delete.

    ``to_ome_zarr`` removes what is at the path before writing, and the path
    comes from an agent, so only a Zarr store, and only with ``overwrite``, may go.
    """
    path = Path(output_path)
    if not path.exists():
        return
    if not overwrite:
        raise FileExistsError(
            f"Output path already exists: {output_path}. "
            "Pass overwrite=True to replace the store there."
        )
    if path.is_dir() and any(path.iterdir()) and not is_zarr_store(output_path):
        raise FileExistsError(
            f"Refusing to overwrite {output_path}: it is a non-empty directory "
            "but not a Zarr store."
        )


def url_store_mapping(
    store_path: str, storage_options: dict | None = None
) -> MutableMapping:
    """Key-to-bytes mapping over a remote store URL (S3 needs s3fs)."""
    import fsspec  # type: ignore[import-untyped]

    return fsspec.get_mapper(store_path, **(storage_options or {}))


def _store_doc(store: str | Path | Mapping, name: str) -> str | None:
    """Raw metadata document *name* at the store root, or None if unreadable."""
    if isinstance(store, (str, Path)):
        try:
            if Path(store).is_file():  # an .ozx archive (RFC-9)
                with zipfile.ZipFile(store) as archive:
                    return archive.read(name).decode()
            return (Path(store) / name).read_text()
        except (OSError, KeyError, zipfile.BadZipFile):
            return None
    try:
        data = store[name]
    except Exception:
        return None
    return data.decode() if isinstance(data, (bytes, bytearray)) else str(data)


def read_root_attrs(
    store: str | Path | Mapping, storage_options: dict | None = None
) -> dict:
    """Root group attributes read directly from the store's metadata documents.

    Accepts a local directory or .ozx path, a remote store URL, or a key-to-bytes
    mapping. Prefers the zarr v3 ``zarr.json`` document, falling back to the
    zarr v2 ``.zattrs``; returns ``{}`` when neither is readable. No
    zarr-python involved.
    """
    if isinstance(store, str) and is_url(store):
        store = url_store_mapping(store, storage_options)
    text = _store_doc(store, "zarr.json")
    if text is not None:
        try:
            doc = json.loads(text)
        except json.JSONDecodeError:
            doc = None
        if isinstance(doc, dict) and doc.get("node_type") == "group":
            attrs = doc.get("attributes")
            if isinstance(attrs, dict) and attrs:
                return attrs
    text = _store_doc(store, ".zattrs")
    if text is not None:
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            return {}
        if isinstance(loaded, dict):
            return loaded
    return {}


def detect_ome_zarr_version(root_attrs: dict) -> str | None:
    """OME-Zarr version declared in *root_attrs*, or None when undeclared.

    Recognizes the v0.5+ layout (``ome.version``, defaulting to "0.5" when
    the ``ome`` key is present without a version) and the v0.4 layout
    (``multiscales[0].version``, defaulting to "0.4").
    """
    if "ome" in root_attrs:
        ome_attrs = root_attrs["ome"]
        if isinstance(ome_attrs, dict):
            version_attr = ome_attrs.get("version", "0.5")
            if isinstance(version_attr, str):
                return version_attr
    multiscales_attr = root_attrs.get("multiscales")
    if isinstance(multiscales_attr, list) and multiscales_attr:
        ms_attrs = multiscales_attr[0]
        if isinstance(ms_attrs, dict):
            version_attr = ms_attrs.get("version", "0.4")
            if isinstance(version_attr, str):
                return version_attr
    return None


def get_store_size_and_files(store_path: str) -> tuple[int, int]:
    """Get total size and number of files in a store."""
    if is_url(store_path):
        # For remote stores, this would need special handling
        return 0, 0

    path = Path(store_path)
    if not path.exists():
        return 0, 0
    if path.is_file():  # an .ozx archive
        return path.stat().st_size, 1

    total_size = 0
    file_count = 0

    for file_path in path.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
            file_count += 1

    return total_size, file_count


def analyze_zarr_store(
    store_path: str, storage_options: dict | None = None, validate: bool = False
) -> StoreInfo:
    """Analyze a Zarr store and return information."""
    try:
        try:
            multiscales = from_ome_zarr(
                store_path, validate=validate, storage_options=storage_options
            )
        except KeyError as e:
            if str(e) == "'start'" and store_path.startswith(("http://", "https://")):
                # Handle OMERO metadata compatibility issue for remote stores
                # Some stores have 'min'/'max' instead of 'start'/'end' in channel window
                raise ValueError(
                    "Remote store has incompatible OMERO metadata format: missing 'start' key in channel window. This is a known compatibility issue with some OME-Zarr stores that use 'min'/'max' instead of 'start'/'end'."
                ) from e
            else:
                raise e
        first_image = multiscales.images[0]

        # Get store size and file count
        size_bytes, num_files = get_store_size_and_files(store_path)

        # Determine OME-Zarr version from the root metadata documents
        version = "0.4"  # Default
        try:
            detected = detect_ome_zarr_version(
                read_root_attrs(store_path, storage_options)
            )
            if detected is not None:
                version = detected
        except Exception:
            pass

        return StoreInfo(
            path=store_path,
            version=version,
            size_bytes=size_bytes,
            num_files=num_files,
            num_scales=len(multiscales.images),
            dimensions=list(first_image.dims),
            shape=list(first_image.data.shape),
            dtype=str(first_image.data.dtype),
            chunks=[int(size) for size in first_image.data.chunksize],
            scale_info=dict(first_image.scale) if first_image.scale else {},
            translation_info=(
                dict(first_image.translation) if first_image.translation else {}
            ),
            method_type=getattr(multiscales, "method", None),
            method_metadata=getattr(multiscales, "method_metadata", None),
            anatomical_orientation=None,  # Will be populated if available
            rfc_support=None,  # Will be populated if available
        )

    except Exception as e:
        raise ValueError(f"Failed to analyze store {store_path}: {str(e)}")


# Common file extensions supported by both ITK and ITKWasm
COMMON_EXTENSIONS = [
    ".bmp",
    ".dcm",
    ".gipl",
    ".gipl.gz",
    ".hdf5",
    ".jpg",
    ".jpeg",
    ".iwi",
    ".iwi.cbor",
    ".iwi.cbor.zst",
    ".lsm",
    ".mnc",
    ".mnc.gz",
    ".mnc2",
    ".mgh",
    ".mhz",
    ".mha",
    ".mhd",
    ".mrc",
    ".nia",
    ".nii",
    ".nii.gz",
    ".hdr",
    ".nrrd",
    ".nhdr",
    ".png",
    ".pic",
    ".vtk",
]


def get_supported_formats() -> SupportedFormats:
    """Get information about supported formats."""

    input_formats = {
        "ngff_zarr": [".zarr", ".ome.zarr"],
        "zarr": [".zarr"],  # Raw zarr arrays
        "itkwasm": COMMON_EXTENSIONS
        + [".aim", ".isq", ".fdf"],  # ITKWasm-specific extensions
        "itk": COMMON_EXTENSIONS + [],  # ITK-specific extensions
        "tifffile": [
            ".tif",
            ".tiff",  # Standard TIFF
            ".ome.tiff",  # OME-TIFF microscopy format
            ".stk",  # MetaMorph STK format
            ".gel",  # Molecular Dynamics GEL format
            ".seq",  # Media Cybernetics SEQ format
            ".zif",  # Zoomable Image File Format
            ".qptiff",  # PerkinElmer QPTIFF format
            ".bif",  # Roche BIF format
            ".avs",  # Argos AVS format
            ".dp",  # Philips DP format
            # Digital pathology formats
            ".svs",  # Aperio SVS format
            ".ndpi",  # Hamamatsu NDPI format
            ".scn",  # Leica SCN format
            # Note: .lsm is already covered by ITK/ITKWasm in COMMON_EXTENSIONS
        ],
        "imageio": [
            # Video formats (FFMPEG plugin)
            ".webm",
            ".mp4",
            ".avi",
            ".mov",
            ".gif",  # Already present
            ".mkv",
            ".mpeg",
            ".mpg",
            ".wmv",
            ".flv",
            ".3gp",
            ".3g2",
            ".m4v",
            ".f4v",
            ".m2ts",
            ".vob",
            ".ogv",
            ".dv",
            ".asf",
            ".rm",
            ".rmvb",
            ".ts",
            ".mts",
            ".divx",
            ".xvid",
            # Image formats not well-supported by ITK/tifffile
            ".psd",  # Photoshop Document
            ".pcx",  # ZSoft Paintbrush
            ".sgi",  # Silicon Graphics Image
            ".ras",  # Sun Raster
            ".xbm",
            ".xpm",  # X Window System
            ".dds",  # DirectDraw Surface
            ".cut",  # Dr. Halo
            ".exr",  # OpenEXR
            ".ppm",
            ".pgm",
            ".pbm",  # Portable Pixmap formats
            ".webp",  # WebP format
            ".icns",  # Apple Icon format
            ".ico",  # Windows Icon format
            ".tga",  # Targa format
            ".pict",  # Macintosh PICT
            ".pcd",  # Kodak PhotoCD
            # Camera raw formats (FreeImage plugin)
            ".3fr",
            ".arw",
            ".cr2",
            ".crw",
            ".nef",
            ".orf",
            ".raf",
            ".rw2",
            ".dng",
            ".raw",
            ".bay",
            ".cap",
            ".dcs",
            ".dcr",
            ".drf",
            ".erf",
            ".fff",
            ".iiq",
            ".k25",
            ".kdc",
            ".mdc",
            ".mef",
            ".mos",
            ".mrw",
            ".nrw",
            ".pef",
            ".ptx",
            ".pxn",
            ".r3d",
            ".rwl",
            ".sr2",
            ".srf",
            ".srw",
            ".x3f",
        ],
    }

    output_formats = [".zarr", ".ome.zarr"]

    backends = ["ngff_zarr", "zarr", "itkwasm", "itk", "tifffile", "imageio"]

    return SupportedFormats(
        input_formats=input_formats, output_formats=output_formats, backends=backends
    )


def get_available_methods() -> list[str]:
    """Get available downsampling methods."""
    from ngff_zarr.methods import methods_values  # type: ignore[import-untyped]

    return methods_values


def get_available_compression_codecs() -> list[str]:
    """Get available compression codecs.

    Delegates to :func:`ngff_zarr.codecs.get_available_codecs`.
    """
    from ngff_zarr.codecs import get_available_codecs  # type: ignore[import-untyped]

    return get_available_codecs()


@contextlib.contextmanager
def setup_dask_config(
    use_local_cluster: bool = False,
    cache_dir: str | None = None,
) -> Iterator[Any | None]:
    """Set the cache directory and start a LocalCluster for one conversion.

    Yields the Client, or None without a LocalCluster. Both are undone on exit.
    """
    previous_cache_store = config.cache_store
    if cache_dir:
        cache_path = Path(cache_dir).resolve()
        cache_path.mkdir(parents=True, exist_ok=True)
        # ngff-zarr's cache_store is a directory path; large-image cache
        # arrays are written into it through the zarrista backend.
        config.cache_store = cache_path

    client = None
    try:
        if use_local_cluster:
            try:
                import psutil
                from dask.distributed import Client
            except ImportError:
                raise ImportError("dask[distributed] required for LocalCluster")

            # Given worker options, the Client starts its own LocalCluster and
            # closes it with itself.
            client = Client(
                n_workers=max(1, (psutil.cpu_count(False) or 8) // 2),
                processes=True,
                threads_per_worker=2,
            )
        yield client
    finally:
        if client is not None:
            client.close()
        config.cache_store = previous_cache_store


def validate_conversion_options(options: dict[str, Any]) -> list[str]:
    """Validate conversion options and return list of errors."""
    errors = []

    # Validate dimensions
    if "dims" in options and options["dims"]:
        valid_dims = {"t", "z", "y", "x", "c"}
        invalid_dims = set(options["dims"]) - valid_dims
        if invalid_dims:
            errors.append(
                f"Invalid dimensions: {invalid_dims}. Must be from {valid_dims}"
            )

    # Validate units
    if "units" in options and options["units"]:
        for dim, unit in options["units"].items():
            if not is_unit_supported(unit.lower()):
                errors.append(f"Unsupported unit '{unit}' for dimension '{dim}'")

    # Validate method
    if "method" in options:
        available_methods = get_available_methods()
        if options["method"] not in available_methods:
            errors.append(
                f"Invalid method '{options['method']}'. Available: {available_methods}"
            )

    # Validate OME-Zarr version
    if "ome_zarr_version" in options:
        if options["ome_zarr_version"] not in ["0.4", "0.5", "0.6"]:
            errors.append("OME-Zarr version must be '0.4', '0.5', or '0.6'")

    return errors


async def prepare_input_files(input_paths: list[str], temp_dir: str) -> list[str]:
    """Prepare input files, downloading remote files if necessary."""
    temp_path = Path(temp_dir)
    temp_path.mkdir(parents=True, exist_ok=True)

    prepared_paths: list[str] = []

    for input_path in input_paths:
        if is_url(input_path) and not is_s3_url(input_path):
            # Download HTTP/HTTPS files
            filename = Path(urlparse(input_path).path).name
            if not filename:
                filename = f"downloaded_file_{len(prepared_paths)}"

            # Keep the name: a header such as .mhd names its data file.
            local_path = temp_path / filename
            if local_path.exists():
                raise ValueError(f"Two inputs download to the same name {filename!r}.")
            await download_file(input_path, local_path)
            prepared_paths.append(str(local_path))
        else:
            # Local files or S3 URLs (handled by fsspec)
            prepared_paths.append(input_path)

    return prepared_paths
