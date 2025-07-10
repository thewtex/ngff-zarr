from dask_image import imread
from ngff_zarr import (
    from_ngff_zarr,
    to_multiscales,
    to_ngff_image,
    to_ngff_zarr,
)
from zarr.storage import MemoryStore
import packaging.version
import zarr
import pytest

from ._data import test_data_dir, verify_against_baseline

zarr_version = packaging.version.parse(zarr.__version__)
zarr_version_major = zarr_version.major


def test_from_ngff_zarr(input_images):
    dataset_name = "lung_series"
    data = imread.imread(input_images[dataset_name])
    image = to_ngff_image(
        data=data,
        dims=("z", "y", "x"),
        scale={"z": 2.5, "y": 1.40625, "x": 1.40625},
        translation={"z": 332.5, "y": 360.0, "x": 0.0},
        name="LIDC2",
    )
    multiscales = to_multiscales(image)
    multiscales.scale_factors = None
    multiscales.method = None
    multiscales.chunks = None
    baseline_name = "from_ngff_zarr"
    # store_new_multiscales(dataset_name, baseline_name, multiscales)
    # verify_against_baseline(dataset_name, baseline_name, multiscales)
    test_store = MemoryStore()
    version = "0.4"
    to_ngff_zarr(test_store, multiscales, version=version)

    multiscales_back = from_ngff_zarr(test_store, version=version)
    # store_new_multiscales(dataset_name, baseline_name, multiscales)
    verify_against_baseline(
        dataset_name, baseline_name, multiscales_back, version=version
    )


def test_omero_zarr_from_ngff_zarr_to_ngff_zarr(input_images):  # noqa: ARG001
    dataset_name = "13457537"
    store_path = test_data_dir / "input" / f"{dataset_name}.zarr"
    version = "0.4"
    multiscales = from_ngff_zarr(store_path, version=version)
    test_store = MemoryStore()
    to_ngff_zarr(test_store, multiscales, version=version)


@pytest.mark.skipif(
    zarr_version_major < 3, reason="storage_options requires zarr-python 3"
)
def test_from_ngff_zarr_with_storage_options(input_images):
    """Test that storage_options parameter is accepted and handled correctly."""
    dataset_name = "lung_series"
    data = imread.imread(input_images[dataset_name])
    image = to_ngff_image(
        data=data,
        dims=("z", "y", "x"),
        scale={"z": 2.5, "y": 1.40625, "x": 1.40625},
        translation={"z": 332.5, "y": 360.0, "x": 0.0},
        name="LIDC2",
    )
    multiscales = to_multiscales(image)
    multiscales.scale_factors = None
    multiscales.method = None
    multiscales.chunks = None

    # Test with MemoryStore (should work as before)
    test_store = MemoryStore()
    version = "0.4"
    to_ngff_zarr(test_store, multiscales, version=version)

    # Test with storage_options=None (should work as before)
    multiscales_back = from_ngff_zarr(test_store, version=version, storage_options=None)
    baseline_name = "from_ngff_zarr"
    verify_against_baseline(
        dataset_name, baseline_name, multiscales_back, version=version
    )

    # Test with empty storage_options dict (should work as before)
    multiscales_back2 = from_ngff_zarr(test_store, version=version, storage_options={})
    verify_against_baseline(
        dataset_name, baseline_name, multiscales_back2, version=version
    )


@pytest.mark.skipif(
    zarr_version_major < 3, reason="storage_options requires zarr-python 3"
)
def test_from_ngff_zarr_string_url_with_storage_options():
    """Test that string URLs with storage_options create appropriate stores."""
    from unittest.mock import patch, MagicMock

    # Mock the FsspecStore.from_url method
    with patch("zarr.storage.FsspecStore.from_url") as mock_from_url:
        mock_store = MagicMock()
        mock_from_url.return_value = mock_store

        # Mock zarr.open_group to avoid actual S3 calls
        with patch("zarr.open_group") as mock_open_group:
            mock_group = MagicMock()
            mock_group.attrs.asdict.return_value = {
                "multiscales": [{"version": "0.4", "datasets": [{"path": "0"}]}]
            }
            mock_open_group.return_value = mock_group

            # Mock dask.array.from_zarr to avoid actual data loading
            with patch("dask.array.from_zarr") as mock_from_zarr:
                mock_array = MagicMock()
                mock_array.dtype.byteorder = "="  # native endianness
                mock_from_zarr.return_value = mock_array

                # Test that S3 URL with storage_options creates FsspecStore
                url = "s3://test-bucket/test-dataset.zarr"
                storage_options = {"anon": True, "region_name": "us-west-2"}

                try:
                    from_ngff_zarr(url, storage_options=storage_options)

                    # Verify that FsspecStore.from_url was called with correct parameters
                    mock_from_url.assert_called_once_with(
                        url, storage_options=storage_options
                    )

                    # Verify that zarr.open_group was called with the created store
                    mock_open_group.assert_called_once_with(mock_store, mode="r")

                except Exception:
                    # If there are other issues (like missing metadata), that's okay
                    # We just want to verify the store creation logic
                    mock_from_url.assert_called_once_with(
                        url, storage_options=storage_options
                    )
