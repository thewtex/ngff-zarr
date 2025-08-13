import { FileSystemStore } from "@zarrita/storage";
import * as zarr from "zarrita";
import { toNgffZarr } from "../src/io/to_ngff_zarr.ts";
import type { Multiscales } from "../src/types/multiscales.ts";
import { assert } from "@std/assert";

/**
 * Get the test data directory path
 */
export function getTestDataDir(): string {
  const testDir = new URL("../../py/test/data", import.meta.url);
import { fromFileUrl } from "@std/path";

/**
 * Get the test data directory path
 */
export function getTestDataDir(): string {
  const testDir = new URL("../../py/test/data", import.meta.url);
  return fromFileUrl(testDir);
}

/**
 * Get all keys from a zarrita store
 */
export async function getStoreKeys(
  store: zarr.Readable | zarr.AsyncReadable,
): Promise<Set<string>> {
  const keys = new Set<string>();

  // For zarrita stores, we need to walk the directory structure
  // This is a simplified approach - in practice, we'd use consolidated metadata
  // or walk the filesystem/fetch store to discover all keys

  if ("contents" in store && typeof store.contents === "function") {
    // For consolidated stores
    const contents = store.contents();
    for (const item of contents) {
      // Add the metadata files for each item
      if (item.kind === "group") {
        keys.add(`${item.path}/.zgroup`);
        keys.add(`${item.path}/.zattrs`);
      } else if (item.kind === "array") {
        keys.add(`${item.path}/.zarray`);
        keys.add(`${item.path}/.zattrs`);
      }
    }
  } else if (store instanceof FileSystemStore) {
    // For FileSystemStore, we need to walk the filesystem
    await walkFileSystemStore(store, "", keys);
  } else {
    // For other stores, try to discover common paths
    await tryDiscoverKeys(store, keys);
  }

  return keys;
}

/**
 * Walk a FileSystemStore to discover all keys
 */
async function walkFileSystemStore(
  store: FileSystemStore,
  prefix: string,
  keys: Set<string>,
): Promise<void> {
  const fs = await import("node:fs/promises");
  const path = await import("node:path");

  try {
    const fullPath = path.join(store.root, prefix);
    const entries = await fs.readdir(fullPath, { withFileTypes: true });

    for (const entry of entries) {
      const relativePath = prefix ? `${prefix}/${entry.name}` : entry.name;
      const key = `/${relativePath}`;

      if (entry.isFile()) {
        keys.add(key);
      } else if (entry.isDirectory()) {
        await walkFileSystemStore(store, relativePath, keys);
      }
    }
  } catch (err) {
    // Ignore errors for missing directories
    if (
      err &&
      typeof err === "object" &&
      "code" in err &&
      err.code === "ENOENT"
    ) {
      return;
    }
    throw err;
  }
}

/**
 * Try to discover keys by checking common zarr metadata patterns
 */
async function tryDiscoverKeys(
  store: zarr.Readable | zarr.AsyncReadable,
  keys: Set<string>,
): Promise<void> {
  const commonKeys = [
    "/.zgroup",
    "/.zattrs",
    "/.zmetadata",
    "/zarr.json",
    "/0/.zarray",
    "/0/.zattrs",
    "/1/.zarray",
    "/1/.zattrs",
    "/2/.zarray",
    "/2/.zattrs",
  ];

  for (const key of commonKeys) {
    try {
      const result = await store.get(key as `/${string}`);
      if (result !== undefined) {
        keys.add(key);
      }
    } catch {
      // Ignore errors for missing keys
    }
  }
}

/**
 * Get contents of all keys from a store
 */
export async function getStoreContents(
  store: zarr.Readable | zarr.AsyncReadable,
  keys: Set<string>,
): Promise<Map<string, Uint8Array>> {
  const contents = new Map<string, Uint8Array>();

  for (const key of keys) {
    try {
      const data = await store.get(key as `/${string}`);
      if (data !== undefined) {
        contents.set(key, data);
      }
    } catch {
      // Ignore errors for missing keys
    }
  }

  return contents;
}

/**
 * Compare two stores for equality
 */
export async function storeEquals(
  baselineStore: zarr.Readable | zarr.AsyncReadable,
  testStore: zarr.Readable | zarr.AsyncReadable,
): Promise<boolean> {
  const baselineKeys = await getStoreKeys(baselineStore);
  const testKeys = await getStoreKeys(testStore);

  const jsonKeys = new Set([".zmetadata", ".zattrs", ".zgroup", "zarr.json"]);

  const baselineContents = await getStoreContents(baselineStore, baselineKeys);
  const testContents = await getStoreContents(testStore, testKeys);

  for (const key of baselineKeys) {
    const isJsonKey = Array.from(jsonKeys).some((suffix) =>
      key.endsWith(suffix)
    );

    if (isJsonKey) {
      const baselineData = baselineContents.get(key);
      const testData = testContents.get(key);

      if (!baselineData || !testData) {
        console.error(`Missing data for key ${key}`);
        return false;
      }

      try {
        const baselineJson = JSON.parse(new TextDecoder().decode(baselineData));
        const testJson = JSON.parse(new TextDecoder().decode(testData));

        // Deep compare JSON objects (simplified - could use a proper deep diff library)
        if (!deepEquals(baselineJson, testJson)) {
          console.error(`Metadata in ${key} files do not match`);
          console.error(`Baseline:`, baselineJson);
          console.error(`Test:`, testJson);
          return false;
        }
      } catch (err) {
        console.error(`Failed to parse JSON for key ${key}:`, err);
        return false;
      }
    } else {
      if (!testKeys.has(key)) {
        console.error(`baseline key ${key} not in test keys`);
        console.error(`test keys:`, Array.from(testKeys));
        return false;
      }

      const baselineData = baselineContents.get(key);
      const testData = testContents.get(key);

      if (!isMetadataKey(key) && !arraysEqual(baselineData, testData)) {
        console.error(`test value != baseline value for key ${key}`);
        return false;
      }
    }
  }

  return true;
}

/**
 * Check if a key represents metadata
 */
function isMetadataKey(key: string): boolean {
  return (
    key.includes(".zattrs") ||
    key.includes(".zgroup") ||
    key.includes("zarr.json")
  );
}

/**
 * Compare two Uint8Arrays for equality
 */
function arraysEqual(a?: Uint8Array, b?: Uint8Array): boolean {
  if (!a && !b) return true;
  if (!a || !b) return false;
  if (a.length !== b.length) return false;

  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}

/**
 * Deep equality check for objects (simplified implementation)
 */
function deepEquals(a: unknown, b: unknown): boolean {
  if (a === b) return true;

  if (a === null || b === null) return a === b;
  if (typeof a !== typeof b) return false;
  if (typeof a !== "object") return a === b;

  if (Array.isArray(a) !== Array.isArray(b)) return false;

  if (Array.isArray(a)) {
    const arrayB = b as unknown[];
    if (a.length !== arrayB.length) return false;
    for (let i = 0; i < a.length; i++) {
      if (!deepEquals(a[i], arrayB[i])) return false;
    }
    return true;
  }

  const objA = a as Record<string, unknown>;
  const objB = b as Record<string, unknown>;
  const keysA = Object.keys(objA);
  const keysB = Object.keys(objB);

  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if (!keysB.includes(key)) return false;
    if (!deepEquals(objA[key], objB[key])) return false;
  }

  return true;
}

/**
 * Verify a multiscales object against a baseline stored on disk
 */
export async function verifyAgainstBaseline(
  datasetName: string,
  baselineName: string,
  multiscales: Multiscales,
  version: "0.4" | "0.5" = "0.4",
): Promise<void> {
  const testDataDir = getTestDataDir();
  const baselinePath =
    `${testDataDir}/baseline/v${version}/${datasetName}/${baselineName}`;

  const baselineStore = new FileSystemStore(baselinePath);
  const testStore = new Map<string, Uint8Array>();

  await toNgffZarr(testStore, multiscales, { version });

  const equal = await storeEquals(baselineStore, testStore);
  assert(equal, `Multiscales does not match baseline at ${baselinePath}`);
}

/**
 * Store new multiscales for creating test baselines
 * Helper method for writing output results to disk for later upload as test baseline
 */
export async function storeNewMultiscales(
  datasetName: string,
  baselineName: string,
  multiscales: Multiscales,
  version: "0.4" | "0.5" = "0.4",
): Promise<void> {
  const testDataDir = getTestDataDir();
  const storePath =
    `${testDataDir}/baseline/zarr3/v${version}/${datasetName}/${baselineName}`;

  await toNgffZarr(storePath, multiscales, { version });
}
