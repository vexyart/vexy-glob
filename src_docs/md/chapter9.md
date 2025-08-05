---
# this_file: src_docs/md/chapter9.md
title: Chapter 9 - Development and Contributing
---

# Chapter 9: Development and Contributing

## Getting Started with Development

Contributing to vexy_glob is a great way to improve your Rust and Python skills while working on a high-performance library. This chapter covers everything you need to know to set up a development environment and contribute effectively.

### Prerequisites

Before you start, ensure you have the following tools installed:

=== "Required Tools"
    - **Python 3.8+** - [Download from python.org](https://python.org)
    - **Rust 1.70+** - [Install from rustup.rs](https://rustup.rs)
    - **maturin** - Build tool for Python extensions in Rust
    - **uv** (recommended) - Fast Python package manager

=== "Optional Tools"
    - **Git** - Version control
    - **VS Code** - IDE with Rust and Python extensions
    - **cargo-flamegraph** - Performance profiling
    - **ruff** - Python linting and formatting

### Development Environment Setup

#### 1. Clone and Initial Setup

```bash
# Clone the repository
git clone https://github.com/vexyart/vexy-glob.git
cd vexy-glob

# Create virtual environment with uv (recommended)
uv venv --python 3.12
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or with standard Python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
# Install Python dependencies
uv sync

# Or with pip
pip install -r requirements-dev.txt

# Install maturin for building Rust extensions
pip install maturin
```

#### 3. Build the Extension

```bash
# Development build (faster, includes debug symbols)
maturin develop

# Release build (optimized, for benchmarking)
maturin develop --release
```

#### 4. Verify Installation

```bash
# Run basic tests
python -m pytest tests/test_basic.py -v

# Test the extension
python -c "import vexy_glob; print(vexy_glob.find('*.py', as_list=True))"

# Run Rust tests
cargo test
```

## Project Architecture

Understanding the project structure is crucial for effective contributions:

### Directory Structure

```
vexy-glob/
├── src/                     # Rust source code
│   ├── lib.rs              # Main Rust library with PyO3 bindings
│   ├── pattern_cache.rs    # Pattern caching optimizations
│   ├── simd_string.rs      # SIMD string operations
│   ├── zero_copy_path.rs   # Zero-copy path handling
│   └── global_init.rs      # Global initialization
├── vexy_glob/              # Python package
│   ├── __init__.py         # Python API wrapper
│   └── __main__.py         # CLI implementation
├── tests/                  # Python tests
│   ├── test_basic.py       # Basic functionality tests
│   ├── test_performance.py # Performance benchmarks
│   └── platform_tests/     # Platform-specific tests
├── benches/                # Rust benchmarks
│   └── comprehensive_benchmarks.rs
├── Cargo.toml              # Rust project configuration
├── pyproject.toml          # Python project configuration
└── sync_version.py         # Version synchronization script
```

### Key Components

#### 1. Rust Core (`src/lib.rs`)

The heart of vexy_glob is the Rust core that provides:

- **High-performance file traversal** using the `ignore` crate
- **Content search** powered by `grep-searcher`
- **Pattern matching** with `globset`
- **PyO3 bindings** for Python integration

```rust
// Key structures and functions (simplified)
#[pyfunction]
fn find(
    paths: Vec<String>,
    glob: Option<String>,
    // ... other parameters
) -> PyResult<PyObject> {
    // Implementation using ignore::WalkBuilder
}

#[pyfunction] 
fn search(
    content_regex: String,
    paths: Vec<String>,
    // ... other parameters
) -> PyResult<PyObject> {
    // Implementation using grep_searcher
}
```

#### 2. Python API (`vexy_glob/__init__.py`)

The Python layer provides:

- **User-friendly API** with type hints
- **Parameter validation** and conversion
- **Error handling** with custom exceptions
- **Backward compatibility** with glob module

#### 3. Performance Optimizations

Several optimizations make vexy_glob fast:

- **Zero-copy operations** (`zero_copy_path.rs`)
- **SIMD string operations** (`simd_string.rs`)
- **Pattern caching** (`pattern_cache.rs`)
- **Parallel execution** with optimal thread management

## Development Workflow

### Testing

vexy_glob has comprehensive tests to ensure reliability across platforms:

#### Python Tests

```bash
# Run all Python tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_basic.py -v           # Basic functionality
python -m pytest tests/test_performance.py -v    # Performance tests
python -m pytest tests/test_content_search.py -v # Content search

# Run with coverage
python -m pytest tests/ --cov=vexy_glob --cov-report=html

# Run platform-specific tests
python -m pytest tests/platform_tests/ -v
```

#### Rust Tests

```bash
# Run all Rust tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test
cargo test test_name

# Run with release optimizations
cargo test --release
```

#### Benchmarks

```bash
# Python benchmarks
python -m pytest tests/test_benchmarks.py -v --benchmark-only

# Rust benchmarks
cargo bench

# Performance profiling
cargo flamegraph --bench comprehensive_benchmarks
```

### Code Quality

#### Rust Code Quality

```bash
# Format code
cargo fmt

# Lint code
cargo clippy -- -D warnings

# Check for common issues
cargo audit
```

#### Python Code Quality

```bash
# Format with ruff
ruff format .

# Lint with ruff
ruff check . --fix

# Type checking with mypy
mypy vexy_glob/

# All quality checks combined
fd -e py -x uvx autoflake -i {}
fd -e py -x uvx pyupgrade --py312-plus {}
fd -e py -x uvx ruff check --output-format=github --fix --unsafe-fixes {}
fd -e py -x uvx ruff format --respect-gitignore --target-version py312 {}
```

### Building and Packaging

#### Development Builds

```bash
# Quick development build
maturin develop

# Development build with specific Python
maturin develop --python python3.11

# Build with debug symbols for profiling
maturin develop --profile=dev
```

#### Release Builds

```bash
# Sync version from git tags
python sync_version.py

# Build optimized wheel
maturin build --release

# Build source distribution
maturin sdist

# Build for specific platform
maturin build --release --target x86_64-unknown-linux-gnu
```

#### Using the Build Script

```bash
# Automated build (recommended)
./build.sh

# This script:
# 1. Syncs version from git tags
# 2. Builds optimized wheel
# 3. Builds source distribution
# 4. Places artifacts in dist/
```

## Contributing Guidelines

### Types of Contributions

We welcome various types of contributions:

=== "Code Contributions"
    - **Bug fixes** - Fix issues in existing functionality
    - **Performance improvements** - Optimize hot paths
    - **New features** - Add functionality with discussion first
    - **Platform support** - Improve cross-platform compatibility

=== "Documentation"
    - **API documentation** - Improve docstrings and type hints
    - **User guides** - Add examples and tutorials
    - **Performance analysis** - Document optimization findings
    - **Platform notes** - Document platform-specific behavior

=== "Testing"
    - **Test coverage** - Add tests for uncovered code paths
    - **Platform testing** - Test on different operating systems
    - **Performance benchmarks** - Add relevant benchmarks
    - **Edge case testing** - Test boundary conditions

### Contribution Process

#### 1. Planning Your Contribution

Before starting work:

1. **Check existing issues** - Look for related discussions
2. **Open an issue** - Describe your proposed changes
3. **Get feedback** - Discuss approach with maintainers
4. **Fork the repository** - Create your own copy

#### 2. Making Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# - Follow coding standards
# - Add tests for new functionality
# - Update documentation as needed

# Test your changes
python -m pytest tests/ -v
cargo test
cargo clippy

# Commit your changes
git add .
git commit -m "feat: descriptive commit message"
```

#### 3. Submitting Your Contribution

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request
# - Describe your changes clearly
# - Reference related issues
# - Include test results
```

### Coding Standards

#### Rust Code Standards

```rust
// Use clear, descriptive names
fn find_files_with_pattern(pattern: &str) -> Result<Vec<PathBuf>, Error> {
    // Implementation
}

// Document public APIs
/// Finds files matching the given glob pattern.
/// 
/// # Arguments
/// * `pattern` - Glob pattern to match against
/// 
/// # Returns
/// * `Result<Vec<PathBuf>, Error>` - List of matching paths or error
pub fn find_files(pattern: &str) -> Result<Vec<PathBuf>, Error> {
    // Implementation
}

// Handle errors properly
match operation_that_can_fail() {
    Ok(result) => process_result(result),
    Err(e) => return Err(e.into()),
}

// Use appropriate error types
#[derive(Debug, thiserror::Error)]
pub enum VexyGlobError {
    #[error("Invalid pattern: {pattern}")]
    InvalidPattern { pattern: String },
    #[error("I/O error: {source}")]
    Io { #[from] source: std::io::Error },
}
```

#### Python Code Standards

```python
# Use type hints extensively
def find_files(
    pattern: str,
    root: Union[str, Path] = ".",
    *,
    content: Optional[str] = None,
) -> Iterator[Union[str, Path]]:
    """Find files matching pattern.
    
    Args:
        pattern: Glob pattern to match
        root: Root directory for search
        content: Optional content search pattern
        
    Returns:
        Iterator of matching file paths
        
    Raises:
        PatternError: If pattern is invalid
        SearchError: If search fails
    """
    # Implementation

# Handle errors gracefully
try:
    result = risky_operation()
except SpecificError as e:
    logger.warning(f"Operation failed: {e}")
    return default_value

# Use descriptive variable names
filtered_python_files = [
    path for path in all_files 
    if path.suffix == '.py' and not path.name.startswith('test_')
]
```

### Performance Considerations

When contributing performance improvements:

#### 1. Measure Before Optimizing

```bash
# Baseline measurement
cargo bench > baseline.txt

# After changes
cargo bench > optimized.txt

# Compare results
diff baseline.txt optimized.txt
```

#### 2. Profile Hot Paths

```bash
# Generate flame graph
cargo flamegraph --bench comprehensive_benchmarks

# Profile specific function
cargo bench --bench comprehensive_benchmarks -- --profile-time=10
```

#### 3. Consider Memory Usage

```rust
// Prefer stack allocation
let mut buffer = [0u8; 1024];

// Use appropriate collection types
use smallvec::SmallVec;
let small_vec: SmallVec<[u8; 32]> = SmallVec::new();

// Avoid unnecessary allocations
fn process_path(path: &Path) -> Result<(), Error> {
    // Work with borrowed data when possible
    let path_str = path.to_str().ok_or(Error::InvalidPath)?;
    // Process without allocating
}
```

### Platform-Specific Development

#### Testing on Multiple Platforms

```bash
# Use GitHub Actions for CI testing
# Local testing with Docker for Linux
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11 bash -c "
    pip install maturin pytest &&
    maturin develop &&
    python -m pytest tests/ -v
"

# Cross-compilation for different targets
rustup target add x86_64-pc-windows-gnu
cargo build --target x86_64-pc-windows-gnu
```

#### Platform-Specific Code

```rust
#[cfg(windows)]
fn platform_specific_function() -> Result<(), Error> {
    // Windows-specific implementation
}

#[cfg(unix)]
fn platform_specific_function() -> Result<(), Error> {
    // Unix-specific implementation
}

#[cfg(target_os = "macos")]
fn handle_macos_specific_case() {
    // macOS-specific handling
}
```

## Advanced Development Topics

### Performance Profiling

#### Rust Profiling

```bash
# Install profiling tools
cargo install flamegraph
cargo install cargo-benchcmp

# Generate flame graph
cargo flamegraph --bench comprehensive_benchmarks

# Compare benchmark results
cargo bench > before.txt
# Make changes
cargo bench > after.txt
cargo benchcmp before.txt after.txt
```

#### Python Profiling

```python
import cProfile
import pstats
import vexy_glob

def profile_operation():
    """Profile vexy_glob operation."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Operation to profile
    list(vexy_glob.find("**/*.py"))
    
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions

profile_operation()
```

### Memory Management

#### Rust Memory Best Practices

```rust
// Use Cow for conditional ownership
use std::borrow::Cow;

fn process_string(input: &str) -> Cow<str> {
    if needs_processing(input) {
        Cow::Owned(process_and_allocate(input))
    } else {
        Cow::Borrowed(input)
    }
}

// Prefer iterators over collecting
fn count_matching_files(pattern: &str) -> usize {
    find_files(pattern)
        .filter(|path| matches_criteria(path))
        .count()  // No intermediate collection
}

// Use appropriate buffer sizes
const BUFFER_SIZE: usize = 64 * 1024;  // 64KB buffer
let mut buffer = vec![0u8; BUFFER_SIZE];
```

#### Python Memory Management

```python
# Use generators for large datasets
def process_large_dataset():
    for item in vexy_glob.find("**/*"):
        yield process_item(item)  # Process one at a time

# Implement cleanup for resources
import contextlib

@contextlib.contextmanager
def temporary_files():
    files = []
    try:
        yield files
    finally:
        for file in files:
            file.unlink(missing_ok=True)
```

### Contributing to Documentation

#### API Documentation

```python
def find(
    pattern: str = "*",
    root: Union[str, Path] = ".",
    *,
    content: Optional[str] = None,
) -> Iterator[Union[str, Path]]:
    """Find files and directories matching pattern.
    
    This function provides high-performance file discovery with optional
    content search capabilities. It uses Rust for optimal performance
    while maintaining a Pythonic API.
    
    Args:
        pattern: Glob pattern to match files. Supports standard glob
            syntax including *, **, ?, [seq], and {a,b} patterns.
            Examples: "*.py", "**/*.{js,ts}", "src/**/test_*.py"
        root: Starting directory for the search. Can be a string path
            or pathlib.Path object. Defaults to current directory.
        content: Optional regex pattern to search within file contents.
            When provided, returns SearchResult objects instead of paths.
            Examples: "TODO", r"def\s+\w+\(", r"class\s+(\w+)"
    
    Returns:
        Iterator yielding file paths as strings (or Path objects if
        as_path=True). When content is specified, yields SearchResult
        objects containing match information.
    
    Raises:
        PatternError: When the glob pattern or regex pattern is invalid.
        SearchError: When a non-recoverable I/O error occurs during search.
    
    Example:
        >>> import vexy_glob
        >>> 
        >>> # Find all Python files
        >>> for path in vexy_glob.find("**/*.py"):
        ...     print(path)
        >>>
        >>> # Search for TODO comments
        >>> for match in vexy_glob.find("**/*.py", content="TODO"):
        ...     print(f"{match.path}:{match.line_number}: {match.line_text}")
    
    Note:
        For maximum performance, use specific patterns and leverage
        built-in filtering options rather than post-processing results.
        The function automatically respects .gitignore files and skips
        hidden files by default.
    """
```

### Release Process

#### Version Management

```bash
# Create new version
git tag v1.0.10
git push origin v1.0.10

# Sync version to Cargo.toml
python sync_version.py

# Verify version sync
grep version Cargo.toml
python -c "import setuptools_scm; print(setuptools_scm.get_version())"
```

#### Building Release Artifacts

```bash
# Build all artifacts
./build.sh

# Verify wheel contents
unzip -l dist/vexy_glob-*.whl

# Test wheel installation
pip install dist/vexy_glob-*.whl --force-reinstall
python -c "import vexy_glob; print('OK')"
```

#### Publishing (Maintainers Only)

```bash
# Test on PyPI Test
maturin publish --repository testpypi

# Publish to PyPI
maturin publish
```

## Getting Help

### Community Resources

- **GitHub Issues** - Report bugs and request features
- **GitHub Discussions** - Ask questions and share ideas
- **Documentation** - Comprehensive guides and examples

### Debugging Tips

1. **Start simple** - Test with minimal examples first
2. **Use verbose output** - Enable debug logging when available
3. **Check platform differences** - Test on your target platforms
4. **Profile performance** - Measure before and after changes
5. **Review similar projects** - Learn from fd, ripgrep, and others

### Common Development Issues

#### Build Failures

```bash
# Clean build artifacts
cargo clean
rm -rf target/
rm -rf .venv/

# Rebuild from scratch
maturin develop --release
```

#### Test Failures

```bash
# Run tests with verbose output
python -m pytest tests/ -v -s

# Run specific failing test
python -m pytest tests/test_specific.py::test_function -v -s

# Debug with pdb
python -m pytest tests/test_specific.py::test_function --pdb
```

Thank you for contributing to vexy_glob! Your contributions help make this library better for everyone. 🚀

---

!!! tip "Start Small"
    Begin with small contributions like fixing typos, adding tests, or improving documentation. This helps you understand the codebase before tackling larger features.

!!! note "Performance Focus"
    vexy_glob prioritizes performance. When contributing, always consider the performance impact of your changes and measure before/after results.

!!! warning "Breaking Changes"
    Avoid breaking changes to the public API without discussion. Use deprecation warnings for a transition period when necessary.