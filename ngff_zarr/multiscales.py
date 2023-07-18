from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from .methods import Methods
from .ngff_image import NgffImage
from .zarr_metadata import Metadata


@dataclass
class Multiscales:
    images: List[NgffImage]
    metadata: Metadata
    scale_factors: Optional[Sequence[Union[Dict[str, int], int]]] = None
    method: Optional[Methods] = None
    chunks: Optional[
        Union[
            int,
            Tuple[int, ...],
            Tuple[Tuple[int, ...], ...],
            Mapping[Any, Union[None, int, Tuple[int, ...]]],
        ]
    ] = None
