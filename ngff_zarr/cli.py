#!/usr/bin/env python

if __name__ == "__main__" and __package__ is None:
    __package__ = "ngff_zarr"

import sys
import argparse
from pathlib import Path
import atexit
import signal

from rich.progress import Progress as RichProgress, SpinnerColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.console import Console
from zarr.storage import DirectoryStore
import dask.utils

from .ngff_image import NgffImage
from .to_multiscales import to_multiscales
from .to_ngff_zarr import to_ngff_zarr
from .cli_input_to_ngff_image import cli_input_to_ngff_image
from .detect_cli_input_backend import detect_cli_input_backend, ConversionBackend, conversion_backends_values
from .methods import Methods, methods_values
from .rich_dask_progress import RichDaskProgress, RichDaskDistributedProgress
from rich import print as rprint
from .config import config

def main():
    parser = argparse.ArgumentParser(description='Convert datasets to and from the OME-Zarr Next Generation File Format.')
    parser.add_argument('input', nargs='+', help='Input image(s)')
    parser.add_argument('output', help='Output image. Just print information with "info"')
    parser.add_argument('-d', '--dims', nargs='+', help='Ordered OME-Zarr NGFF dimensions from {"t", "z", "y", "x", "c"}', metavar='DIM')
    parser.add_argument('-m', '--method', default="dask_image_gaussian", choices=methods_values, help="Downsampling method")
    parser.add_argument('-q', '--quiet', action='store_true', help='Do not display progress information')
    parser.add_argument('--no-local-cluster', action='store_true', help='Do not create a Dask Distributed LocalCluster')
    parser.add_argument('--input-backend', choices=conversion_backends_values, help='Input conversion backend')
    parser.add_argument('--memory-limit', help='Memory limit, e.g. 4GB')

    args = parser.parse_args()

    console = Console()

    if args.memory_limit:
        config.memory_limit = dask.utils.parse_bytes(args.memory_limit)

    with RichProgress(SpinnerColumn(), *RichProgress.get_default_columns(),
            MofNCompleteColumn(), TimeElapsedColumn(), console=console, transient=False,
            redirect_stdout=True, redirect_stderr=True) as progress:

        rich_dask_progress = None

        # Setup LocalCluster
        if not args.no_local_cluster:
            from dask.distributed import Client, LocalCluster

            n_workers = 4
            worker_memory_limit = config.memory_limit // n_workers
            try:
                import psutil
                n_workers = psutil.cpu_count(False) // 2
                worker_memory_limit = config.memory_limit // n_workers
            except ImportError:
                pass

            cluster = LocalCluster(n_workers=n_workers, memory_limit=worker_memory_limit, processes=True, threads_per_worker=2)
            client = Client(cluster)

            def shutdown_client(sig_id, frame):
                client.shutdown()
            atexit.register(shutdown_client, None, None)
            signal.signal(signal.SIGTERM, shutdown_client)
            signal.signal(signal.SIGINT, shutdown_client)

            if not args.quiet:
                console.log(f"[yellow]Dashboard: [cyan]{client.dashboard_link}")

            if not args.quiet:
                rich_dask_progress = RichDaskDistributedProgress(progress)
        else:
            if not args.quiet:
                rich_dask_progress = RichDaskProgress(progress)
                rich_dask_progress.register()

        # Parse conversion options
        if args.input_backend is None:
            input_backend = detect_cli_input_backend(args.input)
        else:
            input_backend = ConversionBackend(args.input_backend)
        if args.method is None:
            method = Methods.ITK_GAUSSIAN
        else:
            method = Methods(args.method)

        if args.output != "info":
            output_store = DirectoryStore(args.output, dimension_separator='/')

        # Generate NgffImage
        ngff_image = cli_input_to_ngff_image(input_backend, args.input)
        if args.dims:
            if len(args.dims) != len(ngff_image.dims):
                rprint(f"[red]Provided number of dims do not match expected: {len(ngff_image.dims)}")
                sys.exit(1)
            ngff_image.dims = args.dims

        # Generate Multiscales
        multiscales = to_multiscales(ngff_image, method=method, progress=rich_dask_progress)
        if args.output == "info":
            rprint(multiscales)
            return
        to_ngff_zarr(output_store, multiscales, progress=rich_dask_progress)

if __name__ == '__main__':
    main()
