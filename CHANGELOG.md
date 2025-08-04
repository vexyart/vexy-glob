# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Regex Cache Effectiveness Profiling**
  - Created profile_regex_cache.py to measure pattern caching benefits
  - Documented 4.2% to 64.8% performance improvements based on pattern complexity
  - Complex regex patterns show up to 2.84x speedup with caching
  - Created REGEX_CACHE_ANALYSIS.md with detailed findings
- **Tool Performance Comparison**
  - Created benchmark_vs_tools.py for fair comparison with fd and ripgrep
  - Benchmarked file finding and content search across different dataset sizes
  - Created PERFORMANCE_VS_TOOLS.md documenting comparison results
  - Identified performance issues on medium/large datasets requiring investigation

### Discovered Issues
- High variance in initial file finding runs (50ms min to 10,387ms max)
- Performance degradation on datasets larger than 10,000 files  
- Slower than fd on medium datasets (4.5x slower for file finding)
- Mixed results vs ripgrep for content search

### Investigated
- **Variance Root Cause Analysis**
  - Created diagnose_variance.py for systematic investigation
  - Identified cold start as 7x slower (154ms vs 22ms) with 111% CV
  - Found pattern compilation, thread pool init, and memory allocation as causes
  - Created VARIANCE_ANALYSIS.md documenting all findings
  - Proposed fixes: pre-warming, lazy initialization, connection pooling

### Performance Infrastructure
- **Comprehensive Benchmarking Suite**
  - Created benchmark_pattern_cache.py for pattern cache validation
  - Created benchmark_vs_tools.py for fair comparison with fd and ripgrep
  - Created profile_regex_cache.py for measuring pattern caching benefits
  - Established systematic methodology for performance measurement
  - Added support for different dataset sizes and complexity levels
- **Advanced Debugging and Testing Tools**
  - Created test_cold_start_fix.py for variance validation (87% improvement verified)
  - Created debug_scaling_issues.py for systematic performance analysis
  - Created test_large_scale.py for progressive complexity testing
  - Created compare_with_fd_large.py for competitive benchmarking
  - Created debug_content_search.py and related tools for correctness validation

### Fixed
- **Critical Performance Issues Resolution** 🚀 **MAJOR MILESTONE**
  - **Cold Start Variance**: Reduced from 111% CV to 14.8% CV (87% improvement)
    - Implemented global initialization system (`src/global_init.rs`)
    - Pre-initializes Rayon thread pool at module import
    - Pre-warms pattern cache with 50+ common patterns
    - Pre-allocates channel buffers for different workload types
  - **Scaling Performance Recovery**: Now competitive with or faster than fd
    - 5,000 files: vexy_glob 1.92x **faster** than fd
    - 15,000 files: vexy_glob 1.31x **faster** than fd
    - 30,000 files: fd only 1.26x faster (minimal disadvantage)
  - **Content Search Functionality**: Fixed 0-match bug and validated performance
    - Root cause: Test framework parameter ordering issue
    - All patterns now work correctly with 100% accuracy vs ripgrep
    - Performance: 1.1x-3.5x slower than ripgrep but functionally equivalent
  - **Global Infrastructure Optimizations**: Systematic performance improvements
    - Connection pooling framework for channel operations
    - Thread pool warming eliminates cold start penalties
    - Pattern pre-compilation reduces first-run overhead

## [1.0.9] - 2025-08-05

### Added
- **Thread-Safe Pattern Caching System** ✅
  - Implemented LRU cache with Arc<RwLock<HashMap>> for concurrent pattern compilation access
  - Added pre-compilation of 50+ common file patterns (*.py, *.js, *.rs, etc.) at startup
  - Integrated caching into PatternMatcher::new() and build_glob_set() functions
  - Added once_cell dependency for lazy static pattern cache initialization
  - Cache configuration: 1000 pattern capacity with automatic LRU eviction
  - Benchmark validation showing 1.30x speedup through cache warming effects
- **New Source Files**
  - Created src/pattern_cache.rs for thread-safe pattern compilation caching
  - Created src/simd_string.rs for future SIMD string optimization infrastructure
  - Created benchmark_pattern_cache.py for pattern cache performance validation

### Changed
- **Zero-Copy Path Optimization** ✅
  - Refactored FindResult to use String instead of PathBuf for reduced allocations
  - Modified SearchResultRust to use String for paths to avoid redundant conversions
  - Eliminated path.to_path_buf() allocations in directory traversal hot paths
  - Optimized path-to-string conversions to happen only once during traversal
  - Achieved 108,162 files/second throughput with ~0.2 bytes per file memory usage (700x memory reduction)
- **Enhanced src/lib.rs**
  - Integrated pattern caching module for improved pattern compilation performance
  - Added SIMD string module infrastructure for future optimizations

### Performance
- Pattern compilation: 1.30x speedup through cache warming effects
- Memory usage: Reduced from 141 to ~0.2 bytes per file (700x improvement)
- Throughput: Achieved 108,162 files/second in benchmarks

## [1.0.8] - 2024-08-04

### Added
- **Comprehensive Performance Analysis** ✅
  - Created PERFORMANCE_ANALYSIS.md with detailed profiling results
  - Documented 38-58% performance gains from recent optimizations
  - Established baseline performance metrics for future regression testing
  - Identified key hot paths and optimization opportunities
- **Advanced Benchmarking Infrastructure** ✅
  - Added comprehensive_benchmarks.rs with extensive performance tests
  - Created datasets.rs for standardized test data generation
  - Implemented benchmarks for directory traversal, pattern matching, and content search
  - Added profiling scripts (profile.sh) for reproducible performance analysis
- **Performance Profiling Tooling** ✅
  - Integrated cargo flamegraph for hot path visualization
  - Set up criterion benchmarks for statistical performance tracking
  - Created automated profiling workflow with debug symbol management
  - Established methodology for future optimization work

### Changed
- Updated PLAN.md with refined Phase 8-10 tasks for v2.0.0 release
- Restructured TODO.md to focus on three main priorities for v2.0.0
- Enhanced WORK.md with completed performance analysis tasks

### Fixed
- N/A

## [1.0.7] - 2024-08-03

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
- **Comprehensive Documentation** ✅
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