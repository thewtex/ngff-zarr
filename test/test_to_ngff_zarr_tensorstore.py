import tempfile
from packaging import version

import pytest
import zarr
from dask_image import imread

from ngff_zarr import (
    Methods,
    to_multiscales,
    to_ngff_zarr,
    from_ngff_zarr,
    config,
    to_ngff_image,
)

from ._data import verify_against_baseline

zarr_version = version.parse(zarr.__version__)


def test_gaussian_isotropic_scale_factors(input_images):
    pytest.importorskip("tensorstore")

    dataset_name = "cthead1"
    image = input_images[dataset_name]
    baseline_name = "2_4/ITKWASM_GAUSSIAN.zarr"
    multiscales = to_multiscales(image, [2, 4], method=Methods.ITKWASM_GAUSSIAN)
    with tempfile.TemporaryDirectory() as tmpdir:
        to_ngff_zarr(tmpdir, multiscales, use_tensorstore=True)
        multiscales = from_ngff_zarr(tmpdir)
        verify_against_baseline(dataset_name, baseline_name, multiscales)

    baseline_name = "auto/ITKWASM_GAUSSIAN.zarr"
    multiscales = to_multiscales(image, method=Methods.ITKWASM_GAUSSIAN)
    with tempfile.TemporaryDirectory() as tmpdir:
        to_ngff_zarr(tmpdir, multiscales, use_tensorstore=True)
        multiscales = from_ngff_zarr(tmpdir)
        verify_against_baseline(dataset_name, baseline_name, multiscales)

    dataset_name = "cthead1"
    image = input_images[dataset_name]
    baseline_name = "2_3/ITKWASM_GAUSSIAN.zarr"
    multiscales = to_multiscales(image, [2, 3], method=Methods.ITKWASM_GAUSSIAN)
    with tempfile.TemporaryDirectory() as tmpdir:
        to_ngff_zarr(tmpdir, multiscales, use_tensorstore=True)
        multiscales = from_ngff_zarr(tmpdir)
        verify_against_baseline(dataset_name, baseline_name, multiscales)

    dataset_name = "MR-head"
    image = input_images[dataset_name]
    baseline_name = "2_3_4/ITKWASM_GAUSSIAN.zarr"
    multiscales = to_multiscales(image, [2, 3, 4], method=Methods.ITKWASM_GAUSSIAN)
    with tempfile.TemporaryDirectory() as tmpdir:
        to_ngff_zarr(tmpdir, multiscales, use_tensorstore=True)
        multiscales = from_ngff_zarr(tmpdir)
        verify_against_baseline(dataset_name, baseline_name, multiscales)


def test_large_image_serialization(input_images):
    pytest.importorskip("tensorstore")

    default_mem_target = config.memory_target
    config.memory_target = int(1e6)

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
    with tempfile.TemporaryDirectory() as tmpdir:
        to_ngff_zarr(tmpdir, multiscales, use_tensorstore=True)
        config.memory_target = default_mem_target
