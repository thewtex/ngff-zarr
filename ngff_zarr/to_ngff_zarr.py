import sys
from collections.abc import MutableMapping
from dataclasses import asdict
from pathlib import Path, PurePosixPath
from typing import Optional, Union
from packaging import version

if sys.version_info < (3, 10):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

import dask.array
import numpy as np
from itkwasm import array_like_to_numpy_array

import zarr
import zarr.storage
from ._zarr_open_array import open_array
from .v04.zarr_metadata import Metadata as Metadata_v04
from .v05.zarr_metadata import Metadata as Metadata_v05

# Zarr Python 3
if hasattr(zarr.storage, "StoreLike"):
    StoreLike = zarr.storage.StoreLike
else:
    StoreLike = Union[MutableMapping, str, Path, zarr.storage.BaseStore]
from ._zarr_kwargs import zarr_kwargs


from .config import config
from .memory_usage import memory_usage
from .methods._support import _dim_scale_factors
from .multiscales import Multiscales
from .rich_dask_progress import NgffProgress, NgffProgressCallback
from .to_multiscales import to_multiscales

zarr_version = version.parse(zarr.__version__)
zarr_version_major = zarr_version.major


def _pop_metadata_optionals(metadata_dict):
    for ax in metadata_dict["axes"]:
        if ax["unit"] is None:
            ax.pop("unit")

    if metadata_dict["coordinateTransformations"] is None:
        metadata_dict.pop("coordinateTransformations")

    return metadata_dict


def _prep_for_to_zarr(store: StoreLike, arr: dask.array.Array) -> dask.array.Array:
    try:
        importlib_metadata.distribution("kvikio")
        _KVIKIO_AVAILABLE = True
    except importlib_metadata.PackageNotFoundError:
        _KVIKIO_AVAILABLE = False

    if _KVIKIO_AVAILABLE:
        from kvikio.zarr import GDSStore

        if not isinstance(store, GDSStore):
            arr = dask.array.map_blocks(
                array_like_to_numpy_array,
                arr,
                dtype=arr.dtype,
                meta=np.empty(()),
            )
        return arr
    return dask.array.map_blocks(
        array_like_to_numpy_array, arr, dtype=arr.dtype, meta=np.empty(())
    )


def _numpy_to_zarr_dtype(dtype):
    dtype_map = {
        "bool": "bool",
        "int8": "int8",
        "int16": "int16",
        "int32": "int32",
        "int64": "int64",
        "uint8": "uint8",
        "uint16": "uint16",
        "uint32": "uint32",
        "uint64": "uint64",
        "float16": "float16",
        "float32": "float32",
        "float64": "float64",
        "complex64": "complex64",
        "complex128": "complex128",
    }

    dtype_str = str(dtype)

    # Handle endianness - strip byte order chars
    if dtype_str.startswith(("<", ">", "|")):
        dtype_str = dtype_str[1:]

    # Look up corresponding zarr dtype
    try:
        return dtype_map[dtype_str]
    except KeyError:
        raise ValueError(f"dtype {dtype} cannot be mapped to Zarr v3 core dtype")


def _write_with_tensorstore(
    store_path: str, array, region, chunks, zarr_format, dimension_names=None
) -> None:
    """Write array using tensorstore backend"""
    import tensorstore as ts

    spec = {
        "kvstore": {
            "driver": "file",
            "path": store_path,
        },
        "metadata": {
            "shape": array.shape,
        },
    }
    if zarr_format == 2:
        spec["driver"] = "zarr"
        spec["metadata"]["chunks"] = chunks
        spec["metadata"]["dimension_separator"] = "/"
        spec["metadata"]["dtype"] = array.dtype.str
    elif zarr_format == 3:
        spec["driver"] = "zarr3"
        spec["metadata"]["chunk_grid"] = {
            "name": "regular",
            "configuration": {"chunk_shape": chunks},
        }
        spec["metadata"]["data_type"] = _numpy_to_zarr_dtype(array.dtype)
        if dimension_names:
            spec["metadata"]["dimension_names"] = dimension_names
    else:
        raise ValueError(f"Unsupported zarr format: {zarr_format}")
    dataset = ts.open(spec, create=True, dtype=array.dtype).result()
    dataset[...] = array[region]


def to_ngff_zarr(
    store: StoreLike,
    multiscales: Multiscales,
    version: str = "0.4",
    overwrite: bool = True,
    use_tensorstore: bool = False,
    chunk_store: Optional[StoreLike] = None,
    progress: Optional[Union[NgffProgress, NgffProgressCallback]] = None,
    **kwargs,
) -> None:
    """
    Write an image pixel array and metadata to a Zarr store with the OME-NGFF standard data model.

    :param store: Store or path to directory in file system.
    :type  store: StoreLike

    :param multiscales: Multiscales OME-NGFF image pixel data and metadata. Can be generated with ngff_zarr.to_multiscales.
    :type  multiscales: Multiscales

    :param version: OME-Zarr specification version.
    :type  version: str, optional

    :param overwrite: If True, delete any pre-existing data in `store` before creating groups.
    :type  overwrite: bool, optional

    :param use_tensorstore: If True, write array using tensorstore backend.
    :type  use_tensorstore: bool, optional

    :param chunk_store: Separate storage for chunks. If not provided, `store` will be used
        for storage of both chunks and metadata.
    :type  chunk_store: StoreLike, optional

    :type  progress: RichDaskProgress
    :param progress: Optional progress logger

    :param **kwargs: Passed to the zarr.creation.create() function, e.g., compression options.
    """

    if use_tensorstore:
        if isinstance(store, (str, Path)):
            store_path = str(store)
        else:
            raise ValueError("use_tensorstore currently requires a path-like store")

    if version != "0.4" and version != "0.5":
        raise ValueError(f"Unsupported version: {version}")

    metadata = multiscales.metadata
    if version == "0.4" and isinstance(metadata, Metadata_v05):
        metadata = Metadata_v04(
            axes=metadata.axes,
            datasets=metadata.datasets,
            coordinateTransformations=metadata.coordinateTransformations,
            name=metadata.name,
        )
    if version == "0.5" and isinstance(metadata, Metadata_v04):
        metadata = Metadata_v05(
            axes=metadata.axes,
            datasets=metadata.datasets,
            coordinateTransformations=metadata.coordinateTransformations,
            name=metadata.name,
        )
    dimension_names = tuple([ax.name for ax in metadata.axes])
    dimension_names_kwargs = (
        {"dimension_names": dimension_names} if version != "0.4" else {}
    )

    metadata_dict = asdict(metadata)
    metadata_dict = _pop_metadata_optionals(metadata_dict)
    metadata_dict["@type"] = "ngff:Image"
    zarr_format = 2 if version == "0.4" else 3
    format_kwargs = {"zarr_format": zarr_format} if zarr_version_major >= 3 else {}
    if version == "0.4":
        root = zarr.open_group(
            store,
            mode="w" if overwrite else "a",
            chunk_store=chunk_store,
            **format_kwargs,
        )
    else:
        if zarr_version_major < 3:
            raise ValueError(
                "zarr-python version >= 3.0.0b2 required for OME-Zarr version >= 0.5"
            )
        # For version >= 0.5, open root with Zarr v3
        root = zarr.open_group(
            store,
            mode="w" if overwrite else "a",
            chunk_store=chunk_store,
            **format_kwargs,
        )

    if version != "0.4":
        # RFC 2, Zarr 3
        root.attrs["ome"] = {"version": version, "multiscales": [metadata_dict]}
    else:
        root.attrs["multiscales"] = [metadata_dict]

    nscales = len(multiscales.images)
    if progress:
        progress.add_multiscales_task("[green]Writing scales", nscales)
    next_image = multiscales.images[0]
    dims = next_image.dims
    previous_dim_factors = {d: 1 for d in dims}
    for index in range(nscales):
        if progress:
            progress.update_multiscales_task_completed(index + 1)
        image = next_image
        arr = image.data
        path = metadata.datasets[index].path
        parent = str(PurePosixPath(path).parent)
        if parent not in (".", "/"):
            array_dims_group = root.create_group(parent)
            array_dims_group.attrs["_ARRAY_DIMENSIONS"] = image.dims

        if index > 0 and index < nscales - 1 and multiscales.scale_factors:
            dim_factors = _dim_scale_factors(
                dims, multiscales.scale_factors[index], previous_dim_factors
            )
        else:
            dim_factors = {d: 1 for d in dims}
        previous_dim_factors = dim_factors

        if memory_usage(image) > config.memory_target and multiscales.scale_factors:
            shrink_factors = []
            for dim in dims:
                if dim in dim_factors:
                    shrink_factors.append(dim_factors[dim])
                else:
                    shrink_factors.append(1)

            chunks = tuple([c[0] for c in arr.chunks])

            zarr_array = open_array(
                shape=arr.shape,
                chunks=chunks,
                dtype=arr.dtype,
                store=store,
                path=path,
                mode="a",
                **zarr_kwargs,
                **dimension_names_kwargs,
            )

            shape = image.data.shape
            x_index = dims.index("x")
            y_index = dims.index("y")
            if "z" in dims:
                z_index = dims.index("z")
                # TODO address, c, t, large 2D
                slice_bytes = memory_usage(image, {"z"})
                slab_slices = min(
                    int(np.ceil(config.memory_target / slice_bytes)), arr.shape[z_index]
                )
                z_chunks = chunks[z_index]
                slice_planes = False
                if slab_slices < z_chunks:
                    slab_slices = z_chunks
                    slice_planes = True
                if slab_slices > arr.shape[z_index]:
                    slab_slices = arr.shape[z_index]
                slab_slices = int(slab_slices / z_chunks) * z_chunks
                num_z_splits = int(np.ceil(shape[z_index] / slab_slices))
                while num_z_splits % shrink_factors[z_index] > 1:
                    num_z_splits += 1
                num_y_splits = 1
                num_x_splits = 1
                regions = []
                for slab_index in range(num_z_splits):
                    if slice_planes:
                        plane_bytes = memory_usage(image, {"z", "y"})
                        plane_slices = min(
                            int(np.ceil(config.memory_target / plane_bytes)),
                            arr.shape[y_index],
                        )
                        y_chunks = chunks[y_index]
                        slice_strips = False
                        if plane_slices < y_chunks:
                            plane_slices = y_chunks
                            slice_strips = True
                        if plane_slices > arr.shape[y_index]:
                            plane_slices = arr.shape[y_index]
                        plane_slices = int(plane_slices / y_chunks) * y_chunks
                        num_y_splits = int(np.ceil(shape[y_index] / plane_slices))
                        while num_y_splits % shrink_factors[y_index] > 1:
                            num_y_splits += 1
                        if slice_strips:
                            strip_bytes = memory_usage(image, {"z", "y", "x"})
                            strip_slices = min(
                                int(np.ceil(config.memory_target / strip_bytes)),
                                arr.shape[x_index],
                            )
                            x_chunks = chunks[x_index]
                            strip_slices = max(strip_slices, x_chunks)
                            slice_strips = False
                            if strip_slices > arr.shape[x_index]:
                                strip_slices = arr.shape[x_index]
                            strip_slices = int(strip_slices / x_chunks) * x_chunks
                            num_x_splits = int(np.ceil(shape[x_index] / strip_slices))
                            while num_x_splits % shrink_factors[x_index] > 1:
                                num_x_splits += 1
                            for plane_index in range(num_y_splits):
                                for strip_index in range(num_x_splits):
                                    region = [
                                        slice(arr.shape[i]) for i in range(arr.ndim)
                                    ]
                                    region[z_index] = slice(
                                        slab_index * z_chunks,
                                        min(
                                            (slab_index + 1) * z_chunks,
                                            arr.shape[z_index],
                                        ),
                                    )
                                    region[y_index] = slice(
                                        plane_index * y_chunks,
                                        min(
                                            (plane_index + 1) * y_chunks,
                                            arr.shape[y_index],
                                        ),
                                    )
                                    region[x_index] = slice(
                                        strip_index * x_chunks,
                                        min(
                                            (strip_index + 1) * x_chunks,
                                            arr.shape[x_index],
                                        ),
                                    )
                                    regions.append(tuple(region))
                        else:
                            for plane_index in range(num_y_splits):
                                region = [slice(arr.shape[i]) for i in range(arr.ndim)]
                                region[z_index] = slice(
                                    slab_index * z_chunks,
                                    min(
                                        (slab_index + 1) * z_chunks, arr.shape[z_index]
                                    ),
                                )
                                region[y_index] = slice(
                                    plane_index * y_chunks,
                                    min(
                                        (plane_index + 1) * y_chunks, arr.shape[y_index]
                                    ),
                                )
                                regions.append(tuple(region))
                    else:
                        region = [slice(arr.shape[i]) for i in range(arr.ndim)]
                        region[z_index] = slice(
                            slab_index * z_chunks,
                            min((slab_index + 1) * z_chunks, arr.shape[z_index]),
                        )
                        regions.append(tuple(region))
                regions = tuple(regions)
                for region_index, region in enumerate(regions):
                    if isinstance(progress, NgffProgressCallback):
                        progress.add_callback_task(
                            f"[green]Writing scale {index+1} of {nscales}, region {region_index+1} of {len(regions)}"
                        )
                    arr_region = arr[region]
                    arr_region = _prep_for_to_zarr(store, arr_region)
                    optimized = dask.array.Array(
                        dask.array.optimize(
                            arr_region.__dask_graph__(), arr_region.__dask_keys__()
                        ),
                        arr_region.name,
                        arr_region.chunks,
                        meta=arr_region,
                    )
                    if use_tensorstore:
                        scale_path = f"{store_path}/{path}"
                        _write_with_tensorstore(
                            scale_path,
                            optimized,
                            region,
                            [c[0] for c in arr_region.chunks],
                            zarr_format=zarr_format,
                            dimension_names=dimension_names,
                            **kwargs,
                        )
                    else:
                        dask.array.to_zarr(
                            optimized,
                            zarr_array,
                            region=region,
                            component=path,
                            overwrite=False,
                            compute=True,
                            return_stored=False,
                            **zarr_kwargs,
                            **dimension_names_kwargs,
                            **kwargs,
                        )
        else:
            if isinstance(progress, NgffProgressCallback):
                progress.add_callback_task(
                    f"[green]Writing scale {index+1} of {nscales}"
                )
            if use_tensorstore:
                scale_path = f"{store_path}/{path}"
                region = tuple([slice(arr.shape[i]) for i in range(arr.ndim)])
                _write_with_tensorstore(
                    scale_path,
                    arr,
                    region,
                    [c[0] for c in arr.chunks],
                    zarr_format=zarr_format,
                    dimension_names=dimension_names,
                    **kwargs,
                )
            else:
                arr = _prep_for_to_zarr(store, arr)
                dask.array.to_zarr(
                    arr,
                    store,
                    component=path,
                    overwrite=False,
                    compute=True,
                    return_stored=False,
                    **zarr_kwargs,
                    **dimension_names_kwargs,
                    **kwargs,
                )

        # Minimize task graph depth
        if (
            index > 1
            and index < nscales - 2
            and multiscales.scale_factors
            and multiscales.method
            and multiscales.chunks
            and multiscales.scale_factors
        ):
            for callback in image.computed_callbacks:
                callback()
            image.computed_callbacks = []

            image.data = dask.array.from_zarr(store, component=path)
            next_multiscales_factor = multiscales.scale_factors[index]
            if isinstance(next_multiscales_factor, int):
                next_multiscales_factor = (
                    next_multiscales_factor // multiscales.scale_factors[index - 1]
                )
            else:
                updated_factors = {}
                for d, f in next_multiscales_factor.items():
                    updated_factors[d] = f // multiscales.scale_factors[index - 1][d]
                next_multiscales_factor = updated_factors

            next_multiscales = to_multiscales(
                image,
                scale_factors=[
                    next_multiscales_factor,
                ],
                method=multiscales.method,
                chunks=multiscales.chunks,
                progress=progress,
                cache=False,
            )
            multiscales.images[index + 1] = next_multiscales.images[1]
            next_image = next_multiscales.images[1]
        elif index < nscales - 1:
            next_image = multiscales.images[index + 1]

    for image in multiscales.images:
        for callback in image.computed_callbacks:
            callback()
        image.computed_callbacks = []

    zarr.consolidate_metadata(store, **format_kwargs)
