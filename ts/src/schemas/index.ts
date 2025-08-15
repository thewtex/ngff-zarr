// Re-export all schemas with explicit naming to avoid conflicts
export * from "./units.ts";
export * from "./methods.ts";

// RFC4 schemas
export {
  AnatomicalOrientationValuesSchema,
  AnatomicalOrientationSchema,
  OrientationSchema,
  AxesNamesSchema,
  SpaceAxesNamesSchema,
  AxisTypeSchema,
  SpaceUnitSchema,
  TimeUnitSchema,
  BaseAxisSchema,
  ChannelAxisSchema,
  SpaceAxisSchema,
  TimeAxisSchema,
  AxisSchema as RFC4AxisSchema,
  AxesSchema as RFC4AxesSchema,
  // Type exports
  type AnatomicalOrientationValues,
  type AnatomicalOrientation,
  type Orientation,
  type AxesNames,
  type SpaceAxesNames,
  type AxisType,
  type SpaceUnit,
  type TimeUnit,
  type BaseAxis,
  type ChannelAxis,
  type SpaceAxis,
  type TimeAxis,
  type Axis as RFC4Axis,
  type Axes as RFC4Axes,
} from "./rfc4.ts";

// Coordinate systems (RFC5)
export * from "./coordinate_systems.ts";

// Zarr metadata schemas (with RFC4 integration)
export {
  AxisSchema,
  IdentitySchema,
  ScaleSchema,
  TranslationSchema,
  TransformSchema,
  DatasetSchema,
  OmeroWindowSchema,
  OmeroChannelSchema,
  OmeroSchema,
  MetadataSchema,
} from "./zarr_metadata.ts";

// OME-Zarr specification schemas
export {
  // Version schemas
  OmeZarrVersionSchema,
  OmeZarrVersion01Schema,
  OmeZarrVersion02Schema,
  OmeZarrVersion03Schema,
  OmeZarrVersion04Schema,
  OmeZarrVersion05Schema,

  // Core schemas
  OmeroWindowSchema as OmeZarrOmeroWindowSchema,
  OmeroChannelSchema as OmeZarrOmeroChannelSchema,
  OmeroSchema as OmeZarrOmeroSchema,
  OmeZarrCoordinateTransformationSchema,

  // Dataset schemas
  DatasetSchemaV01,
  DatasetSchemaV05,

  // Axis schemas
  AxisSchemaV05,

  // Multiscales schemas
  MultiscalesSchemaV01,
  MultiscalesSchemaV05,
  MultiscalesSchema,

  // Image schemas
  ImageSchemaV01,
  ImageSchemaV05,
  ImageSchema,

  // Label schemas
  LabelColorSchema,
  LabelPropertySchema,
  LabelSchemaV04,

  // Plate schemas
  PlateAcquisitionSchema,
  PlateColumnSchema,
  PlateRowSchema,
  PlateWellSchema,
  PlateSchemaV05,

  // Well schemas
  WellImageSchema,
  WellSchemaV05,

  // OME metadata schemas
  OmeSeriesSchema,
  OmeMetadataSchema,

  // Comprehensive schema
  OmeZarrMetadataSchema,

  // Type exports
  type OmeZarrVersion,
  type OmeroWindow as OmeZarrOmeroWindow,
  type OmeroChannel as OmeZarrOmeroChannel,
  type Omero as OmeZarrOmero,
  type CoordinateTransformation as OmeZarrCoordinateTransformation,
  type DatasetV01,
  type DatasetV05,
  type AxisV05,
  type MultiscalesV01,
  type MultiscalesV05,
  type ImageV01,
  type ImageV05,
  type LabelColor,
  type LabelProperty,
  type LabelV04,
  type PlateAcquisition,
  type PlateColumn,
  type PlateRow,
  type PlateWell,
  type PlateV05,
  type WellImage,
  type WellV05,
  type OmeSeries,
  type OmeMetadata,
  type Image,
  type Multiscales,
  type OmeZarrMetadata,
} from "./ome_zarr.ts";

// NGFF Image and Multiscales
export * from "./ngff_image.ts";
export * from "./multiscales.ts";
