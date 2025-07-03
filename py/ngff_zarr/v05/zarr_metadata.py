from typing import List, Optional
from dataclasses import dataclass

from ..v04.zarr_metadata import Axis, Transform, Dataset, Omero


@dataclass
class Metadata:
    axes: List[Axis]
    datasets: List[Dataset]
    coordinateTransformations: Optional[List[Transform]]
    omero: Optional[Omero] = None
    name: str = "image"
