from ngff_zarr import Methods, to_multiscales

from ._data import store_new_multiscales, verify_against_baseline


def test_bin_shrink_isotropic_scale_factors(input_images):
    dataset_name = "cthead1"
    image = input_images[dataset_name]
    baseline_name = "2_4/ITKWASM_BIN_SHRINK.zarr"
    multiscales = to_multiscales(image, [2, 4], method=Methods.ITKWASM_BIN_SHRINK)
    store_new_multiscales(dataset_name, baseline_name, multiscales)
    verify_against_baseline(dataset_name, baseline_name, multiscales)

    baseline_name = "auto/ITKWASM_BIN_SHRINK.zarr"
    multiscales = to_multiscales(image, method=Methods.ITKWASM_BIN_SHRINK)
    store_new_multiscales(dataset_name, baseline_name, multiscales)
    verify_against_baseline(dataset_name, baseline_name, multiscales)


def test_gaussian_isotropic_scale_factors(input_images):
    dataset_name = "cthead1"
    image = input_images[dataset_name]
    baseline_name = "2_4/ITKWASM_GAUSSIAN.zarr"
    multiscales = to_multiscales(image, [2, 4], method=Methods.ITKWASM_GAUSSIAN)
    store_new_multiscales(dataset_name, baseline_name, multiscales)
    verify_against_baseline(dataset_name, baseline_name, multiscales)

    baseline_name = "auto/ITKWASM_GAUSSIAN.zarr"
    multiscales = to_multiscales(image, method=Methods.ITKWASM_GAUSSIAN)
    store_new_multiscales(dataset_name, baseline_name, multiscales)
    verify_against_baseline(dataset_name, baseline_name, multiscales)


#     dataset_name = "cthead1"
#     image = input_images[dataset_name]
#     baseline_name = "2_3/DASK_IMAGE_GAUSSIAN"
#     multiscale = to_multiscale(image, [2, 3], method=Methods.DASK_IMAGE_GAUSSIAN)
#     verify_against_baseline(dataset_name, baseline_name, multiscale)

#     dataset_name = "small_head"
#     image = input_images[dataset_name]
#     baseline_name = "2_3_4/DASK_IMAGE_GAUSSIAN"
#     multiscale = to_multiscale(image, [2, 3, 4], method=Methods.DASK_IMAGE_GAUSSIAN)
#     verify_against_baseline(dataset_name, baseline_name, multiscale)


def test_gaussian_anisotropic_scale_factors(input_images):
    dataset_name = "cthead1"
    image = input_images[dataset_name]
    scale_factors = [{"x": 2, "y": 2}, {"x": 2, "y": 4}]
    multiscales = to_multiscales(image, scale_factors, method=Methods.ITKWASM_GAUSSIAN)
    baseline_name = "x2y2_x2y4/ITKWASM_GAUSSIAN.zarr"
    store_new_multiscales(dataset_name, baseline_name, multiscales)
    verify_against_baseline(dataset_name, baseline_name, multiscales)

    # dataset_name = "small_head"
    # image = input_images[dataset_name]
    # scale_factors = [
    #     {"x": 3, "y": 2, "z": 4},
    #     {"x": 2, "y": 2, "z": 2},
    #     {"x": 1, "y": 2, "z": 1},
    # ]
    # multiscale = to_multiscale(image, scale_factors, method=Methods.DASK_IMAGE_GAUSSIAN)
    # baseline_name = "x3y2z4_x2y2z2_x1y2z1/DASK_IMAGE_GAUSSIAN"
    # verify_against_baseline(dataset_name, baseline_name, multiscale)


def test_label_image_isotropic_scale_factors(input_images):
    dataset_name = "2th_cthead1"
    image = input_images[dataset_name]
    baseline_name = "2_4/ITKWASM_LABEL_IMAGE.zarr"
    multiscales = to_multiscales(image, [2, 4], method=Methods.ITKWASM_LABEL_IMAGE)
    store_new_multiscales(dataset_name, baseline_name, multiscales)
    verify_against_baseline(dataset_name, baseline_name, multiscales)

    dataset_name = "2th_cthead1"
    image = input_images[dataset_name]
    baseline_name = "2_3/ITKWASM_LABEL_IMAGE.zarr"
    multiscales = to_multiscales(image, [2, 3], method=Methods.ITKWASM_LABEL_IMAGE)
    store_new_multiscales(dataset_name, baseline_name, multiscales)
    verify_against_baseline(dataset_name, baseline_name, multiscales)


def test_label_image_anisotropic_scale_factors(input_images):
    dataset_name = "2th_cthead1"
    image = input_images[dataset_name]
    scale_factors = [{"x": 2, "y": 2}, {"x": 2, "y": 4}]
    multiscales = to_multiscales(
        image, scale_factors, method=Methods.ITKWASM_LABEL_IMAGE
    )
    baseline_name = "x2y4_x2y8/ITKWASM_LABEL_IMAGE.zarr"
    store_new_multiscales(dataset_name, baseline_name, multiscales)
    verify_against_baseline(dataset_name, baseline_name, multiscales)
