from dataclasses import dataclass

from pathlib import Path
from platformdirs import user_cache_dir
from zarr.storage import StoreLike
import zarr

_store_dir = Path(user_cache_dir('ngff-zarr'))
default_cache_store = zarr.storage.DirectoryStore(_store_dir,
            dimension_separator='/')

try:
    import psutil
    default_memory_limit = int(psutil.virtual_memory().available*0.5)
except ImportError:
    default_memory_limit = int(1e9)


@dataclass
class NgffZarrConfig:
    # Rough memory limit in bytes
    memory_limit: int = default_memory_limit
    cache_store: StoreLike = default_cache_store

config = NgffZarrConfig()
