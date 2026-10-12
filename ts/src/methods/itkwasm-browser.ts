// SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
// SPDX-License-Identifier: MIT

/**
 * Browser-compatible ITK-Wasm downsampling support
 * Uses WebWorker-based implementations from @itk-wasm/downsample
 */

import {
  downsample,
  downsampleBinShrink,
  downsampleLabelImage,
} from "@itk-wasm/downsample";

import type { NgffImage } from "../types/ngff_image.ts";
import type { ZarrCodec } from "../utils/codecs.ts";
import { downsampleItkWasmCore } from "./itkwasm-core.ts";

const downsamplers = { downsample, downsampleBinShrink, downsampleLabelImage };

/**
 * Main downsampling function for ITK-Wasm (browser version)
 */
export function downsampleItkWasm(
  ngffImage: NgffImage,
  scaleFactors: (Record<string, number> | number)[],
  smoothing: "gaussian" | "bin_shrink" | "label_image",
  chunks?: number | number[] | Record<string, number>,
  codecs?: ZarrCodec[],
): Promise<NgffImage[]> {
  return downsampleItkWasmCore(
    downsamplers,
    ngffImage,
    scaleFactors,
    smoothing,
    chunks,
    codecs,
  );
}
