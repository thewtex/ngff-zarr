import dask
import dask.array as da
import numpy as np

from .methods._support import _spatial_dims
from .multiscales import Multiscales
from .to_ngff_image import to_ngff_image
from .zarr_metadata import Axis, Dataset, Metadata, Scale, Translation


def _read_region_data(cuimage, location, size, level):
    return np.array(cuimage.read_region(location, size, level))


def cucim_image_to_multiscales(cuimage) -> Multiscales:
    dims = tuple(d for d in cuimage.dims.lower())
    spatial_dims = set(dims).intersection(_spatial_dims)
    spatial_dims = [d for d in dims if d in spatial_dims]
    spatial_dims_str = "".join(spatial_dims).upper()

    images = []

    axes = []
    for dim in dims:
        unit = None
        if dim in {"x", "y", "z"}:
            axis = Axis(name=dim, type="space", unit=unit)
        elif dim == "c":
            axis = Axis(name=dim, type="channel", unit=unit)
        elif dim == "t":
            axis = Axis(name=dim, type="time", unit=unit)
        else:
            msg = f"Dimension identifier is not valid: {dim}"
            raise KeyError(msg)
        axes.append(axis)

    for level in range(cuimage.resolutions["level_count"]):
        scale_dimensions = cuimage.resolutions["level_dimensions"][level]
        scale_downsamples = cuimage.resolutions["level_downsamples"][level]
        scale_tile_size = cuimage.resolutions["level_tile_sizes"][level]
        # hard coded for 2d
        blocks = []
        for ii in range(scale_dimensions[0] // scale_tile_size[0]):
            block_row = []
            for jj in range(scale_dimensions[1] // scale_tile_size[1]):
                location = (ii * scale_tile_size[0], jj * scale_tile_size[1])
                size = scale_tile_size
                block_row.append(
                    dask.delayed(_read_region_data)(cuimage, location, size, level)
                )
            blocks.append(block_row)
        data = da.block(blocks)

        spacing = cuimage.spacing(spatial_dims_str)
        scale = {d: 1.0 for d in spatial_dims}
        for idx, dim in enumerate(spatial_dims):
            scale[dim] = spacing[idx] * scale_downsamples

        translation = {d: 0.0 for d in spatial_dims}
        for idx, dim in enumerate(spatial_dims):
            # cucim: Should origin have a dim_order argument like spacing?
            translation[dim] = (
                cuimage.origin[idx] + spacing[idx] * scale_downsamples / 2
            )

        image = to_ngff_image(data, dims=dims, translation=translation, scale=scale)
        images.append(image)

    datasets = []
    for index, image in enumerate(images):
        path = f"scale{index}/{image.name}"
        scale = []
        for dim in image.dims:
            if dim in image.scale:
                scale.append(image.scale[dim])
            else:
                scale.append(1.0)
        translation = []
        for dim in image.dims:
            if dim in image.translation:
                translation.append(image.translation[dim])
            else:
                translation.append(1.0)
        coordinateTransformations = [Scale(scale), Translation(translation)]
        dataset = Dataset(
            path=path, coordinateTransformations=coordinateTransformations
        )
        datasets.append(dataset)
    metadata = Metadata(
        axes=axes,
        datasets=datasets,
        name=image.name,
        coordinateTransformations=None,
    )
    return Multiscales(
        images=images,
        metadata=metadata,
        scale_factors=cuimage.resolutions["level_downsamples"],
    )
