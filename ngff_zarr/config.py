from dataclasses import dataclass

from pathlib import Path
from platformdirs import user_cache_dir

@dataclass
class NgffZarrConfig:
    # Rough memory limit in bytes
    memory_limit: int = int(1e9)
    cache_dir: Path = Path(user_cache_dir('ngff-zarr'))

config = NgffZarrConfig()
