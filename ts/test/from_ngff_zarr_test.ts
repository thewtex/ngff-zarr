import { assertEquals, assertExists } from "@std/assert";
import { fromNgffZarr } from "../src/io/from_ngff_zarr.ts";
import { toNgffZarr } from "../src/io/to_ngff_zarr.ts";

Deno.test("omero zarr from_ngff_zarr to_ngff_zarr", async () => {
  const datasetName = "13457537";
  // Use better cross-platform path handling
  const storePath = new URL(
    "../../py/test/data/input/13457537.zarr",
    import.meta.url,
  );
  const resolvedPath = storePath.pathname.replace(/^\/([A-Za-z]:)/, "$1"); // Fix Windows paths
  const version = "0.4";

  const multiscales = await fromNgffZarr(resolvedPath, { validate: true });

  // Verify that we got valid multiscales data
  assertExists(multiscales);
  assertExists(multiscales.images);
  assertEquals(Array.isArray(multiscales.images), true);
  assertEquals(multiscales.images.length > 0, true);

  // Verify metadata exists
  assertExists(multiscales.metadata);
  assertExists(multiscales.metadata.axes);
  assertExists(multiscales.metadata.datasets);

  // Check that we have the expected structure
  const firstImage = multiscales.images[0];
  assertExists(firstImage);
  assertExists(firstImage.data);
  assertExists(firstImage.dims);
  assertExists(firstImage.scale);

  // Log some information about the loaded data for debugging
  console.log(`Loaded ${multiscales.images.length} images from ${datasetName}`);
  console.log(`First image shape: ${firstImage.data.shape}`);
  console.log(`First image dims: ${firstImage.dims}`);
  console.log(
    `Metadata axes: ${multiscales.metadata.axes.map((a) => a.name).join(", ")}`,
  );

  // console.log(`Multiscales:`, multiscales.toString());

  const memoryStore = new Map<string, Uint8Array>();
  await toNgffZarr(memoryStore, multiscales, { version });

  // TODO: When toNgffZarr is fully implemented, this test should be updated to:
  // 1. Create a proper memory store (equivalent to Python's MemoryStore())
  // 2. Call toNgffZarr(memoryStore, multiscales, { version })
  // 3. Verify the write was successful
  // 4. Optionally, read back from the memory store and verify round-trip consistency
});
