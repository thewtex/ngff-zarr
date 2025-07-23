import type { ArrayLike } from "./array_interface.ts";

export interface LazyArrayMetadata {
  shape: number[];
  dtype: string;
  chunks: number[][];
  name: string;
}

export class LazyArray implements ArrayLike {
  public readonly shape: number[];
  public readonly dtype: string;
  public readonly chunks: number[];
  public readonly name: string;
  public readonly path: string;

  constructor(metadata: LazyArrayMetadata) {
    this.shape = [...metadata.shape];
    this.dtype = metadata.dtype;
    this.chunks = metadata.chunks[0] || [...metadata.shape]; // Use first chunk as the chunk shape
    this.name = metadata.name;
    this.path = "/" + metadata.name;
  }

  get ndim(): number {
    return this.shape.length;
  }

  get size(): number {
    return this.shape.reduce((acc, dim) => acc * dim, 1);
  }

  get chunksize(): number[] {
    return this.chunks;
  }

  toString(): string {
    const chunkStr =
      this.chunks.length > 0
        ? `chunksize=(${this.chunks.join(", ")})`
        : "chunksize=()";
    return `LazyArray(name=${this.name}, shape=(${this.shape.join(
      ", "
    )}), dtype=${this.dtype}, ${chunkStr}, chunktype=TypedArray)`;
  }
}
