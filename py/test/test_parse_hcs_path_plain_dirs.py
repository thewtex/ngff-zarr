# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""A directory merely named *.zarr is a folder, not a store to split at."""

import numpy as np
from ngff_zarr import (
    ConversionBackend,
    detect_cli_io_backend,
    from_ome_zarr,
    to_multiscales,
    to_ngff_image,
    to_ome_zarr,
)
from ngff_zarr.parse_metadata import _parse_hcs_path


def test_file_inside_a_plain_zarr_named_folder(tmp_path):
    folder = tmp_path / "run.zarr"
    folder.mkdir()
    path = str(folder / "img.tif")

    assert _parse_hcs_path(path) == (path, None)
    assert detect_cli_io_backend([path]) is ConversionBackend.TIFFFILE


def test_store_inside_a_plain_zarr_named_folder(tmp_path):
    store = tmp_path / "proj.zarr" / "img"
    image = to_ngff_image(np.ones((8, 8), np.uint8), dims=("y", "x"))
    to_ome_zarr(store, to_multiscales(image, scale_factors=[]))

    assert from_ome_zarr(store).images[0].data.shape == (8, 8)


def test_sub_path_of_a_real_store_still_splits(tmp_path):
    store = tmp_path / "plate.zarr"
    image = to_ngff_image(np.ones((8, 8), np.uint8), dims=("y", "x"))
    to_ome_zarr(store, to_multiscales(image, scale_factors=[]))

    assert _parse_hcs_path(str(store / "A" / "1")) == (str(store), "A/1")
