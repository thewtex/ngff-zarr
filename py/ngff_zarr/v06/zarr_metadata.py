from typing import List, Optional, Union
from dataclasses import dataclass

from ..v04.zarr_metadata import Omero, MethodMetadata, AxesType, SupportedDims, Units
from ..rfc4 import AnatomicalOrientation
# from ..rfc5 import (
#     NgffBaseTransformation, NgffCoordinateSystem
# )

@dataclass
class Axis:
    name: SupportedDims
    type: AxesType
    unit: Optional[Units] = None
    orientation: Optional[AnatomicalOrientation] = None

@dataclass
class CoordinateSystem:
    name: str
    axes: List[Axis]

@dataclass
class Identity:
    type: str = "identity"
    name: str = ''


@dataclass
class Scale:
    scale: List[float]
    type: str = "scale"
    name: str = ''
    input: Union[str, CoordinateSystem] = None
    output: Union[str, CoordinateSystem] = None


@dataclass
class Translation:
    translation: List[float]
    type: str = "translation"
    name: str = ''
    input: Union[str, CoordinateSystem] = None
    output: Union[str, CoordinateSystem] = None

@dataclass
class TransformSequence:
    sequence: List[Union[Scale, Translation]]
    name: str = ''
    type: str = "sequence"
    input: Union[str, CoordinateSystem] = None
    output: Union[str, CoordinateSystem] = None

Transform = Union[Scale, Translation, TransformSequence, Identity]

@dataclass
class Dataset:
    path: str
    coordinateTransformations: List[Transform]


@dataclass
class Metadata:
    coordinateSystems: Union[NgffCoordinateSystem, List[NgffCoordinateSystem]]
    datasets: List[Dataset]
    omero: Optional[Omero] = None
    name: str = "image"
    type: Optional[str] = None
    metadata: Optional[MethodMetadata] = None

    @property
    def axes(self) -> List:
        cs = self.coordinateSystems
        if isinstance(cs, list):
            if len(cs) == 1:
                return [cs[0].get_axis(d) for d in cs[0].axes_names]
            return {_cs.name: [cs.get_axis(d) for d in _cs.axes_names] for _cs in cs}
        return [cs.get_axis(d) for d in cs.axes_names]
