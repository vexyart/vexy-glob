# TODO.md - vexy_glob Implementation Tasks

## 🚀 CURRENT PRIORITIES

### Priority 1: Performance Optimizations

- [ ] **Hot Path Profiling & Optimization**
  - Profile critical performance paths using cargo flamegraph and perf
  - Identify bottlenecks in directory traversal and pattern matching
  - Optimize memory allocations and reduce unnecessary string copies
  - Implement SIMD optimizations where applicable
  - Benchmark improvements against baseline performance metrics
  - Target: Additional 20-30% performance improvement in hot paths

### Priority 2: Platform Testing & Validation

- [ ] **Windows Compatibility Testing**
  - Test UNC paths (\\server\share) and drive letters (C:\)
  - Verify handling of Windows path separators and case insensitivity
  - Test with Windows-specific files (pagefile.sys, System Volume Information)
  - Validate symlink and junction handling on NTFS
  - Test with PowerShell and cmd.exe environments

- [ ] **Linux Distribution Testing**
  - Test on Ubuntu LTS, CentOS/RHEL, Debian, Alpine Linux
  - Verify different filesystem types (ext4, btrfs, xfs, zfs)
  - Test with different locale settings and character encodings
  - Validate handling of special files (/proc, /sys, /dev)
  - Test with container environments (Docker, Podman)

- [ ] **macOS Ecosystem Testing**
  - Test with .DS_Store, .Trashes, and Resource Forks
  - Verify APFS and HFS+ filesystem compatibility
  - Test with macOS-specific extended attributes and metadata
  - Validate case-preservation behavior on case-insensitive filesystems
  - Test with Time Machine and Spotlight exclusions

- [ ] **Real-World Validation**
  - Test against large codebases (Linux kernel, Chromium, LLVM)
  - Benchmark vs fd and ripgrep on identical workloads
  - Stress test with 1M+ file directories
  - Memory profiling under extreme loads
  - Signal handling and graceful shutdown testing

### Priority 3: Production Release (v2.0.0)

- [ ] **Pre-Release Validation**
  - Execute full CI/CD test matrix (Python 3.8-3.12, Linux/macOS/Windows)
  - Manual verification on clean VM environments
  - Installation testing from wheels on fresh systems
  - Validation of all README.md examples and cookbook recipes
  - Performance regression testing against v1.0.6 baseline

- [ ] **Release Engineering**
  - Update version to 2.0.0 in pyproject.toml (semantic versioning for new features)
  - Generate comprehensive release notes highlighting performance improvements
  - Build and test wheels for all supported platforms (Linux x86_64, macOS Intel/ARM, Windows x64)
  - Upload to Test PyPI and validate installation/functionality
  - Create staging environment for final validation

- [ ] **Launch & Distribution**
  - Publish stable release to PyPI with all platform wheels
  - Create GitHub release with detailed changelog and downloadable artifacts
  - Update project documentation and badges with new version
  - Announce on Python Package Index, Hacker News, Reddit r/Python
  - Submit to Python Weekly newsletter and relevant community channels

- [ ] **Post-Release Monitoring**
  - Monitor PyPI download statistics and user feedback
  - Set up issue templates for bug reports and feature requests  
  - Establish maintenance schedule for dependency updates
  - Plan roadmap for future enhancements based on user adoption

## Notes

- Build system has been modernized to use maturin directly instead of hatch
- Version management now uses git tags with setuptools-scm
