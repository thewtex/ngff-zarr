# 🐍 Python Array API

NGFF-Zarr supports conversion of any NumPy array-like object that follows the
[Python Array API Standard](https://data-apis.org/array-api/latest/) into
OME-Zarr. This includes such objects an NumPy `ndarray`'s, Dask Arrays, PyTorch
Tensors, CuPy arrays, Zarr array, etc.

## Array to NGFF Image

Convert the array to an `NgffImage`, which is a standard
[Python dataclass](https://docs.python.org/3/library/dataclasses.html) that
represents an OME-Zarr image for a single scale.

When creating the image from the array, you can specify

- names of the `dims` from `{‘t’, ‘z’, ‘y’, ‘x’, ‘c’}`
- the `scale`, the pixel spacing for the spatial dims
- the `translation`, the origin or offset of the center of the first pixel
- a `name` for the image
- and `axes_units` with
  [UDUNITS-2 identifiers](https://ngff.openmicroscopy.org/latest/#axes-md)

```python
>>> # Load an image as a NumPy array
>>> from imageio.v3 import imread
>>> data = imread('cthead1.png')
>>> print(type(data))
<class 'numpy.ndarray'>
```

Specify optional additional metadata with `to_ngff_zarr`.

```python
>>> import ngff_zarr as nz
>>> image = nz.to_ngff_image(data,
                             dims=['y', 'x'],
                             scale={'y': 1.0, 'x': 1.0},
                             translation={'y': 0.0, 'x': 0.0})
>>> print(image)
NgffImage(
    data=dask.array<array, shape=(256, 256),
    dtype=uint8,
chunksize=(256, 256), chunktype=numpy.ndarray>,
    dims=['y', 'x'],
    scale={'y': 1.0, 'x': 1.0},
    translation={'y': 0.0, 'x': 0.0},
    name='image',
    axes_units=None,
    computed_callbacks=[]
)
```

The image data is nested in a lazy `dask.array` and chucked.

If `dims`, `scale`, or `translation` are not specified, NumPy-compatible
defaults are used.

## Generate multiscales

OME-Zarr represents images in a chunked, multiscale data structure. Use
`to_multiscales` to build a task graph that will produce a chunked, multiscale
image pyramid. `to_multiscales` has optional `scale_factors` and `chunks`
parameters. An [antialiasing method](./methods.md) can also be prescribed.

```python
>>> multiscales = nz.to_multiscales(image,
                                    scale_factors=[2,4],
                                    chunks=64)
>>> print(multiscales)
Multiscales(
    images=[
        NgffImage(
            data=dask.array<rechunk-merge, shape=(256, 256), dtype=uint8,chunksize=(64, 64), chunktype=numpy.ndarray>,
            dims=['y', 'x'],
            scale={'y': 1.0, 'x': 1.0},
            translation={'y': 0.0, 'x': 0.0},
            name='image',
            axes_units=None,
            computed_callbacks=[]
        ),
        NgffImage(
            data=dask.array<rechunk-merge, shape=(128, 128), dtype=uint8,
chunksize=(64, 64), chunktype=numpy.ndarray>,
            dims=['y', 'x'],
            scale={'x': 2.0, 'y': 2.0},
            translation={'x': 0.5, 'y': 0.5},
            name='image',
            axes_units=None,
            computed_callbacks=[]
        ),
        NgffImage(
            data=dask.array<rechunk-merge, shape=(64, 64), dtype=uint8,
chunksize=(64, 64), chunktype=numpy.ndarray>,
            dims=['y', 'x'],
            scale={'x': 4.0, 'y': 4.0},
            translation={'x': 1.5, 'y': 1.5},
            name='image',
            axes_units=None,
            computed_callbacks=[]
        )
    ],
    metadata=Metadata(
        axes=[
            Axis(name='y', type='space', unit=None),
            Axis(name='x', type='space', unit=None)
        ],
        datasets=[
            Dataset(
                path='scale0/image',
                coordinateTransformations=[
                    Scale(scale=[1.0, 1.0], type='scale'),
                    Translation(
                        translation=[0.0, 0.0],
                        type='translation'
                    )
                ]
            ),
            Dataset(
                path='scale1/image',
                coordinateTransformations=[
                    Scale(scale=[2.0, 2.0], type='scale'),
                    Translation(
                        translation=[0.5, 0.5],
                        type='translation'
                    )
                ]
            ),
            Dataset(
                path='scale2/image',
                coordinateTransformations=[
                    Scale(scale=[4.0, 4.0], type='scale'),
                    Translation(
                        translation=[1.5, 1.5],
                        type='translation'
                    )
                ]
            )
        ],
        coordinateTransformations=None,
        name='image',
        version='0.4'
    ),
    scale_factors=[2, 4],
    method=<Methods.ITKWASM_GAUSSIAN: 'itkwasm_gaussian'>,
    chunks={'y': 64, 'x': 64}
)
```

The `Multiscales` dataclass stores all the images and their metadata for each
scale according the OME-Zarr data model. Note that the correct `scale` and
`translation` for each scale are automatically computed.

## Write to Zarr

To write the multiscales to Zarr, use `to_ngff_zarr`.

```python
nz.to_ngff_zarr('cthead1.ome.zarr', multiscales)
```

Use the `.ome.zarr` extension for local directory stores by convention.

Any other
[Zarr store type](https://zarr.readthedocs.io/en/stable/api/storage.html) can
also be used.

The multiscales will be computed and written out-of-core, limiting memory usage.
