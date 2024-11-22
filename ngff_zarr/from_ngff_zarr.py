from collections.abc import MutableMapping
from pathlib import Path
from typing import Union, Optional
from packaging import version

import dask.array
import zarr
import zarr.storage

# Zarr Python 3
if hasattr(zarr.storage, "StoreLike"):
    StoreLike = zarr.storage.StoreLike
else:
    StoreLike = Union[MutableMapping, str, Path, zarr.storage.BaseStore]

from .ngff_image import NgffImage
from .to_multiscales import Multiscales
from .v04.zarr_metadata import Axis, Dataset, Scale, Translation
from .validate import validate as validate_ngff

zarr_version = version.parse(zarr.__version__)
zarr_version_major = zarr_version.major


def from_ngff_zarr(
    store: StoreLike,
    validate: bool = False,
    version: Optional[str] = None,
) -> Multiscales:
    """
    Read an OME-Zarr NGFF Multiscales data structure from a Zarr store.

    store : StoreLike
        Store or path to directory in file system.

    validate : bool
        If True, validate the NGFF metadata against the schema.

    version : string, optional
        OME-Zarr version, if known.

    Returns
    -------

    multiscales: multiscale ngff image with dask-chunked arrays for data

    """

    format_kwargs = {}
    if version and zarr_version_major >= 3:
        format_kwargs = {"zarr_format": 2} if version == "0.4" else {"zarr_format": 3}
    root = zarr.open_group(store, mode="r", **format_kwargs)
    root_attrs = root.attrs.asdict()

    if not version:
        if "ome" in root_attrs:
            version = root_attrs["ome"]["version"]
        else:
            version = root_attrs["multiscales"][0].get("version", "0.4")

    if validate:
        validate_ngff(root_attrs, version=version)

    if "ome" in root_attrs:
        metadata = root.attrs["ome"]["multiscales"][0]
    else:
        metadata = root.attrs["multiscales"][0]

    dims = [a["name"] for a in metadata["axes"]]

    name = "image"
    if name in metadata:
        name = metadata["name"]

    units = {d: None for d in dims}
    for axis in metadata["axes"]:
        if "unit" in axis:
            units[axis["name"]] = axis["unit"]

    images = []
    datasets = []
    for dataset in metadata["datasets"]:
        data = dask.array.from_zarr(store, component=dataset["path"])

        scale = {d: 1.0 for d in dims}
        translation = {d: 0.0 for d in dims}
        coordinateTransformations = []
        for transformation in dataset["coordinateTransformations"]:
            if "scale" in transformation:
                scale = transformation["scale"]
                scale = dict(zip(dims, scale))
                coordinateTransformations.append(Scale(transformation["scale"]))
            elif "translation" in transformation:
                translation = transformation["translation"]
                translation = dict(zip(dims, translation))
                coordinateTransformations.append(
                    Translation(transformation["translation"])
                )
        datasets.append(
            Dataset(
                path=dataset["path"],
                coordinateTransformations=coordinateTransformations,
            )
        )

        ngff_image = NgffImage(data, dims, scale, translation, name, units)
        images.append(ngff_image)

    metadata.pop("@type", None)
    axes = [Axis(**axis) for axis in metadata["axes"]]
    coordinateTransformations = None
    if "coordinateTransformations" in metadata:
        coordinateTransformations = metadata["coordinateTransformations"]
    if version == "0.5":
        from .v05.zarr_metadata import Metadata

        metadata = Metadata(
            axes=axes,
            datasets=datasets,
            name=name,
            coordinateTransformations=coordinateTransformations,
        )
    else:
        from .v04.zarr_metadata import Metadata

        metadata = Metadata(
            axes=axes,
            datasets=datasets,
            name=name,
            version=metadata["version"],
            coordinateTransformations=coordinateTransformations,
        )

    return Multiscales(images, metadata)
