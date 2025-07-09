import { z } from "zod";

export const MethodsSchema = z.enum([
  "itkwasm_gaussian",
  "itkwasm_bin_shrink",
  "itkwasm_label_image",
  "itk_gaussian",
  "itk_bin_shrink",
  "dask_image_gaussian",
  "dask_image_mode",
  "dask_image_nearest",
]);
