// SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
// SPDX-License-Identifier: MIT
import type { HCSPlate } from "../types/hcs.ts";

export interface FromHcsZarrOptions {
  validate?: boolean;
  wellCacheSize?: number;
  imageCacheSize?: number;
}

export interface ToHcsZarrOptions {
  // Future options for writing HCS data
  compressionLevel?: number;
}

/**
 * Read an HCS plate from an OME-Zarr NGFF store.
 *
 * Not supported yet: the plate metadata is not read from the store. Use the
 * Python package's `from_hcs_zarr`, or build an {@link HCSPlate} from
 * metadata you have read.
 */
export function fromHcsZarr(
  _store: string | object,
  _options: FromHcsZarrOptions = {},
): HCSPlate {
  throw new Error(
    "fromHcsZarr is not supported yet: it does not read the plate metadata " +
      "from the store. Use the Python package's from_hcs_zarr.",
  );
}

/**
 * Write an HCS plate to an OME-Zarr NGFF store.
 *
 * Not supported yet. Use the Python package's `to_hcs_zarr`.
 */
export function toHcsZarr(
  _plate: HCSPlate,
  _store: string | object,
  _options: ToHcsZarrOptions = {},
): void {
  throw new Error(
    "toHcsZarr is not supported yet: it writes nothing. Use the Python " +
      "package's to_hcs_zarr.",
  );
}
