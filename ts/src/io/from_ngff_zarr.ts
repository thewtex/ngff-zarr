import * as zarr from "zarrita";
import { Multiscales } from "../types/multiscales.ts";
import { NgffImage } from "../types/ngff_image.ts";
import type { Metadata, Omero } from "../types/zarr_metadata.ts";
import { LazyArray } from "../types/lazy_array.ts";
import { MetadataSchema } from "../schemas/zarr_metadata.ts";
import type { Units } from "../types/units.ts";

export interface FromNgffZarrOptions {
  validate?: boolean;
}

export async function fromNgffZarr(
  storePath: string,
  options: FromNgffZarrOptions = {},
): Promise<Multiscales> {
  const validate = options.validate ?? false;

  try {
    // Determine the appropriate store type based on the path
    let store;
    if (storePath.startsWith("http://") || storePath.startsWith("https://")) {
      // Use FetchStore for HTTP/HTTPS URLs
      store = new zarr.FetchStore(storePath);
    } else {
      // For local paths, check if we're in a browser environment
      if (typeof window !== "undefined") {
        throw new Error(
          "Local file paths are not supported in browser environments. Use HTTP/HTTPS URLs instead.",
        );
      }

      // Use dynamic import for FileSystemStore in Node.js/Deno environments
      try {
        const { FileSystemStore } = await import("@zarrita/storage");
        // Normalize the path for cross-platform compatibility
        const normalizedPath = storePath.replace(/^\/([A-Za-z]:)/, "$1");
        store = new FileSystemStore(normalizedPath);
      } catch (error) {
        throw new Error(
          `Failed to load FileSystemStore: ${error}. Use HTTP/HTTPS URLs for browser compatibility.`,
        );
      }
    }

    const root = zarr.root(store);

    // Try to use consolidated metadata for better performance
    let consolidatedRoot;
    try {
      consolidatedRoot = await zarr.tryWithConsolidated(store);
    } catch {
      consolidatedRoot = store;
    }

    // Try to open as zarr v2 first, then v3 if that fails
    let group;
    try {
      group = await zarr.open.v2(zarr.root(consolidatedRoot), {
        kind: "group",
      });
    } catch (v2Error) {
      try {
        group = await zarr.open.v3(zarr.root(consolidatedRoot), {
          kind: "group",
        });
      } catch (v3Error) {
        throw new Error(
          `Failed to open zarr store as either v2 or v3 format. v2 error: ${v2Error}. v3 error: ${v3Error}`,
        );
      }
    }
    const attrs = group.attrs as unknown;

    if (!attrs || !(attrs as Record<string, unknown>).multiscales) {
      throw new Error("No multiscales metadata found in Zarr store");
    }

    const multiscalesArray = (attrs as Record<string, unknown>)
      .multiscales as unknown[];
    if (!Array.isArray(multiscalesArray) || multiscalesArray.length === 0) {
      throw new Error("No multiscales metadata found in Zarr store");
    }
    const multiscalesMetadata = multiscalesArray[0] as unknown;

    if (validate) {
      const result = MetadataSchema.safeParse(multiscalesMetadata);
      if (!result.success) {
        throw new Error(`Invalid OME-Zarr metadata: ${result.error.message}`);
      }
    }

    const metadata = multiscalesMetadata as Metadata;

    // Extract omero metadata from root attributes if present
    if ((attrs as Record<string, unknown>).omero) {
      metadata.omero = (attrs as Record<string, unknown>).omero as Omero;
    }

    const images: NgffImage[] = [];

    for (const dataset of metadata.datasets) {
      const arrayPath = dataset.path;

      // Try to open as zarr v2 first, then v3 if that fails
      let zarrArray;
      try {
        zarrArray = await zarr.open.v2(root.resolve(arrayPath), {
          kind: "array",
        });
      } catch (v2Error) {
        try {
          zarrArray = await zarr.open.v3(root.resolve(arrayPath), {
            kind: "array",
          });
        } catch (v3Error) {
          throw new Error(
            `Failed to open zarr array ${arrayPath} as either v2 or v3 format. v2 error: ${v2Error}. v3 error: ${v3Error}`,
          );
        }
      }

      const lazyArray = new LazyArray({
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
      }, {} as Record<string, Units>);

      const ngffImage = new NgffImage({
        data: lazyArray,
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

export async function readArrayData(
  storePath: string,
  arrayPath: string,
  selection?: (number | null)[],
): Promise<unknown> {
  try {
    const store = new zarr.FetchStore(storePath);
    const root = zarr.root(store);

    // Try to open as zarr v2 first, then v3 if that fails
    let zarrArray;
    try {
      zarrArray = await zarr.open.v2(root.resolve(arrayPath), {
        kind: "array",
      });
    } catch (v2Error) {
      try {
        zarrArray = await zarr.open.v3(root.resolve(arrayPath), {
          kind: "array",
        });
      } catch (v3Error) {
        throw new Error(
          `Failed to open zarr array ${arrayPath} as either v2 or v3 format. v2 error: ${v2Error}. v3 error: ${v3Error}`,
        );
      }
    }

    if (selection) {
      return await zarr.get(zarrArray, selection);
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
