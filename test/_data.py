import sys
from pathlib import Path

import itk
import pooch
import pytest
from ngff_zarr import itk_image_to_ngff_image, to_ngff_zarr
from zarr.storage import DirectoryStore, MemoryStore

test_data_ipfs_cid = "bafybeidycdocaf7muhwt73m6vxfeaxfidbq7prvnhgn4tzrpxmpui5rila"
test_data_sha256 = "675a2cb532cb6fbabfd2b1e19f26f05b059ac51f0b611eed1164d8dd1a22e4cb"

test_dir = Path(__file__).resolve().parent
extract_dir = "data"
test_data_dir = test_dir / extract_dir


@pytest.fixture(scope="package")
def input_images():
    untar = pooch.Untar(extract_dir=extract_dir)
    pooch.retrieve(
        fname="data.tar.gz",
        path=test_dir,
        url=f"https://{test_data_ipfs_cid}.ipfs.w3s.link",
        known_hash=f"sha256:{test_data_sha256}",
        processor=untar,
    )
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


def store_equals(baseline_store, test_store):
    baseline_keys = set(baseline_store.keys())
    test_keys = set(test_store.keys())
    if baseline_keys != test_keys:
        sys.stderr.write("test keys != baseline keys\n")
        sys.stderr.write("baseline - test:", baseline_keys.difference(test_keys), "\n")
        sys.stderr.write("test - baseline:", test_keys.difference(baseline_keys), "\n")
        return False
    for k in baseline_keys:
        if baseline_store[k] != test_store[k]:
            sys.stderr.write(f"test value != baseline value for key {k}\n")
            sys.stderr.write("baseline:", baseline_store[k], "\n")
            sys.stderr.write("test:", test_store[k], "\n")
            return False
    return True


def verify_against_baseline(dataset_name, baseline_name, multiscales):
    baseline_store = DirectoryStore(
        test_data_dir / f"baseline/{dataset_name}/{baseline_name}",
        dimension_separator="/",
    )
    test_store = MemoryStore(dimension_separator="/")
    to_ngff_zarr(test_store, multiscales)
    assert store_equals(baseline_store, test_store)


def store_new_multiscales(dataset_name, baseline_name, multiscales):
    """Helper method for writing output results to disk
    for later upload as test baseline"""
    store = DirectoryStore(
        test_data_dir / f"baseline/{dataset_name}/{baseline_name}",
        dimension_separator="/",
    )
    to_ngff_zarr(store, multiscales)
