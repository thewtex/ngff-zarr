from typing import Union, Optional, Sequence, Hashable, Mapping
from collections.abc import MutableMapping
from pathlib import Path

from zarr.storage import BaseStore
from numpy.typing import ArrayLike
import numpy as np

AllInteger = Union[
    np.uint8, np.int8, np.uint16, np.int16, np.uint32, np.int32, np.uint64, np.int64
]
AllFloat = Union[np.float32, np.float64]

def to_zarr(store: Union[MutableMapping, str, Path, BaseStore],
    array: ArrayLike,
    dims: Optional[Sequence[Union["t", "z", "y", "x", "c"]]] = None,
    scale: Optional[Union[Mapping[Hashable, float]]] = None,
    translation: Optional[Union[Mapping[Hashable, float]]] = None,
    name: str = "image",
    axis_units: Optional[Union[Mapping[Hashable, str]]] = None,
    mode: str = "w",
    encoding=None,
    **kwargs):
    """
    Write an image pixel array and metadata to a Zarr store with the OME-NGFF standard data model.

    array_like:
        Multi-dimensional array that provides the image pixel values.

    dims: sequence of hashable, optional
        Tuple specifying the data dimensions.
        Values should drawn from: {'t', 'z', 'y', 'x', 'c'} for time, third spatial direction
        second spatial direction, first spatial dimension, and channel or
        component, respectively spatial dimension, and time, respectively.

    scale: dict of floats, optional
        Pixel spacing for the spatial dims

    translation: dict of floats, optional
        Origin or offset of the center of the first pixel.

    name: str, optional
        Name of the resulting xarray DataArray

    axis_names: dict of str, optional
        Long names for the dim axes, e.g. {'x': 'x-axis'} or {'x': 'anterior-posterior'}

    store : MutableMapping, str or Path, optional
        Store or path to directory in file system

    mode : {{"w", "w-", "a", "r+", None}, default: "w"
        Persistence mode: “w” means create (overwrite if exists); “w-” means create (fail if exists);
        “a” means override existing variables (create if does not exist); “r+” means modify existing
        array values only (raise an error if any metadata or shapes would change). The default mode
        is “a” if append_dim is set. Otherwise, it is “r+” if region is set and w- otherwise.

    kwargs :
        Additional keyword arguments to be passed to ``datatree.DataTree.to_zarr``
    """

    multiscales = []
    scale0 = self[self.groups[1]]
    for name in scale0.ds.data_vars.keys():

        ngff_datasets = []
        for child in self.children:
            image = self[child].ds
            scale_transform = []
            translate_transform = []
            for dim in image.dims:
                if len(image.coords[dim]) > 1 and np.issubdtype(image.coords[dim].dtype, np.number):
                    scale_transform.append(
                        float(image.coords[dim][1] - image.coords[dim][0])
                    )
                else:
                    scale_transform.append(1.0)
                if len(image.coords[dim]) > 0 and np.issubdtype(image.coords[dim].dtype, np.number):
                    translate_transform.append(float(image.coords[dim][0]))
                else:
                    translate_transform.append(0.0)

            ngff_datasets.append(
                {
                    "path": f"{self[child].name}/{name}",
                    "coordinateTransformations": [
                        {
                            "type": "scale",
                            "scale": scale_transform,
                        },
                        {
                            "type": "translation",
                            "translation": translate_transform,
                        },
                    ],
                }
            )

        image = scale0.ds
        axes = []
        for axis in image.dims:
            if axis == "t":
                axes.append({"name": "t", "type": "time"})
            elif axis == "c":
                axes.append({"name": "c", "type": "channel"})
            else:
                axes.append({"name": axis, "type": "space"})
            if "units" in image.coords[axis].attrs:
                axes[-1]["unit"] = image.coords[axis].attrs["units"]

        multiscales.append(
            {
                "@type": "ngff:Image",
                "version": "0.4",
                "name": name,
                "axes": axes,
                "datasets": ngff_datasets,
            }
        )

    # NGFF v0.4 metadata
    ngff_metadata = {"multiscales": multiscales, "multiscaleSpatialImageVersion": 1}
    self.ds = self.ds.assign_attrs(**ngff_metadata)

    super().to_zarr(store, **kwargs)