from typing import Union, Optional
from collections.abc import MutableMapping
from pathlib import Path
from dataclasses import asdict
from functools import reduce

from zarr.storage import BaseStore
import zarr
import dask.array
import numpy as np

from .to_multiscales import Multiscales, to_multiscales
from .config import config
from .rich_dask_progress import NgffProgress, NgffProgressCallback

def to_ngff_zarr(
    store: Union[MutableMapping, str, Path, BaseStore],
    multiscales: Multiscales,
    compute: bool = True,
    overwrite: bool = True,
    chunk_store: Optional[Union[MutableMapping, str, Path, BaseStore]] = None,
    progress: Optional[NgffProgress] = None,
    **kwargs,
) -> None:
    """
    Write an image pixel array and metadata to a Zarr store with the OME-NGFF standard data model.

    store : MutableMapping, str or Path, zarr.storage.BaseStore
        Store or path to directory in file system.

    multiscales: Multiscales
        Multiscales OME-NGFF image pixel data and metadata. Can be generated with ngff_zarr.to_multiscales.

    compute: Boolean, optional
        Compute the result instead of just building the Dask task graph. Recommended for large data.

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
    for index in range(nscales):
        if progress:
            progress.update_multiscales_task_completed((index+1))
            if compute and isinstance(progress, NgffProgressCallback):
                progress.add_multiscales_callback_task(f"[green]Wring scale {index+1} of {nscales}")
        image = multiscales.images[index]
        arr = image.data
        path = multiscales.metadata.datasets[index].path
        path_group = root.create_group(path)
        path_group.attrs["_ARRAY_DIMENSIONS"] = image.dims
        dask.array.to_zarr(
            arr,
            store,
            component=path,
            overwrite=overwrite,
            compute=compute,
            return_stored=False,
            **kwargs,
        )

        remaining_bytes = reduce(lambda x,y: x+y.data.nbytes, multiscales.images[index:], 0)
        # Minimize task graph depth
        if remaining_bytes > config.memory_limit and index < nscales - 1 and index > 0 and compute and multiscales.scale_factors and multiscales.method and multiscales.chunks:
            arr = dask.array.from_zarr(store, component=path)
            out_chunks_list = []
            for dim in image.dims:
                if dim in multiscales.chunks:
                    out_chunks_list.append(multiscales.chunks[dim])
                else:
                    out_chunks_list.append(1)
            image.data = arr.rechunk(tuple(out_chunks_list))

            next_multiscales = to_multiscales(image,
                    multiscales.scale_factors[index:], multiscales.method,
                    multiscales.chunks,
                    progress=progress)
            multiscales.images[index+1] = next_multiscales.images[1]

    zarr.consolidate_metadata(store)