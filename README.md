# ngff-zarr

[![PyPI - Version](https://img.shields.io/pypi/v/ngff-zarr.svg)](https://pypi.org/project/ngff-zarr)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ngff-zarr.svg)](https://pypi.org/project/ngff-zarr)
[![Test](https://github.com/thewtex/ngff-zarr/actions/workflows/test.yml/badge.svg)](https://github.com/thewtex/ngff-zarr/actions/workflows/test.yml)
[![DOI](https://zenodo.org/badge/541840158.svg)](https://zenodo.org/badge/latestdoi/541840158)
[![Documentation Status](https://readthedocs.org/projects/ngff-zarr/badge/?version=latest)](https://ngff-zarr.readthedocs.io/en/latest/?badge=latest)

---

A lean and kind Open Microscopy Environment (OME) Next Generation File Format
(NGFF) Zarr implementation.

## Features

- Minimal dependencies
- Work with arbitrary Zarr store types
- Lazy, parallel, and web ready -- no local filesystem required
- Process extremely large datasets
- Multiple downscaling methods
- Supports Python>=3.8
- Implements version 0.4 of the
  [OME-Zarr NGFF specification](https://github.com/ome/ngff)

## Installation

To install the command line interface (CLI):

```console
pip install 'ngff-zarr[cli]'
```

## Documentation

More information an command line usage, the Python API, library features, and
how to contribute can be found in
[our documentation](https://ngff-zarr.readthedocs.io/).

## See also

- [ome-zarr-py](https://github.com/ome/ome-zarr-py)
- [multiscale-spatial-image](https://github.com/spatial-image/multiscale-spatial-image)

## License

`ngff-zarr` is distributed under the terms of the
[MIT](https://spdx.org/licenses/MIT.html) license.
