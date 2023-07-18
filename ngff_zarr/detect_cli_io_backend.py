import sys
from enum import Enum
from pathlib import Path
from typing import List

conversion_backends = [
    ("NGFF_ZARR", "ngff_zarr"),
    ("ZARR_ARRAY", "zarr"),
    ("ITK", "itk"),
    ("TIFFFILE", "tifffile"),
    ("IMAGEIO", "imageio"),
]
conversion_backends_values = [b[1] for b in conversion_backends]
ConversionBackend = Enum("ConversionBackend", conversion_backends)


def detect_cli_io_backend(input: List[str]) -> ConversionBackend:
    if (Path(input[0]) / ".zarray").exists():
        return ConversionBackend.ZARR_ARRAY

    extension = "".join(Path(input[0]).suffixes).lower()

    ngff_zarr_supported_extensions = (".zarr",)
    if extension in ngff_zarr_supported_extensions:
        return ConversionBackend.NGFF_ZARR

    itk_supported_extensions = (
        ".bmp",
        ".dcm",
        ".gipl",
        ".hdf5",
        ".jpg",
        ".jpeg",
        ".iwi",
        ".iwi.cbor",
        ".lsm",
        ".mnc",
        ".mnc.gz",
        ".mnc2",
        ".mgh",
        ".mhz",
        ".mha",
        ".mhd",
        ".mrc",
        ".nia",
        ".nii",
        ".nii.gz",
        ".hdr",
        ".nrrd",
        ".nhdr",
        ".png",
        ".pic",
        ".vtk",
        ".isq",  # Requires pip install itk-ioscanco,
        ".fdf",  # Requires pip install itk-iofdf
    )

    if extension in itk_supported_extensions:
        return ConversionBackend.ITK

    try:
        import tifffile

        tifffile_supported_extensions = [
            f".{ext}" for ext in tifffile.TIFF.FILE_EXTENSIONS
        ]
        if extension in tifffile_supported_extensions:
            return ConversionBackend.TIFFFILE
    except ImportError:
        from rich import print

        print("[red]Please install the [i]tifffile[/i] package")
        sys.exit(1)

    return ConversionBackend.IMAGEIO
