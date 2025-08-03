# TODO.md - vexy_glob Implementation Tasks

## 🚀 CURRENT PRIORITIES

### Priority 1: Performance Optimizations
- [ ] Add same_file_system option to prevent crossing mount points
- [ ] Add result sorting options (name, size, mtime)
- [ ] Implement smart-case matching optimization
- [ ] Add literal string optimization paths
- [ ] Configure optimal buffer sizes for different workloads
- [ ] Optimize hot paths based on profiling

### Priority 2: Platform Testing
- [ ] Test and fix Windows-specific path handling
- [ ] Verify Linux compatibility across distributions
- [ ] Test macOS-specific features (e.g., .DS_Store handling)
- [ ] Handle platform-specific file system features
- [ ] Test performance across different platforms
- [ ] Verify Unicode path handling on all platforms
- [ ] Test with real-world codebases
- [ ] Benchmark against fd and ripgrep directly
- [ ] Test with extremely large directories (1M+ files)
- [ ] Verify memory usage stays constant
- [ ] Test interruption and cleanup behavior

### Priority 3: Release Preparation
- [ ] Run full test suite on all platforms via CI
- [ ] Manual testing on Windows, Linux, macOS
- [ ] Test installation from wheels on clean systems
- [ ] Verify all examples work correctly
- [ ] Performance regression testing
- [ ] Update version to 1.0.0
- [ ] Create comprehensive release notes
- [ ] Build wheels for all platforms
- [ ] Publish to Test PyPI
- [ ] Test installation from Test PyPI
- [ ] Publish to PyPI
- [ ] Create GitHub release with artifacts
- [ ] Announce on Python forums and social media

## Notes

- Build system has been modernized to use maturin directly instead of hatch
- Version management now uses git tags with setuptools-scm
- Current version: 1.0.3
