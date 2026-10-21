// SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
// SPDX-License-Identifier: MIT

/**
 * Node-compatible ITK-Wasm downsampling support
 * Uses native WASM implementations from @itk-wasm/downsample
 *
 * Note: Imports Node-specific functions that are available when the
 * "node" condition is active in package.json exports resolution.
 * The @itk-wasm/downsample package uses conditional exports to provide
 * different implementations for browser vs Node environments.
 */

import {
  downsampleBinShrinkNode,
  downsampleLabelImageNode,
  downsampleNode,
} from "@itk-wasm/downsample";

import type { NgffImage } from "../types/ngff_image.ts";
import type { ZarrCodec } from "../utils/codecs.ts";
import { downsampleItkWasmCore } from "./itkwasm-core.ts";

const downsamplers = {
  downsample: downsampleNode,
  downsampleBinShrink: downsampleBinShrinkNode,
  downsampleLabelImage: downsampleLabelImageNode,
};

/**
 * Main downsampling function for ITK-Wasm (Node version)
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
