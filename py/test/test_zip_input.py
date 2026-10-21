# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""A plain .zip of an OME-Zarr store reads like an .ozx archive."""

import zipfile

import numpy as np
import pytest
from ngff_zarr import (
    ConversionBackend,
    detect_cli_io_backend,
    from_ome_zarr,
    to_multiscales,
    to_ngff_image,
    to_ome_zarr,
)


@pytest.mark.parametrize("version", ["0.4", "0.5"])
def test_read_zipped_store(tmp_path, version):
    data = np.arange(64, dtype=np.uint8).reshape(8, 8)
    store = tmp_path / "image.ome.zarr"
    image = to_ngff_image(data, dims=("y", "x"))
    to_ome_zarr(store, to_multiscales(image, scale_factors=[]), version=version)

    archive = tmp_path / "image.ome.zarr.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for path in sorted(store.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(store).as_posix())

    read = from_ome_zarr(archive)
    np.testing.assert_array_equal(np.asarray(read.images[0].data), data)


def test_cli_detects_zip_as_ome_zarr():
    assert detect_cli_io_backend(["image.ome.zarr.zip"]) is ConversionBackend.NGFF_ZARR


def test_cli_refuses_a_zip_output(tmp_path):
    from ngff_zarr.cli import main

    image = tmp_path / "image.ome.zarr"
    to_ome_zarr(image, to_multiscales(to_ngff_image(np.ones((8, 8), np.uint8))))
    output = tmp_path / "out.zip"

    with pytest.raises(SystemExit) as exit_info:
        main(["-i", str(image), "-o", str(output)])
    assert exit_info.value.code == 1
    assert not output.exists()
