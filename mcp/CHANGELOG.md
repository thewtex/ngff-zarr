# Changelog

All notable changes to the ngff-zarr-mcp package will be documented in this
file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-01-18

### Added

- **RFC 4 - Anatomical Orientation Support**: Added parameters for medical
  imaging orientation systems
  - `anatomical_orientation` parameter for LPS/RAS coordinate system presets
  - `enable_rfc4` parameter to enable RFC 4 support
  - `enabled_rfcs` parameter to enable specific RFC features
- **Enhanced Storage Support**: Added `storage_options` parameter for cloud
  storage authentication
  - Support for AWS S3, Google Cloud Storage, Azure Blob Storage
  - Authentication and configuration options for remote storage
- **New Tool**: `read_ome_zarr_store` for reading OME-Zarr data with remote
  storage support
- **Enhanced Metadata**: Extended StoreInfo model with new fields:
  - `method_type`: Type of multiscale method used
  - `method_metadata`: Detailed method information
  - `anatomical_orientation`: Anatomical orientation information
  - `rfc_support`: List of enabled RFC features

### Changed

- Updated `convert_images_to_ome_zarr` tool with new parameters for RFC 4 and
  storage options
- Enhanced documentation in README with new features
- Improved type annotations and error handling

### Technical Details

- Compatible with ngff-zarr Python package versions 0.14.0 and 0.15.0
- Maintains backward compatibility with existing MCP tool calls
- Prepared infrastructure for future RFC 4 and method metadata integration
- Added graceful fallbacks for features not yet available in the core library

## [0.2.1] - Previous Release

- Previous MCP server functionality
