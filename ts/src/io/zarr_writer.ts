import * as zarr from "zarrita";
import type { Multiscales } from "../types/multiscales.ts";
import type { NgffImage } from "../types/ngff_image.ts";

export interface ZarrWriterOptions {
  overwrite?: boolean;
  version?: "0.4" | "0.5";
  useTensorstore?: boolean;
  chunksPerShard?: number | number[] | Record<string, number>;
}

export class ZarrWriter {
  private overwrite: boolean;
  private version: string;
  private useTensorstore: boolean;

  constructor(options: ZarrWriterOptions = {}) {
    this.overwrite = options.overwrite ?? true;
    this.version = options.version ?? "0.4";
    this.useTensorstore = options.useTensorstore ?? false;
  }

  async toNgffZarr(
    storePath: string,
    multiscales: Multiscales,
    options: ZarrWriterOptions = {},
  ): Promise<void> {
    const overwrite = options.overwrite ?? this.overwrite;
    const version = options.version ?? this.version;

    try {
      // Note: zarrita writing is complex and would need proper store implementation
      // This is a simplified placeholder
      throw new Error(
        "Writing OME-Zarr files is not yet fully implemented with zarrita",
      );
    } catch (error) {
      throw new Error(
        `Failed to write OME-Zarr: ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
  }

  private async writeImage(
    group: any,
    image: NgffImage,
    arrayPath: string,
  ): Promise<void> {
    try {
      const chunks = this.getChunksFromImage(image);

      const zarrArray = await zarr.create(group.resolve(arrayPath), {
        shape: image.data.shape,
        data_type: image.data.dtype as any,
        chunk_shape: chunks,
        fill_value: 0,
      });

      // Note: zarrita doesn't have attrs.set, this would need to be implemented differently
      // For now, we'll skip setting array attributes
    } catch (error) {
      throw new Error(
        `Failed to write image array: ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
  }

  private getChunksFromImage(image: NgffImage): number[] {
    if (image.data.chunks.length > 0 && image.data.chunks[0].length > 0) {
      return image.data.chunks[0];
    }

    return image.data.shape.map((dim) => Math.min(dim, 1024));
  }

  async writeArrayData(
    storePath: string,
    arrayPath: string,
    data: ArrayLike<number>,
    selection?: number[][],
  ): Promise<void> {
    try {
      // Note: zarrita doesn't have a direct set method for arrays
      // This would need to be implemented differently
      throw new Error("Writing array data not yet implemented with zarrita");
    } catch (error) {
      throw new Error(
        `Failed to write array data: ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
  }
}
