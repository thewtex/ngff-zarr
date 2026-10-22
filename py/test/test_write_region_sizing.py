# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""Large writes split into as few regions as memory_target allows."""

import dask.array as da
import numpy as np
import pytest
from ngff_zarr import config, to_ngff_image
from ngff_zarr.to_ngff_zarr import _compute_write_regions


def _region_bytes(region, itemsize):
    return int(np.prod([s.stop - (s.start or 0) for s in region])) * itemsize


@pytest.mark.parametrize(
    ("memory_target", "expected_regions"),
    [(4 * 2**30, 2), (64 * 2**20, 128), (16 * 2**20, 512)],
    ids=["slabs", "planes", "strips"],
)
def test_regions_fill_memory_target(monkeypatch, memory_target, expected_regions):
    # 8 GiB of uint16 in 128-voxel chunks; nothing is computed.
    arr = da.zeros((1024, 2048, 2048), dtype=np.uint16, chunks=128)
    image = to_ngff_image(arr, dims=("z", "y", "x"))
    monkeypatch.setattr(config, "memory_target", memory_target)

    regions = _compute_write_regions(
        image, ("z", "y", "x"), arr, arr.shape, 2, 1, (128, 128, 128)
    )

    assert len(regions) == expected_regions
    assert max(_region_bytes(r, 2) for r in regions) <= memory_target


@pytest.mark.parametrize(
    ("shape", "chunks", "start", "stored", "memory_target"),
    [
        # Shards of 256 over 128-voxel dask chunks, as chunks_per_shard=2 writes.
        ((1024, 2048, 2048), 128, 0, (256, 256, 256), 64 * 2**20),
        # Slicing leaves an 8-slice leading z chunk.
        ((1032, 2048, 2048), 128, 120, (128, 128, 128), 4 * 2**30),
        # Targets just short of a whole number of 8 MiB slices, rows or columns.
        ((64, 2048, 2048), (2, 128, 128), 0, (2, 128, 128), 12 * 2**20),
        ((64, 2048, 2048), (2, 128, 128), 0, (2, 128, 128), 2**20 - 1),
        ((64, 2048, 2048), (2, 128, 128), 0, (2, 128, 128), 2**17 - 1),
    ],
    ids=["shards", "partial-chunk", "slabs", "planes", "strips"],
)
def test_regions_stay_within_memory_target(
    monkeypatch, shape, chunks, start, stored, memory_target
):
    arr = da.zeros(shape, dtype=np.uint16, chunks=chunks)[start:]
    image = to_ngff_image(arr, dims=("z", "y", "x"))
    monkeypatch.setattr(config, "memory_target", memory_target)

    regions = _compute_write_regions(
        image, ("z", "y", "x"), arr, arr.shape, 2, 1, stored
    )

    assert max(_region_bytes(r, 2) for r in regions) <= memory_target
