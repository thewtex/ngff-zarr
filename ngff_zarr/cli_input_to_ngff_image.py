import sys

from rich import print
from dask.array.image import imread as daimread
import zarr

from .detect_cli_io_backend import ConversionBackend
from .ngff_image import NgffImage
from .to_ngff_image import to_ngff_image
from .itk_image_to_ngff_image import itk_image_to_ngff_image
from .from_ngff_zarr import from_ngff_zarr

def cli_input_to_ngff_image(backend: ConversionBackend, input, output_scale: int=0) -> NgffImage:
    if backend is ConversionBackend.NGFF_ZARR:
        store = zarr.storage.DirectoryStore(input[0])
        multiscales = from_ngff_zarr(store)
        return multiscales.images[output_scale]
    elif backend is ConversionBackend.ZARR_ARRAY:
        arr = zarr.open_array(input[0], mode='r')
        return to_ngff_image(arr)
    elif backend is ConversionBackend.ITK:
        try:
            import itk
        except ImportError:
            print('[red]Please install the [i]itk-io[/i] package.')
            sys.exit(1)
        if len(input) == 1:
            if '*' in str(input[0]):
                def imread(filename):
                    image = itk.imread(filename)
                    return itk.array_from_image(image)
                da = daimread(str(input[0]), imread=imread)
                return to_ngff_image(da)
            else:
                image = itk.imread(input[0])
                return itk_image_to_ngff_image(image)
        image = itk.imread(input)
        return itk_image_to_ngff_image(image)
    elif backend is ConversionBackend.TIFFFILE:
        try:
            import tifffile
        except ImportError:
            print('[red]Please install the [i]tifffile[/i] package.')
            sys.exit(1)
        if len(input) == 1:
            store = tifffile.imread(input[0], aszarr=True)
        else:
            store = tifffile.imread(input, aszarr=True)
        root = zarr.open(store, mode='r')
        return to_ngff_image(root)
    elif backend is ConversionBackend.IMAGEIO:
        try:
            import imageio
        except ImportError:
            print('[red]Please install the [i]imageio[/i] package.')
            sys.exit(1)
        import imageio.v3 as iio
        image = iio.imread(str(input[0]))

        ngff_image = to_ngff_image(image)

        props = iio.improps(str(input[0]))
        if props.spacing is not None:
            if len(spacing) == 1:
                scale = {d: spacing for d in ngff_image.dims}
                ngff_image.scale = scale
            else:
                scale = {d: spacing[i] for i, d in enumerate(ngff_image.dims)}
                ngff_image.scale = scale

        return ngff_image
