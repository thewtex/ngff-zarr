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
        # if a dim is not in the scale_factors, add it with a scale factor of 1
        for d in dims:
            if d not in result_scale_factors:
                result_scale_factors[d] = 1

    return result_scale_factors


def _update_previous_dim_factors(scale_factor, spatial_dims, previous_dim_factors):
    previous_dim_factors = copy.copy(previous_dim_factors)
    if isinstance(scale_factor, int):
        for d in spatial_dims:
            previous_dim_factors[d] = scale_factor
    else:
        for d in scale_factor:
            previous_dim_factors[d] = scale_factor[d]
    return previous_dim_factors


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


def _compute_downsampled_block_metadata(
    input_block,
    shrink_factors: list,
) -> tuple:
    """
    Compute output metadata for a downsampled block.

    :param input_block: Input block (numpy array or ITKWasm image)
    :param shrink_factors: Shrink factors for each spatial dimension

    :return: Tuple of (output_shape, output_spacing, output_origin, scale_dict, translation_dict)
    """
    import math
    import itkwasm

    # Handle different input types
    if hasattr(input_block, "GetSpacing") and hasattr(input_block, "GetOrigin"):
        # This is an ITK image
        import itk

        input_size = list(itk.size(input_block))
        input_spacing = list(input_block.GetSpacing())
        input_origin = list(input_block.GetOrigin())
        # Get the numpy array for shape calculation
        input_array = itk.array_from_image(input_block)
    elif hasattr(input_block, "size") and hasattr(input_block, "spacing"):
        # This is already an ITKWasm image
        input_image = input_block
        # Get the image size, spacing, and origin
        if hasattr(input_image.size, "__iter__"):
            input_size = list(input_image.size)
        else:
            input_size = [input_image.size]

        if hasattr(input_image.spacing, "__iter__"):
            input_spacing = list(input_image.spacing)
        else:
            input_spacing = [input_image.spacing]

        if hasattr(input_image.origin, "__iter__"):
            input_origin = list(input_image.origin)
        else:
            input_origin = [input_image.origin]

        # Use the input block shape if available, otherwise derive from ITKWasm image
        if hasattr(input_block, "shape"):
            input_array = input_block
        else:
            input_array = input_image.data if hasattr(input_image, "data") else None
    else:
        # This is a numpy array, convert to ITKWasm image
        is_vector = (
            len(input_block.shape) > 0 and input_block.shape[-1] < 10
        )  # Heuristic for vector images
        input_image = itkwasm.image_from_array(input_block, is_vector=is_vector)

        if hasattr(input_image.size, "__iter__"):
            input_size = list(input_image.size)
        else:
            input_size = [input_image.size]

        if hasattr(input_image.spacing, "__iter__"):
            input_spacing = list(input_image.spacing)
        else:
            input_spacing = [input_image.spacing]

        if hasattr(input_image.origin, "__iter__"):
            input_origin = list(input_image.origin)
        else:
            input_origin = [input_image.origin]

        input_array = input_block

    # For consistency, use the same size computation strategy that ensures
    # all spatial dimensions with the same shrink factor get the same treatment
    # This prevents edge blocks with different spatial dimension sizes from
    # causing inconsistent output shapes
    output_size = []
    for i, (input_len, shrink_factor) in enumerate(zip(input_size, shrink_factors)):
        # Use floor division like the original ITK implementation
        output_len = int(math.floor(input_len / shrink_factor))
        output_size.append(output_len)

    # Compute output spacing as input_spacing * shrink_factor
    output_spacing = [
        spacing * shrink_factor
        for spacing, shrink_factor in zip(input_spacing, shrink_factors)
    ]

    # Compute output origin as input_origin + 0.5 * (shrink_factor - 1) * input_spacing
    output_origin = [
        origin + 0.5 * (shrink_factor - 1) * spacing
        for origin, shrink_factor, spacing in zip(
            input_origin, shrink_factors, input_spacing
        )
    ]

    # For chunk size computation, we need the shape in the same order as the input array
    # ITK uses (x,y,z) ordering but numpy arrays use (z,y,x) ordering
    if input_array is not None and hasattr(input_array, "shape"):
        # This is a numpy array, use its shape directly to determine the output ordering
        input_array_shape = input_array.shape
        # Only apply shrink factors to spatial dimensions
        # The shrink_factors list corresponds to spatial dimensions only
        # We need to identify which array dimensions are spatial vs non-spatial
        output_shape = list(input_array_shape)  # Start with original shape

        # Apply shrink factors only to spatial dimensions
        # Assume spatial dimensions are consecutive and shrink_factors is in the same order
        # For most cases, spatial dims are the last few dimensions (excluding channel)
        spatial_start_idx = len(input_array_shape) - len(shrink_factors)
        if (
            input_array_shape[-1] < 10
        ):  # Heuristic: if last dimension is small, it's likely a channel
            spatial_start_idx = len(input_array_shape) - len(shrink_factors) - 1

        for i, shrink_factor in enumerate(shrink_factors):
            spatial_idx = spatial_start_idx + i
            if 0 <= spatial_idx < len(output_shape):
                output_shape[spatial_idx] = int(
                    math.floor(input_array_shape[spatial_idx] / shrink_factor)
                )

        output_shape = tuple(output_shape)
    else:
        # This is an ITK/ITKWasm image, need to compute array shape from image size
        # ITK image.size is in (x,y,z) order, but we need (z,y,x) for numpy arrays
        output_shape = tuple(output_size[::-1])

    # Create scale and translation dictionaries
    _image_dims = ("x", "y", "z", "t")
    scale = {_image_dims[i]: s for i, s in enumerate(output_spacing)}
    translation = {_image_dims[i]: o for i, o in enumerate(output_origin)}

    return output_shape, output_spacing, output_origin, scale, translation
