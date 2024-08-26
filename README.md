# ngff-zarr

[![PyPI - Version](https://img.shields.io/pypi/v/ngff-zarr.svg)](https://pypi.org/project/ngff-zarr)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ngff-zarr.svg)](https://pypi.org/project/ngff-zarr)
[![Test](https://github.com/thewtex/ngff-zarr/actions/workflows/pixi-test.yml/badge.svg)](https://github.com/thewtex/ngff-zarr/actions/workflows/pixi-test.yml)
[![DOI](https://zenodo.org/badge/541840158.svg)](https://zenodo.org/badge/latestdoi/541840158)
[![Documentation Status](https://readthedocs.org/projects/ngff-zarr/badge/?version=latest)](https://ngff-zarr.readthedocs.io/en/latest/?badge=latest)

---

A lean and kind Open Microscopy Environment (OME) Next Generation File Format
(NGFF) Zarr implementation.

## ✨ Features

- Minimal dependencies
- Work with arbitrary Zarr store types
- Lazy, parallel, and web ready -- no local filesystem required
- Process extremely large datasets
- Multiple downscaling methods
- Supports Python>=3.8
- Implements version 0.4 of the
  [OME-Zarr NGFF specification](https://github.com/ome/ngff)

## Documentation

More information an command line usage, the Python API, library features, and
how to contribute can be found in
[our documentation](https://ngff-zarr.readthedocs.io/).

## See also

- [ome-zarr-py](https://github.com/ome/ome-zarr-py)
- [multiscale-spatial-image](https://github.com/spatial-image/multiscale-spatial-image)
- [itk-ioomezarrngff](https://github.com/InsightSoftwareConsortium/ITKIOOMEZarrNGFF)
- [iohub](https://czbiohub-sf.github.io/iohub/)
- [pydantic-ome-ngff](https://janeliascicomp.github.io/pydantic-ome-ngff/)
- [aicsimageio](https://allencellmodeling.github.io/aicsimageio/)
- [bfio](https://bfio.readthedocs.io/)

## License

`ngff-zarr` is distributed under the terms of the
[MIT](https://spdx.org/licenses/MIT.html) license.
