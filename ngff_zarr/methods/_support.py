from typing import List

_spatial_dims = {"x", "y", "z"}


def _dim_scale_factors(dims, scale_factor, previous_dim_factors):
    if isinstance(scale_factor, int):
        result_scale_factors = {
            dim: int(scale_factor / previous_dim_factors[dim])
            for dim in _spatial_dims.intersection(dims)
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
