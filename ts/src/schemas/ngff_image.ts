import { z } from "zod";
import { UnitsSchema } from "./units.ts";
import { DaskArrayMetadataSchema } from "./dask_array.ts";

export const NgffImageOptionsSchema = z.object({
  data: DaskArrayMetadataSchema,
  dims: z.array(z.string()),
  scale: z.record(z.string(), z.number()),
  translation: z.record(z.string(), z.number()),
  name: z.string().default("image"),
  axesUnits: z.record(z.string(), UnitsSchema).optional(),
  computedCallbacks: z.array(z.function()).default([]),
});
