import numpy as np
import zarr
from ngff_zarr import (
    Multiscales,
    to_multiscales,
    to_ngff_zarr,
    validate,
    from_ngff_zarr,
)
from packaging import version

zarr_version = version.parse(zarr.__version__)
zarr_version_major = zarr_version.major


def check_valid_ngff(multiscale: Multiscales):
    store = zarr.storage.MemoryStore()
    version = "0.4"
    to_ngff_zarr(store, multiscale, version=version)
    format_kwargs = {}
    if version and zarr_version_major >= 3:
        format_kwargs = {"zarr_format": 2} if version == "0.4" else {"zarr_format": 3}
    root = zarr.open_group(store, mode="r", **format_kwargs)

    validate(root.attrs.asdict())
    # Need to add NGFF metadata property
    # validate(ngff, strict=True)

    from_ngff_zarr(store, validate=True, version=version)


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
