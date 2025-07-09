# RFC 4: Anatomical Orientation Support

RFC 4 adds support for anatomical orientation metadata to OME-NGFF axes,
enabling precise description of spatial axis directions in biological and
medical imaging data.

## Overview

Anatomical orientation refers to the specific arrangement and directional
alignment of anatomical structures within an imaging dataset. This is crucial
for ensuring accurate alignment and comparison of images to anatomical atlases,
facilitating consistent analysis and interpretation of biological data.

## Usage

### Programmatic Usage

#### Enabling RFC 4

To enable RFC 4 support when writing OME-NGFF Zarr data, include `4` in the
`enabled_rfcs` parameter:

```python
import ngff_zarr

# Enable RFC 4 when converting to NGFF Zarr
ngff_zarr.to_ngff_zarr(
    store="output.ome.zarr",
    multiscales=multiscales,
    enabled_rfcs=[4]  # Enable RFC 4
)
```

### CLI Usage

RFC 4 can be enabled via the command line using the `--enable-rfc` flag:

```bash
# Convert a medical image with RFC 4 anatomical orientation enabled
ngff-zarr -i image.nii.gz -o output.ome.zarr --enable-rfc 4

# Enable multiple RFCs (when available)
ngff-zarr -i image.nii.gz -o output.ome.zarr --enable-rfc 4 --enable-rfc 5

# Without RFC 4 (default behavior - orientation metadata filtered out)
ngff-zarr -i image.nii.gz -o output.ome.zarr
```

### ITK Integration

When converting ITK images (including from NRRD, NIfTI, or DICOM formats),
anatomical orientation is automatically added based on ITK's LPS coordinate
system (see the sections `Anatomical Orientation Values`  and `ITK LPS Coordinate System` below for an explanation):

```python
import ngff_zarr
from itk import imread

# Read a medical image (NRRD, NIfTI, DICOM, etc.)
image = imread("image.nrrd")

# Convert to NGFF image with anatomical orientation
ngff_image = ngff_zarr.itk_image_to_ngff_image(
    image,
    add_anatomical_orientation=True
)

# Convert to multiscales and write to Zarr with RFC 4 enabled
multiscales = ngff_zarr.to_multiscales(ngff_image)
ngff_zarr.to_ngff_zarr(
    store="output.ome.zarr",
    multiscales=multiscales,
    enabled_rfcs=[4]
)
```

### ITK-Wasm Integration

Similar support is available for ITK-Wasm:

```python
import ngff_zarr
from itkwasm_image_io import imread

# Read with ITK-Wasm
image = imread("image.nii.gz")

# Convert with anatomical orientation
ngff_image = ngff_zarr.itk_image_to_ngff_image(
    image,
    add_anatomical_orientation=True
)
```

## Anatomical Orientation Values

RFC 4 supports the following anatomical orientation values:

- `left-to-right`: From left side to right lateral side
- `right-to-left`: From right side to left lateral side
- `anterior-to-posterior`: From front (anterior) to back (posterior)
- `posterior-to-anterior`: From back (posterior) to front (anterior)
- `inferior-to-superior`: From below (inferior) to above (superior)
- `superior-to-inferior`: From above (superior) to below (inferior)
- `dorsal-to-ventral`: From top/upper (dorsal) to belly/lower (ventral)
- `ventral-to-dorsal`: From belly/lower (ventral) to top/upper (dorsal)
- `dorsal-to-palmar`: From top/upper (dorsal) to palm of hand (palmar)
- `palmar-to-dorsal`: From palm of hand (palmar) to top/upper (dorsal)
- `dorsal-to-plantar`: From top/upper (dorsal) to sole of foot (plantar)
- `plantar-to-dorsal`: From sole of foot (plantar) to top/upper (dorsal)

## ITK LPS Coordinate System

ITK uses the LPS (Left-to-right, Posterior-to-anterior, Superior-to-inferior)
coordinate system by default. When converting ITK images, the following mappings
are applied:

- **X axis**: `left-to-right`
- **Y axis**: `posterior-to-anterior`
- **Z axis**: `inferior-to-superior`

## Manual Orientation Specification

You can also manually specify orientations:

```python
from ngff_zarr import (
    AnatomicalOrientation,
    AnatomicalOrientationValues,
    NgffImage
)
import dask.array as da

# Create orientation objects
x_orientation = AnatomicalOrientation(
    value=AnatomicalOrientationValues.left_to_right
)
y_orientation = AnatomicalOrientation(
    value=AnatomicalOrientationValues.anterior_to_posterior
)
z_orientation = AnatomicalOrientation(
    value=AnatomicalOrientationValues.inferior_to_superior
)

# Create NGFF image with orientations
data = da.zeros((100, 100, 100))
ngff_image = NgffImage(
    data=data,
    dims=("z", "y", "x"),
    scale={"x": 1.0, "y": 1.0, "z": 1.0},
    translation={"x": 0.0, "y": 0.0, "z": 0.0},
    axes_orientations={
        "x": x_orientation,
        "y": y_orientation,
        "z": z_orientation
    }
)
```

## Metadata Format

When RFC 4 is enabled, spatial axes in the OME-NGFF metadata include an
`orientation` field:

```json
{
  "axes": [
    {
      "name": "z",
      "type": "space",
      "unit": "micrometer",
      "orientation": {
        "type": "anatomical",
        "value": "inferior-to-superior"
      }
    },
    {
      "name": "y",
      "type": "space",
      "unit": "micrometer",
      "orientation": {
        "type": "anatomical",
        "value": "posterior-to-anterior"
      }
    },
    {
      "name": "x",
      "type": "space",
      "unit": "micrometer",
      "orientation": {
        "type": "anatomical",
        "value": "left-to-right"
      }
    }
  ]
}
```

## RFC 4 Functions

### Core Functions

- `itk_lps_to_anatomical_orientation(axis_name)`: Map ITK LPS axes to
  orientations
- `add_anatomical_orientation_to_axis(axis_dict, orientation)`: Add orientation
  to axis
- `remove_anatomical_orientation_from_axis(axis_dict)`: Remove orientation from
  axis

### Data Classes

- `AnatomicalOrientation`: Orientation specification with type and value
- `AnatomicalOrientationValues`: Enum of supported orientation values

## Compatibility

When RFC 4 is not enabled (the default), orientation metadata is automatically
filtered out during Zarr writing to maintain compatibility with standard
OME-NGFF consumers.

## Best Practices

1. **Enable RFC 4** when working with medical/biological images where
   orientation matters
2. **Use ITK integration** for automatic LPS-based orientation when converting
   from medical image formats
3. **Document orientation assumptions** in your analysis pipelines when working
   with oriented data
4. **Validate orientations** match your expectations, especially when combining
   data from different sources
