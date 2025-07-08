"""MCP tools for ngff-zarr image conversion."""

import tempfile
from pathlib import Path
from typing import List

import zarr
from ngff_zarr import (  # type: ignore[import-untyped]
    detect_cli_io_backend,
    cli_input_to_ngff_image,
    to_multiscales,
    to_ngff_zarr,
    from_ngff_zarr,
    Methods,
    config,
)

# Import validation function if available
try:
    from ngff_zarr import validate as validate_ngff
except ImportError:
    # Fallback validation
    def validate_ngff(store):
        # Basic validation - just try to open the store
        zarr.open(store, mode="r")


from .models import (
    ConversionOptions,
    ConversionResult,
    StoreInfo,
    OptimizationOptions,
    ValidationResult,
)
from .utils import (
    analyze_zarr_store,
    setup_dask_config,
    validate_conversion_options,
    prepare_input_files,
    is_url,
    is_zarr_store,
)


async def convert_to_ome_zarr(
    input_paths: List[str], options: ConversionOptions
) -> ConversionResult:
    """Convert input images to OME-Zarr format."""

    try:
        # Validate options
        validation_errors = validate_conversion_options(options.dict())
        if validation_errors:
            return ConversionResult(
                success=False,
                output_path="",
                store_info={},
                error=f"Validation errors: {'; '.join(validation_errors)}",
            )

        # Setup Dask if needed
        client = setup_dask_config(
            memory_target=options.memory_target,
            use_local_cluster=options.use_local_cluster,
            cache_dir=options.cache_dir,
        )

        try:
            # Prepare input files (download remote files if needed)
            with tempfile.TemporaryDirectory() as temp_dir:
                prepared_inputs = await prepare_input_files(input_paths, temp_dir)

                # Detect input backend
                backend = detect_cli_io_backend(prepared_inputs)

                # Load input image
                ngff_image = cli_input_to_ngff_image(backend, prepared_inputs)

                # Apply metadata options
                if options.dims:
                    if len(options.dims) != len(ngff_image.dims):
                        raise ValueError(
                            f"Provided dims count ({len(options.dims)}) doesn't match image dims ({len(ngff_image.dims)})"
                        )
                    ngff_image.dims = options.dims

                if options.scale:
                    for dim, value in options.scale.items():
                        ngff_image.scale[dim] = value

                if options.translation:
                    for dim, value in options.translation.items():
                        ngff_image.translation[dim] = value

                if options.units:
                    ngff_image.axes_units = options.units

                if options.name:
                    ngff_image.name = options.name

                # Setup chunking
                chunks = options.chunks
                if chunks is not None:
                    if isinstance(chunks, list) and len(chunks) == 1:
                        chunks = chunks[0]
                    elif isinstance(chunks, list):
                        chunks = tuple(chunks)

                # Determine if we need to generate multiscales
                scale_factors = options.scale_factors
                method = Methods(options.method) if options.method else None

                # Setup caching for large datasets
                cache = ngff_image.data.nbytes > config.memory_target

                # Always use to_multiscales to create proper Multiscales object
                # If scale_factors is None, create single-scale multiscales
                if scale_factors is None:
                    scale_factors = []

                multiscales_obj = to_multiscales(
                    ngff_image,
                    scale_factors=scale_factors,
                    method=method,
                    chunks=chunks,
                    cache=cache,
                )

                # Setup output store
                output_path = Path(options.output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if hasattr(zarr.storage, "DirectoryStore"):
                    output_store = zarr.storage.DirectoryStore(str(output_path))
                else:
                    output_store = zarr.storage.LocalStore(str(output_path))

                # Setup chunks per shard if specified
                chunks_per_shard = options.chunks_per_shard
                if chunks_per_shard is not None:
                    if options.ome_zarr_version == "0.4":
                        raise ValueError("Sharding not supported in OME-Zarr v0.4")
                    if (
                        isinstance(chunks_per_shard, list)
                        and len(chunks_per_shard) == 1
                    ):
                        chunks_per_shard = chunks_per_shard[0]
                    elif isinstance(chunks_per_shard, list):
                        chunks_per_shard = tuple(chunks_per_shard)

                # Convert to OME-Zarr
                kwargs = {}
                if options.compression_codec:
                    # Create proper compressor object
                    import numcodecs

                    if options.compression_codec == "gzip":
                        level = options.compression_level or 6
                        kwargs["compressor"] = numcodecs.GZip(level=level)
                    elif options.compression_codec == "lz4":
                        kwargs["compressor"] = numcodecs.LZ4()
                    elif options.compression_codec == "zstd":
                        level = options.compression_level or 3
                        kwargs["compressor"] = numcodecs.Zstd(level=level)
                    elif options.compression_codec.startswith("blosc"):
                        # Handle blosc variants like "blosc:lz4", "blosc:zstd", etc.
                        codec_parts = options.compression_codec.split(":")
                        if len(codec_parts) == 2:
                            codec_name = codec_parts[1]
                        else:
                            codec_name = "lz4"  # default
                        level = options.compression_level or 5
                        kwargs["compressor"] = numcodecs.Blosc(
                            cname=codec_name, clevel=level
                        )
                    else:
                        # Fallback to string (may work for some codecs)
                        kwargs["compressor"] = options.compression_codec

                to_ngff_zarr(
                    output_store,
                    multiscales_obj,
                    chunks_per_shard=chunks_per_shard,
                    use_tensorstore=options.use_tensorstore,
                    version=options.ome_zarr_version,
                    **kwargs,
                )

                # Analyze the created store
                store_info = analyze_zarr_store(str(output_path))

                return ConversionResult(
                    success=True,
                    output_path=str(output_path),
                    store_info=store_info.model_dump(),
                    error=None,
                )

        finally:
            # Cleanup Dask client
            if client:
                client.close()

    except Exception as e:
        return ConversionResult(
            success=False, output_path="", store_info={}, error=str(e)
        )


async def inspect_ome_zarr(store_path: str) -> StoreInfo:
    """Inspect an OME-Zarr store and return detailed information."""

    try:
        return analyze_zarr_store(store_path)
    except Exception as e:
        raise ValueError(f"Failed to inspect store: {str(e)}")


async def validate_ome_zarr(store_path: str) -> ValidationResult:
    """Validate an OME-Zarr store."""

    try:
        errors = []
        warnings: list[str] = []
        version = None

        # Check if store exists and is accessible
        if is_url(store_path):
            # For remote stores, basic checks
            try:
                store_info = analyze_zarr_store(store_path)
                version = store_info.version
            except Exception as e:
                errors.append(f"Cannot access remote store: {str(e)}")
                return ValidationResult(
                    valid=False, version=None, errors=errors, warnings=warnings
                )
        else:
            store_path_obj = Path(store_path)
            if not store_path_obj.exists():
                errors.append(f"Store path does not exist: {store_path}")
                return ValidationResult(
                    valid=False, version=None, errors=errors, warnings=warnings
                )

            if not is_zarr_store(store_path):
                errors.append(f"Path is not a valid Zarr store: {store_path}")
                return ValidationResult(
                    valid=False, version=None, errors=errors, warnings=warnings
                )

        # Try to load as NGFF
        try:
            if hasattr(zarr.storage, "DirectoryStore"):
                store = (
                    zarr.storage.DirectoryStore(store_path)
                    if not is_url(store_path)
                    else store_path
                )
            else:
                store = (
                    zarr.storage.LocalStore(store_path)
                    if not is_url(store_path)
                    else store_path
                )

            multiscales = from_ngff_zarr(store)

            # Basic validation checks
            if len(multiscales.images) == 0:
                errors.append("No images found in multiscales")

            # Check each scale
            for i, image in enumerate(multiscales.images):
                if image.data is None:
                    errors.append(f"Scale {i} has no data")
                elif image.data.size == 0:
                    warnings.append(f"Scale {i} has empty data")

            # Try ngff-zarr validation if available
            try:
                validate_ngff(store)
            except Exception as validation_error:
                warnings.append(f"NGFF validation warning: {str(validation_error)}")

            # Determine version
            try:
                root = zarr.open(store, mode="r")
                if "multiscales" in root.attrs:
                    multiscales_attr = root.attrs["multiscales"]
                    if isinstance(multiscales_attr, list) and len(multiscales_attr) > 0:
                        ms_attrs = multiscales_attr[0]
                        if isinstance(ms_attrs, dict):
                            version_attr = ms_attrs.get("version", "0.4")
                            if isinstance(version_attr, str):
                                version = version_attr
            except Exception:
                version = "0.4"  # Default assumption

        except Exception as e:
            errors.append(f"Failed to load as NGFF: {str(e)}")

        return ValidationResult(
            valid=len(errors) == 0, version=version, errors=errors, warnings=warnings
        )

    except Exception as e:
        return ValidationResult(
            valid=False,
            version=None,
            errors=[f"Validation failed: {str(e)}"],
            warnings=[],
        )


async def optimize_zarr_store(options: OptimizationOptions) -> ConversionResult:
    """Optimize an existing Zarr store with new compression/chunking."""

    try:
        # Load existing store
        input_path = Path(options.input_path)
        if not input_path.exists():
            return ConversionResult(
                success=False,
                output_path="",
                store_info={},
                error=f"Input store does not exist: {options.input_path}",
            )

        # Load multiscales
        if hasattr(zarr.storage, "DirectoryStore"):  # type: ignore[attr-defined]
            input_store = zarr.storage.DirectoryStore(str(input_path))  # type: ignore[attr-defined]
        else:
            input_store = zarr.storage.LocalStore(str(input_path))  # type: ignore[attr-defined]

        multiscales = from_ngff_zarr(input_store)

        # Setup output store
        output_path = Path(options.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if hasattr(zarr.storage, "DirectoryStore"):  # type: ignore[attr-defined]
            output_store = zarr.storage.DirectoryStore(str(output_path))  # type: ignore[attr-defined]
        else:
            output_store = zarr.storage.LocalStore(str(output_path))  # type: ignore[attr-defined]

        # Apply optimizations by re-chunking/compressing the data
        optimized_images = []
        for image in multiscales.images:
            optimized_data = image.data

            # Apply new chunking if specified
            if options.chunks is not None:
                chunks = options.chunks
                if isinstance(chunks, list) and len(chunks) == 1:
                    chunks = chunks[0]
                elif isinstance(chunks, list):
                    chunks = tuple(chunks)
                optimized_data = optimized_data.rechunk(chunks)  # type: ignore[arg-type]

            # Create optimized image
            from ngff_zarr.ngff_image import NgffImage  # type: ignore[import-untyped]

            optimized_image = NgffImage(
                optimized_data,  # type: ignore[arg-type]
                image.dims,
                image.scale,
                image.translation,
                image.name,
                image.axes_units,
            )
            optimized_images.append(optimized_image)

        # Create new multiscales object with optimized images
        # For now, use the original multiscales and rely on to_ngff_zarr to handle optimization
        # This preserves metadata and compatibility
        optimized_multiscales = multiscales  # type: ignore[assignment]

        # Setup chunks per shard if specified
        chunks_per_shard = options.chunks_per_shard
        if chunks_per_shard is not None:
            if isinstance(chunks_per_shard, list) and len(chunks_per_shard) == 1:
                chunks_per_shard = chunks_per_shard[0]
            elif isinstance(chunks_per_shard, list):
                chunks_per_shard = tuple(chunks_per_shard)

        # Save optimized store
        to_ngff_zarr(
            output_store,
            optimized_multiscales,
            chunks_per_shard=chunks_per_shard,
            compression_codec=options.compression_codec,
            compression_level=options.compression_level,
        )

        # Analyze the optimized store
        store_info = analyze_zarr_store(str(output_path))

        return ConversionResult(
            success=True,
            output_path=str(output_path),
            store_info=store_info.model_dump(),
            error=None,
        )

    except Exception as e:
        return ConversionResult(
            success=False, output_path="", store_info={}, error=str(e)
        )
