import numpy as np

from ._support import _align_chunks, _dim_scale_factors, _compute_sigma
from ..ngff_image import NgffImage


def _compute_next_scale(previous_image, dim_factors):
    """Helper method to manually compute output image spacing.

    previous_image: _NgffImage
        The image for which voxel spacings are use to compute spacing for the next scale

    dim_factors: Dict
        Shrink ratio along each enumerated axis

    result: Dict
        Spacing along each enumerated image axis
        Example {'x': 2.0, 'y': 1.0}
    """
    input_scale = previous_image.scale
    return {dim: input_scale[dim] * dim_factors[dim] for dim in previous_image.dims}


def _compute_next_translation(previous_image, dim_factors):
    """Helper method to manually compute output image physical offset.
        Note that this method does not account for an image direction matrix.

    previous_image: NgffImage
        The image for which voxel offsets are input

    dim_factors: Dict
        Shrink ratio along each enumerated axis

    result: Dict
        Offset in physical space of first voxel in output image
        Example {'x': 0.5, 'y': 1.0}
    """
    input_scale = previous_image.scale
    input_translation = previous_image.translation

    # Index in input image space corresponding to offset after shrink
    input_index = {
        dim: 0.5 * (dim_factors[dim] - 1)
        for dim in previous_image.dims
        if dim in dim_factors
    }
    # Translate input index coordinate to offset in physical space
    # NOTE: This method fails to account for direction matrix
    return {
        dim: input_index[dim] * input_scale[dim] + input_translation[dim]
        for dim in previous_image.dims
        if dim in dim_factors
    }


def _get_truncate(previous_image, sigma_values, truncate_start=4.0) -> float:
    """Discover truncate parameter yielding a viable kernel width
        for dask_image.ndfilters.gaussian_filter processing. Block overlap
        cannot be greater than image size, so kernel radius is more limited
        for small images. A lower stddev truncation ceiling for kernel
        generation can result in a less precise kernel.

    previous_image: _NgffImage
        Chunked image to be smoothed

    sigma:values: List
        Gaussian kernel standard deviations in tzyx order

    truncate_start: float
        First truncation value to try.

    result: float
        Truncation value found to yield largest possible kernel width without
        extending beyond one chunk such that chunked smoothing would fail.
    """

    from dask_image.ndfilters._gaussian import _get_border

    truncate = truncate_start
    stddev_step = 0.5  # search by stepping down by 0.5 stddev in each iteration

    border = _get_border(previous_image.data, sigma_values, truncate)
    while any(
        [
            border_len > image_len
            for border_len, image_len in zip(border, previous_image.data.shape)
        ]
    ):
        truncate = truncate - stddev_step
        if truncate <= 0.0:
            break
        border = _get_border(previous_image.data, sigma_values, truncate)

    return truncate


def _downsample_dask_image(
    ngff_image: NgffImage, default_chunks, out_chunks, scale_factors, label=False
):
    import dask_image.ndfilters
    import dask_image.ndinterp

    multiscales = [
        ngff_image,
    ]
    previous_image = ngff_image
    dims = ngff_image.dims
    for scale_factor in scale_factors:
        dim_factors = _dim_scale_factors(dims, scale_factor)
        previous_image = _align_chunks(previous_image, default_chunks, dim_factors)

        shrink_factors = []
        for dim in dims:
            if dim in dim_factors:
                shrink_factors.append(dim_factors[dim])
            else:
                shrink_factors.append(1)

        # Compute output shape and metadata
        output_shape = [
            int(image_len / shrink_factor)
            for image_len, shrink_factor in zip(
                previous_image.data.shape, shrink_factors
            )
        ]
        output_scale = _compute_next_scale(previous_image, dim_factors)
        output_translation = _compute_next_translation(previous_image, dim_factors)

        if label == "mode":

            def largest_mode(arr):
                values, counts = np.unique(arr, return_counts=True)
                m = counts.argmax()
                return values[m]

            size = tuple(shrink_factors)
            blurred_array = dask_image.ndfilters.generic_filter(
                image=previous_image.data,
                function=largest_mode,
                size=size,
                mode="nearest",
            )
        elif label == "nearest":
            blurred_array = previous_image.data
        else:
            input_scale_list = []
            for dim in dims:
                if dims in previous_image.scale:
                    input_scale_list.append(previous_image.scale[dim])
                else:
                    input_scale_list.append(1.0)

            sigma_values = _compute_sigma(input_scale_list, shrink_factors)
            truncate = _get_truncate(previous_image, sigma_values)

            blurred_array = dask_image.ndfilters.gaussian_filter(
                image=previous_image.data,
                sigma=sigma_values,  # tzyx order
                mode="nearest",
                truncate=truncate,
            )

        # Construct downsample parameters
        image_dimension = len(dim_factors)
        transform = np.eye(image_dimension)
        for dim, shrink_factor in enumerate(shrink_factors):
            transform[dim, dim] = shrink_factor
        if label:
            order = 0
        else:
            order = 1

        downscaled_array = dask_image.ndinterp.affine_transform(
            blurred_array,
            matrix=transform,
            order=order,
            output_shape=output_shape,  # tzyx order
        )

        out_chunks_list = []
        for dim in dims:
            if dim in out_chunks:
                out_chunks_list.append(out_chunks[dim])
            else:
                out_chunks_list.append(1)
        downscaled_array = downscaled_array.rechunk(tuple(out_chunks_list))

        previous_image = NgffImage(
            downscaled_array, dims, output_scale, output_translation
        )
        multiscales.append(previous_image)

    return multiscales
