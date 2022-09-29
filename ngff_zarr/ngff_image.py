from dataclasses import dataclass
from typing import Sequence, Dict

from dask.array.core import Array as DaskArray

@dataclass
class NgffImage:
    data: DaskArray
    dims: Sequence[str]
    scale: Dict[str, float]
    translation: Dict[str, float]
    name: str = "image"
