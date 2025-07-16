import { z } from "zod";
import { AxesTypeSchema, SupportedDimsSchema, UnitsSchema } from "./units.ts";

export const AxisSchema: z.ZodObject<{
  name: typeof SupportedDimsSchema;
  type: typeof AxesTypeSchema;
  unit: z.ZodOptional<typeof UnitsSchema>;
}> = z.object({
  name: SupportedDimsSchema,
  type: AxesTypeSchema,
  unit: UnitsSchema.optional(),
});

export const IdentitySchema: z.ZodObject<{
  type: z.ZodLiteral<"identity">;
}> = z.object({
  type: z.literal("identity"),
});

export const ScaleSchema: z.ZodObject<{
  scale: z.ZodArray<z.ZodNumber>;
  type: z.ZodLiteral<"scale">;
}> = z.object({
  scale: z.array(z.number()),
  type: z.literal("scale"),
});

export const TranslationSchema: z.ZodObject<{
  translation: z.ZodArray<z.ZodNumber>;
  type: z.ZodLiteral<"translation">;
}> = z.object({
  translation: z.array(z.number()),
  type: z.literal("translation"),
});

export const TransformSchema: z.ZodUnion<
  [typeof ScaleSchema, typeof TranslationSchema]
> = z.union([ScaleSchema, TranslationSchema]);

export const DatasetSchema: z.ZodObject<{
  path: z.ZodString;
  coordinateTransformations: z.ZodArray<typeof TransformSchema>;
}> = z.object({
  path: z.string(),
  coordinateTransformations: z.array(TransformSchema),
});

export const OmeroWindowSchema: z.ZodObject<{
  min: z.ZodNumber;
  max: z.ZodNumber;
  start: z.ZodNumber;
  end: z.ZodNumber;
}> = z.object({
  min: z.number(),
  max: z.number(),
  start: z.number(),
  end: z.number(),
});

export const OmeroChannelSchema: z.ZodObject<{
  color: z.ZodString;
  window: typeof OmeroWindowSchema;
  label: z.ZodOptional<z.ZodString>;
}> = z.object({
  color: z.string().regex(/^[0-9A-Fa-f]{6}$/, {
    message: "Color must be 6 hex digits",
  }),
  window: OmeroWindowSchema,
  label: z.string().optional(),
});

export const OmeroSchema: z.ZodObject<{
  channels: z.ZodArray<typeof OmeroChannelSchema>;
}> = z.object({
  channels: z.array(OmeroChannelSchema),
});

export const MetadataSchema: z.ZodObject<{
  axes: z.ZodArray<typeof AxisSchema>;
  datasets: z.ZodArray<typeof DatasetSchema>;
  coordinateTransformations: z.ZodOptional<z.ZodArray<typeof TransformSchema>>;
  omero: z.ZodOptional<typeof OmeroSchema>;
  name: z.ZodDefault<z.ZodString>;
  version: z.ZodDefault<z.ZodString>;
}> = z.object({
  axes: z.array(AxisSchema),
  datasets: z.array(DatasetSchema),
  coordinateTransformations: z.array(TransformSchema).optional(),
  omero: OmeroSchema.optional(),
  name: z.string().default("image"),
  version: z.string().default("0.4"),
});
