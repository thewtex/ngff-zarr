import json
from packaging import version
import tempfile

import pytest

import zarr.storage
from zarr.storage import MemoryStore
import zarr

from dask_image import imread

from ngff_zarr import Methods, to_multiscales, to_ngff_zarr, config, to_ngff_image

# from ._data import verify_against_baseline

zarr_version = version.parse(zarr.__version__)

# Skip tests if zarr version is less than 3.0.0b1
pytestmark = pytest.mark.skipif(
    zarr_version < version.parse("3.0.0b1"), reason="zarr version < 3.0.0b1"
)


def test_zarr_v3_compression(input_images):
    dataset_name = "cthead1"
    image = input_images[dataset_name]
    baseline_name = "2_4/RFC3_GAUSSIAN.zarr"
    chunks = (64, 64)
    multiscales = to_multiscales(
        image, [2, 4], chunks=chunks, method=Methods.ITKWASM_GAUSSIAN
    )
    store = zarr.storage.MemoryStore()


    compressors = zarr.codecs.BloscCodec(cname="zlib", clevel=5, shuffle=zarr.codecs.BloscShuffle.shuffle)

    # chunks_per_shard = 2
    # Test this with sharding also

    version = "0.5"
    with tempfile.TemporaryDirectory() as tmpdir:

        to_ngff_zarr(
            tmpdir, multiscales, version=version, compressors=compressors
        )

        with open(tmpdir + "/zarr.json") as f:
            zarr_json = json.load(f)
        assert zarr_json["zarr_format"] == 3
        metadata = zarr_json["consolidated_metadata"]["metadata"]

        scale0 = metadata["scale0/image"]

        assert scale0['codecs'][1]['name'] == 'blosc'
        assert scale0['codecs'][1]['configuration']['cname'] == 'zlib'
        assert scale0['codecs'][1]['configuration']['clevel'] == 5
        assert scale0['codecs'][1]['configuration']['shuffle'] == 'shuffle'

        scale1 = metadata["scale1/image"]

        assert scale1['codecs'][1]['name'] == 'blosc'
        assert scale1['codecs'][1]['configuration']['cname'] == 'zlib'
        assert scale1['codecs'][1]['configuration']['clevel'] == 5
        assert scale1['codecs'][1]['configuration']['shuffle'] == 'shuffle'

        scale2 = metadata["scale2/image"]

        assert scale2['codecs'][1]['name'] == 'blosc'
        assert scale2['codecs'][1]['configuration']['cname'] == 'zlib'
        assert scale2['codecs'][1]['configuration']['clevel'] == 5
        assert scale2['codecs'][1]['configuration']['shuffle'] == 'shuffle'


    # Save to a persistent location
    persistent_path = "/mnt/c/scratch/ngff-zarr-test/test.zarr"
    to_ngff_zarr(
        persistent_path, multiscales, version=version, compressors=compressors
    )
