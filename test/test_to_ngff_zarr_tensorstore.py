import tempfile
from packaging import version
import logging
import pathlib
import shutil
import time
import uuid

import pytest
import zarr
from dask_image import imread
import numpy as np

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


def create_input_data(shape, dtype):
    """Generates random input data."""
    data = np.random.rand(*shape).astype(dtype)
    return data


def test_tensorstore_already_exists_failure():
    """
    Demonstrates the ALREADY_EXISTS failure with use_tensorstore=True during Zarr writing.
    This failure occurs with large data sizes that trigger regional writing.
    """
    # --- Logging Setup ---
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("ZarrReproducer")
    # ---------------------

    # --- Configuration ---
    BASE_OUTPUT_DIR = pathlib.Path("./zarr_reproducer_output")
    LARGE_SHAPE = (1024, 2048, 2048)  # Large shape for TensorStore test
    INPUT_DTYPE = np.float32
    PIXEL_SIZE = 1.3

    """Runs the specific reproducer test cases."""
    # Prepare output directory
    if BASE_OUTPUT_DIR.exists():
        logger.warning(f"Removing base output directory: {BASE_OUTPUT_DIR}")
        shutil.rmtree(BASE_OUTPUT_DIR)
    BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    input_array = create_input_data(LARGE_SHAPE, INPUT_DTYPE)
    output_dir_base = BASE_OUTPUT_DIR

    test_name = "tensorstore_already_exists_write_failure"
    test_output_dir = output_dir_base / test_name
    scan_id = str(uuid.uuid4())[:8]
    zarr_path = test_output_dir / f"{scan_id}.zarr"

    logger.info(f"\n--- Running Test Case: {test_name} ---")
    logger.info(f"  Input Shape: {input_array.shape}")
    logger.info(
        f"  Multiscale Method: {Methods.DASK_IMAGE_GAUSSIAN.name} (using a working method)"
    )
    logger.info("  Use TensorStore: True")
    logger.info(f"  Output Path: {zarr_path}")

    # Clean up previous run if exists
    if test_output_dir.exists():
        logger.warning(f"Removing existing directory: {test_output_dir}")
        shutil.rmtree(test_output_dir)
    test_output_dir.mkdir(parents=True)

    start_time_total = time.time()
    try:
        # 1. Create NGFF Image
        logger.info("  Creating NGFF image object...")
        image = to_ngff_image(
            input_array,
            dims=("z", "y", "x"),
            scale={"z": PIXEL_SIZE, "y": PIXEL_SIZE, "x": PIXEL_SIZE},
            axes_units={"z": "micrometer", "y": "micrometer", "x": "micrometer"},
        )

        # 2. Create Multiscales (Using a method known to work)
        logger.info("  Creating multiscales...")
        start_time_multiscale = time.time()
        multiscales = to_multiscales(
            image,
            method=Methods.DASK_IMAGE_GAUSSIAN,  # Use a reliable method
            chunks=None,  # Default chunking
            cache=False,
        )
        end_time_multiscale = time.time()
        logger.info(
            f"  Multiscales created in {end_time_multiscale - start_time_multiscale:.2f} seconds."
        )

        # 3. Write Zarr (This is expected to fail)
        logger.info("  Writing NGFF Zarr with TensorStore (expecting failure)...")
        start_time_write = time.time()
        to_ngff_zarr(
            store=zarr_path,
            multiscales=multiscales,
            use_tensorstore=True,  # Enable TensorStore
        )
        end_time_write = time.time()
        logger.info(
            f"  Zarr written in {end_time_write - start_time_write:.2f} seconds (UNEXPECTED SUCCESS)."
        )
        logger.warning(
            f"  UNEXPECTED SUCCESS: Test case '{test_name}' completed without the expected error."
        )
        return False  # Indicate unexpected success

    except ValueError as e:
        end_time_total = time.time()
        if "ALREADY_EXISTS" in str(e):
            logger.info(
                f"  EXPECTED FAILURE: Test case '{test_name}' failed as expected after {end_time_total - start_time_total:.2f} seconds."
            )
            logger.info(f"  Caught expected ValueError (ALREADY_EXISTS): {e}")
            logger.exception(f"  Error details: {e}")
            assert False  # Indicate unexpected failure type
        else:
            logger.error(
                f"  UNEXPECTED FAILURE: Test case '{test_name}' failed after {end_time_total - start_time_total:.2f} seconds with an unexpected ValueError."
            )
            logger.exception(f"  Error details: {e}")
            assert False  # Indicate unexpected failure type
