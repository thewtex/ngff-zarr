import { assertEquals, assertThrows } from "@std/assert";
import { LazyArray } from "../src/types/lazy_array.ts";
import { NgffImage } from "../src/types/ngff_image.ts";
import { Multiscales } from "../src/types/multiscales.ts";
import { Methods } from "../src/types/methods.ts";
import { validateColor } from "../src/types/zarr_metadata.ts";

Deno.test("LazyArray creation and properties", () => {
  const metadata = {
    shape: [256, 256],
    dtype: "uint8",
    chunks: [[256, 256]],
    name: "test_array",
  };

  const lazyArray = new LazyArray(metadata);

  assertEquals(lazyArray.shape, [256, 256]);
  assertEquals(lazyArray.dtype, "uint8");
  assertEquals(lazyArray.ndim, 2);
  assertEquals(lazyArray.size, 65536);
  assertEquals(lazyArray.chunksize, [256, 256]);
  assertEquals(lazyArray.name, "test_array");
});

Deno.test("LazyArray toString", () => {
  const metadata = {
    shape: [100, 200],
    dtype: "float32",
    chunks: [[50, 100]],
    name: "float_array",
  };

  const lazyArray = new LazyArray(metadata);
  const str = lazyArray.toString();

  assertEquals(
    str,
    "dask.array<float_array, shape=(100, 200), dtype=float32, chunksize=(50, 100), chunktype=TypedArray>",
  );
});

Deno.test("NgffImage creation", () => {
  const lazyArray = new LazyArray({
    shape: [256, 256],
    dtype: "uint8",
    chunks: [[64, 64]],
    name: "image",
  });

  const ngffImage = new NgffImage({
    data: lazyArray,
    dims: ["y", "x"],
    scale: { y: 1.0, x: 1.0 },
    translation: { y: 0.0, x: 0.0 },
    name: "test_image",
    axesUnits: undefined,
    computedCallbacks: undefined,
  });

  assertEquals(ngffImage.dims, ["y", "x"]);
  assertEquals(ngffImage.scale, { y: 1.0, x: 1.0 });
  assertEquals(ngffImage.translation, { y: 0.0, x: 0.0 });
  assertEquals(ngffImage.name, "test_image");
  assertEquals(ngffImage.axesUnits, undefined);
  assertEquals(ngffImage.computedCallbacks.length, 0);
});

Deno.test("NgffImage with axes units", () => {
  const lazyArray = new LazyArray({
    shape: [100, 100, 100],
    dtype: "uint16",
    chunks: [[50, 50, 50]],
    name: "volume",
  });

  const ngffImage = new NgffImage({
    data: lazyArray,
    dims: ["z", "y", "x"],
    scale: { z: 2.5, y: 1.0, x: 1.0 },
    translation: { z: 0.0, y: 0.0, x: 0.0 },
    name: "image",
    axesUnits: { z: "micrometer", y: "micrometer", x: "micrometer" },
    computedCallbacks: undefined,
  });

  assertEquals(ngffImage.axesUnits, {
    z: "micrometer",
    y: "micrometer",
    x: "micrometer",
  });
});

Deno.test("Multiscales creation", () => {
  const lazyArray = new LazyArray({
    shape: [256, 256],
    dtype: "uint8",
    chunks: [[64, 64]],
    name: "image",
  });

  const ngffImage = new NgffImage({
    data: lazyArray,
    dims: ["y", "x"],
    scale: { y: 1.0, x: 1.0 },
    translation: { y: 0.0, x: 0.0 },
    name: "image",
    axesUnits: undefined,
    computedCallbacks: undefined,
  });

  const metadata = {
    axes: [
      { name: "y" as const, type: "space" as const, unit: undefined },
      { name: "x" as const, type: "space" as const, unit: undefined },
    ],
    datasets: [
      {
        path: "0",
        coordinateTransformations: [
          { type: "scale" as const, scale: [1.0, 1.0] },
          { type: "translation" as const, translation: [0.0, 0.0] },
        ],
      },
    ],
    coordinateTransformations: undefined,
    omero: undefined,
    name: "test",
    version: "0.4",
  };

  const multiscales = new Multiscales({
    images: [ngffImage],
    metadata,
    scaleFactors: [2, 4],
    method: Methods.ITKWASM_GAUSSIAN,
    chunks: undefined,
  });

  assertEquals(multiscales.images.length, 1);
  assertEquals(multiscales.scaleFactors, [2, 4]);
  assertEquals(multiscales.method, Methods.ITKWASM_GAUSSIAN);
});

Deno.test("validateColor function", () => {
  validateColor("FF0000");
  validateColor("00FF00");
  validateColor("0000FF");
  validateColor("123ABC");

  assertThrows(() => validateColor("GG0000"), Error, "Invalid color");
  assertThrows(() => validateColor("FF00"), Error, "Invalid color");
  assertThrows(() => validateColor("FF00000"), Error, "Invalid color");
  assertThrows(() => validateColor("#FF0000"), Error, "Invalid color");
});
