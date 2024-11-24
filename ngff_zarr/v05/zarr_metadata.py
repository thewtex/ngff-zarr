from typing import List, Optional
from dataclasses import dataclass

from ..v04.zarr_metadata import Axis, Transform, Dataset


@dataclass
class Metadata:
    axes: List[Axis]
    datasets: List[Dataset]
    coordinateTransformations: Optional[List[Transform]]
    name: str = "image"
