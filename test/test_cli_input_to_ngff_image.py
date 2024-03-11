import pytest
from ngff_zarr import ConversionBackend, cli_input_to_ngff_image

from ._data import test_data_dir


def test_cli_input_to_ngff_image_itk(input_images):  # noqa: ARG001
    input = [
        test_data_dir / "input" / "cthead1.png",
    ]
    image = cli_input_to_ngff_image(ConversionBackend.ITK, input)
    assert image.dims == ("y", "x")


def test_cli_input_to_ngff_image_itk_glob(input_images):  # noqa: ARG001
    input = [
        test_data_dir / "input" / "lung_series" / "*.png",
    ]
    image = cli_input_to_ngff_image(ConversionBackend.ITK, input)
    assert image.dims == ("z", "y", "x")


def test_cli_input_to_ngff_image_itk_list(input_images):  # noqa: ARG001
    input = [
        test_data_dir / "input" / "lung_series" / "LIDC2-025.png",
        test_data_dir / "input" / "lung_series" / "LIDC2-026.png",
        test_data_dir / "input" / "lung_series" / "LIDC2-027.png",
    ]
    image = cli_input_to_ngff_image(ConversionBackend.ITK, input)
    assert image.dims == ("z", "y", "x")


def test_cli_input_to_ngff_image_tifffile(input_images):  # noqa: ARG001
    input = [
        test_data_dir / "input" / "bat-cochlea-volume.tif",
    ]
    image = cli_input_to_ngff_image(ConversionBackend.TIFFFILE, input)
    assert image.dims == ("z", "y", "x")


def test_cli_input_to_ngff_image_cucim(input_images):  # noqa: ARG001
    pytest.importorskip("cucim")
    input = [
        test_data_dir
        / "input"
        / "TCGA-C8-A26W-01A-01-TSA.5870b3d4-a81e-423e-bb93-5897ebc922a3.svs"
    ]
    image = cli_input_to_ngff_image(ConversionBackend.CUCIM, input)
    assert image.dims == ("y", "x", "c")
    assert image.translation["x"] == 0.0
    assert image.translation["y"] == 0.0
    assert image.scale["x"] == 1.0
    assert image.scale["y"] == 1.0


def test_cli_input_to_ngff_image_imageio(input_images):  # noqa: ARG001
    input = [
        test_data_dir / "input" / "cthead1.png",
    ]
    image = cli_input_to_ngff_image(ConversionBackend.IMAGEIO, input)
    assert image.dims == ("y", "x")
