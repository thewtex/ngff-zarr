import numpy as np
from ngff_zarr.to_multiscales import _ngff_image_scale_factors
from ngff_zarr.to_ngff_image import to_ngff_image

rng = np.random.default_rng(12345)


def test_scale_factors_520_520():
    array = rng.random(size=(520, 520), dtype=np.float32) * 100.0
    image = to_ngff_image(array)
    image.data = image.data.rechunk(64)
    scale_factors = _ngff_image_scale_factors(image, 64, {"x": 64, "y": 64})
    assert len(scale_factors) == 3
    assert scale_factors[2]["x"] == 8
    assert scale_factors[2]["y"] == 8


def test_scale_factors_520_530():
    array = rng.random(size=(520, 530), dtype=np.float32) * 100.0
    image = to_ngff_image(array)
    image.data = image.data.rechunk(64)
    scale_factors = _ngff_image_scale_factors(image, 64, {"x": 64, "y": 64})
    assert len(scale_factors) == 3
    assert scale_factors[2]["x"] == 8
    assert scale_factors[2]["y"] == 8
