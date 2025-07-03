from dataclasses import asdict

import dask.array

from .ngff_image import NgffImage


def itk_image_to_ngff_image(
    itk_image,
    # anatomical_axes: bool = False,
    # axis_names: List[str] = None,
    # axis_units: List[str] = None,
):
    """Convert an itk.Image or an itkwasm.Image to an NgffImage, preserving spatial metadata."""

    # Handle anatomical axes
    # Todo: add axis names support to NGFF
    # axis_names = None
    # if anatomical_axes and (axis_names is None):
    #     axis_names = {"x": "right-left", "y": "anterior-posterior", "z": "inferior-superior"}

    # # Orient 3D image so that direction is identity wrt RAI coordinates
    # image_dimension = image.GetImageDimension()
    # input_direction = np.array(image.GetDirection())
    # oriented_image = image
    # if anatomical_axes and image_dimension == 3 and not (np.eye(image_dimension) == input_direction).all():
    #     desired_orientation = itk.SpatialOrientationEnums.ValidCoordinateOrientations_ITK_COORDINATE_ORIENTATION_RAI
    #     oriented_image = itk.orient_image_filter(image, use_image_direction=True, desired_coordinate_orientation=desired_orientation)
    # elif anatomical_axes and image_dimension != 3:
    #     raise ValueError(f'Cannot use anatomical axes for input image of size {image_dimension}')

    image_dict = None

    try:
        import itk

        if isinstance(itk_image, (itk.Image, itk.VectorImage)):
            image_dict = itk.dict_from_image(itk_image)
    except ImportError:
        pass

    try:
        import itkwasm

        if isinstance(itk_image, itkwasm.Image):
            image_dict = asdict(itk_image)
    except ImportError:
        pass

    if image_dict is None:
        msg = (
            "Could not import itk or itkwasm or input is not itk.Image or itkwasm.Image"
        )
        raise RuntimeError(msg)

    data = dask.array.from_array(image_dict["data"])
    ndim = data.ndim
    if ndim == 3 and image_dict["imageType"]["components"] > 1:
        dims = ("y", "x", "c")
    elif ndim < 4:
        dims = ("z", "y", "x")[-ndim:]
    elif ndim < 5:
        dims = ("z", "y", "x", "c")
    elif ndim < 6:
        dims = ("t", "z", "y", "x", "c")
    all_spatial_dims = {"x", "y", "z"}
    spatial_dims = [dim for dim in dims if dim in all_spatial_dims]

    spacing = image_dict["spacing"]
    scale = {dim: spacing[::-1][idx] for idx, dim in enumerate(spatial_dims)}

    origin = image_dict["origin"]
    translation = {dim: origin[::-1][idx] for idx, dim in enumerate(spatial_dims)}

    return NgffImage(data, dims, scale, translation)
