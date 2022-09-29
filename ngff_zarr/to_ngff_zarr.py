from curses import meta
from typing import Union, Optional, Sequence, Hashable, Mapping, Dict, Tuple, Any, List
from typing_extensions import Literal
from collections.abc import MutableMapping
from pathlib import Path
from dataclasses import asdict

from zarr.storage import BaseStore
from zarr.core import Array as ZarrArray
import zarr
from numpy.typing import ArrayLike
import numpy as np
import dask.array
from dask.array.core import Array as DaskArray

from .methods._dask_image import _downsample_dask_image
from .methods._support import _spatial_dims, _NgffImage
from .methods import Methods
from .metadata import Metadata, Axis, Translation, Scale, Dataset

def to_ngff_zarr(store: Union[MutableMapping, str, Path, BaseStore],
    data: Union[ArrayLike, MutableMapping, str, ZarrArray],
    scale_factors: Sequence[Union[Dict[str, int], int]],
    dims: Optional[Sequence[Union["t", "z", "y", "x", "c"]]] = None,
    scale: Optional[Union[Mapping[Hashable, float]]] = None,
    translation: Optional[Union[Mapping[Hashable, float]]] = None,
    name: str = "image",
    method: Optional[Methods] = None,
    chunks: Optional[
        Union[
            Literal['auto'],
            int,
            Tuple[int, ...],
            Tuple[Tuple[int, ...], ...],
            Mapping[Any, Union[None, int, Tuple[int, ...]]],
        ]
    ] = None,
    compute: bool = True,
    axes_units: Optional[Union[Mapping[Hashable, str]]] = None,
    overwrite: bool = True,
    chunk_store: Optional[Union[MutableMapping, str, Path, BaseStore]] = None,
    **kwargs,
    ) -> Tuple[List[DaskArray], Metadata]:
    """
    Write an image pixel array and metadata to a Zarr store with the OME-NGFF standard data model.

    store : MutableMapping, str or Path, zarr.storage.BaseStore
        Store or path to directory in file system

    data: ArrayLike, ZarrArray, MutableMapping, str
        Multi-dimensional array that provides the image pixel values. It can be a numpy.ndarray
         or another type that behaves like a numpy.ndarray, i.e. an ArrayLike.
         If a ZarrArray, MutableMapping, or str, it will be loaded into Dask lazily
         as a zarr Array.

    scale_factors : int per scale or dict of spatial dimension int's per scale
        Integer scale factors to apply uniformly across all spatial dimensions or
        along individual spatial dimensions.
        Examples: [2, 2] or [{'x': 2, 'y': 4 }, {'x': 5, 'y': 10}]

    dims: sequence of hashable, optional
        Tuple specifying the data dimensions.
        Values should drawn from: {'t', 'z', 'y', 'x', 'c'} for time, third spatial direction
        second spatial direction, first spatial dimension, and channel or
        component, respectively spatial dimension, and time, respectively.

    scale: dict of floats, optional
        Pixel spacing for the spatial dims

    translation: dict of floats, optional
        Origin or offset of the center of the first pixel.

    name: str, optional
        Name of the resulting xarray DataArray

    method : ngff_zarr.Methods, optional
        Method to reduce the input image for a multiscale representation.

    chunks : Dask array chunking specification, optional
        Specify the chunking used in each output scale.

    compute: Boolean, optional
        Compute the result instead of just building the Dask task graph

    axes_units: dict of str, optional
        Units to associate with the axes. Should be drawn from UDUNITS-2, enumerated at 
        https://ngff.openmicroscopy.org/latest/#axes-md

    overwrite : bool, optional
        If True, delete any pre-existing data in `store` before creating groups.
    
    chunk_store : MutableMapping, str or Path, zarr.storage.BaseStore, optional
        Separate storage for chunks. If not provided, `store` will be used
        for storage of both chunks and metadata.

    **kwargs:
        Passed to the zarr.creation.create() function, e.g., compression options.


    Returns
    -------

    (data, metadata): list(dask.Array), Metadata
        Arrays for each scale and NGFF multiscales metadata
    """

    ndim = data.ndim
    if dims is None:
        if ndim < 4:
            dims = ("z", "y", "x")[-ndim:]
        elif ndim < 5:
            dims = ("z", "y", "x", "c")
        elif ndim < 6:
            dims = ("t", "z", "y", "x", "c")
        else:
            raise ValueError("Unsupported dimension: " + str(ndim))
    else:
        _supported_dims = {"c", "x", "y", "z", "t"}
        if not set(dims).issubset(_supported_dims):
            raise ValueError("dims not valid") 

    if scale is None:
        scale = {dim: 1.0 for dim in dims if dim in _spatial_dims}

    if translation is None:
        translation = {dim: 0.0 for dim in dims if dim in _spatial_dims}

    if method is None:
        method = Methods.DASK_IMAGE_GAUSSIAN

    # IPFS and visualization friendly default chunks
    if "z" in dims:
        default_chunks = 64
    else:
        default_chunks = 256
    default_chunks = {d: default_chunks for d in dims}
    if "t" in dims:
        default_chunks["t"] = 1
    out_chunks = chunks
    if out_chunks is None:
        out_chunks = default_chunks

    if not isinstance(data, DaskArray):
        if isinstance(data, (ZarrArray, str, MutableMapping)):
            data = dask.array.from_zarr(data, chunks=out_chunks)
        else:
            data = dask.array.from_array(data, chunks=out_chunks)

    ngff_image = _NgffImage(data, dims, scale, translation)

    if method is None:
        method = Methods.DASK_IMAGE_GAUSSIAN

    if method is Methods.DASK_IMAGE_GAUSSIAN:
        multiscales = _downsample_dask_image(ngff_image, default_chunks, out_chunks, scale_factors, label=False)
    # elif method is Methods.DASK_IMAGE_NEAREST:
    #     data_objects = _downsample_dask_image(current_input, default_chunks, out_chunks, scale_factors, data_objects, image, label='nearest')
    # elif method is Methods.DASK_IMAGE_MODE:
    #     data_objects = _downsample_dask_image(current_input, default_chunks, out_chunks, scale_factors, data_objects, image, label='mode')

    axes = []
    for dim in dims:
        unit = None
        if axes_units and dim in axes_units:
            unit = axes_units[dim]
        if dim in {'x', 'y', 'z'}:
            axis = Axis(name=dim, type='space', unit=unit)
        elif dim == 'c':
            axis = Axis(name=dim, type='channel', unit=unit)
        elif dim == 't':
            axis = Axis(name=dim, type='time', unit=unit)
        axes.append(axis)
    
    datasets = []
    for index, image in enumerate(multiscales):
        path = f"scale{index}/{name}"
        scale = []
        for dim in image.dims:
            if dim in image.scale:
                scale.append(image.scale[dim])
            else:
                scale.append(1.0)
        translation = []
        for dim in image.dims:
            if dim in image.translation:
                translation.append(image.translation[dim])
            else:
                translation.append(1.0)
        coordinateTransformations = [Scale(scale), Translation(translation)]
        dataset = Dataset(path=path, coordinateTransformations=coordinateTransformations)
        datasets.append(dataset)
    metadata = Metadata(axes=axes, datasets=datasets, name=name)

    root = zarr.group(store, overwrite=overwrite, chunk_store=chunk_store)
    metadata_dict = asdict(metadata)
    metadata_dict['@type'] = "ngff:Image"
    root.attrs['multiscales'] = [metadata_dict]

    data = []
    for index, dataset in enumerate(datasets):
        arr = multiscales[index].data
        path = dataset.path
        path_group = root.create_group(path)
        path_group.attrs["_ARRAY_DIMENSIONS"] = ngff_image.dims
        arr = dask.array.to_zarr(arr, store, component=path, overwrite=overwrite, compute=compute, return_stored=True, **kwargs)
        data.append(arr)

    return data, metadata