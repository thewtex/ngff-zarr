from ngff_zarr import from_ngff_zarr

from ._data import test_data_dir


def test_read_omero(input_images):  # noqa: ARG001
    dataset_name = "13457537"
    store_path = test_data_dir / "input" / f"{dataset_name}.zarr"
    multiscales = from_ngff_zarr(store_path, validate=True)

    omero = multiscales.metadata.omero
    assert omero is not None
    assert len(omero.channels) == 6

    # Channel 0
    assert omero.channels[0].color == "FFFFFF"
    assert omero.channels[0].window.min == 0.0
    assert omero.channels[0].window.max == 65535.0
    assert omero.channels[0].window.start == 0.0
    assert omero.channels[0].window.end == 1200.0

    # Channel 1
    assert omero.channels[1].color == "FFFFFF"
    assert omero.channels[1].window.min == 0.0
    assert omero.channels[1].window.max == 65535.0
    assert omero.channels[1].window.start == 0.0
    assert omero.channels[1].window.end == 1200.0

    # Channel 2
    assert omero.channels[2].color == "FFFFFF"
    assert omero.channels[2].window.min == 0.0
    assert omero.channels[2].window.max == 65535.0
    assert omero.channels[2].window.start == 0.0
    assert omero.channels[2].window.end == 1200.0

    # Channel 3
    assert omero.channels[3].color == "FFFFFF"
    assert omero.channels[3].window.min == 0.0
    assert omero.channels[3].window.max == 65535.0
    assert omero.channels[3].window.start == 0.0
    assert omero.channels[3].window.end == 1200.0

    # Channel 4
    assert omero.channels[4].color == "0000FF"
    assert omero.channels[4].window.min == 0.0
    assert omero.channels[4].window.max == 65535.0
    assert omero.channels[4].window.start == 0.0
    assert omero.channels[4].window.end == 5000.0

    # Channel 5
    assert omero.channels[5].color == "FF0000"
    assert omero.channels[5].window.min == 0.0
    assert omero.channels[5].window.max == 65535.0
    assert omero.channels[5].window.start == 0.0
    assert omero.channels[5].window.end == 100.0
