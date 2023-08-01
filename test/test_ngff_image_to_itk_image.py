import itk
import itkwasm
import numpy as np
from ngff_zarr import itk_image_to_ngff_image, ngff_image_to_itk_image

from ._data import test_data_dir

rng = np.random.default_rng(12345)


def test_2d_itk_image(input_images):  # noqa: ARG001
    itk_image = itk.imread(test_data_dir / "input" / "cthead1.png")
    ngff_image = itk_image_to_ngff_image(itk_image)
    itk_image_back = ngff_image_to_itk_image(ngff_image, wasm=False)
    diff = itk.comparison_image_filter(itk_image, itk_image_back)
    assert np.sum(np.asarray(diff)) == 0.0


def test_2d_rgb_itk_image(input_images):  # noqa: ARG001
    array = rng.integers(0, 255, size=(224, 224, 3), dtype=np.uint8)
    itk_image = itk.image_from_array(array, is_vector=True)
    ngff_image = itk_image_to_ngff_image(itk_image)  # noqa: F841
    # Requires fixes for itk
    # itk_image_back = ngff_image_to_itk_image(ngff_image, wasm=False)
    # diff = itk.comparison_image_filter(itk_image, itk_image_back)
    # assert np.sum(np.asarray(diff)) == 0.0


def test_2d_itk_vector_image(input_images):  # noqa: ARG001
    array = rng.random(size=(224, 224, 3), dtype=np.float32)
    itk_image = itk.image_from_array(array, is_vector=True)
    ngff_image = itk_image_to_ngff_image(itk_image)  # noqa: F841
    # Requires fixes for itk
    # itk_image_back = ngff_image_to_itk_image(ngff_image, wasm=False)
    # assert np.array_equal(itk.array_from_image(itk_image), itk.array_from_image(itk_image_back))


def test_3d_itk_image(input_images):  # noqa: ARG001
    array = rng.integers(0, 255, size=(32, 32, 32), dtype=np.uint8)
    itk_image = itk.image_from_array(array, is_vector=False)
    ngff_image = itk_image_to_ngff_image(itk_image)
    itk_image_back = ngff_image_to_itk_image(ngff_image, wasm=False)
    diff = itk.comparison_image_filter(itk_image, itk_image_back)
    assert np.sum(np.asarray(diff)) == 0.0


def test_3d_itk_vector_image(input_images):  # noqa: ARG001
    array = rng.random(size=(224, 224, 128, 3), dtype=np.float32)
    itk_image = itk.image_from_array(array, is_vector=True)
    ngff_image = itk_image_to_ngff_image(itk_image)  # noqa: F841
    # Requires fixes for itk
    # itk_image_back = ngff_image_to_itk_image(ngff_image, wasm=False)
    # assert np.array_equal(itk.array_from_image(itk_image), itk.array_from_image(itk_image_back))


def test_2d_itkwasm_image(input_images):  # noqa: ARG001
    itk_image = itk.imread(test_data_dir / "input" / "cthead1.png")
    itk_image_dict = itk.dict_from_image(itk_image)
    itkwasm_image = itkwasm.Image(**itk_image_dict)
    ngff_image = itk_image_to_ngff_image(itkwasm_image)
    itkwasm_image_back = ngff_image_to_itk_image(ngff_image)
    assert np.array_equal(
        np.asarray(itkwasm_image.data), np.asarray(itkwasm_image_back.data)
    )
