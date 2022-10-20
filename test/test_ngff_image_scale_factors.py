from ngff_zarr.to_ngff_image import to_ngff_image
from ngff_zarr.to_multiscales import _ngff_image_scale_factors

import numpy as np

def test_scale_factors_520_520():
    array = np.random.uniform(high=100.0, size=(520,520)).astype(np.float32)
    image = to_ngff_image(array)
    scale_factors = _ngff_image_scale_factors(image, 64)
    assert len(scale_factors) == 3
    assert scale_factors[2]['x'] == 8
    assert scale_factors[2]['y'] == 8

