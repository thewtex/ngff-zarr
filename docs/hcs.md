# 🧬 High Content Screening (HCS) Support

NGFF-Zarr provides comprehensive support for High Content Screening (HCS) data,
implementing the plate and well metadata structures defined in the OME-Zarr
specification. This enables working with multi-well plate data commonly used in
drug discovery, phenotypic screening, and high-throughput imaging experiments.

## Background

High Content Screening is a method used in biological research and drug
discovery that involves the automated analysis of complex biological systems
using fluorescence microscopy. In HCS experiments, biological samples are
typically arranged in multi-well plates (such as 96-well or 384-well plates),
with each well containing different experimental conditions, treatments, or
samples.

The OME-Zarr specification defines a hierarchical structure for HCS data:

- **Plate**: The top-level container representing a physical screening plate
- **Wells**: Individual wells within the plate, identified by row and column
  coordinates
- **Fields**: Multiple imaging fields (fields of view) within each well
- **Acquisitions**: Different time points or experimental conditions

## Implementation

NGFF-Zarr's HCS implementation follows the OME-Zarr v0.4 specification and
provides:

### Core Data Classes

- `Plate`: Plate-level metadata including rows, columns, wells, and acquisitions
- `PlateWell`: Well location and path information
- `PlateRow` / `PlateColumn`: Row and column definitions
- `PlateAcquisition`: Acquisition metadata for time series or multi-condition
  experiments
- `Well`: Well-level metadata with image references
- `WellImage`: Individual field/image metadata within a well

### High-Level Interface

- `HCSPlate`: Convenient wrapper for plate-level operations
- `HCSWell`: Convenient wrapper for well-level operations and image access

## Reading HCS Data

### Loading a Plate

```python
import ngff_zarr as nz

# Load HCS plate data
plate = nz.from_hcs_zarr("path/to/hcs.ome.zarr")

print(f"Plate: {plate.metadata.name}")
print(f"Rows: {len(plate.metadata.rows)}")
print(f"Columns: {len(plate.metadata.columns)}")
print(f"Wells: {len(plate.metadata.wells)}")
```

### Accessing Wells

```python
# Get a specific well by row and column
well = plate.get_well("A", "1")  # Row A, Column 1

if well:
    print(f"Well A/1 has {len(well.images)} field(s)")

    # Access images/fields within the well
    image = well.get_image(0)  # First field
    if image:
        print(f"Image shape: {image.images[0].data.shape}")
        print(f"Image axes: {image.images[0].dims}")
```

### Working with Acquisitions

```python
# If the plate has multiple acquisitions (time points)
if plate.metadata.acquisitions:
    for acq in plate.metadata.acquisitions:
        print(f"Acquisition {acq.id}: {acq.name}")

    # Get image from specific acquisition
    well = plate.get_well("A", "1")
    image = well.get_image_by_acquisition(acquisition_id=0, field_index=0)
```

### Iterating Through Plate Data

```python
# Iterate through all wells
for well_meta in plate.metadata.wells:
    row_name = plate.metadata.rows[well_meta.rowIndex].name
    col_name = plate.metadata.columns[well_meta.columnIndex].name

    well = plate.get_well(row_name, col_name)
    if well:
        print(f"Well {row_name}/{col_name}: {len(well.images)} field(s)")

        # Process each field in the well
        for field_idx in range(len(well.images)):
            image = well.get_image(field_idx)
            if image:
                # Process the multiscale image
                ngff_image = image.images[0]  # First scale level
                print(f"  Field {field_idx}: {ngff_image.data.shape}")
```

## Writing HCS Data

### Creating Plate Metadata

```python
from ngff_zarr.v04.zarr_metadata import (
    Plate, PlateColumn, PlateRow, PlateWell,
    Well, WellImage, PlateAcquisition
)

# Define plate structure
columns = [PlateColumn(name="1"), PlateColumn(name="2")]
rows = [PlateRow(name="A"), PlateRow(name="B")]

# Define wells
wells = [
    PlateWell(path="A/1", rowIndex=0, columnIndex=0),
    PlateWell(path="A/2", rowIndex=0, columnIndex=1),
    PlateWell(path="B/1", rowIndex=1, columnIndex=0),
    PlateWell(path="B/2", rowIndex=1, columnIndex=1),
]

# Create plate metadata
plate_metadata = Plate(
    name="My Screening Plate",
    columns=columns,
    rows=rows,
    wells=wells,
    field_count=2  # Number of fields per well
)
```

### Writing Well Data

```python
# Create well metadata with multiple fields
well_images = [
    WellImage(path="0"),  # Field 0
    WellImage(path="1"),  # Field 1
]

well_metadata = Well(images=well_images)

# Write to zarr (this is typically done as part of a larger workflow)
# The exact implementation depends on your specific data and requirements
```

## Validation

HCS data can be validated against the OME-Zarr specification:

```python
# Validate HCS metadata during loading
plate = nz.from_hcs_zarr("path/to/hcs.ome.zarr", validate=True)
```

This uses the appropriate HCS-specific JSON schema validation rather than the
standard image schema.

## Integration with Standard Workflows

HCS data integrates seamlessly with other NGFF-Zarr functionality:

```python
# Each field is a standard multiscale image
well = plate.get_well("A", "1")
image = well.get_image(0)

# Use standard multiscale operations
first_scale = image.images[0]
print(f"Dimensions: {first_scale.dims}")
print(f"Scale: {first_scale.scale}")
print(f"Translation: {first_scale.translation}")

# Access the dask array for computation
data_array = first_scale.data
processed = data_array.mean(axis=0)  # Example processing
```

## Common Use Cases

### Drug Screening Analysis

```python
import numpy as np

plate = nz.from_hcs_zarr("drug_screen.ome.zarr")

results = {}
for well_meta in plate.metadata.wells:
    row = plate.metadata.rows[well_meta.rowIndex].name
    col = plate.metadata.columns[well_meta.columnIndex].name

    well = plate.get_well(row, col)
    if well:
        # Analyze all fields in the well
        field_intensities = []
        for field_idx in range(len(well.images)):
            image = well.get_image(field_idx)
            if image:
                data = image.images[0].data.compute()
                mean_intensity = np.mean(data)
                field_intensities.append(mean_intensity)

        results[f"{row}/{col}"] = np.mean(field_intensities)

print("Well intensities:", results)
```

### Time Series Analysis

```python
# For plates with multiple acquisitions (time points)
plate = nz.from_hcs_zarr("time_series.ome.zarr")

if plate.metadata.acquisitions:
    well = plate.get_well("A", "1")

    time_series = []
    for acq in plate.metadata.acquisitions:
        image = well.get_image_by_acquisition(acq.id, field_index=0)
        if image:
            data = image.images[0].data.compute()
            time_series.append(data.mean())

    print(f"Time series for well A/1: {time_series}")
```

## Technical Details

### Metadata Structure

The HCS implementation uses the following metadata hierarchy:

```
Plate Root (.zattrs)
├── plate/
│   ├── name
│   ├── rows[]
│   ├── columns[]
│   ├── wells[]
│   ├── acquisitions[]
│   └── field_count
└── bioformats2raw.layout (optional)

Well Groups (e.g., A/1/.zattrs)
├── well/
│   ├── images[]
│   └── version
└── Standard multiscale metadata for each field
```

### Path Conventions

- Plate root: Contains plate metadata and well groups
- Well paths: `{row}/{column}/` (e.g., `A/1/`, `B/2/`)
- Field paths: `{row}/{column}/{field}/` (e.g., `A/1/0/`, `A/1/1/`)

### Performance Considerations

- **Lazy Loading**: Images are loaded on-demand
- **Dask Integration**: Large datasets can be processed in chunks
- **Memory Management**: Only requested wells and fields are loaded into memory
- **Parallel Access**: Multiple wells can be processed in parallel using Dask

## See Also

- [OME-Zarr HCS Specification](https://ngff.openmicroscopy.org/latest/#plate-md)
- [Python API Reference](./python.md)
- [Specification Features](./spec_features.md)
