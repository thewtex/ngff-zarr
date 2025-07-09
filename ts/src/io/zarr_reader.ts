import * as zarr from "zarrita";
import { Multiscales } from "../types/multiscales.ts";
import { NgffImage } from "../types/ngff_image.ts";
import type { Metadata } from "../types/zarr_metadata.ts";
import { DaskArray } from "../types/dask_array.ts";
import { MetadataSchema } from "../schemas/zarr_metadata.ts";

export interface ZarrReaderOptions {
  validate?: boolean;
}

export class ZarrReader {
  private validate: boolean;

  constructor(options: ZarrReaderOptions = {}) {
    this.validate = options.validate ?? false;
  }

  async fromNgffZarr(
    storePath: string,
    options: ZarrReaderOptions = {},
  ): Promise<Multiscales> {
    const validate = options.validate ?? this.validate;

    try {
      const store = new zarr.FetchStore(storePath);
      const root = zarr.root(store);
      
      // Try to use consolidated metadata for better performance
      let consolidatedRoot;
      try {
        consolidatedRoot = await zarr.tryWithConsolidated(store);
      } catch {
        consolidatedRoot = store;
      }
      
      const group = await zarr.open(zarr.root(consolidatedRoot), { kind: "group" });
      const attrs = group.attrs as unknown;

      if (!attrs || !(attrs as Record<string, unknown>).multiscales) {
        throw new Error("No multiscales metadata found in Zarr store");
      }

      const multiscalesMetadata = (attrs as Record<string, unknown>).multiscales?.[0] as unknown;

      if (validate) {
        const result = MetadataSchema.safeParse(multiscalesMetadata);
        if (!result.success) {
          throw new Error(
            `Invalid OME-Zarr metadata: ${result.error.message}`,
          );
        }
      }

      const metadata: Metadata = multiscalesMetadata;
      const images: NgffImage[] = [];

      for (const dataset of metadata.datasets) {
        const arrayPath = dataset.path;
        const zarrArray = await zarr.open(root.resolve(arrayPath), {
          kind: "array",
        });

        const daskArray = new DaskArray({
          shape: zarrArray.shape,
          dtype: zarrArray.dtype,
          chunks: [zarrArray.chunks],
          name: arrayPath,
        });

        const scale: Record<string, number> = {};
        const translation: Record<string, number> = {};

        for (const transform of dataset.coordinateTransformations) {
          if (transform.type === "scale") {
            metadata.axes.forEach((axis, i) => {
              if (i < transform.scale.length) {
                scale[axis.name] = transform.scale[i];
              }
            });
          } else if (transform.type === "translation") {
            metadata.axes.forEach((axis, i) => {
              if (i < transform.translation.length) {
                translation[axis.name] = transform.translation[i];
              }
            });
          }
        }

        const dims = metadata.axes.map((axis) => axis.name);
        const axesUnits = metadata.axes.reduce((acc, axis) => {
          if (axis.unit) {
            acc[axis.name] = axis.unit;
          }
          return acc;
        }, {} as Record<string, string>);

        const ngffImage = new NgffImage({
          data: daskArray,
          dims,
          scale,
          translation,
          name: metadata.name,
          axesUnits: Object.keys(axesUnits).length > 0 ? axesUnits : undefined,
          computedCallbacks: undefined,
        });

        images.push(ngffImage);
      }

      return new Multiscales({
        images,
        metadata,
        scaleFactors: undefined,
        method: undefined,
        chunks: undefined,
      });
    } catch (error) {
      throw new Error(
        `Failed to read OME-Zarr: ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
  }

  async readArrayData(
    storePath: string,
    arrayPath: string,
    selection?: unknown[],
  ): Promise<unknown> {
    try {
      const store = new zarr.FetchStore(storePath);
      const root = zarr.root(store);
      const zarrArray = await zarr.open(root.resolve(arrayPath), {
        kind: "array",
      });

      if (selection) {
        return await zarr.get(zarrArray, selection as unknown);
      } else {
        return await zarr.get(zarrArray);
      }
    } catch (error) {
      throw new Error(
        `Failed to read array data: ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
  }
}
