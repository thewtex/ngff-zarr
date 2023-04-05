from typing import Union, Optional
from collections.abc import MutableMapping
from pathlib import Path
from dataclasses import asdict
from functools import reduce

from zarr.storage import BaseStore
import zarr
import dask.array
import numpy as np

from .multiscales import Multiscales
from .to_multiscales import to_multiscales
from .config import config
from .rich_dask_progress import NgffProgress, NgffProgressCallback
from .memory_usage import memory_usage
from .task_count import task_count

def to_ngff_zarr(
    store: Union[MutableMapping, str, Path, BaseStore],
    multiscales: Multiscales,
    overwrite: bool = True,
    chunk_store: Optional[Union[MutableMapping, str, Path, BaseStore]] = None,
    progress: Optional[Union[NgffProgress, NgffProgressCallback]] = None,
    **kwargs,
) -> None:
    """
    Write an image pixel array and metadata to a Zarr store with the OME-NGFF standard data model.

    store : MutableMapping, str or Path, zarr.storage.BaseStore
        Store or path to directory in file system.

    multiscales: Multiscales
        Multiscales OME-NGFF image pixel data and metadata. Can be generated with ngff_zarr.to_multiscales.

    overwrite : bool, optional
        If True, delete any pre-existing data in `store` before creating groups.

    chunk_store : MutableMapping, str or Path, zarr.storage.BaseStore, optional
        Separate storage for chunks. If not provided, `store` will be used
        for storage of both chunks and metadata.

    progress: RichDaskProgress
        Optional progress logger

    **kwargs:
        Passed to the zarr.creation.create() function, e.g., compression options.


    Returns
    -------

    None

    """

    metadata_dict = asdict(multiscales.metadata)
    metadata_dict["@type"] = "ngff:Image"
    root = zarr.group(store, overwrite=overwrite, chunk_store=chunk_store)
    root.attrs["multiscales"] = [metadata_dict]

    nscales = len(multiscales.images)
    if progress:
        progress.add_multiscales_task(f"[green]Writing scales", nscales)
    next_image = multiscales.images[0]
    for index in range(nscales):
        if progress:
            progress.update_multiscales_task_completed((index+1))
        image = next_image
        arr = image.data
        path = multiscales.metadata.datasets[index].path
        path_group = root.create_group(path)
        path_group.attrs["_ARRAY_DIMENSIONS"] = image.dims

        # if memory_usage(image) > config.memory_target or task_count(image) > config.task_target:
        if memory_usage(image) > config.memory_target:
            chunks = tuple([c[0] for c in arr.chunks])
            zarr_array = zarr.create(
                shape=arr.shape,
                chunks=chunks,
                dtype=arr.dtype,
                store=store,
                path=path,
                overwrite=overwrite,
            )

            dims = list(image.dims)
            x_index = dims.index('x')
            y_index = dims.index('y')
            if 'z' in dims:
                z_index = dims.index('z')
                # TODD address, c, t, large 2D
                slice_bytes = memory_usage(image, {'z'})
                from rich import print
                print(slice_bytes)
                scale_factors = multiscales.scale_factors
                print(scale_factors)
                print(nscales, index)
                # if index < nscales - 1:
                    # print(scale_factors[index])
                    # for s in multiscales.scale_factors[index].values():
                        # slice_bytes *= s
                print(slice_bytes)
                slab_slices = min(int(np.ceil(config.memory_target / slice_bytes)), arr.shape[z_index])
                print(slab_slices)
                # slice_tasks = task_count(image, {'z'})
                # slab_slices = min(int(np.ceil(config.task_target / slice_tasks)), slab_slices)
                z_chunks = chunks[z_index]
                slice_planes = False
                print('slab_slices, z_chunks', slab_slices, z_chunks)
                if slab_slices < z_chunks:
                    slab_slices = z_chunks
                    slice_planes = True
                # slab_slices = max(slab_slices, z_chunks)
                print(max(slab_slices, z_chunks))
                print('slab_slices', slab_slices)
                if slab_slices > arr.shape[z_index]:
                    slab_slices = arr.shape[z_index]
                slab_slices = int(slab_slices / z_chunks) * z_chunks
                regions = []
                for slab_index in range(int(np.ceil(arr.shape[z_index]/slab_slices))):
                    if slice_planes:
                        plane_bytes = memory_usage(image, {'z', 'y'})
                        print(plane_bytes)
                        plane_slices = min(int(np.ceil(config.memory_target / plane_bytes)), arr.shape[y_index])
                        y_chunks = chunks[y_index]
                        print('plane_slices pre', plane_slices, y_chunks)
                        slice_strips = False
                        if plane_slices < y_chunks:
                            plane_slices = y_chunks
                            slice_strips = True
                        if plane_slices > arr.shape[y_index]:
                            plane_slices = arr.shape[y_index]
                        plane_slices = int(plane_slices / y_chunks) * y_chunks
                        print('plane_slices', plane_slices)
                        print('plane_slices', plane_slices)
                        print('plane_slices', plane_slices)
                        if slice_strips:
                            strip_bytes = memory_usage(image, {'z', 'y', 'x'})
                            print(strip_bytes)
                            strip_slices = min(int(np.ceil(config.memory_target / strip_bytes)), arr.shape[x_index])
                            x_chunks = chunks[x_index]
                            print('strip_slices pre', strip_slices, x_chunks)
                            strip_slices = max(strip_slices, x_chunks)
                            slice_strips = False
                            if strip_slices > arr.shape[x_index]:
                                strip_slices = arr.shape[x_index]
                            strip_slices = int(strip_slices / x_chunks) * x_chunks
                            print('strip_slices', strip_slices)
                            print('strip_slices', strip_slices)
                            print('strip_slices', strip_slices)
                            for plane_index in range(int(np.ceil(arr.shape[y_index]/plane_slices))):
                                for strip_index in range(int(np.ceil(arr.shape[x_index]/strip_slices))):
                                    region = [slice(arr.shape[i]) for i in range(arr.ndim)]
                                    region[z_index] = slice(slab_index*z_chunks, min((slab_index+1)*z_chunks, arr.shape[z_index]))
                                    region[y_index] = slice(plane_index*y_chunks, min((plane_index+1)*y_chunks, arr.shape[y_index]))
                                    region[x_index] = slice(plane_index*x_chunks, min((plane_index+1)*x_chunks, arr.shape[x_index]))
                                    regions.append(tuple(region))
                        else:
                            for plane_index in range(int(np.ceil(arr.shape[y_index]/plane_slices))):
                                region = [slice(arr.shape[i]) for i in range(arr.ndim)]
                                region[z_index] = slice(slab_index*z_chunks, min((slab_index+1)*z_chunks, arr.shape[z_index]))
                                region[y_index] = slice(plane_index*y_chunks, min((plane_index+1)*y_chunks, arr.shape[y_index]))
                                regions.append(tuple(region))
                    else:
                        region = [slice(arr.shape[i]) for i in range(arr.ndim)]
                        region[z_index] = slice(slab_index*z_chunks, min((slab_index+1)*z_chunks, arr.shape[z_index]))
                        regions.append(tuple(region))
                regions = tuple(regions)
                for region_index, region in enumerate(regions):
                    if isinstance(progress, NgffProgressCallback):
                        progress.add_callback_task(f"[green]Writing scale {index+1} of {nscales}, region {region_index+1} of {len(regions)}")
                    print(region)
                    # print(arr[region])
                    # print(arr)
                    # print(arr.dask)
                    # print(type(arr.dask))
                    # print(len(arr.dask))
                    arr_region = arr[region]
                    arr.visualize(f"arr_index_{index}_region_{region_index}.pdf")
                    arr_region.visualize(f"arr_region_index_{index}_region_{region_index}.pdf")
                    # print(arr_region)
                    # print(arr_region.dask)
                    # print(type(arr_region.dask))
                    # print(dir(arr_region.dask))
                    # print(arr.dask.keys())
                    # print(dir(arr_region))
                    # print(arr_region.dask.keys())
                    # print(arr.name)
                    # print(arr_region.name)
                    print(len(arr.dask), len(arr_region.dask), len(arr_region.dask.cull(arr_region.__dask_keys__())))
                    print(len(arr.dask), len(arr_region.dask), len(dask.array.optimize(arr_region.dask, arr_region.__dask_keys__())))
                    # optimized = dask.array.Array(dask.array.optimize(arr_region.__dask_graph__(),
                        # arr_region.__dask_keys__()),
                        # f"{arr_region.name}-optimized", arr_region.chunks,
                        # dtype=arr_region.dtype, meta=arr_region._meta,
                        # shape=arr_region.shape)
                    # optimized = arr_region.copy()
                    # optimized.dask = dask.array.optimize(arr_region.__dask_graph__(), arr_region.__dask_keys__())
                    optimized = dask.array.Array(dask.array.optimize(arr_region.__dask_graph__(),
                        arr_region.__dask_keys__()), arr_region.name,
                        arr_region.chunks, meta=arr_region)
                    print(len(optimized.dask))
                    optimized.visualize(f"optimized_index_{index}_region_{region_index}.pdf")
                    print(len(optimized.dask))
                    print(len(optimized.dask))
                    print(len(optimized.dask))
                    print(len(optimized.dask))
                    print(len(optimized.dask))
                    # print(optimized)
                    # print(optimized)
                    # print(optimized)
                    # print(optimized)
                    # print(optimized)
                    # print(optimized)
                    # print(optimized)
                    dask.array.to_zarr(
                        optimized,
                        # arr_region,
                        zarr_array,
                        region=region,
                        component=path,
                        overwrite=overwrite,
                        compute=True,
                        return_stored=False,
                        **kwargs,
                    )
        else:
            if isinstance(progress, NgffProgressCallback):
                progress.add_callback_task(f"[green]Writing scale {index+1} of {nscales}")
            dask.array.to_zarr(
                arr,
                store,
                component=path,
                overwrite=overwrite,
                compute=True,
                return_stored=False,
                **kwargs,
            )

        # Minimize task graph depth
        if index < nscales - 1 and multiscales.scale_factors and multiscales.method and multiscales.chunks:
            image.data = dask.array.from_zarr(store, component=path)
            next_multiscales = to_multiscales(image,
                scale_factors=multiscales.scale_factors[index:],
                method=multiscales.method,
                chunks=multiscales.chunks,
                progress=progress,
                cache=False)
            multiscales.images[index+1] = next_multiscales.images[1]
            next_image = next_multiscales.images[1]
        elif index < nscales - 1:
            next_image = multiscales.images[index+1]

    zarr.consolidate_metadata(store)
