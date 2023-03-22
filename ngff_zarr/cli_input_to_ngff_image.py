import sys

from rich import print
from dask.array.image import imread as daimread

from .detect_cli_input_backend import ConversionBackend
from .ngff_image import NgffImage
from .itk_image_to_ngff_image import itk_image_to_ngff_image

def cli_input_to_ngff_image(backend: ConversionBackend, input) -> NgffImage:
    if backend is ConversionBackend.ITK:
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
        # TODO
        pass
    elif backend is ConversionBackend.IMAGEIO:
        # TODO
        pass


