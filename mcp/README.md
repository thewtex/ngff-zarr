# ngff-zarr MCP Server

A Model Context Protocol (MCP) server that provides AI agents with the ability to convert images to OME-Zarr format using the ngff-zarr library.

## Features

### Tools
- **convert_images_to_ome_zarr**: Convert various image formats to OME-Zarr with full control over metadata, compression, and multiscale generation
- **get_ome_zarr_info**: Inspect existing OME-Zarr stores and get detailed information
- **validate_ome_zarr_store**: Validate OME-Zarr structure and metadata
- **optimize_ome_zarr_store**: Optimize existing stores with new compression and chunking

### Resources
- **supported-formats**: List of supported input/output formats and backends
- **downsampling-methods**: Available downsampling methods for multiscale generation
- **compression-codecs**: Available compression codecs and their characteristics

### Input Support
- Local files (all formats supported by ngff-zarr)
- Local directories (Zarr stores)
- Network URLs (HTTP/HTTPS)
- S3 URLs (with optional s3fs dependency)

### Output Optimization
- Multiple compression codecs (gzip, lz4, zstd, blosc variants)
- Configurable compression levels
- Flexible chunk sizing
- Sharding support (Zarr v3/OME-Zarr v0.5)
- OME-Zarr version selection (0.4 or 0.5)

## Installation

### Using pixi (Recommended)

[Pixi](https://pixi.sh) provides the easiest way to manage dependencies and run tasks:

```bash
# Install pixi if not already installed
curl -fsSL https://pixi.sh/install.sh | bash

# Install dependencies and run tests
cd mcp/
pixi install
pixi run test

# Run all checks (linting, formatting, type checking)
pixi run all-checks

# Start the MCP server
pixi run dev-server

# Build documentation with context7
pixi run docs
```

### Using pip

```bash
# Install the package
cd mcp/
pip install -e .

# For cloud storage support
pip install -e ".[cloud]"

# For all optional dependencies
pip install -e ".[all]"
```

## Usage

### As MCP Server

The server can be run in different transport modes:

```bash
# STDIO transport (default)
ngff-zarr-mcp

# Server-Sent Events transport
ngff-zarr-mcp --transport sse --host localhost --port 8000
```

### Configuration for MCP Clients

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "ngff-zarr": {
      "command": "ngff-zarr-mcp",
      "args": []
    }
  }
}
```

For SSE transport:
```json
{
  "mcpServers": {
    "ngff-zarr": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Examples

### Convert a Single Image

```python
# Through MCP client, the agent can:
result = await convert_images_to_ome_zarr(
    input_paths=["image.tif"],
    output_path="output.ome.zarr",
    ome_zarr_version="0.4",
    scale_factors=[2, 4, 8],
    method="itkwasm_gaussian",
    compression_codec="zstd"
)
```

### Convert with Metadata

```python
result = await convert_images_to_ome_zarr(
    input_paths=["image.nii.gz"],
    output_path="brain.ome.zarr", 
    dims=["z", "y", "x"],
    scale={"z": 2.0, "y": 0.5, "x": 0.5},
    units={"z": "micrometer", "y": "micrometer", "x": "micrometer"},
    name="Brain MRI",
    scale_factors=[2, 4]
)
```

### Optimize Existing Store

```python
result = await optimize_ome_zarr_store(
    input_path="large.ome.zarr",
    output_path="optimized.ome.zarr",
    compression_codec="blosc:zstd",
    chunks=[64, 64, 64]
)
```

### Get Store Information

```python
info = await get_ome_zarr_info("data.ome.zarr")
print(f"Size: {info.size_bytes} bytes")
print(f"Scales: {info.num_scales}")
print(f"Dimensions: {info.dimensions}")
```

## Supported Formats

### Input Formats
- **ITK/ITK-Wasm**: .nii, .nii.gz, .mha, .mhd, .nrrd, .dcm, .jpg, .png, .bmp, etc.
- **TIFF**: .tif, .tiff, .svs, .ndpi, .scn (via tifffile)
- **Video**: .webm, .mp4, .avi, .mov, .gif (via imageio)
- **Zarr**: .zarr, .ome.zarr

### Output Formats
- OME-Zarr (.ome.zarr, .zarr)

## Performance Options

### Memory Management
- Set memory targets to control RAM usage
- Use caching for large datasets
- Configure Dask LocalCluster for distributed processing

### Compression
- Choose from multiple codecs: gzip, lz4, zstd, blosc variants
- Adjust compression levels for speed vs. size tradeoffs
- Use sharding to reduce file count (Zarr v3)

### Chunking
- Optimize chunk sizes for your access patterns
- Configure sharding for better performance with cloud storage

## Development

### Using pixi (Recommended)

Pixi provides reproducible, cross-platform environment management. All Python dependencies are defined in `pyproject.toml` and automatically managed by pixi.

```bash
# Clone and setup environment
git clone <repository>
cd mcp/
pixi install

# Development environment (includes all dev tools)
pixi shell -e dev

# Run tests
pixi run test
pixi run test-cov

# Lint and format code  
pixi run lint
pixi run format
pixi run typecheck

# Run all checks
pixi run all-checks

# Build and serve documentation
pixi run docs
pixi run docs-build

# Start MCP server for testing
pixi run dev-server        # STDIO mode
pixi run dev-server-sse    # SSE mode
```

#### Pixi Environments

- **default**: Runtime dependencies only (from `[project.dependencies]`)
- **dev**: Development tools (pytest, black, mypy, ruff)
- **cloud**: Cloud storage support (s3fs, gcsfs)
- **all**: Complete feature set (all ngff-zarr dependencies + cloud)

```bash
pixi shell -e dev      # Development work
pixi shell -e cloud    # Cloud storage testing
pixi shell -e all      # Full feature testing
```

### Using traditional tools

```bash
# Clone and install in development mode
git clone <repository>
cd mcp/
pip install -e ".[all]"

# Run tests
pytest

# Lint code
black .
ruff check .
```

## Dependencies

### Core
- mcp: Model Context Protocol implementation
- ngff-zarr: Core image conversion functionality
- pydantic: Data validation
- httpx: HTTP client for remote files
- aiofiles: Async file operations

### Optional
- s3fs: S3 storage support
- gcsfs: Google Cloud Storage support
- dask[distributed]: Distributed processing

## License

MIT License - see LICENSE file for details.
