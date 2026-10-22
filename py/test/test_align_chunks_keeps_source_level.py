# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
import ngff_zarr as nz
import numpy as np
import pytest
import zarr
from ngff_zarr import Methods

# An axis shorter than the requested chunk and of odd length makes the first
# block indivisible by the shrink factor, so the downsampler realigns chunks
# before it shrinks. That realignment must not leak into the levels already in
# the pyramid, whose chunks are what to_ngff_zarr writes.


@pytest.mark.parametrize(
    "method",
    [
        Methods.ITKWASM_GAUSSIAN,
        Methods.ITKWASM_BIN_SHRINK,
        Methods.DASK_IMAGE_GAUSSIAN,
    ],
)
def test_requested_chunks_survive_downsampling(method):
    data = np.arange(11 * 96 * 96, dtype=np.uint16).reshape(11, 96, 96)
    image = nz.to_ngff_image(data, dims=["z", "y", "x"])

    multiscales = nz.to_multiscales(image, scale_factors=[2], chunks=16, method=method)

    assert multiscales.images[0].data.chunksize == (11, 16, 16)
    np.testing.assert_array_equal(multiscales.images[0].data.compute(), data)


def test_requested_chunks_survive_on_intermediate_levels():
    data = np.zeros((1, 11, 37, 53), dtype=np.uint16)
    image = nz.to_ngff_image(data, dims=["c", "z", "y", "x"])

    multiscales = nz.to_multiscales(image, scale_factors=[2, 4], chunks=8)

    assert multiscales.images[0].data.chunksize == (1, 8, 8, 8)
    assert multiscales.images[1].data.chunksize == (1, 5, 8, 8)


def test_written_scale0_keeps_requested_chunks(tmp_path):
    data = np.arange(11 * 96 * 96, dtype=np.uint16).reshape(11, 96, 96)
    image = nz.to_ngff_image(data, dims=["z", "y", "x"])
    multiscales = nz.to_multiscales(image, scale_factors=[2], chunks=16)

    store = tmp_path / "chunks.ome.zarr"
    # 0.4 is Zarr v2, which zarr-python 2 and 3 can both open.
    nz.to_ome_zarr(store, multiscales, version="0.4")

    level0 = zarr.open_array(store / "scale0" / "image", mode="r")
    assert level0.chunks == (11, 16, 16)
    np.testing.assert_array_equal(level0[:], data)
