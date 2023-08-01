import itk
import pooch
import pytest
from ngff_zarr import itk_image_to_ngff_image

from ._data import extract_dir, test_data, test_data_dir


@pytest.fixture(scope="package")
def input_images():
    untar = pooch.Untar(extract_dir=extract_dir)
    test_data.fetch("data.tar.gz", processor=untar)
    result = {}

    # store = DirectoryStore(
    #     test_data_dir / "input" / "cthead1.zarr", dimension_separator="/"
    # )
    # image_ds = xr.open_zarr(store)
    # image_da = image_ds.cthead1
    image = itk.imread(test_data_dir / "input" / "cthead1.png")
    image_ngff = itk_image_to_ngff_image(image)
    result["cthead1"] = image_ngff

    result["lung_series"] = test_data_dir / "input" / "lung_series" / "*"

    image = itk.imread(
        test_data_dir / "input" / "brain_two_components.nrrd",
        itk.VariableLengthVector[itk.SS],
    )
    image_ngff = itk_image_to_ngff_image(image)
    result["brain_two_components"] = image_ngff

    # store = DirectoryStore(
    #     test_data_dir / "input" / "small_head.zarr", dimension_separator="/"
    # )
    # image_ds = xr.open_zarr(store)
    # image_da = image_ds.small_head
    # result["small_head"] = image_da

    # store = DirectoryStore(
    #     test_data_dir / "input" / "2th_cthead1.zarr",
    # )
    # image_ds = xr.open_zarr(store)
    # image_da = image_ds['2th_cthead1']
    # result["2th_cthead1"] = image_da

    return result
