# ngff-zarr

[![PyPI - Version](https://img.shields.io/pypi/v/ngff-zarr.svg)](https://pypi.org/project/ngff-zarr)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ngff-zarr.svg)](https://pypi.org/project/ngff-zarr)
[![Test](https://github.com/thewtex/ngff-zarr/actions/workflows/test.yml/badge.svg)](https://github.com/thewtex/ngff-zarr/actions/workflows/test.yml)

-----

A lean and kind Open Microscopy Environment (OME) Next Generation File Format (NGFF) Zarr implementation.

**Table of Contents**

- [Installation](#installation)
- [Features](#features)
- [Usage](#usage)
- [See also](#see-also)
- [License](#license)

## Installation

To install the command line interface (CLI):

```console
pip install 'ngff-zarr[cli]'
```

## Features

- Minimal dependencies
- Work with arbitrary Zarr store types
- Lazy, parallel, and web ready -- no local filesystem required
- Process extremely large datasets
- Multiple downscaling methods
- Supports Python>=3.7
- Implements version 0.4 of the [OME-Zarr
NGFF specification](https://github.com/ome/ngff)

## Usage

### Convert an image file

Convert any scientific image file format supported by either [itk](https://wasm.itk.org/docs/image_formats), [tifffile](https://pypi.org/project/tifffile/), or [imageio](https://imageio.readthedocs.io/en/stable/formats/index.html).

Example:

```console
ngff-zarr -i ./MR-head.nrrd -o ./MR-head.zarr
```

![ngff-zarr convert](https://i.imgur.com/I7gTG52.png)

### Convert an image volume slice series

Note the quotes:

```console
ngff-zarr -i "series/*.tif" -o ome-ngff.zarr
```

### Print information about generated multiscales

To print information about the input, omit the output argument.

```console
ngff-zarr -i ./MR-head.nrrd
```

![ngff-zarr information](https://i.imgur.com/25RhzG2.png)

### Specify output chunks

```console
ngff-zarr -c 64 -i ./MR-head.nrrd
```

![ngff-zarr output chunks](https://i.imgur.com/OGHyGQe.png)

### Specify metadata

```console
ngff-zarr --dims "z" "y" "x" --scale x 1.4 y 1.4 z 2.5 --translation x 6.24 y 360.0 z 332.5 --name LIDC2 -i "series/*.tif"
```

![ngff-zarr metadata](https://i.imgur.com/AecFANr.png)


### Limit memory consumption

Limit memory consumption by passing a rough memory limit in human-readable units, e.g. *8GB* with the `--memory-target` option.

```console
ngff-zarr --memory-target 50M -i ./LIDCFull.vtk -o ./LIDCFull.zarr
```

![ngff-zarr memory-target](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZmQ2NzVmMzU0NDA5ZDcyNzczNTU3MWE2YjczZjY5YmJkNWE4OTRhZSZjdD1n/ODobGeUYQr9wrE9J2s/giphy.gif)

### More options

```console
ngff-zarr --help
```

## See also

- [ome-zarr-py](https://github.com/ome/ome-zarr-py)
- [multiscale-spatial-image](https://github.com/spatial-image/multiscale-spatial-image)

## License

`ngff-zarr` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

## Development

Contributions are welcome and appreciated.

To run the unit tests:

```sh
pip install -e ".[test,dask-image,itk,cli]"
pytest
```

### Updating test data

1. Generate new test data tarball

```
cd test/data
tar cvf ../data.tar baseline input
gzip -9 ../data.tar
```

2. Upload the data to [web3.storage](https://web3.storage)

3. Upload the `test_data_ipfs_cid` (from web3.storage web UI) and `test_data_sha256` (`sh256sum ../data.tar.gz`) variables in *test/_data.py*.
