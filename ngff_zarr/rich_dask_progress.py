from typing import Dict, Optional

from rich.progress import TaskID
from dask.callbacks import Callback

class RichDaskProgress(Callback):
    def __init__(self, rich_progress):
        self.rich = rich_progress
        self.tasks: Dict[str, Optional[TaskId]] = {}

    def add_next_task(self, description: str):
        """Next task to be started with .compute(), .persist()"""
        self.next_task = description
        self.tasks[description] = self.rich.add_task(description)

    def _start(self, dsk):
        description = self.next_task
        dsk['ngff_zarr_task'] = description

    def _start_state(self, dsk, state):
        pass

    def _pretask(self, key, dsk, state):
        description = dsk['ngff_zarr_task']
        task = self.tasks[description]
        ndone = len(state["finished"])
        ntasks = sum(len(state[k]) for k in ["ready", "waiting", "running"]) + ndone
        self.rich.update(task, total=ntasks, completed=ndone)

    def _posttask(self, key, result, dsk, state, worker_id):
        pass

    def _finish(self, dsk, state, errored):
        description = dsk['ngff_zarr_task']
        task = self.tasks[description]
        if not errored:
            self.rich.update(task, total=1.0, completed=1.0)

class RichDaskDistributedProgress:
    def __init__(self, rich_progress):
        self.rich = rich_progress

    def add_next_task(self, description: str):
        self.rich.log(description)