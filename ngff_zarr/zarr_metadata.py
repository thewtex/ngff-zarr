from dataclasses import dataclass, field
from typing import Union, Optional, List
from typing_extensions import Literal

SupportedDims = Union[
    Literal["c"], Literal["x"], Literal["y"], Literal["z"], Literal["t"]
]

SpatialDims = Union[Literal["x"], Literal["y"], Literal["z"]]
AxesType = Union[Literal["time"], Literal["space"], Literal["channel"]]
SpaceUnits = Union[
    Literal["angstrom"],
    Literal["attometer"],
    Literal["centimeter"],
    Literal["decimeter"],
    Literal["exameter"],
    Literal["femtometer"],
    Literal["foot"],
    Literal["gigameter"],
    Literal["hectometer"],
    Literal["inch"],
    Literal["kilometer"],
    Literal["megameter"],
    Literal["meter"],
    Literal["micrometer"],
    Literal["mile"],
    Literal["millimeter"],
    Literal["nanometer"],
    Literal["parsec"],
    Literal["petameter"],
    Literal["picometer"],
    Literal["terameter"],
    Literal["yard"],
    Literal["yoctometer"],
    Literal["yottameter"],
    Literal["zeptometer"],
    Literal["zettameter"],
]
TimeUnits = Union[
    Literal["attosecond"],
    Literal["centisecond"],
    Literal["day"],
    Literal["decisecond"],
    Literal["exasecond"],
    Literal["femtosecond"],
    Literal["gigasecond"],
    Literal["hectosecond"],
    Literal["hour"],
    Literal["kilosecond"],
    Literal["megasecond"],
    Literal["microsecond"],
    Literal["millisecond"],
    Literal["minute"],
    Literal["nanosecond"],
    Literal["petasecond"],
    Literal["picosecond"],
    Literal["second"],
    Literal["terasecond"],
    Literal["yoctosecond"],
    Literal["yottasecond"],
    Literal["zeptosecond"],
    Literal["zettasecond"],
]
Units = Union[SpaceUnits, TimeUnits]


@dataclass
class Axis:
    name: SupportedDims
    type: AxesType
    unit: Optional[Units] = None


@dataclass
class Scale:
    scale: List[float]
    type: str = "scale"


@dataclass
class Translation:
    translation: List[float]
    type: str = "translation"


Transform = Union[Scale, Translation]


@dataclass
class Dataset:
    path: str
    coordinateTransformations: List[Transform]


@dataclass
class Metadata:
    axes: List[Axis]
    datasets: List[Dataset]
    name: str = "image"
    version: str = "0.4"
    coordinateTransformations: List[Transform] = field(default_factory=list)
