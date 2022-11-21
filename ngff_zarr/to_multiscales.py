from typing import Union, Optional, Sequence, Mapping, Dict, Tuple, Any, List
from typing_extensions import Literal
from collections.abc import MutableMapping
from dataclasses import dataclass

from zarr.core import Array as ZarrArray
from numpy.typing import ArrayLike
from dask.array.core import Array as DaskArray
import numpy as np

from .methods._dask_image import _downsample_dask_image
from .to_ngff_image import to_ngff_image
from .ngff_image import NgffImage
from .zarr_metadata import Metadata, Axis, Translation, Scale, Dataset
from .methods import Methods

@dataclass
class Multiscales:
    images: List[NgffImage]
    metadata: Metadata

def _ngff_image_scale_factors(ngff_image, min_length):
    sizes = { d: s for d, s in zip(ngff_image.dims, ngff_image.data.shape) }
    scale_factors = []
    dims = ngff_image.dims
    previous = { d: 1 for d in { 'x', 'y', 'z' }.intersection(dims) }
    sizes_array = np.array(list(sizes.values()))
    while np.logical_and(sizes_array > min_length + 1, sizes_array > np.array(ngff_image.data.chunksize)*2).any():
        max_size = np.array(list(sizes.values())).max()
        to_skip = { d: sizes[d] <= max_size / 2 for d in previous.keys() }
        scale_factor = {}
        for idx, dim in enumerate(previous.keys()):
            if to_skip[dim] or sizes[dim] < ngff_image.data.chunksize[idx]:
                scale_factor[dim] = previous[dim]
                continue
            scale_factor[dim] = 2 * previous[dim]

            sizes[dim] = int(sizes[dim] / 2)
        sizes_array = np.array(list(sizes.values()))
        previous = scale_factor
        scale_factors.append(scale_factor)

    return scale_factors

def to_multiscales(
    data: Union[NgffImage, ArrayLike, MutableMapping, str, ZarrArray],
    scale_factors: Union[int, Sequence[Union[Dict[str, int], int]]] = 64,
    method: Optional[Methods] = None,
    chunks: Optional[
        Union[
            Literal["auto"],
            int,
            Tuple[int, ...],
            Tuple[Tuple[int, ...], ...],
            Mapping[Any, Union[None, int, Tuple[int, ...]]],
        ]
    ] = None,
) -> Multiscales:
    """
    Generate multiple resolution scales for the OME-NGFF standard data model.

    data: NgffImage, ArrayLike, ZarrArray, MutableMapping, str
        Multi-dimensional array that provides the image pixel values, or image pixel values + image metadata when an NgffImage.

    scale_factors : int of minimum length, int per scale or dict of spatial dimension int's per scale
        If a single integer, scale factors in spatial dimensions will be increased by a factor of two until this minimum length is reached.
        If a list, integer scale factors to apply uniformly across all spatial dimensions or
        along individual spatial dimensions.
        Examples: 64 or [2, 4] or [{'x': 2, 'y': 4 }, {'x': 5, 'y': 10}]

    chunks : Dask array chunking specification, optional
        Specify the chunking used in each output scale.

    Returns
    -------

    multiscales: Multiscales
        NgffImage for each resolution and NGFF multiscales metadata
    """
    image = data
    if isinstance(data, NgffImage):
        ngff_image = data
    else:
        ngff_image = to_ngff_image(data)

    # IPFS and visualization friendly default chunks
    if "z" in ngff_image.dims:
        default_chunks = 64
    else:
        default_chunks = 256
    default_chunks = {d: default_chunks for d in ngff_image.dims}
    if "t" in ngff_image.dims:
        default_chunks["t"] = 1
    out_chunks = chunks
    if out_chunks is None:
        out_chunks = default_chunks

    da_out_chunks = tuple(out_chunks[d] for d in ngff_image.dims)
    if not isinstance(ngff_image.data, DaskArray):
        if isinstance(ngff_image.data, (ZarrArray, str, MutableMapping)):
            ngff_image.data = dask.array.from_zarr(ngff_image.data, chunks=da_out_chunks)
        else:
            ngff_image.data = dask.array.from_array(ngff_image.data, chunks=da_out_chunks)
    else:
        ngff_image.data = ngff_image.data.rechunk(da_out_chunks)

    if isinstance(scale_factors, int):
        scale_factors = _ngff_image_scale_factors(ngff_image, scale_factors)

    if method is None:
        method = Methods.DASK_IMAGE_GAUSSIAN

    if method is Methods.DASK_IMAGE_GAUSSIAN:
        images = _downsample_dask_image(
            ngff_image, default_chunks, out_chunks, scale_factors, label=False
        )
    elif method is Methods.DASK_IMAGE_NEAREST:
        images = _downsample_dask_image(
            ngff_image, default_chunks, out_chunks, scale_factors, label="nearest"
        )
    elif method is Methods.DASK_IMAGE_MODE:
        images = _downsample_dask_image(
            ngff_image, default_chunks, out_chunks, scale_factors, label="mode"
        )

    axes = []
    for dim in ngff_image.dims:
        unit = None
        if ngff_image.axes_units and dim in ngff_image.axes_units:
            unit = axes_units[dim]
        if dim in {"x", "y", "z"}:
            axis = Axis(name=dim, type="space", unit=unit)
        elif dim == "c":
            axis = Axis(name=dim, type="channel", unit=unit)
        elif dim == "t":
            axis = Axis(name=dim, type="time", unit=unit)
        axes.append(axis)

    datasets = []
    for index, image in enumerate(images):
        path = f"scale{index}/{ngff_image.name}"
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
        dataset = Dataset(
            path=path, coordinateTransformations=coordinateTransformations
        )
        datasets.append(dataset)
    metadata = Metadata(axes=axes, datasets=datasets, name=ngff_image.name)

    multiscales = Multiscales(images, metadata)
    return multiscales
