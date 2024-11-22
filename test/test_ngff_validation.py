import json

import numpy as np
import zarr
from ngff_zarr import Multiscales, to_multiscales, to_ngff_zarr, validate


def check_valid_ngff(multiscale: Multiscales):
    store = zarr.storage.MemoryStore(dimension_separator="/")
    store = zarr.storage.DirectoryStore("/tmp/test.zarr", dimension_separator="/")
    to_ngff_zarr(store, multiscale)
    zarr.convenience.consolidate_metadata(store)
    metadata = json.loads(store.get(".zmetadata"))["metadata"]
    ngff = metadata[".zattrs"]

    validate(ngff)
    # Need to add NGFF metadata property
    # validate(ngff, strict=True)


def test_y_x_valid_ngff():
    array = np.random.random((32, 16))
    multiscale = to_multiscales(array, [2, 4])

    check_valid_ngff(multiscale)


# def test_z_y_x_valid_ngff():
#     array = np.random.random((32, 32, 16))
#     image = to_spatial_image(array)
#     multiscale = to_multiscale(image, [2, 4])

#     check_valid_ngff(multiscale)


# def test_z_y_x_c_valid_ngff():
#     array = np.random.random((32, 32, 16, 3))
#     image = to_spatial_image(array)
#     multiscale = to_multiscale(image, [2, 4])

#     check_valid_ngff(multiscale)


# def test_t_z_y_x_c_valid_ngff():
#     array = np.random.random((2, 32, 32, 16, 3))
#     image = to_spatial_image(array)
#     multiscale = to_multiscale(image, [2, 4])

#     check_valid_ngff(multiscale)
