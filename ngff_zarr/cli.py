#!/usr/bin/env python

import sys
import argparse
from pathlib import Path

from dask.callbacks import Callback
from rich.progress import Progress
from rich.console import Console
from zarr.storage import DirectoryStore

if __name__ == "__main__" and __package__ is None:
    __package__ = "ngff_zarr"

from .ngff_image import NgffImage
from .to_multiscales import to_multiscales
from .to_ngff_zarr import to_ngff_zarr
from .cli_input_to_ngff_image import cli_input_to_ngff_image
from .detect_cli_input_backend import detect_cli_input_backend, conversion_backends_values

class RichDaskProgress(Callback):
    def __init__(self, rich_progress):
        self.rich = rich_progress

    def _start(self, dsk):
        pass

    def _start_state(self, dsk, state):
        self.task1 = self.rich.add_task("[red]Downloading...", total=len(state['ready']))
        pass

    def _pretask(self, key, dsk, state):
        self._state = state

    def _posttask(self, key, result, dsk, state, worker_id):
        self.rich.update(self.task1)

    def _finish(self, dsk, state, errored):
        self._running = False

console = Console()

def main():
    parser = argparse.ArgumentParser(description='Convert datasets to and from the OME-Zarr Next Generation File Format.')
    parser.add_argument('input', nargs='+', help='Input image(s)')
    parser.add_argument('output', help='Output image')
    parser.add_argument('-q', '--quiet', action='store_true', help='Do not display progress information')
    parser.add_argument('--input-backend', choices=conversion_backends_values, help='Input conversion backend')

    args = parser.parse_args()

    if args.input_backend is None:
        input_backend = detect_cli_input_backend(args.input)
    else:
        input_backend = ConversionBackend(args.input_backend)

    output_store = DirectoryStore(args.output, dimension_separator='/')

    if args.quiet:
        ngff_image = cli_input_to_ngff_image(input_backend, args.input)
        multiscales = to_multiscales(ngff_image)
        to_ngff_zarr(output_store, multiscales)
    else:
        with Progress() as progress:
            rich_dask_progress = RichDaskProgress(progress)
            rich_dask_progress.register()

        # convert_to_zarr(input_type, args.input)

if __name__ == '__main__':
    main()
