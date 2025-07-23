import * as zarr from "zarrita";
import type { ArrayLike } from "./array_interface.ts";
import type { Units } from "./units.ts";

export type ComputedCallback = () => void;

export interface NgffImageOptions {
  data: ArrayLike | zarr.Array<zarr.DataType, zarr.Readable>;
  dims: string[];
  scale: Record<string, number>;
  translation: Record<string, number>;
  name: string | undefined;
  axesUnits: Record<string, Units> | undefined;
  computedCallbacks: ComputedCallback[] | undefined;
}

export class NgffImage {
  public readonly data: ArrayLike | zarr.Array<zarr.DataType, zarr.Readable>;
  public readonly dims: string[];
  public readonly scale: Record<string, number>;
  public readonly translation: Record<string, number>;
  public readonly name: string;
  public readonly axesUnits: Record<string, Units> | undefined;
  public readonly computedCallbacks: ComputedCallback[];

  constructor(options: NgffImageOptions) {
    this.data = options.data;
    this.dims = [...options.dims];
    this.scale = { ...options.scale };
    this.translation = { ...options.translation };
    this.name = options.name ?? "image";
    this.axesUnits = options.axesUnits ? { ...options.axesUnits } : undefined;
    this.computedCallbacks = [...(options.computedCallbacks ?? [])];
  }

  toString(): string {
    const axesUnitsStr = this.axesUnits
      ? JSON.stringify(this.axesUnits)
      : "None";

    // Create LazyArray-like string representation
    const path =
      "path" in this.data && this.data.path ? this.data.path : this.name;
    const chunks = Array.isArray(this.data.chunks)
      ? this.data.chunks.join(", ")
      : String(this.data.chunks);

    const arrayStr = `LazyArray(name=${path}, shape=(${this.data.shape.join(
      ", "
    )}), dtype=${
      this.data.dtype
    }, chunksize=(${chunks}), chunktype=TypedArray)`;

    return `NgffImage(
    data=${arrayStr},
    dims=[${this.dims.map((d) => `'${d}'`).join(", ")}],
    scale=${JSON.stringify(this.scale)},
    translation=${JSON.stringify(this.translation)},
    name='${this.name}',
    axes_units=${axesUnitsStr},
    computed_callbacks=[${this.computedCallbacks.length} callbacks]
)`;
  }
}
