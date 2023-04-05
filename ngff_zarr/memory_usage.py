from typing import Set
from .ngff_image import NgffImage

def memory_usage(image: NgffImage, constrained_dims: Set[str] = set()) -> int:
    """Approximate array partition task graph memory usage in bytes.

    Assumes tasks will have the same memory usage as an array chunk."""
    arr = image.data
    dims = image.dims
    chunk = [c[0] for c in arr.chunks]
    chunksize = 1
    for dim in range(arr.ndim):
        if dims[dim] in constrained_dims:
            continue
        chunksize *= chunk[dim] * arr.itemsize
    ntasks = len(arr.dask)
    return ntasks*chunksize

