from dataclasses import dataclass, field
from pathlib import Path

import dask.config
import zarr
from platformdirs import user_cache_dir
from zarr.storage import StoreLike

if dask.config.get("temporary-directory") is not None:
    _store_dir = dask.config.get("temporary-directory")
else:
    _store_dir = Path(user_cache_dir("ngff-zarr"))


def default_store_factory():
    return zarr.storage.DirectoryStore(_store_dir, dimension_separator="/")


try:
    import psutil

    default_memory_target = int(psutil.virtual_memory().available * 0.5)
except ImportError:
    default_memory_target = int(1e9)


@dataclass
class NgffZarrConfig:
    # Rough memory target in bytes
    memory_target: int = default_memory_target
    task_target: int = 50000
    cache_store: StoreLike = field(default_factory=default_store_factory)


config = NgffZarrConfig()
