import numpy as np

from .methods._support import _spatial_dims
from .ngff_image import NgffImage


def _dtype_to_component_type(dtype):
    from itkwasm import FloatTypes, IntTypes

    if dtype == np.uint8:
        return IntTypes.UInt8
    if dtype == np.int8:
        return IntTypes.Int8
    if dtype == np.uint16:
        return IntTypes.UInt16
    if dtype == np.int16:
        return IntTypes.Int16
    if dtype == np.uint32:
        return IntTypes.UInt32
    if dtype == np.int32:
        return IntTypes.Int32
    if dtype == np.uint64:
        return IntTypes.UInt64
    if dtype == np.int64:
        return IntTypes.Int64
    if dtype == np.float32:
        return FloatTypes.Float32
    if dtype == np.float64:
        return FloatTypes.Float64
    msg = f"Unsupported dtype {dtype}"
    raise ValueError(msg)


def ngff_image_to_itk_image(
    ngff_image: NgffImage,
    wasm: bool = True,
):
    from itkwasm import IntTypes, PixelTypes

    dims = ngff_image.dims
    dimension = 3 if "z" in dims else 2

    componentType = _dtype_to_component_type(ngff_image.data.dtype)

    components = 1
    pixelType = PixelTypes.Scalar
    if "c" in dims:
        components = ngff_image.data.shape[dims.index("c")]
        if components == 3 and componentType == IntTypes.UInt8:
            pixelType = PixelTypes.RGB
        else:
            pixelType = PixelTypes.VariableLengthVector
    imageType = {
        "dimension": dimension,
        "componentType": str(componentType),
        "pixelType": str(pixelType),
        "components": components,
    }

    spatial_dims = [dim for dim in dims if dim in _spatial_dims]
    spatial_dims.sort()
    spacing = [ngff_image.scale[dim] for dim in spatial_dims]
    origin = [ngff_image.translation[dim] for dim in spatial_dims]
    size = [ngff_image.data.shape[dims.index(d)] for d in spatial_dims]

    # TODO: reorder as needed
    data = np.asarray(ngff_image.data)

    image_dict = {
        "imageType": imageType,
        "name": ngff_image.name,
        "origin": origin,
        "spacing": spacing,
        "direction": np.eye(dimension),
        "size": size,
        "metadata": {},
        "data": data,
    }

    if wasm:
        from itkwasm import Image

        return Image(**image_dict)

    import itk

    return itk.image_from_dict(image_dict)
