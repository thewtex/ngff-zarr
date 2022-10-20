from collections.abc import MutableMapping
from pathlib import Path
from typing import Union

import dask.array
import zarr
from zarr.storage import BaseStore

from .ngff_image import NgffImage
from .to_multiscales import Multiscales
from .zarr_metadata import Axis, Dataset, Metadata, Scale, Translation


def from_ngff_zarr(
    store: Union[MutableMapping, str, Path, BaseStore],
) -> Multiscales:
    """
    Read an OME-Zarr NGFF Multiscales data structure from a Zarr store.

    store : MutableMapping, str or Path, zarr.storage.BaseStore
        Store or path to directory in file system.


    Returns
    -------

    multiscales: multiscale ngff image with dask-chunked arrays for data

    """

    root = zarr.open_group(store, mode="r")
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
    metadata = Metadata(
        axes=axes,
        datasets=datasets,
        name=name,
        version=metadata["version"],
        coordinateTransformations=coordinateTransformations,
    )

    return Multiscales(images, metadata)
