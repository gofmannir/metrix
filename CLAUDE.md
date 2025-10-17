# metrix Project - Development Notes

## Project Setup

## Python

- use python 3.13 features
- specify type hints
- instead of Optional[X], List, Tuple, etc. use python 3.10+ way with X|None, list, tuple
- for data models use pydantic 2 and `Annotated`
- use Loguru `logger.debug()` with built-in templating `logger.debug("text {metavar}", metavar=expression)`. I often use a variable for both metavar and expression: `x=42; logger.debug("x={x}", x=x)`
- use loguru.debug() instead of `print()` everywhere, except for short one-off scripts.
- use pytest for testing
- use uv to manage python projects. To add dependencies use `uv add [--dev] package` without exact version. Do not edit dependencies in pyproject.toml directly.
- use ruff and mypy for static analysis
- if Makefile is available use targets: check, fix, test

### Python testing

- use pytest for testing
- use pytest plugins and fixtures even where the direct approach is available: mocking, tmp files, etc.
- try hard to avoid code-level monkey patching. If unavoidable, ask.
- whenever adding new functionality to a subpackage in that uv workspace run the tests for that package instead for the whole project.

This is a Python 3.13 project managed with `uv`, configured with strict linting (ruff) and type checking (mypy).

### Configuration

**Ruff** (pyproject.toml:15-19):
- Line length: 120
- Target: Python 3.13
- Comprehensive linting rules enabled
- Ignored: ANN401, COM812, ISC001

**Mypy** (pyproject.toml:21-33):
- Strict type checking enabled
- Python 3.13 target
- All warnings enabled (return_any, unused_configs, etc.)

**Build System** (pyproject.toml:11-19):
- Backend: hatchling
- Source layout: src/metrix
- Entry point script: `metrix` command → `metrix.__main__:main`

## Running the Project

### Using uv

```bash
# Run as module
uv run python -m metrix

# Run using installed script
uv run metrix

# Direct Python execution
uv run python main.py
```

### Using Make

```bash
# Initialize project (create venv + sync deps)
make init

# Run linting and type checking
make check

# Auto-fix formatting and linting issues
make fix

# Format code only
make format

# Clean virtual environment
make clean
```

## Makefile Targets

- `make init`: Creates `.venv` and syncs all dependencies
- `make check`: Runs ruff check, ruff format --check, and mypy
- `make fix`: Runs ruff format and ruff check --fix
- `make clean`: Removes `.venv`
- `make help`: Lists all available targets

## Development Workflow

1. Install dependencies: `make init`
2. Make code changes in `src/metrix/`
3. Run checks: `make check`
4. Fix issues: `make fix`
5. Test execution: `uv run python -m metrix`

## Notes

- The project uses a src-layout for better package isolation
- Loguru is configured for logging (see `__main__.py`)
- The package is installed in editable mode during `uv sync`
- Entry point allows running via `uv run metrix` command

## HistoricalDataProvider

The `HistoricalDataProvider` class wraps the Polygon.io API for fetching historical market data with automatic caching.

### Configuration

Uses `pydantic-settings` with environment variable loading:

```python
class HistoricalDataProviderConfig(BaseSettings):
    polygon_api_key: str           # Required: METRIX_POLYGON_API_KEY
    cache_dir: Path = Path(".cache/historical_data")  # Cache directory
    use_cache: bool = True          # Enable/disable caching
```

Environment variables use the `METRIX_` prefix (e.g., `METRIX_POLYGON_API_KEY`).

### Usage

```python
from metrix.historical_data_provider import HistoricalDataProvider

# Initialize (loads config from .env automatically)
provider = HistoricalDataProvider()

# Fetch data
df = provider.get_historical_data(
    ticker="AAPL",
    multiplier=1,
    timespan="day",
    from_date="2021-01-01",
    to_date="2021-12-31",
    adjusted=True,
    sort="asc",
    limit=50000,
)
```

### Caching Behavior

- **Automatic caching**: Data is cached as parquet files in `cache_dir`
- **Cache key**: SHA256 hash of all request parameters
- **Cache hit**: Loads data from parquet file (no API call)
- **Cache miss**: Fetches from Polygon API and saves to cache
- **Disable caching**: Set `use_cache=False` in config

### Data Format

Returns pandas DataFrame with columns:
- `open`, `high`, `low`, `close`: Price data
- `volume`: Trading volume
- `vwap`: Volume-weighted average price
- `timestamp`: Pandas datetime (UTC)
- `transactions`: Number of transactions

### Dependencies

- `polygon-api-client`: Polygon.io REST API wrapper
- `pyarrow`: Required for parquet file I/O
- `pydantic-settings`: Configuration management
- `pandas`: DataFrame operations
