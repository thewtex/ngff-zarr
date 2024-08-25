import sys
from pathlib import Path

import pooch
import pytest
from itkwasm_image_io import imread
from ngff_zarr import itk_image_to_ngff_image, to_ngff_zarr
from zarr.storage import DirectoryStore, MemoryStore

test_data_ipfs_cid = "bafybeif6s65ezzpejhcj5366nwvyljfcj4brmefqtjxymbrcicbo3ggcei"
test_data_sha256 = "c70c024e79d3dd6ecff86b9da1367b761d5f157f5cdad529c1fe482d2bce699a"

test_dir = Path(__file__).resolve().parent
extract_dir = "data"
test_data_dir = test_dir / extract_dir


@pytest.fixture(scope="package")
def input_images():
    untar = pooch.Untar(extract_dir=extract_dir)
    pooch.retrieve(
        fname="data.tar.gz",
        path=test_dir,
        url=f"https://itk.mypinata.cloud/ipfs/{test_data_ipfs_cid}/data.tar.gz",
        # url=f"https://{test_data_ipfs_cid}.ipfs.w3s.link/ipfs/{test_data_ipfs_cid}/data.tar.gz",
        known_hash=f"sha256:{test_data_sha256}",
        processor=untar,
    )
    result = {}

    image = imread(test_data_dir / "input" / "cthead1.png")
    image_ngff = itk_image_to_ngff_image(image)
    result["cthead1"] = image_ngff

    result["lung_series"] = test_data_dir / "input" / "lung_series" / "*"

    image = imread(
        test_data_dir / "input" / "brain_two_components.nrrd",
    )
    image_ngff = itk_image_to_ngff_image(image)
    result["brain_two_components"] = image_ngff

    image = imread(test_data_dir / "input" / "2th_cthead1.png")
    image_ngff = itk_image_to_ngff_image(image)
    result["2th_cthead1"] = image_ngff

    image = imread(test_data_dir / "input" / "MR-head.nrrd")
    image_ngff = itk_image_to_ngff_image(image)
    result["MR-head"] = image_ngff

    return result


def store_equals(baseline_store, test_store):
    baseline_keys = set(baseline_store.keys())
    test_keys = set(test_store.keys())
    if baseline_keys != test_keys:
        sys.stderr.write("test keys != baseline keys\n")
        sys.stderr.write(f"baseline - test: {baseline_keys.difference(test_keys)}, \n")
        sys.stderr.write(f"test - baseline: {test_keys.difference(baseline_keys)}, \n")
        return False
    for k in baseline_keys:
        if baseline_store[k] != test_store[k]:
            sys.stderr.write(f"test value != baseline value for key {k}\n")
            sys.stderr.write(f"baseline: {baseline_store[k]}, \n")
            sys.stderr.write(f"test: {test_store[k]}, \n")
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
