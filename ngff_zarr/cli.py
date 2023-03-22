#!/usr/bin/env python

import sys
import argparse
from pathlib import Path

from dask.callbacks import Callback
from dask.array.image import imread as daimread
from rich.progress import Progress
from rich.console import Console
from zarr.storage import DirectoryStore

if __name__ == "__main__" and __package__ is None:
    __package__ = "ngff_zarr"

from .itk_image_to_ngff_image import itk_image_to_ngff_image
from .ngff_image import NgffImage
from .to_multiscales import to_multiscales
from .to_ngff_zarr import to_ngff_zarr

class RichDaskProgress(Callback):

    def __init__(self, rich_progress):
        self.rich = rich_progress

    def _start(self, dsk):
        pass

    def _start_state(self, dsk, state):
        self.task1 = self.rich.add_task("[red]Downloading...", total=len(state['ready']))
        print(dir(self.rich))
        pass

    def _pretask(self, key, dsk, state):
        self._state = state

    def _posttask(self, key, result, dsk, state, worker_id):
        self.rich.update(self.task1)

    def _finish(self, dsk, state, errored):
        self._running = False

console = Console()

def cli_input_to_ngff_image(backend: ConversionBackend, input) -> NgffImage:
    if backend is ConversionBackend.ITK:
        import itk
        print(input)
        if len(input) == 1:
            if '*' in input[0]:
                def imread(filename):
                    image = itk.imread(filename)
                    return itk.array_from_image(image)
                da = daimread(input[0], imread=imread)
                return to_ngff_image(da)
            else:
                image = itk.imread(input[0])
                return itk_image_to_ngff_image(image)
        image = itk.imread(input)
        return itk_image_to_ngff_image(input)
    elif backend is ConversionBackend.TIFFFILE:
        # TODO
        pass
    elif backend is ConversionBackend.IMAGEIO:
        # TODO
        pass


def main():
    parser = argparse.ArgumentParser(description='Convert datasets to and from the OME-Zarr Next Generation File Format.')
    parser.add_argument('input', nargs='+', help='Input image(s)')
    parser.add_argument('output', help='Output image')
    parser.add_argument('-q', '--quiet', action='store_true', help='Do not display progress information')
    parser.add_argument('--input-backend', choices=conversion_backends_values, help='Input conversion backend')


    args = parser.parse_args()
    print(args.input_backend)
    print(args.input)

    if args.input_backend is None:
        input_backend = detect_input_backend(args.input)
    else:
        input_backend = ConversionBackend(args.input_backend)

    print(input_backend)
    output_store = DirectoryStore(args.output, dimension_separator='/')

    if args.quiet:
        ngff_image = input_to_ngff_image(input_backend, args.input)
        multiscales = to_multiscales(ngff_image)
        to_ngff_zarr(output_store, multiscales)
    else:
        with Progress() as progress:
            rich_dask_progress = RichDaskProgress(progress)
            rich_dask_progress.register()

        # convert_to_zarr(input_type, args.input)

    print(args.quiet)

if __name__ == '__main__':
    main()
