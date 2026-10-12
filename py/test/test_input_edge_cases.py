# SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
# SPDX-License-Identifier: MIT
"""Inputs the readers and the CLI must accept without crashing."""

from types import SimpleNamespace

from ngff_zarr import ConversionBackend, detect_cli_io_backend
from ngff_zarr.tiff_to_ngff_image import _extract_ome_translation_metadata


def test_binary_only_ome_tiff_has_no_translation():
    """A multi-file OME-TIFF data file points to a companion file instead of
    carrying <Image> elements."""
    tif = SimpleNamespace(
        is_ome=True,
        ome_metadata=(
            '<OME xmlns="http://www.openmicroscopy.org/Schemas/OME/2016-06">'
            '<BinaryOnly MetadataFile="plate.companion.ome" '
            'UUID="urn:uuid:00000000-0000-0000-0000-000000000000"/></OME>'
        ),
    )
    assert _extract_ome_translation_metadata(tif, 0) == (None, None)


def test_lif_file_name_with_dots():
    backend = detect_cli_io_backend(["2024.01.15 sample.lif"])
    assert backend is ConversionBackend.LIFFILE
