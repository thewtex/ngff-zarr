from typing import List
import copy


from ..ngff_image import NgffImage

_spatial_dims = {"x", "y", "z"}


def _spatial_dims_last(ngff_image: NgffImage) -> NgffImage:
    dims = list(ngff_image.dims)
    spatial_dims = [dim for dim in dims if dim in _spatial_dims]

    dims_spatial_channel = len(spatial_dims)
    if dims[-1] == "c":
        dims_spatial_channel += 1

    # If spatial dimensions are already last (and 'c' can be last), return the original image
    if all(dim in dims[-dims_spatial_channel:] for dim in spatial_dims + ["c"]):
        return ngff_image

    # Move spatial dimensions to the end, keeping 'c' as the last pre-spatial dimension if present
    non_spatial_dims = [dim for dim in dims if dim not in _spatial_dims]
    if "c" in non_spatial_dims:
        non_spatial_dims.remove("c")
        new_dims = non_spatial_dims + ["c"] + spatial_dims
    else:
        new_dims = non_spatial_dims + spatial_dims

    new_order = [dims.index(dim) for dim in new_dims]

    if tuple(new_dims) == tuple(ngff_image.dims):
        return ngff_image

    # Reorder the data array
    reordered_data = ngff_image.data.transpose(new_order)

    result = copy.copy(ngff_image)
    result.data = reordered_data
    result.dims = tuple(new_dims)

    return result


def _spatial_dims_last_zyx(ngff_image: NgffImage) -> NgffImage:
    dims = list(ngff_image.dims)
    spatial_dims = [dim for dim in dims if dim in _spatial_dims]

    # If spatial dimensions are already zyx, return the original image
    if spatial_dims == ["z", "y", "x"] or spatial_dims == ["y", "x"]:
        dims_spatial_channel = len(spatial_dims)
        if dims[-1] == "c":
            dims_spatial_channel += 1

        # If spatial dimensions are already last (and 'c' can be last), return the original image
        if all(dim in dims[-dims_spatial_channel:] for dim in spatial_dims + ["c"]):
            return ngff_image

    # Move spatial dimensions to the end, keeping 'c' as the last pre-spatial dimension if present
    non_spatial_dims = [dim for dim in dims if dim not in _spatial_dims]
    new_spatial_dims = ["z", "y", "x"][-len(spatial_dims) :]
    if "c" in non_spatial_dims:
        non_spatial_dims.remove("c")
        new_dims = non_spatial_dims + ["c"] + new_spatial_dims
    else:
        new_dims = non_spatial_dims + new_spatial_dims

    new_order = [dims.index(dim) for dim in new_dims]

    if tuple(new_dims) == tuple(ngff_image.dims):
        return ngff_image

    # Reorder the data array
    reordered_data = ngff_image.data.transpose(new_order)

    result = copy.copy(ngff_image)
    result.data = reordered_data
    result.dims = tuple(new_dims)

    return result


def _channel_dim_last(ngff_image: NgffImage) -> NgffImage:
    if "c" not in ngff_image.dims or ngff_image.dims[-1] == "c":
        return ngff_image

    dims = list(ngff_image.dims)
    # Move 'c' dimension to the end
    dims.remove("c")
    dims.append("c")

    # Reorder the data array
    new_order = [ngff_image.dims.index(dim) for dim in dims]
    reordered_data = ngff_image.data.transpose(new_order)

    result = copy.copy(ngff_image)
    result.data = reordered_data
    result.dims = tuple(dims)

    return result


def _dim_scale_factors(dims, scale_factor, previous_dim_factors):
    if isinstance(scale_factor, int):
        result_scale_factors = {
            dim: int(scale_factor / previous_dim_factors[dim])
            for dim in dims
            if dim in _spatial_dims
        }
    else:
        result_scale_factors = {
            d: int(scale_factor[d] / previous_dim_factors[d]) for d in scale_factor
        }
    return result_scale_factors


def _align_chunks(previous_image, default_chunks, dim_factors):
    block_0_shape = [c[0] for c in previous_image.data.chunks]

    rechunk = False
    aligned_chunks = {}
    for dim, factor in dim_factors.items():
        dim_index = previous_image.dims.index(dim)
        if block_0_shape[dim_index] % factor:
            aligned_chunks[dim] = block_0_shape[dim_index] * factor
            rechunk = True
        else:
            aligned_chunks[dim] = default_chunks[dim]
    if rechunk:
        dask_aligned_chunks = {
            previous_image.dims.index(dim): aligned_chunks[dim]
            for dim in aligned_chunks
        }
        previous_image.data = previous_image.data.rechunk(dask_aligned_chunks)

    return previous_image


def _compute_sigma(shrink_factors: List[int]) -> List[float]:
    """Compute Gaussian kernel sigma values in pixel units for downsampling.
    sigma = sqrt((k^2 - 1^2)/(2*sqrt(2*ln(2)))^2)
    Ref https://discourse.itk.org/t/resampling-to-isotropic-signal-processing-theory/1403/16
    https://doi.org/10.1007/978-3-319-24571-3_81
    http://discovery.ucl.ac.uk/1469251/1/scale-factor-point-5.pdf

    Note: If input spacing / output sigma in physical units, the function would be
        sigma = sqrt((input_spacing^2*(k^2 - 1^2))/(2*sqrt(2*ln(2)))^2)

    input spacings: List
        Input image physical spacings in xyzt order

    shrink_factors: List
        Shrink ratio along each axis in xyzt order

    result: List
        Standard deviation of Gaussian kernel along each axis in xyzt order
    """
    import math

    denominator = (2 * ((2 * math.log(2)) ** 0.5)) ** 2
    return [((factor**2 - 1**2) / denominator) ** 0.5 for factor in shrink_factors]


def _get_block(previous_image: NgffImage, block_index: int):
    """Helper method for accessing an enumerated chunk from input"""
    block_shape = [c[block_index] for c in previous_image.data.chunks]
    block = previous_image.data[tuple([slice(0, s) for s in block_shape])]
    dims = list(previous_image.dims)
    # Also take "c" if it is the last dimension
    if dims[-1] == "c":
        dims[-1] = "x"
    indexer = []
    for d in dims:
        if d in _spatial_dims:
            indexer.append(slice(None))
        else:
            indexer.append(0)
    block = block[tuple(indexer)]
    return block
