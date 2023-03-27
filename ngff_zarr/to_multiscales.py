from typing import Union, Optional, Sequence, Mapping, Dict, Tuple, Any, List
from typing_extensions import Literal
from collections.abc import MutableMapping
from dataclasses import dataclass
import time
import shutil
from pathlib import Path
import atexit
import signal

from zarr.core import Array as ZarrArray
from numpy.typing import ArrayLike
from dask.array.core import Array as DaskArray
import numpy as np
import zarr
import dask

from .methods._dask_image import _downsample_dask_image
from .methods._itk import _downsample_itk_bin_shrink, _downsample_itk_gaussian, _downsample_itk_label
from .to_ngff_image import to_ngff_image
from .ngff_image import NgffImage
from .zarr_metadata import Metadata, Axis, Translation, Scale, Dataset
from .methods import Methods
from .config import config
from .rich_dask_progress import NgffProgress, NgffProgressCallback

_spatial_dims = {'x', 'y', 'z'}

@dataclass
class Multiscales:
    images: List[NgffImage]
    metadata: Metadata
    scale_factors: Optional[Union[int, Sequence[Union[Dict[str, int], int]]]] = None
    method: Optional[Methods] = None
    chunks: Optional[
        Union[
            int,
            Tuple[int, ...],
            Tuple[Tuple[int, ...], ...],
            Mapping[Any, Union[None, int, Tuple[int, ...]]],
        ]
    ] = None

def _array_split(ary, indices_or_sections, axis=0):
    """
    *** From NumPy, adapted for Dask Array's

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

def _ngff_image_scale_factors(ngff_image, min_length, out_chunks):
    sizes = { d: s for d, s in zip(ngff_image.dims, ngff_image.data.shape) if d in _spatial_dims }
    scale_factors = []
    dims = ngff_image.dims
    previous = { d: 1 for d in _spatial_dims.intersection(dims) }
    sizes_array = np.array(list(sizes.values()))
    sizes = { d: s for d, s in zip(ngff_image.dims, ngff_image.data.shape) if d in _spatial_dims }
    double_chunks = np.array([2*out_chunks[d] for d in _spatial_dims.intersection(out_chunks)])
    while (sizes_array > double_chunks).any():
        max_size = np.array(list(sizes.values())).max()
        to_skip = { d: sizes[d] <= max_size / 2 for d in previous.keys() }
        scale_factor = {}
        for dim in previous.keys():
            if to_skip[dim] or sizes[dim] / 2 < out_chunks[dim]:
                scale_factor[dim] = previous[dim]
                continue
            scale_factor[dim] = 2 * previous[dim]

            sizes[dim] = int(sizes[dim] / 2)
        sizes_array = np.array(list(sizes.values()))
        previous = scale_factor
        # There should be sufficient data in the result for statistics, etc.
        if (np.prod(sizes_array) / min_length) < 2:
            break
        scale_factors.append(scale_factor)

    return scale_factors

def _large_image_serialization(image: NgffImage, progress: Optional[Union[NgffProgress, NgffProgressCallback]]):
    # TODO: Most definitely needs to be refined
    limit = int(np.ceil(0.25*config.memory_limit))
    if "z" in image.dims:
        optimized_chunks = 512
    else:
        optimized_chunks = 1024
    base_path = f"{image.name}-cache-{time.time()}"

    cache_store = config.cache_store
    base_path_removed = False
    def remove_from_cache_store(sig_id, frame):
        nonlocal base_path_removed
        if not base_path_removed:
            if isinstance(cache_store, zarr.storage.DirectoryStore):
                full_path = Path(cache_store.dir_path()) / base_path
                if full_path.exists():
                    shutil.rmtree(full_path, ignore_errors=True)
            else:
                zarr.storage.rmdir(cache_store, base_path)
            base_path_removed = True
    atexit.register(remove_from_cache_store, None, None)
    signal.signal(signal.SIGTERM, remove_from_cache_store)
    signal.signal(signal.SIGINT, remove_from_cache_store)

    data = image.data

    dims = list(image.dims)
    x_index = dims.index('x')
    y_index = dims.index('y')

    rechunks = {}
    for index, dim in enumerate(dims):
        if dim == 't':
            rechunks[index] = 1
        elif dim == 'c':
            rechunks[index] = 1
        else:
            rechunks[index] = min(optimized_chunks, data.shape[index])

    if 'z' in dims:
        z_index = dims.index('z')
        slice_bytes = data.dtype.itemsize * data.shape[x_index] * data.shape[y_index]

        slab_slices = min(int(np.ceil(limit / slice_bytes)), data.shape[z_index])
        if optimized_chunks < data.shape[z_index]:
            slab_slices = min(slab_slices, optimized_chunks)
        rechunks[z_index] = slab_slices

        split = _array_split(data, data.shape[z_index]//slab_slices, z_index)

        if progress:
            progress.add_cache_task(f"[blue]Caching z-slabs", len(split))
        split_arrays = []
        for slab_index, slab in enumerate(split):
            path = base_path + f"/slab/{slab_index}"
            if progress:
                if isinstance(progress, NgffProgressCallback):
                    progress.add_cache_callback_task(f"[blue]Caching z-slabs {slab_index+1} of {len(split)}")
                progress.update_cache_task_completed((slab_index+1))
            slab = slab.rechunk(rechunks)
            dask.array.to_zarr(
                slab,
                cache_store,
                component=path,
                overwrite=True,
                compute=True,
                return_stored=False,
            )
            arr = dask.array.from_zarr(cache_store, component=path)
            split_arrays.append(arr)
        data = dask.array.concatenate(split_arrays)
        if optimized_chunks < data.shape[z_index] and slab_slices < optimized_chunks:
            rechunks[z_index] = optimized_chunks
            data = data.rechunk(rechunks)
            path = base_path + f"/optimized_chunks"
            if progress and isinstance(progress, NgffProgressCallback):
                progress.add_cache_callback_task(f"[blue]Caching z rechunk")
            dask.array.to_zarr(
                data,
                cache_store,
                component=path,
                overwrite=True,
                compute=True,
                return_stored=False,
            )
            data = dask.array.from_zarr(cache_store, component=path)
        else:
            data = data.rechunk(rechunks)
    else:
        data = data.rechunk(rechunks)
        # TODO: Do we need to split / concat very large 2D images
        path = base_path + f"/optimized_chunks"
        if progress:
            progress.add_cache_callback_task(f"[blue]Caching optimized chunks")
        dask.array.to_zarr(
            data,
            cache_store,
            component=path,
            overwrite=True,
            compute=True,
            return_stored=False,
        )
        data = dask.array.from_zarr(cache_store, component=path)

    image.data = data
    return image

def to_multiscales(
    data: Union[NgffImage, ArrayLike, MutableMapping, str, ZarrArray],
    scale_factors: Union[int, Sequence[Union[Dict[str, int], int]]] = 128,
    method: Optional[Methods] = None,
    chunks: Optional[
        Union[
            int,
            Tuple[int, ...],
            Tuple[Tuple[int, ...], ...],
            Mapping[Any, Union[None, int, Tuple[int, ...]]],
        ]
    ] = None,
    progress: Optional[Union[NgffProgress, NgffProgressCallback]] = None,
    cache: Optional[bool] = None,
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

    cache : bool, optional
        Cache intermediate results to disk to limit memory consumption. If None, the default, determine based on ngff_zarr.config.memory_limit.

    progress:
        Optional progress logger

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
        default_chunks = 128
    else:
        default_chunks = 256
    default_chunks = {d: default_chunks for d in ngff_image.dims}
    if "t" in ngff_image.dims:
        default_chunks["t"] = 1
    out_chunks = chunks
    if out_chunks is None:
        out_chunks = default_chunks
    elif isinstance(out_chunks, int):
        out_chunks = {d: chunks for d in ngff_image.dims}
    elif isinstance(out_chunks, tuple):
        out_chunks = {d: chunks[i] for i, d in enumerate(ngff_image.dims)}

    da_out_chunks = tuple(out_chunks[d] for d in ngff_image.dims)
    if not isinstance(ngff_image.data, DaskArray):
        if isinstance(ngff_image.data, (ZarrArray, str, MutableMapping)):
            ngff_image.data = dask.array.from_zarr(ngff_image.data)
        else:
            ngff_image.data = dask.array.from_array(ngff_image.data)

    if isinstance(scale_factors, int):
        scale_factors = _ngff_image_scale_factors(ngff_image, scale_factors, out_chunks)

    if cache is None and ngff_image.data.nbytes > config.memory_limit or cache:
        ngff_image = _large_image_serialization(ngff_image, progress)

    ngff_image.data = ngff_image.data.rechunk(da_out_chunks)

    if method is None:
        method = Methods.DASK_IMAGE_GAUSSIAN

    if method is Methods.ITK_BIN_SHRINK:
        images = _downsample_itk_bin_shrink(
            ngff_image, default_chunks, out_chunks, scale_factors
        )
    elif method is Methods.ITK_GAUSSIAN:
        images = _downsample_itk_gaussian(
            ngff_image, default_chunks, out_chunks, scale_factors
        )
    elif method is Methods.DASK_IMAGE_GAUSSIAN:
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

    multiscales = Multiscales(images, metadata, scale_factors, method, out_chunks)
    return multiscales
