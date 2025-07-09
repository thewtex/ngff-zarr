import { LazyArray } from "../types/lazy_array.ts";
import { NgffImage } from "../types/ngff_image.ts";
import { Multiscales } from "../types/multiscales.ts";
import type {
  Axis,
  Dataset,
  Metadata,
  Scale,
  Translation,
} from "../types/zarr_metadata.ts";
import type { SupportedDims, AxesType, Units } from "../types/units.ts";
import type { Methods } from "../types/methods.ts";

export function createNgffImage(
  _data: ArrayBuffer | number[],
  shape: number[],
  dtype: string,
  dims: string[],
  scale: Record<string, number>,
  translation: Record<string, number>,
  name = "image"
): NgffImage {
  const lazyArray = new LazyArray({
    shape,
    dtype,
    chunks: [shape],
    name,
  });

  return new NgffImage({
    data: lazyArray,
    dims,
    scale,
    translation,
    name,
    axesUnits: undefined,
    computedCallbacks: undefined,
  });
}

export function createAxis(
  name: SupportedDims,
  type: AxesType,
  unit?: Units
): Axis {
  return {
    name,
    type,
    unit: unit || undefined,
  };
}

export function createScale(scale: number[]): Scale {
  return {
    scale: [...scale],
    type: "scale",
  };
}

export function createTranslation(translation: number[]): Translation {
  return {
    translation: [...translation],
    type: "translation",
  };
}

export function createDataset(
  path: string,
  scale: number[],
  translation: number[]
): Dataset {
  return {
    path,
    coordinateTransformations: [
      createScale(scale),
      createTranslation(translation),
    ],
  };
}

export function createMetadata(
  axes: Axis[],
  datasets: Dataset[],
  name = "image",
  version = "0.4"
): Metadata {
  return {
    axes: [...axes],
    datasets: [...datasets],
    coordinateTransformations: undefined,
    omero: undefined,
    name,
    version,
  };
}

export function createMultiscales(
  images: NgffImage[],
  metadata: Metadata,
  scaleFactors?: (Record<string, number> | number)[],
  method?: Methods
): Multiscales {
  return new Multiscales({
    images: [...images],
    metadata,
    scaleFactors: scaleFactors || undefined,
    method: method || undefined,
    chunks: undefined,
  });
}
