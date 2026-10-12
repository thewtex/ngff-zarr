# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""An .ozx is staged beside its destination, not in the system temp dir."""

import sys
from pathlib import Path

import numpy as np
from ngff_zarr import to_multiscales, to_ngff_image, to_ome_zarr


def test_ozx_staged_next_to_the_archive(tmp_path, monkeypatch):
    # The package exports a function under the module's name.
    writer = sys.modules["ngff_zarr.to_ngff_zarr"]
    staged = []
    real_write = writer.write_store_to_zip

    def spy(source, *args, **kwargs):
        staged.append(Path(source))
        return real_write(source, *args, **kwargs)

    monkeypatch.setattr(writer, "write_store_to_zip", spy)
    archive = tmp_path / "out.ozx"
    image = to_ngff_image(np.ones((8, 8), np.uint8), dims=("y", "x"))
    to_ome_zarr(archive, to_multiscales(image, scale_factors=[]))

    assert staged[0].parent == tmp_path
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out.ozx"]
