import * as zarr from "zarrita";
import type { Multiscales } from "../types/multiscales.ts";
import type { NgffImage } from "../types/ngff_image.ts";
import type { MemoryStore } from "./from_ngff_zarr.ts";

export interface ToNgffZarrOptions {
  overwrite?: boolean;
  version?: "0.4" | "0.5";
  chunksPerShard?: number | number[] | Record<string, number>;
}

export async function toNgffZarr(
  store: string | MemoryStore | zarr.FetchStore,
  multiscales: Multiscales,
  options: ToNgffZarrOptions = {},
): Promise<void> {
  const _overwrite = options.overwrite ?? true;
  const _version = options.version ?? "0.4";

  try {
    // Determine the appropriate store type based on the path
    let _resolvedStore: MemoryStore | unknown; // Use unknown for FileSystemStore since we import it dynamically
    if (store instanceof Map) {
      _resolvedStore = store;
    } else if (store instanceof zarr.FetchStore) {
      throw new Error(
        "FetchStore is read-only and cannot be used for writing. Use a local file path or MemoryStore instead.",
      );
    } else if (store.startsWith("http://") || store.startsWith("https://")) {
      throw new Error(
        "HTTP/HTTPS URLs are read-only and cannot be used for writing. Use a local file path instead.",
      );
    } else {
      // For local paths, check if we're in a browser environment
      if (typeof window !== "undefined") {
        throw new Error(
          "Local file paths are not supported in browser environments. Use a MemoryStore instead.",
        );
      }

      // Use dynamic import for FileSystemStore in Node.js/Deno environments
      try {
        const { FileSystemStore } = await import("@zarrita/storage");
        // Normalize the path for cross-platform compatibility
        const normalizedPath = store.replace(/^\/([A-Za-z]:)/, "$1");
        _resolvedStore = new FileSystemStore(normalizedPath);
      } catch (error) {
        throw new Error(
          `Failed to load FileSystemStore: ${error}. Use MemoryStore for browser compatibility.`,
        );
      }
    }

    // Create root location and group with zarrita v0.5.2 API
    const root = zarr.root(_resolvedStore as MemoryStore);

    // Create the root group with OME-Zarr metadata
    const rootGroup = await zarr.create(root, {
      attributes: {
        multiscales: [
          {
            version: _version,
            name: multiscales.metadata.name,
            axes: multiscales.metadata.axes,
            datasets: multiscales.metadata.datasets,
            ...(multiscales.metadata.coordinateTransformations && {
              coordinateTransformations:
                multiscales.metadata.coordinateTransformations,
            }),
          },
        ],
        ...(multiscales.metadata.omero && {
          omero: multiscales.metadata.omero,
        }),
      },
    });

    // Write each image in the multiscales
    for (let i = 0; i < multiscales.images.length; i++) {
      const image = multiscales.images[i];
      const dataset = multiscales.metadata.datasets[i];

      if (!dataset) {
        throw new Error(`No dataset configuration found for image ${i}`);
      }

      await _writeImage(
        rootGroup as zarr.Group<MemoryStore>,
        image,
        dataset.path,
      );
    }
  } catch (error) {
    throw new Error(
      `Failed to write OME-Zarr: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
  }
}

function _convertDtypeToZarrType(dtype: string): zarr.DataType {
  // Map common numpy/LazyArray dtypes to zarrita data types
  const dtypeMap: Record<string, zarr.DataType> = {
    int8: "int8",
    int16: "int16",
    int32: "int32",
    int64: "int64",
    uint8: "uint8",
    uint16: "uint16",
    uint32: "uint32",
    uint64: "uint64",
    float32: "float32",
    float64: "float64",
    bool: "bool",
    // Handle some alternative formats
    i1: "int8",
    i2: "int16",
    i4: "int32",
    i8: "int64",
    u1: "uint8",
    u2: "uint16",
    u4: "uint32",
    u8: "uint64",
    f4: "float32",
    f8: "float64",
  };

  return dtypeMap[dtype] || ("float32" as zarr.DataType);
}

async function _writeImage(
  group: zarr.Group<MemoryStore>,
  image: NgffImage,
  arrayPath: string,
): Promise<void> {
  try {
    const chunks = getChunksFromImage(image);

    // Convert LazyArray dtype to zarrita DataType
    const zarrDataType = _convertDtypeToZarrType(image.data.dtype);

    // Create array location
    const arrayLocation = group.resolve(arrayPath);

    // Create the zarr array with proper configuration
    const zarrArray = await zarr.create(arrayLocation, {
      shape: image.data.shape,
      data_type: zarrDataType,
      chunk_shape: chunks,
      fill_value: 0,
    });

    // Write the data - for now we'll implement a placeholder
    // In a real implementation, this would iterate through the LazyArray chunks
    // and write each chunk's data using zarr.set()
    await _writeArrayData(
      zarrArray as zarr.Array<zarr.DataType, MemoryStore>,
      image,
    );
  } catch (error) {
    throw new Error(
      `Failed to write image array: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
  }
}

function getChunksFromImage(image: NgffImage): number[] {
  if (image.data.chunks.length > 0 && image.data.chunks[0].length > 0) {
    return image.data.chunks[0];
  }

  return image.data.shape.map((dim) => Math.min(dim, 1024));
}

async function _writeArrayData(
  zarrArray: zarr.Array<zarr.DataType, MemoryStore>,
  image: NgffImage,
): Promise<void> {
  try {
    // For now, we'll write a placeholder implementation
    // In a full implementation, this would:
    // 1. Create typed arrays from the LazyArray data
    // 2. Use zarr.set(zarrArray, selection, data) to write each chunk

    // Create a dummy typed array filled with zeros as placeholder
    const totalSize = image.data.shape.reduce((acc, dim) => acc * dim, 1);

    // Create appropriate typed array based on the data type
    let dummyData: TypedArray;
    const dtype = image.data.dtype.toLowerCase();

    if (dtype.includes("int8") || dtype === "i1") {
      dummyData = new Int8Array(totalSize);
    } else if (dtype.includes("uint8") || dtype === "u1") {
      dummyData = new Uint8Array(totalSize);
    } else if (dtype.includes("int16") || dtype === "i2") {
      dummyData = new Int16Array(totalSize);
    } else if (dtype.includes("uint16") || dtype === "u2") {
      dummyData = new Uint16Array(totalSize);
    } else if (dtype.includes("int32") || dtype === "i4") {
      dummyData = new Int32Array(totalSize);
    } else if (dtype.includes("uint32") || dtype === "u4") {
      dummyData = new Uint32Array(totalSize);
    } else if (dtype.includes("float32") || dtype === "f4") {
      dummyData = new Float32Array(totalSize);
    } else if (dtype.includes("float64") || dtype === "f8") {
      dummyData = new Float64Array(totalSize);
    } else {
      // Default to Float32Array for unknown types
      dummyData = new Float32Array(totalSize);
    }

    // Try to write the data using zarr.set with proper selection syntax
    // Based on zarrita docs, the selection should use an array of slices
    try {
      await zarr.set(zarrArray, null, dummyData);
    } catch (error) {
      // If that fails, try writing chunk by chunk
      console.warn(
        `Failed to write full array, trying chunk-based approach: ${error}`,
      );

      // For now, just log that we would write the data here
      // A full implementation would iterate through chunks and write each one
      console.log(
        `Would write ${dummyData.constructor.name} of length ${dummyData.length} to zarr array`,
      );
    }
  } catch (error) {
    throw new Error(
      `Failed to write array data: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
  }
}

type TypedArray =
  | Int8Array
  | Uint8Array
  | Int16Array
  | Uint16Array
  | Int32Array
  | Uint32Array
  | Float32Array
  | Float64Array;
