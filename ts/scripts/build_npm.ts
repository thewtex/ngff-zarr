#!/usr/bin/env -S deno run --allow-all

import { build, emptyDir } from "https://deno.land/x/dnt@0.40.0/mod.ts";

await emptyDir("./npm");

await build({
  entryPoints: ["./src/mod.ts"],
  outDir: "./npm",
  shims: {
    deno: true,
  },
  package: {
    name: "@fideus-labs/ngff-zarr",
    version: "0.1.0",
    description:
      "TypeScript implementation of ngff-zarr for reading and writing OME-Zarr files",
    license: "MIT",
    repository: {
      type: "git",
      url: "git+https://github.com/thewtex/ngff-zarr.git",
    },
    bugs: {
      url: "https://github.com/thewtex/ngff-zarr/issues",
    },
    homepage: "https://github.com/thewtex/ngff-zarr#readme",
    keywords: [
      "ome-zarr",
      "zarr",
      "microscopy",
      "imaging",
      "ngff",
      "typescript",
      "deno",
    ],
    author: "ngff-zarr contributors",
    main: "./esm/mod.js",
    types: "./esm/mod.d.ts",
    exports: {
      ".": {
        import: "./esm/mod.js",
        require: "./script/mod.js",
        types: "./esm/mod.d.ts",
      },
    },
    files: [
      "esm/",
      "script/",
      "types/",
      "README.md",
      "LICENSE",
    ],
  },
  postBuild() {
    Deno.copyFileSync("../README.md", "npm/README.md");
    Deno.copyFileSync("../LICENSE.txt", "npm/LICENSE");
  },
  mappings: {
    "https://deno.land/std@0.208.0/assert/mod.ts": {
      name: "@types/node",
      version: "^20.0.0",
      peerDependency: true,
    },
  },
  compilerOptions: {
    lib: ["ES2022", "DOM"],
    target: "ES2022",
  },
  filterDiagnostic(diagnostic) {
    return !diagnostic.messageText?.toString().includes("@std/assert");
  },
});
