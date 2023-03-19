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

def _array_split(ary, indices_or_sections, axis=0):
    """
    *** Taken from NumPy, adapted for Dask Array's

    Split an array into multiple sub-arrays.

    Please refer to the ``split`` documentation.  The only difference
    between these functions is that ``array_split`` allows
    `indices_or_sections` to be an integer that does *not* equally
    divide the axis. For an array of length l that should be split
    into n sections, it returns l % n sub-arrays of size l//n + 1
    and the rest of size l//n.

    See Also
    --------
    split : Split array into multiple sub-arrays of equal size.

    Examples
    --------
    >>> x = np.arange(8.0)
    >>> np.array_split(x, 3)
    [array([0.,  1.,  2.]), array([3.,  4.,  5.]), array([6.,  7.])]

    >>> x = np.arange(9)
    >>> np.array_split(x, 4)
    [array([0, 1, 2]), array([3, 4]), array([5, 6]), array([7, 8])]

    """
    try:
        Ntotal = ary.shape[axis]
    except AttributeError:
        Ntotal = len(ary)
    try:
        # handle array case.
        Nsections = len(indices_or_sections) + 1
        div_points = [0] + list(indices_or_sections) + [Ntotal]
    except TypeError:
        # indices_or_sections is a scalar, not an array.
        Nsections = int(indices_or_sections)
        if Nsections <= 0:
            raise ValueError('number sections must be larger than 0.') from None
        Neach_section, extras = divmod(Ntotal, Nsections)
        section_sizes = ([0] +
                         extras * [Neach_section+1] +
                         (Nsections-extras) * [Neach_section])
        div_points = np.array(section_sizes, dtype=np.intp).cumsum()

    sub_arys = []
    sary = dask.array.swapaxes(ary, axis, 0)
    for i in range(Nsections):
        st = div_points[i]
        end = div_points[i + 1]
        sub_arys.append(dask.array.swapaxes(sary[st:end], axis, 0))

    return sub_arys

def to_ngff_zarr(
    store: Union[MutableMapping, str, Path, BaseStore],
    multiscales: Multiscales,
    compute: bool = True,
    overwrite: bool = True,
    chunk_store: Optional[Union[MutableMapping, str, Path, BaseStore]] = None,
    **kwargs,
) -> None:
    """
    Write an image pixel array and metadata to a Zarr store with the OME-NGFF standard data model.

    store : MutableMapping, str or Path, zarr.storage.BaseStore
        Store or path to directory in file system.

    multiscales: Multiscales
        Multiscales OME-NGFF image pixel data and metadata. Can be generated with ngff_zarr.to_multiscales.

    compute: Boolean, optional
        Compute the result instead of just building the Dask task graph.

    overwrite : bool, optional
        If True, delete any pre-existing data in `store` before creating groups.

    chunk_store : MutableMapping, str or Path, zarr.storage.BaseStore, optional
        Separate storage for chunks. If not provided, `store` will be used
        for storage of both chunks and metadata.

    **kwargs:
        Passed to the zarr.creation.create() function, e.g., compression options.


    Returns
    -------

    arrays: tuple of dask Arrays

    """

    root = zarr.group(store, overwrite=overwrite, chunk_store=chunk_store)

    from rich import print

    multiscales_bytes = reduce(lambda x,y: x+y.data.nbytes, multiscales.images, 0)
    large_serialization = False
    if multiscales_bytes > config.memory_limit:
        large_serialization = True
        if not compute:
            raise ValueError('Large data requires compute=True')
        # TODO: Most definitely needs to be refined
        limit = int(np.ceil(0.5*config.memory_limit))

        scales_split_paths = []
        for index in range(len(multiscales.images)):
            image = multiscales.images[index]
            arr = image.data
            slab_slices = min(int(np.ceil(limit / arr[0, ...].nbytes)), arr.shape[0])
            slab_slices = max(slab_slices, arr.chunks[0][0])
            split = _array_split(arr, arr.shape[0]//slab_slices)

            split_arrays = []
            split_paths = []
            for slab_index, slab in enumerate(split):
                path = multiscales.metadata.datasets[index].path + f".tmp.{slab_index}"
                split_paths.append(path)
                path_group = root.create_group(path)
                path_group.attrs["_ARRAY_DIMENSIONS"] = image.dims
                arr = dask.array.to_zarr(
                    slab,
                    store,
                    component=path,
                    overwrite=True,
                    compute=True,
                    return_stored=True,
                    **kwargs,
                )
                split_arrays.append(arr)
            scales_split_paths.append(split_paths)

            print(split_arrays)
            print(multiscales)

            chunks = image.data.chunks
            image.data = dask.array.concatenate(split_arrays)
            if slab_slices < arr.chunks[0][0]:
                image.data = image.data.rechunk(chunks)

            if index < len(multiscales.images) - 1:
                next_multiscales = to_multiscales(multiscales.images[0], scale_factors=multiscales.scale_factors, method=multiscales.method, chunks=multiscales.chunks)
                multiscales.images[index+1] = next_multiscales.images[index+1]

    metadata_dict = asdict(multiscales.metadata)
    metadata_dict["@type"] = "ngff:Image"
    root.attrs["multiscales"] = [metadata_dict]

    arrays = []
    for index, image in enumerate(multiscales.images):
        arr = image.data
        path = multiscales.metadata.datasets[index].path
        path_group = root.create_group(path)
        path_group.attrs["_ARRAY_DIMENSIONS"] = image.dims
        arr = dask.array.to_zarr(
            arr,
            store,
            component=path,
            overwrite=overwrite,
            compute=compute,
            return_stored=True,
            **kwargs,
        )
        arrays.append(arr)

    if large_serialization:
        for index in range(len(multiscales.images)):
            for path in scales_split_paths[index]:
                zarr.storage.rmdir(root.store, path)
                zarr.storage.rmdir(root.chunk_store, path)

    zarr.consolidate_metadata(store)

    return tuple(arrays)
