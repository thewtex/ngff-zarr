from typing import Tuple

import numpy as np
from dask.array import concatenate, expand_dims, map_blocks, map_overlap, take

from ..ngff_image import NgffImage
from ._support import (
    _align_chunks,
    _compute_sigma,
    _dim_scale_factors,
    _get_block,
    _spatial_dims,
)

_image_dims: Tuple[str, str, str, str] = ("x", "y", "z", "t")


def _itkwasm_blur_and_downsample(
    image_data,
    shrink_factors,
    kernel_radius,
    smoothing,
):
    """Blur and then downsample a given image chunk"""
    import itkwasm

    # chunk does not have metadata attached, values are ITK defaults
    image = itkwasm.image_from_array(image_data)

    # Skip this image block if it has 0 voxels
    block_size = image.size
    if any(block_len == 0 for block_len in block_size):
        return None

    if smoothing == "gaussian":
        from itkwasm_downsample import downsample

        downsampled = downsample(
            image, shrink_factors=shrink_factors, crop_radius=kernel_radius
        )
    elif smoothing == "label_image":
        from itkwasm_downsample import downsample_label_image

        downsampled = downsample_label_image(
            image, shrink_factors=shrink_factors, crop_radius=kernel_radius
        )
    else:
        msg = f"Unknown smoothing method: {smoothing}"
        raise ValueError(msg)

    return downsampled.data


def _itkwasm_chunk_bin_shrink(
    image_data,
    shrink_factors,
):
    """Compute the local mean and downsample on a given image chunk"""
    import itkwasm
    from itkwasm_downsample import downsample_bin_shrink

    # chunk does not have metadata attached, values are ITK defaults
    image = itkwasm.image_from_array(image_data)

    # Skip this image block if it has 0 voxels
    block_size = image.size
    if any(block_len == 0 for block_len in block_size):
        return None

    downsampled = downsample_bin_shrink(image, shrink_factors=shrink_factors)
    return downsampled.data


def _downsample_itkwasm_bin_shrink(
    ngff_image: NgffImage, default_chunks, out_chunks, scale_factors
):
    import itkwasm
    from itkwasm_downsample import downsample_bin_shrink

    multiscales = [
        ngff_image,
    ]
    previous_image = ngff_image
    dims = ngff_image.dims
    previous_dim_factors = {d: 1 for d in dims}
    spatial_dims = [dim for dim in dims if dim in _spatial_dims]
    spatial_dims = _image_dims[: len(spatial_dims)]
    for scale_factor in scale_factors:
        dim_factors = _dim_scale_factors(dims, scale_factor, previous_dim_factors)
        previous_dim_factors = dim_factors
        previous_image = _align_chunks(previous_image, default_chunks, dim_factors)

        shrink_factors = [dim_factors[sd] for sd in spatial_dims]

        block_0 = _get_block(previous_image, 0)

        # For consistency for now, do not utilize direction until there is standardized support for
        # direction cosines / orientation in OME-NGFF
        # block_0.attrs.pop("direction", None)
        block_input = itkwasm.image_from_array(np.ones_like(block_0))
        spacing = [previous_image.scale[d] for d in spatial_dims]
        block_input.spacing = spacing
        origin = [previous_image.translation[d] for d in spatial_dims]
        block_input.origin = origin
        block_output = downsample_bin_shrink(
            block_input, shrink_factors, information_only=True
        )
        scale = {_image_dims[i]: s for (i, s) in enumerate(block_output.spacing)}
        translation = {_image_dims[i]: s for (i, s) in enumerate(block_output.origin)}
        dtype = block_output.data.dtype
        output_chunks = list(previous_image.data.chunks)
        for i, c in enumerate(output_chunks):
            output_chunks[i] = [
                block_output.data.shape[i],
            ] * len(c)

        block_neg1 = _get_block(previous_image, -1)
        # block_neg1.attrs.pop("direction", None)
        block_input = itkwasm.image_from_array(np.ones_like(block_neg1))
        block_input.spacing = spacing
        block_input.origin = origin
        block_output = downsample_bin_shrink(
            block_input, shrink_factors, information_only=False
        )
        for i in range(len(output_chunks)):
            output_chunks[i][-1] = block_output.data.shape[i]
            output_chunks[i] = tuple(output_chunks[i])
        output_chunks = tuple(output_chunks)

        downscaled_array = map_blocks(
            _itkwasm_chunk_bin_shrink,
            previous_image.data,
            shrink_factors=shrink_factors,
            dtype=dtype,
            chunks=output_chunks,
        )
        out_chunks_list = []
        for dim in dims:
            if dim in out_chunks:
                out_chunks_list.append(out_chunks[dim])
            else:
                out_chunks_list.append(1)
        downscaled_array = downscaled_array.rechunk(tuple(out_chunks_list))

        previous_image = NgffImage(downscaled_array, dims, scale, translation)
        multiscales.append(previous_image)

    return multiscales


def _downsample_itkwasm(
    ngff_image: NgffImage, default_chunks, out_chunks, scale_factors, smoothing
):
    import itkwasm
    from itkwasm_downsample import downsample_bin_shrink, gaussian_kernel_radius

    multiscales = [
        ngff_image,
    ]
    previous_image = ngff_image
    dims = ngff_image.dims
    previous_dim_factors = {d: 1 for d in dims}
    spatial_dims = [dim for dim in dims if dim in _spatial_dims]
    spatial_dims = _image_dims[: len(spatial_dims)]
    for scale_factor in scale_factors:
        dim_factors = _dim_scale_factors(dims, scale_factor, previous_dim_factors)
        previous_dim_factors = dim_factors
        previous_image = _align_chunks(previous_image, default_chunks, dim_factors)

        shrink_factors = [dim_factors[sd] for sd in spatial_dims]

        # Compute metadata for region splitting

        # Blocks 0, ..., N-2 have the same shape
        block_0_input = _get_block(previous_image, 0)
        # Block N-1 may be smaller than preceding blocks
        block_neg1_input = _get_block(previous_image, -1)

        # Compute overlap for Gaussian blurring for all blocks
        block_0_image = itkwasm.image_from_array(np.ones_like(block_0_input))
        input_spacing = [previous_image.scale[d] for d in spatial_dims]
        block_0_image.spacing = input_spacing
        input_origin = [previous_image.translation[d] for d in spatial_dims]
        block_0_image.origin = input_origin

        # pixel units
        sigma_values = _compute_sigma(shrink_factors)
        kernel_radius = gaussian_kernel_radius(
            size=block_0_image.size, sigma=sigma_values
        )

        # Compute output size and spatial metadata for blocks 0, .., N-2
        block_output = downsample_bin_shrink(
            block_0_image, shrink_factors, information_only=False
        )
        block_0_output_spacing = block_output.spacing
        block_0_output_origin = block_output.origin

        scale = {_image_dims[i]: s for (i, s) in enumerate(block_0_output_spacing)}
        translation = {_image_dims[i]: s for (i, s) in enumerate(block_0_output_origin)}
        dtype = block_output.data.dtype

        computed_size = [
            int(block_len / shrink_factor)
            for block_len, shrink_factor in zip(block_0_image.size, shrink_factors)
        ]
        assert all(
            block_output.size[dim] == computed_size[dim]
            for dim in range(block_output.data.ndim)
        )
        output_chunks = list(previous_image.data.chunks)
        if "t" in previous_image.dims:
            dims = list(previous_image.dims)
            t_index = dims.index("t")
            output_chunks.pop(t_index)
        for i, c in enumerate(output_chunks):
            output_chunks[i] = [
                block_output.data.shape[i],
            ] * len(c)
        # Compute output size for block N-1
        block_neg1_image = itkwasm.image_from_array(np.ones_like(block_neg1_input))
        block_neg1_image.spacing = input_spacing
        block_neg1_image.origin = input_origin
        block_output = downsample_bin_shrink(
            block_neg1_image, shrink_factors, information_only=False
        )
        computed_size = [
            int(block_len / shrink_factor)
            for block_len, shrink_factor in zip(block_neg1_image.size, shrink_factors)
        ]
        assert all(
            block_output.size[dim] == computed_size[dim]
            for dim in range(block_output.data.ndim)
        )
        for i in range(len(output_chunks)):
            output_chunks[i][-1] = block_output.data.shape[i]
            output_chunks[i] = tuple(output_chunks[i])
        output_chunks = tuple(output_chunks)

        if "t" in previous_image.dims:
            all_timepoints = []
            for timepoint in range(previous_image.data.shape[t_index]):
                data = take(previous_image.data, timepoint, t_index)

                downscaled_timepoint = map_overlap(
                    _itkwasm_blur_and_downsample,
                    data,
                    shrink_factors=shrink_factors,
                    kernel_radius=kernel_radius,
                    smoothing=smoothing,
                    dtype=dtype,
                    depth=dict(enumerate(np.flip(kernel_radius))),  # overlap is in tzyx
                    boundary="nearest",
                    trim=False,  # Overlapped region is trimmed in blur_and_downsample to output size
                    chunks=output_chunks,
                )
                expanded = expand_dims(downscaled_timepoint, t_index)
                all_timepoints.append(expanded)
            downscaled_array = concatenate(all_timepoints, t_index)
        else:
            data = previous_image.data
            downscaled_array = map_overlap(
                _itkwasm_blur_and_downsample,
                data,
                shrink_factors=shrink_factors,
                kernel_radius=kernel_radius,
                smoothing=smoothing,
                dtype=dtype,
                depth=dict(enumerate(np.flip(kernel_radius))),  # overlap is in tzyx
                boundary="nearest",
                trim=False,  # Overlapped region is trimmed in blur_and_downsample to output size
                chunks=output_chunks,
            )

        out_chunks_list = []
        for dim in dims:
            if dim in out_chunks:
                out_chunks_list.append(out_chunks[dim])
            else:
                out_chunks_list.append(1)
        downscaled_array = downscaled_array.rechunk(tuple(out_chunks_list))

        previous_image = NgffImage(downscaled_array, dims, scale, translation)
        multiscales.append(previous_image)

    return multiscales


# todo
# def _downsample_itk_label(
#     current_input,
#     default_chunks,
#     out_chunks,
#     scale_factors,
#     data_objects,
#     image,
# ):
# Uses the LabelImageGaussianInterpolateImageFunction. More appropriate for integer label images.
# import itk

# gaussian_filter_name = "DiscreteGaussianImageFilter"
# interpolator_name = "LabelImageGaussianInterpolateImageFunction"

# for _factor_index, scale_factor in enumerate(scale_factors):
#     dim_factors = _dim_scale_factors(image.dims, scale_factor)
#     current_input = _align_chunks(current_input, default_chunks, dim_factors)

#     shrink_factors = [dim_factors[sf] for sf in _image_dims if sf in dim_factors]

#     # Compute metadata for region splitting

#     # Blocks 0, ..., N-2 have the same shape
#     block_0_input = _get_block(current_input, 0)
#     # Block N-1 may be smaller than preceding blocks
#     block_neg1_input = _get_block(current_input, -1)

#     # Compute overlap for Gaussian blurring for all blocks
#     block_0_image = itk.image_from_xarray(block_0_input)
#     input_spacing = itk.spacing(block_0_image)
#     sigma_values = _compute_sigma(shrink_factors)
#     kernel_radius = _compute_itk_gaussian_kernel_radius(
#         itk.size(block_0_image), sigma_values
#     )

#     # Compute output size and spatial metadata for blocks 0, .., N-2
#     filt = itk.BinShrinkImageFilter.New(
#         block_0_image, shrink_factors=shrink_factors
#     )
#     filt.UpdateOutputInformation()
#     block_output = filt.GetOutput()
#     block_0_output_spacing = block_output.GetSpacing()
#     block_0_output_origin = block_output.GetOrigin()

#     block_0_scale = {
#         _image_dims[i]: s for (i, s) in enumerate(block_0_output_spacing)
#     }
#     block_0_translation = {
#         _image_dims[i]: s for (i, s) in enumerate(block_0_output_origin)
#     }
#     dtype = block_output.dtype

#     computed_size = [
#         int(block_len / shrink_factor)
#         for block_len, shrink_factor in zip(itk.size(block_0_image), shrink_factors)
#     ]
#     assert all(
#         itk.size(block_output)[dim] == computed_size[dim]
#         for dim in range(block_output.ndim)
#     )
#     output_chunks = list(current_input.chunks)
#     for i, c in enumerate(output_chunks):
#         output_chunks[i] = [
#             block_output.shape[i],
#         ] * len(c)

#     # Compute output size for block N-1
#     block_neg1_image = itk.image_from_xarray(block_neg1_input)
#     filt.SetInput(block_neg1_image)
#     filt.UpdateOutputInformation()
#     block_output = filt.GetOutput()
#     computed_size = [
#         int(block_len / shrink_factor)
#         for block_len, shrink_factor in zip(
#             itk.size(block_neg1_image), shrink_factors
#         )
#     ]
#     assert all(
#         itk.size(block_output)[dim] == computed_size[dim]
#         for dim in range(block_output.ndim)
#     )
#     for i in range(len(output_chunks)):
#         output_chunks[i][-1] = block_output.shape[i]
#         output_chunks[i] = tuple(output_chunks[i])
#     output_chunks = tuple(output_chunks)

#     downscaled_array = map_overlap(
#         _itk_blur_and_downsample,
#         current_input.data,
#         gaussian_filter_name=gaussian_filter_name,
#         interpolator_name=interpolator_name,
#         shrink_factors=shrink_factors,
#         sigma_values=sigma_values,
#         kernel_radius=kernel_radius,
#         dtype=dtype,
#         depth=dict(enumerate(np.flip(kernel_radius))),  # overlap is in tzyx
#         boundary="nearest",
#         trim=False,  # Overlapped region is trimmed in blur_and_downsample to output size
#     ).compute()

#     # todo
#     # downscaled = to_spatial_image(
#     #     downscaled_array,
#     #     dims=image.dims,
#     #     scale=block_0_scale,
#     #     translation=block_0_translation,
#     #     name=current_input.name,
#     #     axis_names={
#     #         d: image.coords[d].attrs.get("long_name", d) for d in image.dims
#     #     },
#     #     axis_units={d: image.coords[d].attrs.get("units", "") for d in image.dims},
#     #     t_coords=image.coords.get("t", None),
#     #     c_coords=image.coords.get("c", None),
#     # )
#     # downscaled = downscaled.chunk(out_chunks)
#     # data_objects[f"scale{factor_index+1}"] = downscaled.to_dataset(
#     #     name=image.name, promote_attrs=True
#     # )
#     # current_input = downscaled

# return data_objects
