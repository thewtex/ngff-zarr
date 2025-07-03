"""Utility functions for ngff-zarr MCP server."""

import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
import httpx
import aiofiles

import zarr
from ngff_zarr import (
    from_ngff_zarr,
    config,
)

# Import unit validation function
try:
    from ngff_zarr.v04.zarr_metadata import is_unit_supported
except ImportError:
    # Fallback if not available
    def is_unit_supported(unit):
        common_units = [
            "meter",
            "millimeter",
            "micrometer",
            "nanometer",
            "second",
            "millisecond",
        ]
        return unit.lower() in common_units


from .models import StoreInfo, SupportedFormats


async def download_file(url: str, destination: Path) -> None:
    """Download a file from URL to destination."""
    async with httpx.AsyncClient() as client:
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
    except:
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
    return (path_obj / ".zgroup").exists() or (path_obj / ".zarray").exists()


def get_store_size_and_files(store_path: str) -> tuple[int, int]:
    """Get total size and number of files in a store."""
    if is_url(store_path):
        # For remote stores, this would need special handling
        return 0, 0

    path = Path(store_path)
    if not path.exists():
        return 0, 0

    total_size = 0
    file_count = 0

    for file_path in path.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
            file_count += 1

    return total_size, file_count


def analyze_zarr_store(store_path: str) -> StoreInfo:
    """Analyze a Zarr store and return information."""
    try:
        if is_url(store_path):
            # Handle remote stores
            if is_s3_url(store_path):
                try:
                    import s3fs

                    fs = s3fs.S3FileSystem()
                    store = s3fs.S3Map(store_path, s3=fs)
                except ImportError:
                    raise ImportError("s3fs required for S3 URLs")
            else:
                # HTTP/HTTPS URLs
                import fsspec

                store = fsspec.get_mapper(store_path)
        else:
            store = zarr.DirectoryStore(store_path)

        # Load multiscales
        multiscales = from_ngff_zarr(store)
        first_image = multiscales.images[0]

        # Get store size and file count
        size_bytes, num_files = get_store_size_and_files(store_path)

        # Extract compression info if available
        compression = None
        if hasattr(first_image.data, "chunks"):
            # Get compression from first chunk
            try:
                chunk_info = first_image.data._meta
                if hasattr(chunk_info, "compressor") and chunk_info.compressor:
                    compression = str(chunk_info.compressor)
            except:
                pass

        # Determine OME-Zarr version from metadata
        version = "0.4"  # Default
        try:
            root = zarr.open(store, mode="r")
            if "multiscales" in root.attrs:
                ms_attrs = root.attrs["multiscales"][0]
                if "version" in ms_attrs:
                    version = ms_attrs["version"]
        except:
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
            chunks=(
                list(first_image.data.chunks[0])
                if hasattr(first_image.data, "chunks")
                else []
            ),
            compression=compression,
            scale_info=dict(first_image.scale) if first_image.scale else {},
            translation_info=(
                dict(first_image.translation) if first_image.translation else {}
            ),
        )

    except Exception as e:
        raise ValueError(f"Failed to analyze store {store_path}: {str(e)}")


def get_supported_formats() -> SupportedFormats:
    """Get information about supported formats."""

    input_formats = {
        "ngff_zarr": [".zarr", ".ome.zarr"],
        "zarr": [".zarr"],  # Raw zarr arrays
        "itkwasm": [
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
            ".aim",
            ".isq",
            ".fdf",
        ],
        "itk": [
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
            ".isq",
            ".aim",
            ".fdf",
        ],
        "tifffile": [".tif", ".tiff", ".svs", ".ndpi", ".scn"],
        "imageio": [".webm", ".mp4", ".avi", ".mov", ".gif"],
    }

    output_formats = [".zarr", ".ome.zarr"]

    backends = ["ngff_zarr", "zarr", "itkwasm", "itk", "tifffile", "imageio"]

    return SupportedFormats(
        input_formats=input_formats, output_formats=output_formats, backends=backends
    )


def get_available_methods() -> List[str]:
    """Get available downsampling methods."""
    from ngff_zarr.methods import methods_values

    return methods_values


def get_available_compression_codecs() -> List[str]:
    """Get available compression codecs."""
    codecs = ["gzip", "lz4", "zstd"]

    # Check for blosc variants
    try:
        import numcodecs

        blosc_codecs = ["blosc", "blosclz", "lz4", "lz4hc", "snappy", "zlib", "zstd"]
        codecs.extend([f"blosc:{codec}" for codec in blosc_codecs])
    except ImportError:
        pass

    return codecs


def setup_dask_config(
    memory_target: Optional[str] = None,
    use_local_cluster: bool = False,
    cache_dir: Optional[str] = None,
) -> Optional[Any]:
    """Setup Dask configuration and return client if using LocalCluster."""
    import dask

    if memory_target:
        config.memory_target = dask.utils.parse_bytes(memory_target)

    if cache_dir:
        cache_path = Path(cache_dir).resolve()
        cache_path.mkdir(parents=True, exist_ok=True)
        if hasattr(zarr.storage, "DirectoryStore"):
            LocalStore = zarr.storage.DirectoryStore
        else:
            LocalStore = zarr.storage.LocalStore
        config.cache_store = LocalStore(cache_path)

    client = None
    if use_local_cluster:
        try:
            from dask.distributed import Client, LocalCluster
            import psutil

            n_workers = 4
            worker_memory_target = config.memory_target // n_workers

            try:
                n_workers = psutil.cpu_count(False) // 2
                worker_memory_target = config.memory_target // n_workers
            except:
                pass

            cluster = LocalCluster(
                n_workers=n_workers,
                memory_limit=worker_memory_target,
                processes=True,
                threads_per_worker=2,
            )
            client = Client(cluster)
        except ImportError:
            raise ImportError("dask[distributed] required for LocalCluster")

    return client


def validate_conversion_options(options: Dict[str, Any]) -> List[str]:
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
        if options["ome_zarr_version"] not in ["0.4", "0.5"]:
            errors.append("OME-Zarr version must be '0.4' or '0.5'")

    return errors


async def prepare_input_files(
    input_paths: List[str], temp_dir: Optional[str] = None
) -> List[str]:
    """Prepare input files, downloading remote files if necessary."""
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()

    temp_path = Path(temp_dir)
    temp_path.mkdir(parents=True, exist_ok=True)

    prepared_paths = []

    for input_path in input_paths:
        if is_url(input_path) and not is_s3_url(input_path):
            # Download HTTP/HTTPS files
            filename = Path(urlparse(input_path).path).name
            if not filename:
                filename = f"downloaded_file_{len(prepared_paths)}"

            local_path = temp_path / filename
            await download_file(input_path, local_path)
            prepared_paths.append(str(local_path))
        else:
            # Local files or S3 URLs (handled by fsspec)
            prepared_paths.append(input_path)

    return prepared_paths
