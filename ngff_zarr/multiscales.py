from typing import Union, Optional, Sequence, Mapping, Dict, Tuple, Any, List
from dataclasses import dataclass

from .ngff_image import NgffImage
from .zarr_metadata import Metadata
from .methods import Methods

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

