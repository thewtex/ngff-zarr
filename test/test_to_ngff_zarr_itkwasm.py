from ngff_zarr import Methods, to_multiscales

from ._data import verify_against_baseline

_HAVE_CUCIM = False
try:
    import itkwasm_downsample_cucim  # noqa: F401

    _HAVE_CUCIM = True
except ImportError:
    pass


def test_bin_shrink_isotropic_scale_factors(input_images):
    dataset_name = "cthead1"
    image = input_images[dataset_name]
    if _HAVE_CUCIM:
        baseline_name = "2_4/ITKWASM_BIN_SHRINK_CUCIM.zarr"
    else:
        baseline_name = "2_4/ITKWASM_BIN_SHRINK.zarr"
    multiscales = to_multiscales(image, [2, 4], method=Methods.ITKWASM_BIN_SHRINK)
    verify_against_baseline(dataset_name, baseline_name, multiscales)

    if _HAVE_CUCIM:
        baseline_name = "auto/ITKWASM_BIN_SHRINK_CUCIM.zarr"
    else:
        baseline_name = "auto/ITKWASM_BIN_SHRINK.zarr"
    multiscales = to_multiscales(image, method=Methods.ITKWASM_BIN_SHRINK)
    verify_against_baseline(dataset_name, baseline_name, multiscales)


def test_gaussian_isotropic_scale_factors(input_images):
    dataset_name = "cthead1"
    image = input_images[dataset_name]
    if _HAVE_CUCIM:
        baseline_name = "2_4/ITKWASM_GAUSSIAN_CUCIM.zarr"
    else:
        baseline_name = "2_4/ITKWASM_GAUSSIAN.zarr"
    multiscales = to_multiscales(image, [2, 4], method=Methods.ITKWASM_GAUSSIAN)
    verify_against_baseline(dataset_name, baseline_name, multiscales)

    if _HAVE_CUCIM:
        baseline_name = "auto/ITKWASM_GAUSSIAN_CUCIM.zarr"
    else:
        baseline_name = "auto/ITKWASM_GAUSSIAN.zarr"
    multiscales = to_multiscales(image, method=Methods.ITKWASM_GAUSSIAN)
    verify_against_baseline(dataset_name, baseline_name, multiscales)

    dataset_name = "cthead1"
    image = input_images[dataset_name]
    if _HAVE_CUCIM:
        baseline_name = "2_3/ITKWASM_GAUSSIAN_CUCIM.zarr"
    else:
        baseline_name = "2_3/ITKWASM_GAUSSIAN.zarr"
    multiscales = to_multiscales(image, [2, 3], method=Methods.ITKWASM_GAUSSIAN)
    verify_against_baseline(dataset_name, baseline_name, multiscales)

    dataset_name = "MR-head"
    image = input_images[dataset_name]
    if _HAVE_CUCIM:
        baseline_name = "2_3_4/ITKWASM_GAUSSIAN_CUCIM.zarr"
    else:
        baseline_name = "2_3_4/ITKWASM_GAUSSIAN.zarr"
    multiscales = to_multiscales(image, [2, 3, 4], method=Methods.ITKWASM_GAUSSIAN)
    verify_against_baseline(dataset_name, baseline_name, multiscales)


# def test_gaussian_anisotropic_scale_factors(input_images):
#     dataset_name = "cthead1"
#     image = input_images[dataset_name]
#     scale_factors = [{"x": 2, "y": 2}, {"x": 2, "y": 4}]
#     multiscales = to_multiscales(image, scale_factors, method=Methods.ITKWASM_GAUSSIAN)
#     baseline_name = "x2y2_x2y4/ITKWASM_GAUSSIAN.zarr"
#     verify_against_baseline(dataset_name, baseline_name, multiscales)

# dataset_name = "MR-head"
# image = input_images[dataset_name]
# scale_factors = [
#     {"x": 3, "y": 2, "z": 4},
#     {"x": 6, "y": 4, "z": 4},
#     {"x": 6, "y": 8, "z": 4},
# ]
# multiscales = to_multiscales(image, scale_factors, method=Methods.ITKWASM_GAUSSIAN)
# baseline_name = "x3y2z4_6242z4_x6y8z4/ITKWASM_GAUSSIAN.zarr"
# verify_against_baseline(dataset_name, baseline_name, multiscales)


def test_label_image_isotropic_scale_factors(input_images):
    dataset_name = "2th_cthead1"
    image = input_images[dataset_name]
    baseline_name = "2_4/ITKWASM_LABEL_IMAGE.zarr"
    multiscales = to_multiscales(image, [2, 4], method=Methods.ITKWASM_LABEL_IMAGE)
    verify_against_baseline(dataset_name, baseline_name, multiscales)

    dataset_name = "2th_cthead1"
    image = input_images[dataset_name]
    baseline_name = "2_3/ITKWASM_LABEL_IMAGE.zarr"
    multiscales = to_multiscales(image, [2, 3], method=Methods.ITKWASM_LABEL_IMAGE)
    verify_against_baseline(dataset_name, baseline_name, multiscales)


# def test_label_image_anisotropic_scale_factors(input_images):
#     dataset_name = "2th_cthead1"
#     image = input_images[dataset_name]
#     scale_factors = [{"x": 2, "y": 2}, {"x": 2, "y": 4}]
#     multiscales = to_multiscales(
#         image, scale_factors, method=Methods.ITKWASM_LABEL_IMAGE
#     )
#     baseline_name = "x2y4_x2y4/ITKWASM_LABEL_IMAGE.zarr"
#     store_new_multiscales(dataset_name, baseline_name, multiscales)
#     verify_against_baseline(dataset_name, baseline_name, multiscales)
