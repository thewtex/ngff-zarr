import PQueue from "p-queue";

export type ChunkQueue = {
  add(fn: () => Promise<void>): void;
  onIdle(): Promise<void>;
};

export function create_queue(): ChunkQueue {
  const concurrency = Math.min(navigator?.hardwareConcurrency || 4, 128);
  const queue = new PQueue({ concurrency });
  return {
    add: (fn: () => Promise<void>) => queue.add(fn),
    onIdle: queue.onIdle.bind(queue),
  };
}
