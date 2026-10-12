# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""The store information the tools report matches the store."""

from pathlib import Path

import pytest
from ngff_zarr import from_ome_zarr

from ngff_zarr_mcp import utils
from ngff_zarr_mcp.models import ConversionOptions
from ngff_zarr_mcp.tools import convert_to_ome_zarr, read_ngff_zarr, validate_ome_zarr


async def _convert(test_input_file, output: Path, **kwargs):
    options = ConversionOptions(output_path=str(output), chunks=64, **kwargs)
    result = await convert_to_ome_zarr([str(test_input_file)], options)
    assert result.success, result.error
    return result


@pytest.mark.asyncio
async def test_chunks_are_the_chunk_shape(test_input_file, tmp_path):
    """Not the sizes of the blocks along the first axis."""
    result = await _convert(test_input_file, tmp_path / "image.ome.zarr")

    assert result.store_info["chunks"] == [64, 64, 64]


@pytest.mark.asyncio
async def test_an_ozx_archive_is_a_store(test_input_file, tmp_path):
    archive = tmp_path / "image.ozx"
    result = await _convert(test_input_file, archive, ome_zarr_version="0.5")

    assert result.store_info["version"] == "0.5"
    assert result.store_info["size_bytes"] == archive.stat().st_size
    assert result.store_info["num_files"] == 1
    validation = await validate_ome_zarr(str(archive))
    assert validation.valid, validation.errors
    assert validation.version == "0.5"


@pytest.mark.asyncio
async def test_a_url_and_its_storage_options_reach_the_reader(
    test_input_file, tmp_path, monkeypatch
):
    """from_ome_zarr reads a URL itself, sharded stores included.

    An fsspec mapping in its place cannot read sharded Zarr v3 arrays.
    """
    source = tmp_path / "image.ome.zarr"
    await _convert(test_input_file, source)
    calls = []

    def from_ome_zarr_spy(store, **kwargs):
        calls.append((store, kwargs.get("storage_options")))
        return from_ome_zarr(str(source))

    monkeypatch.setattr(utils, "from_ome_zarr", from_ome_zarr_spy)
    monkeypatch.setattr(utils, "read_root_attrs", lambda *args: {})
    url = "https://example.com/image.ome.zarr"
    storage_options = {"anon": True}

    result = await read_ngff_zarr(url, storage_options)

    assert result.success, result.error
    assert calls == [(url, storage_options)]
