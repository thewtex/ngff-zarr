import { z } from "zod";
import { UnitsSchema } from "./units.ts";
import { LazyArrayMetadataSchema } from "./lazy_array.ts";

export const NgffImageOptionsSchema = z.object({
  data: LazyArrayMetadataSchema,
  dims: z.array(z.string()),
  scale: z.record(z.string(), z.number()),
  translation: z.record(z.string(), z.number()),
  name: z.string().default("image"),
  axesUnits: z.record(z.string(), UnitsSchema).optional(),
  computedCallbacks: z.array(z.function()).default([]),
});
