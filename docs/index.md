# ngff-zarr

[![PyPI - Version](https://img.shields.io/pypi/v/ngff-zarr.svg)](https://pypi.org/project/ngff-zarr)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ngff-zarr.svg)](https://pypi.org/project/ngff-zarr)
[![Test](https://github.com/thewtex/ngff-zarr/actions/workflows/test.yml/badge.svg)](https://github.com/thewtex/ngff-zarr/actions/workflows/test.yml)
[![DOI](https://zenodo.org/badge/541840158.svg)](https://zenodo.org/badge/latestdoi/541840158)
[![Documentation Status](https://readthedocs.org/projects/ngff-zarr/badge/?version=latest)](https://ngff-zarr.readthedocs.io/en/latest/?badge=latest)

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

::::{tab-set}

:::{tab-item} System

```shell
pip install 'ngff-zarr[cli]'
```

:::

:::{tab-item} Browser In Pyodide, e.g. the
[Pyodide REPL](https://pyodide.org/en/stable/console.html) or
[JupyterLite](https://jupyterlite.readthedocs.io/en/latest/try/lab),

````python
import micropip
await micropip.install('ngff-zarr')
:::

::::

```{toctree}
:hidden:
:maxdepth: 3

cli.md
development.md
````

```{toctree}
:hidden:
:maxdepth: 3
:caption: 📖 Reference

apidocs/index.rst
```
