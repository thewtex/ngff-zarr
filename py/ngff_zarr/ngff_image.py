from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Union

from dask.array.core import Array as DaskArray

from .v04.zarr_metadata import Units
from .v06.zarr_metadata import Transform, CoordinateSystem, Scale, TransformSequence, Translation
from .rfc4 import AnatomicalOrientation

ComputedCallback = Callable[[], None]


@dataclass
class NgffImage:
    data: DaskArray
    transformations: Optional[Transform] = None
    name: str = "image"
    axes_orientations: Optional[Mapping[str, AnatomicalOrientation]] = None
    computed_callbacks: List[ComputedCallback] = field(default_factory=list)

    @property
    def coordinate_systems(self) -> Union[List[CoordinateSystem], CoordinateSystem]:
        if self.transformations is not None:
            return [c for c in [self.transformations.input, self.transformations.output] if c is not None]
        return None

    @property
    def dims(self) -> List[str]:
        return [ax.name for ax in self.coordinate_systems[0].axes]
    
    @property
    def axes_units(self) -> Mapping[str, Units]:
        return {ax.name: ax.unit for ax in self.coordinate_systems[0].axes if ax.unit is not None}

    @property
    def scale(self) -> Mapping[str, float]:
        spatial_axes = [ax.name for ax in self.transformations.output.axes if ax.type == "space"]
        if isinstance(self.transformations, Scale):
            t = self.transformations

        elif isinstance(self.transformations, TransformSequence):
            for t in self.transformations.sequence:
                if isinstance(t, Scale):
                    break

        return {spatial_axes[i]: s for i, s in enumerate(t.scale)}
    
    @property
    def translation(self) -> Mapping[str, float]:
        spatial_axes = [ax.name for ax in self.transformations.output.axes if ax.type == "space"]
        if isinstance(self.transformations, Translation):
            t = self.transformations

        elif isinstance(self.transformations, TransformSequence):
            for t in self.transformations.sequence:
                if isinstance(t, Translation):
                    break

        return {spatial_axes[i]: t.translation[i] for i in range(len(spatial_axes))}