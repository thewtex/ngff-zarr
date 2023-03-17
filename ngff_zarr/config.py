from dataclasses import dataclass

@dataclass
class NgffZarrConfig:
    # Rough memory limit in bytes
    memory_limit: int = int(1e9)

config = Config()