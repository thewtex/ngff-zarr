# AGENTS.md - Development Guide for AI Coding Agents

## Build/Test Commands
- **Commands use the software development environment should be run with `pixi
  run`
- **Main package (py/)**: `pixi run test`
- **MCP package (mcp/)**: `pixi run test`
- **Single test**: `pixi run pytest path/to/test_file.py::test_function_name`
- **Lint**: `pixi run lint`
- **Format**: `pixi run format` (MCP only)
- **Type check**: `pixi run typecheck` (MCP only)

## Python Code Style Guidelines
- **Line length**: 88 characters (Black/Ruff standard)
- **Imports**: Use absolute imports, group by standard/third-party/local
- **Types**: Use type hints, especially for public APIs
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error handling**: Use specific exceptions, avoid bare except clauses
- **Docstrings**: Use for public functions/classes
- **Comments**: Minimal, focus on why not what

## Key Python Conventions
- Use `pytest` for testing with fixtures in conftest.py
- Follow Ruff linting rules (see pyproject.toml [tool.lint])
- Use `dask.array` for large array processing
- Import from `.__about__` for version info
- Use `pathlib.Path` over os.path
- Pre-commit hooks enforce style automatically

## Typescript Code Style Guidelines
- Use deno's standard style
