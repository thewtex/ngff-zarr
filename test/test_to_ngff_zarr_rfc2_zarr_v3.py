import zarr.storage

from ngff_zarr import Methods, to_multiscales, to_ngff_zarr, from_ngff_zarr

from ._data import verify_against_baseline


def test_gaussian_isotropic_scale_factors(input_images):
    dataset_name = "cthead1"
    image = input_images[dataset_name]
    baseline_name = "2_4/RFC3_GAUSSIAN.zarr"
    multiscales = to_multiscales(image, [2, 4], method=Methods.ITKWASM_GAUSSIAN)
    store = zarr.storage.MemoryStore()

    version = "0.5"
    to_ngff_zarr(store, multiscales, version=version)
    multiscales = from_ngff_zarr(store, version=version)
    # store_new_multiscales(dataset_name, baseline_name, multiscales, version=version)
    verify_against_baseline(dataset_name, baseline_name, multiscales, version=version)
