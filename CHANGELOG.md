# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **NEW: Command-Line Interface (CLI)** ✅
  - `vexy_glob find` command for finding files with all Python API features
  - `vexy_glob search` command for content searching with grep-like output  
  - Human-readable size parsing (10k, 1M, 1G format)
  - Colored output using rich library with match highlighting
  - `--no-color` option for non-interactive usage and pipelines
  - Broken pipe handling for Unix pipeline compatibility
  - Comprehensive CLI test suite with 100+ tests
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
  - **COMPLETE: Ripgrep-style content searching with regex patterns** ✅
  - **COMPLETE: Structured search results with file path, line number, line text, and matches** ✅
  - **COMPLETE: Content search through `find(content="pattern")` and dedicated `search()` function** ✅
  - **NEW: File size filtering with `min_size` and `max_size` parameters** ✅
  - **NEW: Modification time filtering with `mtime_after` and `mtime_before` parameters** ✅
  - **NEW: Human-readable time format support** ✅
    - Relative time: `-1d`, `-2h`, `-30m`, `-45s`
    - ISO dates: `2024-01-01`, `2024-01-01T12:00:00`
    - Python datetime objects
    - Unix timestamps
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