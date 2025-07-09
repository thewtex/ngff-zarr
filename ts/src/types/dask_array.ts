export interface DaskArrayMetadata {
  shape: number[];
  dtype: string;
  chunks: number[][];
  name: string;
}

export class DaskArray {
  public readonly shape: number[];
  public readonly dtype: string;
  public readonly chunks: number[][];
  public readonly name: string;

  constructor(metadata: DaskArrayMetadata) {
    this.shape = [...metadata.shape];
    this.dtype = metadata.dtype;
    this.chunks = metadata.chunks.map((chunk) => [...chunk]);
    this.name = metadata.name;
  }

  get ndim(): number {
    return this.shape.length;
  }

  get size(): number {
    return this.shape.reduce((acc, dim) => acc * dim, 1);
  }

  get chunksize(): number[] {
    return this.chunks[0] || [];
  }

  toString(): string {
    const chunkStr = this.chunksize.length > 0
      ? `chunksize=(${this.chunksize.join(", ")})`
      : "chunksize=()";
    return `dask.array<${this.name}, shape=(${
      this.shape.join(", ")
    }), dtype=${this.dtype}, ${chunkStr}, chunktype=TypedArray>`;
  }
}
