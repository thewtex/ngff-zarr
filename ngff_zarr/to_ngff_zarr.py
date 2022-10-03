from typing import Union, Optional, Sequence, Hashable, Mapping, Dict, Tuple, Any, List
from typing_extensions import Literal
from collections.abc import MutableMapping
from pathlib import Path
from dataclasses import asdict

from zarr.storage import BaseStore
from zarr.core import Array as ZarrArray
import zarr
from numpy.typing import ArrayLike
import dask.array
from dask.array.core import Array as DaskArray

from .methods._dask_image import _downsample_dask_image
from .ngff_image import NgffImage
from .to_ngff_image import to_ngff_image
from .methods import Methods
from .zarr_metadata import Metadata, Axis, Translation, Scale, Dataset


def to_ngff_zarr(
    store: Union[MutableMapping, str, Path, BaseStore],
    data: Union[NgffImage, ArrayLike, MutableMapping, str, ZarrArray],
    scale_factors: Sequence[Union[Dict[str, int], int]],
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
    compute: bool = True,
    overwrite: bool = True,
    chunk_store: Optional[Union[MutableMapping, str, Path, BaseStore]] = None,
    **kwargs,
) -> Tuple[List[DaskArray], Metadata]:
    """
    Write an image pixel array and metadata to a Zarr store with the OME-NGFF standard data model.

    store : MutableMapping, str or Path, zarr.storage.BaseStore
        Store or path to directory in file system

    data: NgffImage, ArrayLike, ZarrArray, MutableMapping, str
        Multi-dimensional array that provides the image pixel values, or image pixel values + image metadata when an NgffImage.

    scale_factors : int per scale or dict of spatial dimension int's per scale
        Integer scale factors to apply uniformly across all spatial dimensions or
        along individual spatial dimensions.
        Examples: [2, 2] or [{'x': 2, 'y': 4 }, {'x': 5, 'y': 10}]

    chunks : Dask array chunking specification, optional
        Specify the chunking used in each output scale.

    compute: Boolean, optional
        Compute the result instead of just building the Dask task graph

    overwrite : bool, optional
        If True, delete any pre-existing data in `store` before creating groups.

    chunk_store : MutableMapping, str or Path, zarr.storage.BaseStore, optional
        Separate storage for chunks. If not provided, `store` will be used
        for storage of both chunks and metadata.

    **kwargs:
        Passed to the zarr.creation.create() function, e.g., compression options.


    Returns
    -------

    (images, metadata): list(NgffImage), Metadata
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

    if not isinstance(ngff_image.data, DaskArray):
        if isinstance(ngff_image.data, (ZarrArray, str, MutableMapping)):
            ngff_image.data = dask.array.from_zarr(ngff_image.data, chunks=out_chunks)
        else:
            ngff_image.data = dask.array.from_array(ngff_image.data, chunks=out_chunks)

    if method is None:
        method = Methods.DASK_IMAGE_GAUSSIAN

    if method is Methods.DASK_IMAGE_GAUSSIAN:
        multiscales = _downsample_dask_image(
            ngff_image, default_chunks, out_chunks, scale_factors, label=False
        )
    elif method is Methods.DASK_IMAGE_NEAREST:
        multiscales = _downsample_dask_image(
            ngff_image, default_chunks, out_chunks, scale_factors, label="nearest"
        )
    elif method is Methods.DASK_IMAGE_MODE:
        multiscales = _downsample_dask_image(
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
    for index, image in enumerate(multiscales):
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

    root = zarr.group(store, overwrite=overwrite, chunk_store=chunk_store)
    metadata_dict = asdict(metadata)
    metadata_dict["@type"] = "ngff:Image"
    root.attrs["multiscales"] = [metadata_dict]

    data = []
    for index, dataset in enumerate(datasets):
        arr = multiscales[index].data
        path = dataset.path
        path_group = root.create_group(path)
        path_group.attrs["_ARRAY_DIMENSIONS"] = ngff_image.dims
        arr = dask.array.to_zarr(
            arr,
            store,
            component=path,
            overwrite=overwrite,
            compute=compute,
            return_stored=True,
            **kwargs,
        )
        data.append(arr)

    return data, metadata
