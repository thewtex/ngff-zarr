_spatial_dims = {"x", "y", "z"}


def _dim_scale_factors(dims, scale_factor):
    if isinstance(scale_factor, int):
        result_scale_factors = {
            dim: scale_factor for dim in _spatial_dims.intersection(dims)
        }
    else:
        result_scale_factors = scale_factor
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
        dask_aligned_chunks = { previous_image.dims.index(dim):
                aligned_chunks[dim] for dim in aligned_chunks.keys() }
        previous_image.data = previous_image.data.rechunk(dask_aligned_chunks)

    return previous_image


def _compute_sigma(input_spacings, shrink_factors) -> list:
    """Compute Gaussian kernel sigma values for resampling to isotropic spacing.
    sigma = sqrt((isoSpacing^2 - inputSpacing[0]^2)/(2*sqrt(2*ln(2)))^2)
    Ref https://discourse.itk.org/t/resampling-to-isotropic-signal-processing-theory/1403/16

    input spacings: List
        Input image physical spacings in xyzt order

    shrink_factors: List
        Shrink ratio along each axis in xyzt order

    result: List
        Standard deviation of Gaussian kernel along each axis in xyzt order
    """
    assert len(input_spacings) == len(shrink_factors)
    import math

    output_spacings = [
        input_spacing * shrink
        for input_spacing, shrink in zip(input_spacings, shrink_factors)
    ]
    denominator = (2 * ((2 * math.log(2)) ** 0.5)) ** 2
    return [
        ((output_spacing**2 - input_spacing**2) / denominator) ** 0.5
        for input_spacing, output_spacing in zip(input_spacings, output_spacings)
    ]
