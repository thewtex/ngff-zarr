from dataclasses import dataclass
from typing import Union, Optional, Sequence, Hashable, Mapping, Dict, Tuple, Any, Literal, List
from collections.abc import MutableMapping
from pathlib import Path
from enum import Enum

from zarr.storage import BaseStore
from zarr.core import Array as ZarrArray
from numpy.typing import ArrayLike
import numpy as np
import dask.array
from dask.array.core import Array as DaskArray

from .methods._dask_image import _downsample_dask_image
from .methods._support import _spatial_dims, _NgffImage

AllInteger = Union[
    np.uint8, np.int8, np.uint16, np.int16, np.uint32, np.int32, np.uint64, np.int64
]
AllFloat = Union[np.float32, np.float64]

SupportedDims = Union[
    Literal["c"], Literal["x"], Literal["y"], Literal["z"], Literal["t"]
]
SpatialDims = Union[Literal["x"], Literal["y"], Literal["z"]]
AxesType = Union[Literal["time"], Literal["space"], Literal["channel"]]

_supported_dims = {"c", "x", "y", "z", "t"}
_spatial_dims = {"x", "y", "z"}

class Methods(Enum):
    DASK_IMAGE_GAUSSIAN = "dask_image_gaussian"
    DASK_IMAGE_MODE = "dask_image_mode"
    DASK_IMAGE_NEAREST = "dask_image_nearest"

@dataclass
class Axes:
    name: SupportedDims
    type: AxesType
    unit: str

@dataclass
class Metadata:
    version: str
    name: str
    axes: List[Axes]

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
    axis_units: Optional[Union[Mapping[Hashable, str]]] = None,
    mode: str = "w",
    compute=True,
    encoding=None,
    **kwargs):
    """
    Write an image pixel array and metadata to a Zarr store with the OME-NGFF standard data model.

    store : MutableMapping, str or Path, optional
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

    compute: Boolean
        Compute the result instead of just building the Dask task graph

    axis_names: dict of str, optional
        Long names for the dim axes, e.g. {'x': 'x-axis'} or {'x': 'anterior-posterior'}

    mode : {{"w", "w-", "a", "r+", None}, default: "w"
        Persistence mode: “w” means create (overwrite if exists); “w-” means create (fail if exists);
        “a” means override existing variables (create if does not exist); “r+” means modify existing
        array values only (raise an error if any metadata or shapes would change). The default mode
        is “a” if append_dim is set. Otherwise, it is “r+” if region is set and w- otherwise.

    kwargs :
        Additional keyword arguments to be passed to ``datatree.DataTree.to_zarr``
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

    if compute:
        for image in multiscales:
            image.data = image.data.compute()


    # multiscales = []
    # scale0 = self[self.groups[1]]
    # for name in scale0.ds.data_vars.keys():

    #     ngff_datasets = []
    #     for child in self.children:
    #         image = self[child].ds
    #         scale_transform = []
    #         translate_transform = []
    #         for dim in image.dims:
    #             if len(image.coords[dim]) > 1 and np.issubdtype(image.coords[dim].dtype, np.number):
    #                 scale_transform.append(
    #                     float(image.coords[dim][1] - image.coords[dim][0])
    #                 )
    #             else:
    #                 scale_transform.append(1.0)
    #             if len(image.coords[dim]) > 0 and np.issubdtype(image.coords[dim].dtype, np.number):
    #                 translate_transform.append(float(image.coords[dim][0]))
    #             else:
    #                 translate_transform.append(0.0)

    #         ngff_datasets.append(
    #             {
    #                 "path": f"{self[child].name}/{name}",
    #                 "coordinateTransformations": [
    #                     {
    #                         "type": "scale",
    #                         "scale": scale_transform,
    #                     },
    #                     {
    #                         "type": "translation",
    #                         "translation": translate_transform,
    #                     },
    #                 ],
    #             }
    #         )

    #     image = scale0.ds
    #     axes = []
    #     for axis in image.dims:
    #         if axis == "t":
    #             axes.append({"name": "t", "type": "time"})
    #         elif axis == "c":
    #             axes.append({"name": "c", "type": "channel"})
    #         else:
    #             axes.append({"name": axis, "type": "space"})
    #         if "units" in image.coords[axis].attrs:
    #             axes[-1]["unit"] = image.coords[axis].attrs["units"]

    #     multiscales.append(
    #         {
    #             "@type": "ngff:Image",
    #             "version": "0.4",
    #             "name": name,
    #             "axes": axes,
    #             "datasets": ngff_datasets,
    #         }
    #     )

    # NGFF v0.4 metadata
    # ngff_metadata = {"multiscales": multiscales, "multiscaleSpatialImageVersion": 1}
    # self.ds = self.ds.assign_attrs(**ngff_metadata)

    # super().to_zarr(store, **kwargs)