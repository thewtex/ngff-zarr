from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Sequence

from dask.array.core import Array as DaskArray

from .zarr_metadata import Units

ComputedCallback = Callable[[], None]


@dataclass
class NgffImage:
    data: DaskArray
    dims: Sequence[str]
    scale: Dict[str, float]
    translation: Dict[str, float]
    name: str = "image"
    axes_units: Optional[Mapping[str, Units]] = None
    computed_callbacks: List[ComputedCallback] = field(default_factory=list)
