from typing import Sequence, Dict
from pathlib import Path
from dataclasses import dataclass

from numpy.typing import ArrayLike
import pytest
import pooch
import itk

from ngff_zarr import itk_image_to_ngff_image

test_data_ipfs_cid = "bafybeia73oin2pi7hdbfquvrad5jctvcn3vubk3slvh47fvwtwlvbdxqfm"
test_data_sha256 = "29695d19bb6bac5b31b95bdbe451ff5535f202bdc9b43731f9a5fc8e0cfa1230"


test_dir = Path(__file__).resolve().parent
extract_dir = "data"
test_data_dir = test_dir / extract_dir
test_data = pooch.create(
    path=test_dir,
    base_url=f"https://{test_data_ipfs_cid}.ipfs.w3s.link/ipfs/{test_data_ipfs_cid}/",
    registry={
        "data.tar.gz": f"sha256:{test_data_sha256}",
    },
    retry_if_failed=5,
)


@pytest.fixture
def input_images():
    # untar = pooch.Untar(extract_dir=extract_dir)
    # test_data.fetch("data.tar.gz", processor=untar)
    result = {}

    # store = DirectoryStore(
    #     test_data_dir / "input" / "cthead1.zarr", dimension_separator="/"
    # )
    # image_ds = xr.open_zarr(store)
    # image_da = image_ds.cthead1
    image = itk.imread(test_data_dir / "input" / "cthead1.png")
    image_ngff = itk_image_to_ngff_image(image)
    result["cthead1"] = image_ngff

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


# def verify_against_baseline(dataset_name, baseline_name, multiscale):
#     store = DirectoryStore(
#         test_data_dir / f"baseline/{dataset_name}/{baseline_name}", dimension_separator="/"
#     )
#     dt = open_datatree(store, engine="zarr", mode="r")
#     xr.testing.assert_equal(dt.ds, multiscale.ds)
#     for scale in multiscale.children:
#         xr.testing.assert_equal(dt[scale].ds, multiscale[scale].ds)

# def store_new_image(dataset_name, baseline_name, multiscale_image):
#     '''Helper method for writing output results to disk
#        for later upload as test baseline'''
#     store = DirectoryStore(
#         test_data_dir / f"baseline/{dataset_name}/{baseline_name}", dimension_separator="/",
#     )
#     multiscale_image.to_zarr(store)
