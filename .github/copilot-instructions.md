# AI Coding Agent Instructions for ngff-zarr

## Repository Overview

This is a multi-language implementation of the OME Next Generation File Format (NGFF) Zarr specification with three main packages:
- **`py/`** - Core Python implementation with CLI and library
- **`mcp/`** - Model Context Protocol server for AI integration
- **`ts/`** - TypeScript/Deno implementation for web/Node environments

## Core Architecture Patterns

### Data Flow: The Multiscale Pipeline
The central workflow follows this pattern across all implementations:
1. **Input → NgffImage**: Convert various formats to `NgffImage` (single scale + metadata)
2. **NgffImage → Multiscales**: Generate multiple resolution levels via `to_multiscales()`
3. **Multiscales → OME-Zarr**: Write to zarr stores via `to_ngff_zarr()`
4. **OME-Zarr → Multiscales**: Read back via `from_ngff_zarr()`

### Key Data Classes
- **`NgffImage`**: Single-scale image with dims, scale, translation, and dask/lazy array data
- **`Multiscales`**: Container for multiple `NgffImage` scales + OME-Zarr metadata
- **`Metadata`**: OME-Zarr spec metadata (axes, datasets, coordinate transformations)

## Build & Test Commands

**All development uses pixi for consistent environments:**

### Python (py/)
```bash
pixi run test                    # Run pytest test suite
pixi run pytest path/to/test.py::test_name  # Single test
pixi run lint                    # Pre-commit hooks (ruff, black)
```

### MCP Server (mcp/)
```bash
cd mcp && pixi run test         # Run MCP tests
cd mcp && pixi run typecheck    # mypy type checking
cd mcp && pixi run format       # Format code
```

### TypeScript (ts/)
```bash
cd ts && pixi run test          # Deno test suite
cd ts && pixi run lint          # Deno lint
cd ts && pixi run fmt           # Deno format
cd ts && pixi run build         # Full build pipeline
cd ts && deno task test:browser # Browser compatibility tests
```

## Project-Specific Conventions

### Import Patterns
```python
# Python: Always import from .__about__ for version
from .__about__ import __version__

# Import core functions, not classes
from ngff_zarr import from_ngff_zarr, to_ngff_zarr, to_multiscales

# TypeScript: Function-based exports (not classes)
import { fromNgffZarr, toNgffZarr } from "./io/from_ngff_zarr.ts";
```

### Zarr Store Handling
- **Python**: Uses `zarr.storage.DirectoryStore`/`LocalStore` for v2/v3 compatibility
- **TypeScript**: Auto-detects HTTP vs local paths, uses `FetchStore` vs `FileSystemStore`
- **Version Detection**: Always use `zarr.open.v2()` for zarr format 2 stores

### Memory Management
- Large images automatically trigger disk caching via `_large_image_serialization()`
- Controlled by `config.memory_target` (default: available memory)
- Chunking optimized for visualization: 128 (3D) or 256 (2D) pixels

### Testing Infrastructure
- **Fixtures**: `input_images` fixture provides test datasets via pooch downloads
- **Baseline Testing**: `verify_against_baseline()` compares outputs to known-good results
- **Version Skips**: Use `@pytest.mark.skipif(zarr_version < ...)` for version compatibility

## Critical Integration Points

### Multi-Backend Support
```python
# Auto-detection in cli_input_to_ngff_image()
ConversionBackend.NGFF_ZARR     # Existing OME-Zarr
ConversionBackend.ITK           # Medical images via ITK
ConversionBackend.ITKWASM       # WebAssembly processing
ConversionBackend.TIFFFILE      # TIFF via tifffile
```

### Downsampling Methods
```python
Methods.ITKWASM_GAUSSIAN        # Default, web-compatible
Methods.ITK_GAUSSIAN           # Native ITK (better quality)
Methods.DASK_IMAGE_GAUSSIAN    # Pure Python fallback
```

### Error Handling Patterns
- **TypeScript**: `zarrita` operations wrapped with version-specific fallbacks
- **Python**: Specific exceptions for zarr version compatibility issues
- **Store validation**: Always check for consolidated metadata first

## Cross-Component Communication

### TypeScript ↔ Python Equivalence
```typescript
// TypeScript (mirrors Python dataclasses)
export class NgffImage {
  data: LazyArray;     // Equivalent to dask.array
  dims: string[];      // ["t", "c", "z", "y", "x"]
  scale: Record<string, number>;
  translation: Record<string, number>;
}
```

### MCP Server Integration
- Wraps core `ngff-zarr` functions for AI assistant access
- Provides format detection, validation, and optimization tools
- Uses Pydantic models for type-safe parameter validation

## Development Debugging

### Common Issues
1. **"Node not found: v3 array"** → Use `zarr.open.v2()` for zarr format 2
2. **Memory errors** → Check `config.memory_target`, enable caching
3. **TypeScript import errors** → Use relative imports with `.ts` extension
4. **Test fixture failures** → Ensure test data downloaded via pooch

### Performance Optimization
- Enable `use_tensorstore=True` for very large datasets
- Use `chunks_per_shard` for zarr v3 sharding
- Set appropriate `chunks` parameter for your use case

## Essential Files for Understanding
- **`py/ngff_zarr/to_ngff_zarr.py`** - Core write implementation
- **`py/ngff_zarr/to_multiscales.py`** - Downsampling pipeline
- **`ts/src/io/from_ngff_zarr.ts`** - TypeScript read implementation
- **`py/test/_data.py`** - Test infrastructure and baselines
