import { z } from "zod";

export const LazyArrayMetadataSchema = z.object({
  shape: z.array(z.number().int().nonnegative()),
  dtype: z.string(),
  chunks: z.array(z.array(z.number().int().nonnegative())),
  name: z.string(),
});
