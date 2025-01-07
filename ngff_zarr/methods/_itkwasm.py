from typing import Tuple
from itertools import product

import numpy as np
from dask.array import map_blocks, map_overlap
import dask.array

from ..ngff_image import NgffImage
from ._support import (
    _align_chunks,
    _compute_sigma,
    _dim_scale_factors,
    _get_block,
    _spatial_dims,
    _spatial_dims_last_zyx,
)

_image_dims: Tuple[str, str, str, str] = ("x", "y", "z", "t")


def _itkwasm_blur_and_downsample(
    image_data,
    shrink_factors,
    kernel_radius,
    smoothing,
    is_vector=False,
):
    """Blur and then downsample a given image chunk"""
    import itkwasm

    # chunk does not have metadata attached, values are ITK defaults
    image = itkwasm.image_from_array(image_data, is_vector=is_vector)

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
    is_vector=False,
):
    """Compute the local mean and downsample on a given image chunk"""
    import itkwasm
    from itkwasm_downsample import downsample_bin_shrink

    # chunk does not have metadata attached, values are ITK defaults
    image = itkwasm.image_from_array(image_data, is_vector=is_vector)

    # Skip this image block if it has 0 voxels
    block_size = image.size
    if any(block_len == 0 for block_len in block_size):
        return None

    downsampled = downsample_bin_shrink(image, shrink_factors=shrink_factors)
    return downsampled.data


def _downsample_itkwasm(
    ngff_image: NgffImage, default_chunks, out_chunks, scale_factors, smoothing
):
    import itkwasm
    from itkwasm_downsample import downsample_bin_shrink, gaussian_kernel_radius

    multiscales = [
        ngff_image,
    ]
    previous_image = ngff_image
    dims = tuple(ngff_image.dims)
    previous_dim_factors = {d: 1 for d in dims}
    spatial_dims = [dim for dim in dims if dim in _spatial_dims]
    spatial_dims = _image_dims[: len(spatial_dims)]
    transposed_dims = False
    for scale_factor in scale_factors:
        dim_factors = _dim_scale_factors(dims, scale_factor, previous_dim_factors)
        previous_dim_factors = dim_factors
        previous_image = _align_chunks(previous_image, default_chunks, dim_factors)
        # Operate on a contiguous spatial block
        previous_image = _spatial_dims_last_zyx(previous_image)
        if tuple(previous_image.dims) != dims:
            transposed_dims = True
            reorder = [previous_image.dims.index(dim) for dim in dims]

        shrink_factors = [dim_factors[sd] for sd in spatial_dims]

        # Compute metadata for region splitting

        # Blocks 0, ..., N-2 have the same shape
        block_0_input = _get_block(previous_image, 0)
        # Block N-1 may be smaller than preceding blocks
        block_neg1_input = _get_block(previous_image, -1)

        # Compute overlap for Gaussian blurring for all blocks
        is_vector = previous_image.dims[-1] == "c"
        block_0_image = itkwasm.image_from_array(
            np.ones_like(block_0_input), is_vector=is_vector
        )
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
        output_chunks_start = 0
        while previous_image.dims[output_chunks_start] not in _spatial_dims:
            output_chunks_start += 1
        output_chunks = output_chunks[output_chunks_start:]
        for i, c in enumerate(output_chunks):
            output_chunks[i] = [
                block_output.data.shape[i],
            ] * len(c)
        # Compute output size for block N-1
        block_neg1_image = itkwasm.image_from_array(
            np.ones_like(block_neg1_input), is_vector=is_vector
        )
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

        non_spatial_dims = [d for d in dims if d not in _spatial_dims]
        if "c" in non_spatial_dims and previous_image.dims[-1] == "c":
            non_spatial_dims.pop("c")

        if output_chunks_start > 0:
            # We'll iterate over each index for the non-spatial dimensions, run the desired
            # map_overlap, and aggregate the outputs into a final result.

            # Determine the size for each non-spatial dimension
            non_spatial_shapes = previous_image.data.shape[:output_chunks_start]

            # Collect results for each sub-block
            aggregated_blocks = []
            for idx in product(*(range(s) for s in non_spatial_shapes)):
                # Build the slice object for indexing
                slice_obj = []
                non_spatial_index = 0
                for dim in previous_image.dims:
                    if dim in non_spatial_dims:
                        # Take a single index (like "t=0,1,...") for the non-spatial dimension
                        slice_obj.append(idx[non_spatial_index])
                        non_spatial_index += 1
                    else:
                        # Keep full slice for spatial/channel dims
                        slice_obj.append(slice(None))

                slice_obj = tuple(slice_obj)
                # Extract the sub-block data for the chosen index from the non-spatial dims
                sub_block_data = previous_image.data[slice_obj]

                if smoothing == "bin_shrink":
                    downscaled_sub_block = map_blocks(
                        _itkwasm_chunk_bin_shrink,
                        sub_block_data,
                        shrink_factors=shrink_factors,
                        is_vector=is_vector,
                        dtype=dtype,
                        chunks=output_chunks,
                    )
                else:
                    downscaled_sub_block = map_overlap(
                        _itkwasm_blur_and_downsample,
                        sub_block_data,
                        shrink_factors=shrink_factors,
                        kernel_radius=kernel_radius,
                        smoothing=smoothing,
                        is_vector=is_vector,
                        dtype=dtype,
                        depth=dict(
                            enumerate(np.flip(kernel_radius))
                        ),  # overlap is in tzyx
                        boundary="nearest",
                        trim=False,  # Overlapped region is trimmed in blur_and_downsample to output size
                        chunks=output_chunks,
                    )
                aggregated_blocks.append(downscaled_sub_block)
            downscaled_array_shape = non_spatial_shapes + downscaled_sub_block.shape
            downscaled_array = dask.array.empty(downscaled_array_shape, dtype=dtype)
            for sub_block_idx, idx in enumerate(
                product(*(range(s) for s in non_spatial_shapes))
            ):
                # Build the slice object for indexing
                slice_obj = []
                non_spatial_index = 0
                for dim in previous_image.dims:
                    if dim in non_spatial_dims:
                        # Take a single index (like "t=0,1,...") for the non-spatial dimension
                        slice_obj.append(idx[non_spatial_index])
                        non_spatial_index += 1
                    else:
                        # Keep full slice for spatial/channel dims
                        slice_obj.append(slice(None))

                slice_obj = tuple(slice_obj)
                downscaled_array[slice_obj] = aggregated_blocks[sub_block_idx]
        else:
            data = previous_image.data
            if smoothing == "bin_shrink":
                downscaled_array = map_blocks(
                    _itkwasm_chunk_bin_shrink,
                    data,
                    shrink_factors=shrink_factors,
                    is_vector=is_vector,
                    dtype=dtype,
                    chunks=output_chunks,
                )
            else:
                downscaled_array = map_overlap(
                    _itkwasm_blur_and_downsample,
                    data,
                    shrink_factors=shrink_factors,
                    kernel_radius=kernel_radius,
                    smoothing=smoothing,
                    is_vector=is_vector,
                    dtype=dtype,
                    depth=dict(enumerate(np.flip(kernel_radius))),  # overlap is in tzyx
                    boundary="nearest",
                    trim=False,  # Overlapped region is trimmed in blur_and_downsample to output size
                    chunks=output_chunks,
                )

        out_chunks_list = []
        for dim in previous_image.dims:
            if dim in out_chunks:
                out_chunks_list.append(out_chunks[dim])
            else:
                out_chunks_list.append(1)
        downscaled_array = downscaled_array.rechunk(tuple(out_chunks_list))

        # transpose back to original order if needed (_spatial_dims_zyx transposed the order)
        if transposed_dims:
            downscaled_array = downscaled_array.transpose(reorder)

        previous_image = NgffImage(downscaled_array, dims, scale, translation)
        multiscales.append(previous_image)

    return multiscales
