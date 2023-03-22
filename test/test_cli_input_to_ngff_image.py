from ngff_zarr import cli_input_to_ngff_image, ConversionBackend

from ._data import test_data_dir, input_images

def test_cli_input_to_ngff_image_itk(input_images):
    input = [test_data_dir / "input" / "cthead1.png",]
    image = cli_input_to_ngff_image(ConversionBackend.ITK, input)
    assert image.dims == ('y', 'x')

