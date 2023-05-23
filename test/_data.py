from typing import Sequence, Dict
from pathlib import Path

import pytest
import pooch
import itk
from zarr.storage import DirectoryStore, MemoryStore

from ngff_zarr import itk_image_to_ngff_image, to_ngff_zarr

test_data_ipfs_cid = "bafybeid6tqv7og52ycwwwmy6wcsdzgh5a7zwyc7fnsguin3st2at35pvs4"
test_data_sha256 = "2b116ecf57856d0ca7f3f4f0f30fe4a4daa1fbc38d40a41e5c13b3cb836036c3"


test_dir = Path(__file__).resolve().parent
extract_dir = "data"
test_data_dir = test_dir / extract_dir
test_data = pooch.create(
    path=test_dir,
    base_url=f"https://{test_data_ipfs_cid}.ipfs.dweb.link/",
    registry={
        "data.tar.gz": f"sha256:{test_data_sha256}",
    },
    retry_if_failed=5,
)


@pytest.fixture
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

    image = itk.imread(test_data_dir / "input" / "brain_two_components.nrrd", itk.VariableLengthVector[itk.SS])
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
        print('test keys != baseline keys')
        print('baseline - test:', baseline_keys.difference(test_keys))
        print('test - baseline:', test_keys.difference(baseline_keys))
        return False
    for k in baseline_keys:
        if baseline_store[k] != test_store[k]:
            print(f'test value != baseline value for key {k}')
            print('baseline:', baseline_store[k])
            print('test:', test_store[k])
            return False
    return True

def verify_against_baseline(dataset_name, baseline_name, multiscales):
    baseline_store = DirectoryStore(
        test_data_dir / f"baseline/{dataset_name}/{baseline_name}", dimension_separator="/"
    )
    test_store =  MemoryStore(dimension_separator='/')
    to_ngff_zarr(test_store, multiscales)
    assert store_equals(baseline_store, test_store)

def store_new_multiscales(dataset_name, baseline_name, multiscales):
    '''Helper method for writing output results to disk
       for later upload as test baseline'''
    store = DirectoryStore(
        test_data_dir / f"baseline/{dataset_name}/{baseline_name}", dimension_separator="/",
    )
    to_ngff_zarr(store, multiscales)
