import pytest
import numpy as np
from ngff_zarr.to_ngff_image import to_ngff_image
from ngff_zarr.to_multiscales import to_multiscales

rng = np.random.default_rng(12345)

@pytest.mark.parametrize("shape, chunk_shape", [
    (
            (1, 30, 1024, 1024),
            (1, 30, 65, 65),
    ),
    (
            (1, 125, 1024, 1024),
            (1, 50, 51, 50),
    ),
])
def test_to_multiscales_metadata_synced_with_data(shape, chunk_shape):
    array = rng.random(size=shape, dtype=np.float32) * 100.0
    input_image = to_ngff_image(array, dims=['t', 'z', 'y', 'x'])
    multiscales = to_multiscales(input_image, scale_factors=max(chunk_shape), chunks=chunk_shape)
    for i, dataset in enumerate(multiscales.metadata.datasets):
        image = multiscales.images[i]
        toplevel_meta_scale = dataset.coordinateTransformations[0].scale

        # This first assert passes
        image_scale_spatial_only = [image.scale[d] for d in ["z", "y", "x"]]
        assert image_scale_spatial_only == toplevel_meta_scale[1:]

        # Bug 1: "t" not in image.scale
        image_scale_ordered = [image.scale[d] for d in image.dims]  # KeyError: 't'
        assert image_scale_ordered == toplevel_meta_scale  # This is the real assert the test should be doing
        image_translation_ordered = [image.translation[d] for d in image.dims]  # KeyError: 't'
        assert image_translation_ordered == dataset.coordinateTransformations[1].translation  # This should also match

        # Bug 2: Image is not scaled along dimensions reported in the metadata
        expected_shape = tuple(np.array(shape) / np.array(toplevel_meta_scale))
        assert image.data.shape == expected_shape  # (1, 7, 256, 1024) != (1.0, 15.0, 256.0, 512.0)

        # Bug 3: Scale factors are applied to the wrong dimensions
        # E.g. given an image with square shape in yx as in this test, the scaling along yx should be identical
        # Pretty sure this is because at some point xyz scale factors are passed into a function assuming yxz, or vice versa
        assert image.data.shape[2] == image.data.shape[3]  # 512 != 1024