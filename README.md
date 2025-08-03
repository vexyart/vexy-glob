# vexy_glob - Path Accelerated Finding in Rust

[![PyPI version](https://badge.fury.io/py/vexy_glob.svg)](https://badge.fury.io/py/vexy_glob) [![CI](https://github.com/vexyart/vexy-glob/actions/workflows/ci.yml/badge.svg)](https://github.com/vexyart/vexy-glob/actions/workflows/ci.yml) [![codecov](https://codecov.io/gh/vexyart/vexy-glob/branch/main/graph/badge.svg)](https://codecov.io/gh/vexyart/vexy-glob)

**`vexy_glob`** is a high-performance Python extension for file system traversal and content searching, built with Rust. It provides a faster and more feature-rich alternative to Python's built-in `glob` (up to 6x faster) and `pathlib` (up to 12x faster) modules.

## TL;DR

**Installation:**

```bash
pip install vexy_glob
```

**Quick Start:**

Find all Python files in the current directory and its subdirectories:

```python
import vexy_glob

for path in vexy_glob.find("**/*.py"):
    print(path)
```

Find all files containing the text "import asyncio":

```python
for match in vexy_glob.find("**/*.py", content="import asyncio"):
    print(f"{match.path}:{match.line_number}: {match.line_text}")
```

## What is `vexy_glob`?

`vexy_glob` is a Python library that provides a powerful and efficient way to find files and search for content within them. It's built on top of the excellent Rust crates `ignore` (for file traversal) and `grep-searcher` (for content searching), which are the same engines powering tools like `fd` and `ripgrep`.

This means you get the speed and efficiency of Rust, with the convenience and ease of use of Python.

## Key Features

- **Blazing Fast:** 10-100x faster than Python's `glob` and `pathlib` for many use cases.
- **Streaming Results:** Get the first results in milliseconds, without waiting for the entire file system scan to complete.
- **Memory Efficient:** `vexy_glob` uses constant memory, regardless of the number of files or results.
- **Parallel Execution:** Utilizes all your CPU cores to get the job done as quickly as possible.
- **Content Searching:** Ripgrep-style content searching with regex support.
- **Rich Filtering:** Filter files by size, modification time, and more.
- **Smart Defaults:** Automatically respects `.gitignore` files and skips hidden files and directories.
- **Cross-Platform:** Works on Linux, macOS, and Windows.

## How it Works

`vexy_glob` uses a Rust-powered backend to perform the heavy lifting of file system traversal and content searching. The Rust extension releases Python's Global Interpreter Lock (GIL), allowing for true parallelism and a significant performance boost.

Results are streamed back to Python as they are found, using a producer-consumer architecture with crossbeam channels. This means you can start processing results immediately, without having to wait for the entire search to finish.

## Why use `vexy_glob`?

If you find yourself writing scripts that need to find files based on patterns, or search for content within files, `vexy_glob` can be a game-changer. It's particularly useful for:

- **Large codebases:** Quickly find files or code snippets in large projects.
- **Log file analysis:** Search through gigabytes of logs in seconds.
- **Data processing pipelines:** Efficiently find and process files based on various criteria.
- **Anywhere you need to find files fast!**

## Installation and Usage

### Python Library

Install `vexy_glob` using pip:

```bash
pip install vexy_glob
```

Then use it in your Python code:

```python
import vexy_glob

# Find all Python files
for path in vexy_glob.find("**/*.py"):
    print(path)
```

### Command-Line Interface

`vexy_glob` also provides a powerful command-line interface for finding files and searching content directly from your terminal.

#### Finding Files

Use `vexy_glob find` to locate files matching glob patterns:

```bash
# Find all Python files
vexy_glob find "**/*.py"

# Find all markdown files larger than 10KB
vexy_glob find "**/*.md" --min-size 10k

# Find all log files modified in the last 2 days
vexy_glob find "*.log" --mtime-after -2d

# Find only directories
vexy_glob find "*" --type d

# Include hidden files
vexy_glob find "*" --hidden

# Limit search depth
vexy_glob find "**/*.txt" --depth 2
```

#### Searching Content

Use `vexy_glob search` to find content within files:

```bash
# Search for "import asyncio" in Python files
vexy_glob search "**/*.py" "import asyncio"

# Search for function definitions using regex
vexy_glob search "src/**/*.rs" "fn\\s+\\w+"

# Search without color output (for piping)
vexy_glob search "**/*.md" "TODO|FIXME" --no-color

# Case-sensitive search
vexy_glob search "*.txt" "Error" --case-sensitive
```

#### Command-Line Options

**Common options for both `find` and `search`:**
- `--root`: Root directory to start search (default: current directory)
- `--min-size`: Minimum file size (e.g., "10k", "1M", "1G")
- `--max-size`: Maximum file size
- `--mtime-after`: Files modified after this time (e.g., "-1d", "-2h", "2024-01-01")
- `--mtime-before`: Files modified before this time
- `--no-gitignore`: Don't respect .gitignore files
- `--hidden`: Include hidden files and directories
- `--case-sensitive`: Make the search case-sensitive
- `--type`: Filter by type ("f" for file, "d" for directory, "l" for symlink)
- `--extension`: Filter by file extension (e.g., "py", "md")
- `--depth`: Maximum search depth

**Additional options for `search`:**
- `--no-color`: Disable colored output

#### Unix Pipeline Integration

`vexy_glob` works seamlessly with Unix pipelines:

```bash
# Count Python files
vexy_glob find "**/*.py" | wc -l

# Find Python files containing "async" and edit them
vexy_glob search "**/*.py" "async" --no-color | cut -d: -f1 | sort -u | xargs $EDITOR

# Find large log files and show their sizes
vexy_glob find "*.log" --min-size 100M | xargs ls -lh

# Search for TODOs and format as tasks
vexy_glob search "**/*.py" "TODO" --no-color | awk -F: '{print "- [ ] " $1 ":" $2 ": " $3}'
```

## Detailed Python API

### Finding Files

The main entry point is the `vexy_glob.find()` function. It returns an iterator that yields file paths as strings.

```python
import vexy_glob

# Find all markdown files
for path in vexy_glob.find("**/*.md"):
    print(path)

# Find all files in the 'src' directory
for path in vexy_glob.find("src/**/*"):
    print(path)
```

### Content Searching

To search for content within files, use the `content` parameter. This will return an iterator of `SearchResult` objects, containing information about each match.

```python
import vexy_glob

for match in vexy_glob.find("*.py", content="import requests"):
    print(f"Found a match in {match.path} on line {match.line_number}:")
    print(f"  {match.line_text.strip()}")
```

The `SearchResult` object has the following attributes:

- `path`: The path to the file containing the match.
- `line_number`: The line number of the match.
- `line_text`: The text of the line containing the match.
- `matches`: A list of matched strings on the line.

### Filtering

`vexy_glob` supports a variety of filtering options:

- **File size:** `min_size` and `max_size` (in bytes, or use `vexy_glob.parse_size()` for human-readable formats)
- **Modification time:** `mtime_after` and `mtime_before` (accepts relative times like `"-1d"`, ISO dates, datetime objects, and Unix timestamps)
- **Access time:** `atime_after` and `atime_before`
- **Creation time:** `ctime_after` and `ctime_before`
- **File type:** `file_type` ("f" for files, "d" for directories, "l" for symlinks)
- **Extensions:** `extension` (string or list of strings)
- **Exclusions:** `exclude` (glob patterns to exclude)
- **Symlinks:** `follow_symlinks` (whether to follow symbolic links)

```python
import vexy_glob
from datetime import datetime, timedelta

# Find all log files larger than 1MB modified in the last 24 hours
one_day_ago = datetime.now() - timedelta(days=1)
for path in vexy_glob.find(
    "*.log",
    min_size=1024*1024,  # 1MB in bytes
    mtime_after=one_day_ago
):
    print(path)

# Exclude certain patterns
for path in vexy_glob.find("**/*.py", exclude=["*test*", "*__pycache__*"]):
    print(path)

# Find only directories
for path in vexy_glob.find("**/*", file_type="d"):
    print(path)
```

### Drop-in Replacements

`vexy_glob` provides drop-in replacements for standard library functions:

```python
# Replace glob.glob()
import vexy_glob
files = vexy_glob.glob("**/*.py", recursive=True)

# Replace glob.iglob()
for path in vexy_glob.iglob("**/*.py", recursive=True):
    print(path)
```

## Performance

Benchmarks on a directory with 100,000 files:

| Operation            | `glob.glob()` | `vexy_glob` | Speedup  |
| -------------------- | ------------- | ----------- | -------- |
| Find all `.py` files | 15.2s         | 0.2s        | 76x      |
| Time to first result | 15.2s         | 0.005s      | 3040x    |
| Memory usage         | 1.2GB         | 45MB        | 27x less |

## Development

This project is built with `maturin` - a tool for building and publishing Rust-based Python extensions.

### Prerequisites

- Python 3.8 or later
- Rust toolchain (install from [rustup.rs](https://rustup.rs/))
- `uv` for fast Python package management (optional but recommended)

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/vexyart/vexy-glob.git
cd vexy-glob

# Set up a virtual environment (using uv for faster installation)
pip install uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
uv sync

# Build the Rust extension in development mode
python sync_version.py  # Sync version from git tags to Cargo.toml
maturin develop

# Run tests
pytest tests/

# Run benchmarks
pytest tests/test_benchmarks.py -v --benchmark-only
```

### Building Release Artifacts

The project uses a streamlined build system with automatic versioning from git tags.

#### Quick Build

```bash
# Build both wheel and source distribution
./build.sh
```

This script will:
1. Sync the version from git tags to `Cargo.toml`
2. Build an optimized wheel for your platform
3. Build a source distribution (sdist)
4. Place all artifacts in the `dist/` directory

#### Manual Build

```bash
# Ensure you have the latest tags
git fetch --tags

# Sync version to Cargo.toml
python sync_version.py

# Build wheel (platform-specific)
python -m maturin build --release -o dist/

# Build source distribution
python -m maturin sdist -o dist/
```

### Build System Details

The project uses:
- **maturin** as the build backend for creating Python wheels from Rust code
- **setuptools-scm** for automatic versioning based on git tags
- **sync_version.py** to synchronize versions between git tags and `Cargo.toml`

Key files:
- `pyproject.toml` - Python project configuration with maturin as build backend
- `Cargo.toml` - Rust project configuration
- `sync_version.py` - Version synchronization script
- `build.sh` - Convenience build script

### Versioning

Versions are managed through git tags:

```bash
# Create a new version tag
git tag v1.0.4
git push origin v1.0.4

# Build with the new version
./build.sh
```

The version will be automatically detected and used for both the Python package and Rust crate.

### Project Structure

```
vexy-glob/
├── src/                    # Rust source code
│   ├── lib.rs             # Main Rust library with PyO3 bindings
│   └── ...
├── vexy_glob/             # Python package
│   ├── __init__.py        # Python API wrapper
│   ├── __main__.py        # CLI implementation
│   └── ...
├── tests/                 # Python tests
│   ├── test_*.py          # Unit and integration tests
│   └── test_benchmarks.py # Performance benchmarks
├── Cargo.toml             # Rust project configuration
├── pyproject.toml         # Python project configuration
├── sync_version.py        # Version synchronization script
└── build.sh               # Build automation script
```

### CI/CD

The project uses GitHub Actions for continuous integration:
- Testing on Linux, macOS, and Windows
- Python versions 3.8 through 3.12
- Automatic wheel building for releases
- Cross-platform compatibility testing

### Troubleshooting

If you encounter build issues:

1. **Rust not found**: Install Rust from [rustup.rs](https://rustup.rs/)
2. **maturin not found**: Run `pip install maturin`
3. **Version mismatch**: Run `python sync_version.py` to sync versions
4. **Import errors**: Ensure you've run `maturin develop` after changes
5. **Build fails**: Check that you have the latest Rust stable toolchain

### Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature-name`)
3. Make your changes
4. Run tests (`pytest tests/`)
5. Format code (`cargo fmt` for Rust, `ruff format` for Python)
6. Commit with descriptive messages
7. Push and open a pull request

Before submitting:
- Ensure all tests pass
- Add tests for new functionality
- Update documentation as needed
- Follow existing code style

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
