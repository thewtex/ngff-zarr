import { z } from "zod";

export const LazyArrayMetadataSchema: z.ZodObject<{
  shape: z.ZodArray<z.ZodNumber>;
  dtype: z.ZodString;
  chunks: z.ZodArray<z.ZodArray<z.ZodNumber>>;
  name: z.ZodString;
}> = z.object({
  shape: z.array(z.number().int().nonnegative()),
  dtype: z.string(),
  chunks: z.array(z.array(z.number().int().nonnegative())),
  name: z.string(),
});
