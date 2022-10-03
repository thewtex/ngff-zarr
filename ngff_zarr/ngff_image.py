from dataclasses import dataclass
from typing import Sequence, Dict, Optional, Mapping

from dask.array.core import Array as DaskArray
from .zarr_metadata import Units


@dataclass
class NgffImage:
    data: DaskArray
    dims: Sequence[str]
    scale: Dict[str, float]
    translation: Dict[str, float]
    name: str = "image"
    axes_units: Optional[Mapping[str, Units]] = None
