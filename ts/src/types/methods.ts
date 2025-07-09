export enum Methods {
  ITKWASM_GAUSSIAN = "itkwasm_gaussian",
  ITKWASM_BIN_SHRINK = "itkwasm_bin_shrink",
  ITKWASM_LABEL_IMAGE = "itkwasm_label_image",
  ITK_GAUSSIAN = "itk_gaussian",
  ITK_BIN_SHRINK = "itk_bin_shrink",
  DASK_IMAGE_GAUSSIAN = "dask_image_gaussian",
  DASK_IMAGE_MODE = "dask_image_mode",
  DASK_IMAGE_NEAREST = "dask_image_nearest",
}

export const methodsValues = Object.values(Methods);
