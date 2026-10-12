// SPDX-FileCopyrightText: Copyright (c) Fideus Labs LLC
// SPDX-License-Identifier: MIT
/** toOmeZarr honors overwrite: false and the codecs it is given. */
import { assertEquals, assertRejects } from "@std/assert";
import { unzipSync } from "fflate";
import * as zarr from "zarrita";

import { toOmeZarr, toOmeZarrOzxData } from "../src/io/to_ngff_zarr.ts";
import { NgffImage } from "../src/types/ngff_image.ts";
import { bytesOnlyCodecs } from "../src/utils/codecs.ts";
import {
  createAxis,
  createDataset,
  createMetadata,
  createMultiscales,
} from "../src/utils/factory.ts";

async function multiscales() {
  const source = new Map<string, Uint8Array>();
  const data = await zarr.create(zarr.root(source).resolve("d"), {
    shape: [8, 8],
    chunkShape: [4, 4],
    dtype: "uint8",
    fillValue: 0,
  });
  const image = new NgffImage({
    data,
    dims: ["y", "x"],
    scale: { y: 1, x: 1 },
    translation: { y: 0, x: 0 },
    name: "image",
    axesUnits: undefined,
    computedCallbacks: undefined,
  });
  const metadata = createMetadata(
    [createAxis("y", "space"), createAxis("x", "space")],
    [createDataset("s0", [1, 1], [0, 0])],
    "image",
  );
  return createMultiscales([image], metadata);
}

Deno.test("overwrite: false refuses a store that holds the image", async () => {
  const store = new Map<string, Uint8Array>();
  await toOmeZarr(store, await multiscales());
  await assertRejects(
    async () => toOmeZarr(store, await multiscales(), { overwrite: false }),
    Error,
    "already holds",
  );
});

Deno.test(".ozx archives use the codecs they are given", async () => {
  const archive = await toOmeZarrOzxData(await multiscales(), {
    codecs: bytesOnlyCodecs(),
  });
  const array = JSON.parse(
    new TextDecoder().decode(unzipSync(archive)["s0/zarr.json"]),
  );
  const names = JSON.stringify(array.codecs);
  assertEquals(names.includes("blosc"), false, names);
});

Deno.test("overwrite: false refuses an existing .ozx file", async () => {
  const dir = await Deno.makeTempDir();
  const path = `${dir}/image.ozx`;
  await toOmeZarr(path, await multiscales());
  await assertRejects(
    async () => toOmeZarr(path, await multiscales(), { overwrite: false }),
    Error,
    "already exists",
  );
  await Deno.remove(dir, { recursive: true });
});
