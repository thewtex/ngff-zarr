# Methods

To avoid [aliasing artifacts] when generating a multiscale representation, it is
crucial to smooth the input image before downsampling. Different downsampling
methods are available, primarily differing in the smoothing method that is
applied prior to resampling. There can also be differences due to the
interpolator used to resample, but these tend to be negligible since we are
downsampling.

These methods vary in their:

- Amount of artifacts
- Speed
- Hardware requirements and portability
- Appropriateness for intensity or label images

The `ngff_zarr.to_multiscales` function accepts the following methods,
enumerated in `ngff_zarr.Methods`.

## `ITKWASM_GAUSSIAN`

Smoothed with a discrete gaussian filter to generate a [scale space], ideal for
intensity images.

[ITK-Wasm] implementation is extremely portable. [SIMD] accelerated.

The default method.

## `ITKWASM_BIN_SHRINK`

Used the local mean for the output value.

Fast but generates more artifacts than gaussian-based methods.

Appropriate for intensity images.

## `ITKWASM_LABEL_IMAGE`

## `ITK_GAUSSIAN`

Similar to `ITKWASM_GAUSSIAN`, but the package is built to native binaries.

To use a GPU-accelerated version, install the `itk-vkfft` package:

```sh
pip install itk-vkfft
```

## `ITK_BIN_SHRINK`

## `DASK_IMAGE_GAUSSIAN`

## `DASK_IMAGE_MODE`

## `DASK_IMAGE_NEAREST`

[aliasing artifacts]:
  https://en.wikipedia.org/wiki/Nyquist%E2%80%93Shannon_sampling_theorem
[SIMD]: https://en.wikipedia.org/wiki/Single_instruction,_multiple_data
[scale space]: https://en.wikipedia.org/wiki/Scale_space
[ITK-Wasm]: https://wasm.itk.org
