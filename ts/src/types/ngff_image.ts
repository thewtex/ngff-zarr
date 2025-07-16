import type { LazyArray } from "./lazy_array.ts";
import type { Units } from "./units.ts";

export type ComputedCallback = () => void;

export interface NgffImageOptions {
  data: LazyArray;
  dims: string[];
  scale: Record<string, number>;
  translation: Record<string, number>;
  name: string | undefined;
  axesUnits: Record<string, Units> | undefined;
  computedCallbacks: ComputedCallback[] | undefined;
}

export class NgffImage {
  public readonly data: LazyArray;
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
    return `NgffImage(
    data=${this.data.toString()},
    dims=[${this.dims.map((d) => `'${d}'`).join(", ")}],
    scale=${JSON.stringify(this.scale)},
    translation=${JSON.stringify(this.translation)},
    name='${this.name}',
    axes_units=${axesUnitsStr},
    computed_callbacks=[${this.computedCallbacks.length} callbacks]
)`;
  }
}
