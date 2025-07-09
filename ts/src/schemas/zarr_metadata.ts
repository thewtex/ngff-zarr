import { z } from "zod";
import { AxesTypeSchema, SupportedDimsSchema, UnitsSchema } from "./units.ts";

export const AxisSchema = z.object({
  name: SupportedDimsSchema,
  type: AxesTypeSchema,
  unit: UnitsSchema.optional(),
});

export const IdentitySchema = z.object({
  type: z.literal("identity"),
});

export const ScaleSchema = z.object({
  scale: z.array(z.number()),
  type: z.literal("scale"),
});

export const TranslationSchema = z.object({
  translation: z.array(z.number()),
  type: z.literal("translation"),
});

export const TransformSchema = z.union([ScaleSchema, TranslationSchema]);

export const DatasetSchema = z.object({
  path: z.string(),
  coordinateTransformations: z.array(TransformSchema),
});

export const OmeroWindowSchema = z.object({
  min: z.number(),
  max: z.number(),
  start: z.number(),
  end: z.number(),
});

export const OmeroChannelSchema = z.object({
  color: z.string().regex(/^[0-9A-Fa-f]{6}$/, {
    message: "Color must be 6 hex digits",
  }),
  window: OmeroWindowSchema,
  label: z.string().optional(),
});

export const OmeroSchema = z.object({
  channels: z.array(OmeroChannelSchema),
});

export const MetadataSchema = z.object({
  axes: z.array(AxisSchema),
  datasets: z.array(DatasetSchema),
  coordinateTransformations: z.array(TransformSchema).optional(),
  omero: OmeroSchema.optional(),
  name: z.string().default("image"),
  version: z.string().default("0.4"),
});
