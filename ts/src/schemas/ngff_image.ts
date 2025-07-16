import { z } from "zod";
import { UnitsSchema } from "./units.ts";
import { LazyArrayMetadataSchema } from "./lazy_array.ts";

export const NgffImageOptionsSchema: z.ZodObject<{
  data: typeof LazyArrayMetadataSchema;
  dims: z.ZodArray<z.ZodString>;
  scale: z.ZodRecord<z.ZodString, z.ZodNumber>;
  translation: z.ZodRecord<z.ZodString, z.ZodNumber>;
  name: z.ZodDefault<z.ZodString>;
  axesUnits: z.ZodOptional<z.ZodRecord<z.ZodString, typeof UnitsSchema>>;
  computedCallbacks: z.ZodDefault<z.ZodArray<z.ZodAny>>;
}> = z.object({
  data: LazyArrayMetadataSchema,
  dims: z.array(z.string()),
  scale: z.record(z.string(), z.number()),
  translation: z.record(z.string(), z.number()),
  name: z.string().default("image"),
  axesUnits: z.record(z.string(), UnitsSchema).optional(),
  computedCallbacks: z.array(z.any()).default([]),
});
