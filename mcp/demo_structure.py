#!/usr/bin/env python3
"""Simplified demo for ngff-zarr MCP server structure."""

def demo_mcp_structure():
    """Demonstrate the MCP server structure."""
    print("🚀 ngff-zarr MCP Server")
    print("=" * 40)
    
    print("\n📁 Project Structure:")
    print("mcp/")
    print("├── pyproject.toml          # Hatch packaging configuration")
    print("├── README.md               # Comprehensive documentation")
    print("├── ngff_zarr_mcp/")
    print("│   ├── __init__.py         # Package initialization")
    print("│   ├── __about__.py        # Version information")
    print("│   ├── server.py           # Main MCP server with FastMCP")
    print("│   ├── models.py           # Pydantic data models")
    print("│   ├── tools.py            # MCP tools implementation")
    print("│   └── utils.py            # Utility functions")
    print("├── examples/")
    print("│   ├── claude-desktop-config.json")
    print("│   └── sse-config.json")
    print("├── tests/")
    print("│   ├── conftest.py")
    print("│   └── test_basic.py")
    print("└── demo.py")
    
    print("\n🔧 MCP Tools Provided:")
    tools = [
        "convert_images_to_ome_zarr  - Convert various image formats to OME-Zarr",
        "get_ome_zarr_info          - Get detailed information about OME-Zarr stores",
        "validate_ome_zarr_store    - Validate OME-Zarr structure and metadata", 
        "optimize_ome_zarr_store    - Optimize existing stores with new compression"
    ]
    for tool in tools:
        print(f"  • {tool}")
    
    print("\n📚 MCP Resources Provided:")
    resources = [
        "supported-formats     - List of supported input/output formats",
        "downsampling-methods  - Available downsampling methods",
        "compression-codecs    - Available compression codecs"
    ]
    for resource in resources:
        print(f"  • {resource}")
    
    print("\n⚙️  Key Features:")
    features = [
        "Support for local files, URLs, and S3 storage",
        "Multiple input formats (ITK, TIFF, video, Zarr)",
        "Flexible compression options (gzip, lz4, zstd, blosc)",
        "Configurable chunking and sharding",
        "Multiscale generation with various methods",
        "Comprehensive metadata control",
        "Performance optimization options",
        "Async operations for large datasets",
        "Structured outputs with Pydantic validation"
    ]
    for feature in features:
        print(f"  ✓ {feature}")
    
    print("\n🌐 Usage Example:")
    print("  # Start the MCP server")
    print("  ngff-zarr-mcp")
    print("")
    print("  # Or with SSE transport")
    print("  ngff-zarr-mcp --transport sse --port 8000")
    print("")
    print("  # Claude Desktop config:")
    print('  "ngff-zarr": {"command": "ngff-zarr-mcp"}')
    
    print("\n📦 Installation:")
    print("  cd mcp/")
    print("  pip install -e .")
    print("  # Or with cloud support:")
    print("  pip install -e '.[cloud]'")
    
    print("\n✅ MCP Server Ready!")
    print("   Connect this server to any MCP client to enable")
    print("   AI agents to convert images to OME-Zarr format!")


if __name__ == "__main__":
    demo_mcp_structure()
