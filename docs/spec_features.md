# ✨ Specification Features

This page describes the features of the OME-Zarr specification that are supported by `ngff-zarr`.

## Supported Features

- **Multiscales**: Support for multiscale representations of images.
- **Multiscales generation**: Ability to generate multiscale representations from single-scale images.
- **Chunking**: Customizable chunking strategies for efficient data access.
- **Compression**: Support for various compression algorithms to reduce storage requirements.
- **Metadata**: Rich metadata support, including spatial metadata.
- **Anatomical Orientation**: Support for anatomical orientation metadata (RFC 4).
- **Sharded Zarr**: Support for sharded Zarr stores, allowing for scalable data management.
- **Tensorstore Writing**: Optional writing via [tensorstore] for advanced use cases.
- **Model Context Protocol (MCP)**: Integration with the Model Context Protocol for AI agent interaction.

## OME-Zarr Versions

- **OME-Zarr v0.1 to v0.5**: Reads OME-Zarr versions 0.1 to 0.5 into simple Python data classes with Dask arrays.
- **OME-Zarr v0.4 to v0.5**: Writes OME-Zarr versions 0.4 to 0.5, including support for RFC 4.

## RFCs Supported

- **RFC-4**: [Anatomical orientation support](./rfc4.md), allowing images to include metadata about their anatomical orientation.