import numpy as np

from .methods._support import _spatial_dims
from .ngff_image import NgffImage
from .to_ngff_image import to_ngff_image


def cucim_image_to_ngff_image(cuimage) -> NgffImage:
    data = np.array(cuimage)
    dims = tuple(d for d in cuimage.dims.lower())
    spatial_dims = set(dims).intersection(_spatial_dims)
    spatial_dims = [d for d in dims if d in spatial_dims]
    spatial_dims_str = "".join(spatial_dims).upper()
    translation = {d: 0.0 for d in spatial_dims}
    for idx, dim in enumerate(spatial_dims):
        # cucim: Should origin have a dim_order argument like spacing?
        translation[dim] = cuimage.origin[idx]
    spacing = cuimage.spacing(spatial_dims_str)
    scale = {d: 1.0 for d in spatial_dims}
    for idx, dim in enumerate(spatial_dims):
        scale[dim] = spacing[idx]
    return to_ngff_image(data, dims=dims, translation=translation, scale=scale)
