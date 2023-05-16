from typing import Set
from .ngff_image import NgffImage
from dask.array import take

def task_count(image: NgffImage, constrained_dims: Set[str] = set()) -> int:
    """Approximate dask array partition task count."""
    arr = image.data
    dims = image.dims
    slices = []
    for index, dim in enumerate(dims):
        if dim in constrained_dims:
            slices.append(slice(0))
        else:
            slices.append(slice(arr.shape[index]))
    return len(arr[tuple(slices)].dask)

