# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""The write tools must not delete an existing output the caller did not offer.

The output path comes from an AI agent, and ``to_ome_zarr`` removes whatever is
at the path before writing. A path like ``~/Documents`` must come back as an
error with the directory untouched.
"""

from pathlib import Path

import pytest

from ngff_zarr_mcp.models import ConversionOptions, OptimizationOptions
from ngff_zarr_mcp.tools import convert_to_ome_zarr, optimize_zarr_store


def _options(output: Path, **kwargs) -> ConversionOptions:
    return ConversionOptions(output_path=str(output), chunks=64, **kwargs)


@pytest.mark.asyncio
async def test_convert_keeps_an_existing_directory(test_input_file, tmp_path):
    documents = tmp_path / "Documents"
    documents.mkdir()
    thesis = documents / "thesis.txt"
    thesis.write_text("only copy")

    result = await convert_to_ome_zarr([str(test_input_file)], _options(documents))
    assert not result.success
    assert "already exists" in result.error
    assert thesis.read_text() == "only copy"

    # Even when asked to overwrite, a directory that is not a Zarr store stays.
    result = await convert_to_ome_zarr(
        [str(test_input_file)], _options(documents, overwrite=True)
    )
    assert not result.success
    assert "not a Zarr store" in result.error
    assert thesis.read_text() == "only copy"


@pytest.mark.asyncio
async def test_convert_replaces_a_store_only_with_overwrite(test_input_file, tmp_path):
    output = tmp_path / "image.ome.zarr"
    first = await convert_to_ome_zarr([str(test_input_file)], _options(output))
    assert first.success, first.error

    again = await convert_to_ome_zarr([str(test_input_file)], _options(output))
    assert not again.success
    assert "already exists" in again.error

    replaced = await convert_to_ome_zarr(
        [str(test_input_file)], _options(output, overwrite=True)
    )
    assert replaced.success, replaced.error


@pytest.mark.asyncio
async def test_optimize_keeps_an_existing_output(test_input_file, tmp_path):
    source = tmp_path / "source.ome.zarr"
    converted = await convert_to_ome_zarr([str(test_input_file)], _options(source))
    assert converted.success, converted.error
    documents = tmp_path / "Documents"
    documents.mkdir()
    thesis = documents / "thesis.txt"
    thesis.write_text("only copy")

    result = await optimize_zarr_store(
        OptimizationOptions(input_path=str(source), output_path=str(documents))
    )
    assert not result.success
    assert "already exists" in result.error
    assert thesis.read_text() == "only copy"


@pytest.mark.asyncio
async def test_convert_keeps_a_file_that_is_not_a_store(test_input_file, tmp_path):
    """A file named like an archive is replaced only when it is a Zarr store."""
    notes = tmp_path / "notes.ozx"
    notes.write_text("only copy")

    result = await convert_to_ome_zarr(
        [str(test_input_file)], _options(notes, overwrite=True)
    )
    assert not result.success
    assert "not a Zarr store" in result.error
    assert notes.read_text() == "only copy"
