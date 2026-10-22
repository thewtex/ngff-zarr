# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""Every tool option either reaches the written store or is an error.

An option the tool accepts and then drops is reported as success, so the
agent believes the store has a chunking, unit or version it does not have.
"""

import json
from pathlib import Path

import pytest
from ngff_zarr import from_ome_zarr

from ngff_zarr_mcp import tools
from ngff_zarr_mcp.models import ConversionOptions, OptimizationOptions
from ngff_zarr_mcp.tools import convert_to_ome_zarr, optimize_zarr_store


def _ondisk_version(store: Path) -> str:
    zattrs = store / ".zattrs"
    if zattrs.exists():
        return json.loads(zattrs.read_text())["multiscales"][0]["version"]
    return json.loads((store / "zarr.json").read_text())["attributes"]["ome"]["version"]


async def _convert(inputs: list[str], output: Path, **kwargs):
    options = ConversionOptions(output_path=str(output), **kwargs)
    return await convert_to_ome_zarr(inputs, options)


@pytest.mark.asyncio
@pytest.mark.parametrize("version", ["0.4", "0.5", "0.6"])
async def test_optimize_rechunks_and_keeps_the_version(
    test_input_file, tmp_path, version
):
    source = tmp_path / "source.ome.zarr"
    converted = await _convert(
        [str(test_input_file)], source, ome_zarr_version=version, chunks=64
    )
    assert converted.success, converted.error

    output = tmp_path / "optimized.ome.zarr"
    result = await optimize_zarr_store(
        OptimizationOptions(
            input_path=str(source), output_path=str(output), chunks=[32]
        )
    )

    assert result.success, result.error
    assert _ondisk_version(output) == _ondisk_version(source) == version
    assert from_ome_zarr(str(output)).images[0].data.chunksize == (32, 32, 32)


@pytest.mark.asyncio
async def test_convert_applies_units(test_input_file, tmp_path):
    output = tmp_path / "units.ome.zarr"
    units = {"z": "micrometer", "y": "micrometer", "x": "micrometer"}

    result = await _convert([str(test_input_file)], output, units=units)

    assert result.success, result.error
    assert from_ome_zarr(str(output)).images[0].axes_units == units


@pytest.mark.asyncio
async def test_convert_rechunks_a_zarr_input(test_input_file, tmp_path):
    source = tmp_path / "source.ome.zarr"
    assert (await _convert([str(test_input_file)], source, chunks=64)).success

    output = tmp_path / "rechunked.ome.zarr"
    result = await _convert([str(source)], output, chunks=[32])

    assert result.success, result.error
    assert from_ome_zarr(str(output)).images[0].data.chunksize == (32, 32, 32)


@pytest.mark.asyncio
async def test_convert_refuses_metadata_options_for_a_zarr_input(
    test_input_file, tmp_path
):
    """A Zarr store input keeps its own metadata, so overrides are an error."""
    source = tmp_path / "source.ome.zarr"
    assert (await _convert([str(test_input_file)], source)).success

    output = tmp_path / "renamed.ome.zarr"
    result = await _convert([str(source)], output, name="brain")

    assert not result.success
    assert "name" in result.error
    assert not output.exists()


@pytest.mark.asyncio
async def test_storage_options_reach_the_reader(test_input_file, tmp_path, monkeypatch):
    source = tmp_path / "source.ome.zarr"
    assert (await _convert([str(test_input_file)], source)).success
    calls = []

    def from_ome_zarr_spy(store, **kwargs):
        calls.append(kwargs.get("storage_options"))
        return from_ome_zarr(str(source))

    monkeypatch.setattr(tools, "from_ome_zarr", from_ome_zarr_spy)
    remote = "s3://bucket/image.ome.zarr"
    storage_options = {"anon": True}

    converted = await _convert(
        [remote], tmp_path / "copy.ome.zarr", storage_options=storage_options
    )
    assert converted.success, converted.error
    assert calls == [storage_options]
