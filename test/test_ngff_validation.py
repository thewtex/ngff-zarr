import json
from typing import Dict

import numpy as np
import urllib3
import zarr
from jsonschema import Draft202012Validator
from ngff_zarr import Multiscales, to_multiscales, to_ngff_zarr
from referencing import Registry, Resource

HTTP = urllib3.PoolManager()

NGFF_URI = "https://ngff.openmicroscopy.org"


def load_schema(version: str = "0.4", strict: bool = False) -> Dict:
    strict_str = ""
    if strict:
        strict_str = "strict_"
    response = HTTP.request(
        "GET", f"{NGFF_URI}/{version}/schemas/{strict_str}image.schema"
    )
    return json.loads(response.data.decode())


def check_valid_ngff(multiscale: Multiscales):
    store = zarr.storage.MemoryStore(dimension_separator="/")
    store = zarr.storage.DirectoryStore("/tmp/test.zarr", dimension_separator="/")
    to_ngff_zarr(store, multiscale)
    zarr.convenience.consolidate_metadata(store)
    metadata = json.loads(store.get(".zmetadata"))["metadata"]
    ngff = metadata[".zattrs"]

    image_schema = load_schema(version="0.4", strict=False)
    # strict_image_schema = load_schema(version="0.4", strict=True)
    registry = Registry().with_resource(
        NGFF_URI, resource=Resource.from_contents(image_schema)
    )
    validator = Draft202012Validator(image_schema, registry=registry)
    # registry_strict = Registry().with_resource(NGFF_URI, resource=Resource.from_contents(strict_image_schema))
    # strict_validator = Draft202012Validator(strict_schema, registry=registry_strict)

    validator.validate(ngff)
    # Need to add NGFF metadata property
    # strict_validator.validate(ngff)


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
