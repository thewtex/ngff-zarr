import * as zarr from "zarrita";
import type { Multiscales } from "../types/multiscales.ts";
import type { NgffImage } from "../types/ngff_image.ts";

export interface OMEZarrWriterOptions {
  overwrite?: boolean;
  version?: "0.4" | "0.5";
  useTensorstore?: boolean;
  chunksPerShard?: number | number[] | Record<string, number>;
}

export class OMEZarrWriter {
  private overwrite: boolean;
  private version: string;
  private useTensorstore: boolean;

  constructor(options: OMEZarrWriterOptions = {}) {
    this.overwrite = options.overwrite ?? true;
    this.version = options.version ?? "0.4";
    this.useTensorstore = options.useTensorstore ?? false;
  }

  toNgffZarr(
    _storePath: string,
    _multiscales: Multiscales,
    options: OMEZarrWriterOptions = {},
  ): Promise<void> {
    const _overwrite = options.overwrite ?? this.overwrite;
    const _version = options.version ?? this.version;

    try {
      // TODO: Implement using zarrita v0.5.2 API
      // Example implementation would be:
      // 1. Create a writable store (e.g., FileSystemStore for local files)
      // 2. Use zarr.root(store) to create a Location
      // 3. Use zarr.create(root, { attributes: { multiscales: [...] } }) to create group
      // 4. For each image, use zarr.create(root.resolve(path), { shape, data_type, chunk_shape })
      // 5. Use zarr.set() to write actual data

      throw new Error(
        "Writing OME-Zarr files is not yet fully implemented with zarrita v0.5.2",
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
    group: unknown,
    image: NgffImage,
    arrayPath: string,
  ): Promise<void> {
    try {
      const chunks = this.getChunksFromImage(image);

      // TODO: Update to use zarrita v0.5.2 API properly
      // The new API would use:
      // const location = (group as { resolve: (path: string) => Location }).resolve(arrayPath);
      // const zarrArray = await zarr.create(location, { ... });
      // Then use zarr.set(zarrArray, data, selection) to write data

      const resolvedPath = (
        group as { resolve: (path: string) => unknown }
      ).resolve(arrayPath);
      // @ts-ignore - zarrita API types are complex, this is a temporary workaround
      const _zarrArray = await zarr.create(resolvedPath, {
        shape: image.data.shape,
        data_type: image.data.dtype as unknown,
        chunk_shape: chunks,
        fill_value: 0,
      });

      // Note: With zarrita v0.5.2, attributes can be set during creation
      // or updated using the store's set method for metadata files
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

  writeArrayData(
    _storePath: string,
    _arrayPath: string,
    _data: ArrayLike<number>,
    _selection?: number[][],
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
