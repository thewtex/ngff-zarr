# 👋 Quick start

## Installation

```shell
pip install "ngff-zarr[cli]"
```

## Command line conversion

```shell
ngff-zarr -i ./cthead1.png -o ./cthead1.ome.zarr
```

## NumPy array-like to OME-Zarr

```python
import ngff_zarr as nz
import numpy as np

data = np.random.randint(0, 256, int(1e6)).reshape((1000, 1000))
ngff_image = nz.to_ngff_image(data)
multiscales = nz.to_multiscales(ngff_image)
nz.to_ngff_zarr('example.ome.zarr', multiscales)
```
