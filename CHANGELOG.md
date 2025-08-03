# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Smart-case Matching Optimization** ✅
  - Implemented intelligent case sensitivity based on pattern content
  - Patterns with uppercase letters are automatically case-sensitive
  - Patterns with only lowercase letters are automatically case-insensitive
  - Applies independently to glob patterns and content search patterns
  - Can be overridden with explicit `case_sensitive` parameter
  - Added comprehensive test suite in test_smart_case.py
  - Fixed RegexMatcher to properly respect case sensitivity for content search
- **Literal String Optimization** ✅
  - Added PatternMatcher enum to optimize literal patterns vs glob patterns
  - Literal patterns (no wildcards) use direct string comparison instead of glob matching
  - Significantly faster for exact filename matches
  - Handles both filename-only and full-path literal patterns correctly
  - Fixed glob pattern matching to prepend **/ for patterns without path separators
  - Added comprehensive test suite in test_literal_optimization.py
- **Buffer Size Optimization** ✅
  - Added BufferConfig to optimize channel capacity based on workload type
  - Content search uses smaller channel buffer (500) as results are produced slowly
  - Sorting operations use larger channel buffer (10,000) to collect all results efficiently
  - Standard file finding scales channel buffer with thread count for better parallelism
  - Memory usage capped to prevent excessive allocation
  - Added comprehensive test suite in test_buffer_optimization.py
- **Result Sorting Options** ✅
  - Added `sort` parameter to `find()` function with options: 'name', 'path', 'size', 'mtime'
  - Sorting automatically forces collection (returns list instead of iterator)
  - Efficient implementation using Rust's sort_by_key for optimal performance
  - Works seamlessly with as_path option for Path object results
  - Added comprehensive test suite in test_sorting.py
- **same_file_system Option** ✅
  - Added `same_file_system` parameter to prevent crossing filesystem boundaries
  - Useful for avoiding network mounts and external drives during traversal
  - Works with both `find()` and `search()` functions
  - Defaults to False to maintain backward compatibility
- **Comprehensive Documentation** (Issue #102) ✅
  - Expanded README.md from 419 to 1464 lines (3.5x increase)
  - Added architecture diagram showing Rust/Python integration
  - Created complete API reference with all function parameters and types
  - Added extensive cookbook section with 15+ real-world examples
  - Included detailed filtering documentation for size, time, and patterns
  - Expanded CLI documentation with advanced Unix pipeline patterns
  - Added migration guides from glob and pathlib
  - Created platform-specific sections for Windows, macOS, and Linux
  - Added performance tuning guide with optimization tips
  - Included comprehensive FAQ and troubleshooting sections
  - Added acknowledgments and related projects section

### Changed
- **Build System Modernization** ✅
  - Switched from hatch to maturin as primary build backend
  - Configured setuptools-scm for git-tag-based versioning
  - Created sync_version.py script for Cargo.toml version synchronization
  - Updated CI/CD workflows to use maturin directly
  - Created build.sh convenience script for release builds

### Fixed
- **PyO3 0.25 Compatibility** ✅
  - Updated pymodule function signature to use `&Bound<'_, PyModule>`
  - Fixed `add_function` and `add_class` method calls
  - Replaced deprecated `into_py` with `into_pyobject` trait method
  - Replaced `to_object` with `into()` conversion
  - Added explicit type annotations for PyObject conversions
  - Successfully builds with PyO3 0.25 and `uv sync`
- **Build System Duplicate Wheel Issue** ✅
  - Fixed issue where hatch was creating duplicate dev wheels
  - Switched to maturin as the build backend
  - Configured setuptools-scm for git-tag-based versioning
  - Created sync_version.py script for Cargo.toml synchronization
  - Updated CI/CD to use maturin directly
  - Created build.sh script for consistent builds

- Initial project structure and configuration with Rust and Python components
- Complete Rust library with PyO3 bindings for high-performance file finding
- Integration with `ignore` crate for parallel, gitignore-aware directory traversal
- Integration with `globset` crate for efficient glob pattern matching
- **COMPLETE: Content search functionality using `grep-searcher` and `grep-regex` crates** ✅
- Python API wrapper with pathlib integration and drop-in glob compatibility
- Streaming iterator implementation using crossbeam channels for constant memory usage
- Custom exception hierarchy: VexyGlobError, PatternError, SearchError, TraversalNotSupportedError
- Comprehensive test suite with 42 tests covering all major functionality (up from 27)
- Benchmark suite comparing performance against Python's stdlib glob
- **CI/CD Infrastructure**:
  - GitHub Actions workflow for multi-platform testing and builds
  - Cross-platform wheel building with cibuildwheel
  - Automated release workflow for GitHub and PyPI
  - Dependabot configuration for dependency updates
  - Code coverage reporting with codecov integration
  - Contributing guidelines documentation
- Support for:
  - Fast file finding with glob patterns (1.8x faster than stdlib)
    - Gitignore file respect (when in git repositories)
  - Hidden file filtering
  - File type filtering (files, directories, symlinks)
  - Extension filtering
  - Max depth control
  - Streaming results (10x faster time to first result)
  - Path object vs string return types
  - Parallel execution using multiple CPU cores
  - Drop-in replacement functions: `glob()` and `iglob()`

### Changed
- N/A

### Fixed
- N/A

### Performance
- 1.8x faster than stdlib glob for Python file finding
- 10x faster time to first result due to streaming architecture
- Constant memory usage regardless of result count
- Full CPU parallelization with work-stealing algorithms

## [1.0.3] - 2024-08-03

### Added
- **Command-Line Interface (CLI)** ✅
  - `vexy_glob find` command for finding files with all Python API features
  - `vexy_glob search` command for content searching with grep-like output  
  - Human-readable size parsing (10k, 1M, 1G format)
  - Colored output using rich library with match highlighting
  - `--no-color` option for non-interactive usage and pipelines
  - Broken pipe handling for Unix pipeline compatibility
  - Comprehensive CLI test suite with 100+ tests
- **Advanced Filtering Features** ✅
  - File size filtering with `min_size` and `max_size` parameters
  - Modification time filtering with `mtime_after` and `mtime_before` parameters
  - Access time filtering with `atime_after` and `atime_before` parameters
  - Creation time filtering with `ctime_after` and `ctime_before` parameters
  - Human-readable time format support:
    - Relative time: `-1d`, `-2h`, `-30m`, `-45s`
    - ISO dates: `2024-01-01`, `2024-01-01T12:00:00`
    - Python datetime objects
    - Unix timestamps
  - Exclude patterns for sophisticated filtering
  - Custom ignore file support (.ignore, .fdignore)
  - Follow symlinks option with loop detection
- **Content Search Functionality** ✅
  - Ripgrep-style content searching with regex patterns
  - Structured search results with file path, line number, line text, and matches
  - Content search through `find(content="pattern")` and dedicated `search()` function
  - Binary file detection and graceful skipping
  - Case sensitivity controls for content search

### Fixed
- **PyO3 0.25 Compatibility** ✅
  - Updated pymodule function signature to use `&Bound<'_, PyModule>`
  - Fixed `add_function` and `add_class` method calls
  - Replaced deprecated `into_py` with `into_pyobject` trait method
  - Replaced `to_object` with `into()` conversion
  - Added explicit type annotations for PyObject conversions

## [1.0.0] - 2024-07-15

### Added