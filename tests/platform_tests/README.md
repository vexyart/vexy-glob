# vexy_glob Platform Testing Framework

This directory contains comprehensive platform-specific tests for `vexy_glob` to ensure compatibility across Windows, Linux, and macOS environments.

## 🎯 Overview

The platform testing framework validates `vexy_glob` functionality across different operating systems, filesystems, and configurations. It identifies platform-specific issues and ensures consistent behavior in production environments.

## 📁 Test Structure

### Core Test Modules

- **`run_platform_tests.py`** - Master test coordinator and report generator
- **`windows_ecosystem_test.py`** - Windows-specific ecosystem testing
- **`linux_distro_test.py`** - Linux distribution matrix testing  
- **`macos_integration_test.py`** - macOS platform integration testing

### Test Categories

#### 1. Basic Functionality Tests (All Platforms)
- ✅ File finding with glob patterns
- ✅ Content search with regex patterns
- ✅ Streaming iterator behavior
- ✅ Error handling and edge cases

#### 2. Windows Ecosystem Tests
- 🪟 UNC paths (`\\server\share\folder`) with network drives
- 🪟 Windows drive letters (C:\, D:\, mapped drives)
- 🪟 Case-insensitive NTFS behavior
- 🪟 Windows reserved filenames (CON, PRN, AUX, COM1-9, LPT1-9)
- 🪟 NTFS junction points, hard links, symbolic links
- 🪟 Windows file attributes (hidden, system, readonly)
- 🪟 PowerShell compatibility (5.1, 7.x, cmd.exe)
- 🪟 WSL1/WSL2 integration
- 🪟 Windows Defender real-time scanning

#### 3. Linux Distribution Tests
- 🐧 Distribution matrix (Ubuntu, RHEL, Debian, Alpine, etc.)
- 🐧 Filesystem compatibility (ext4, btrfs, xfs, zfs, tmpfs)
- 🐧 Character encoding (UTF-8, ISO-8859-1, locale-specific)
- 🐧 Special filesystems (/proc, /sys, /dev, /tmp)
- 🐧 Container environments (Docker, Podman, LXC)
- 🐧 Security modules (SELinux, AppArmor)
- 🐧 Package manager integration

#### 4. macOS Integration Tests
- 🍎 APFS filesystem features (case-sensitive/insensitive)
- 🍎 macOS metadata (.DS_Store, .fseventsd, .Spotlight-V100)
- 🍎 Extended attributes (xattr, com.apple.*)
- 🍎 Resource forks (legacy handling)
- 🍎 Time Machine integration
- 🍎 Spotlight indexing
- 🍎 System Integrity Protection (SIP)
- 🍎 Xcode development environment

#### 5. Performance Benchmarks (Cross-Platform)
- ⚡ Small dataset performance (100 files)
- ⚡ Medium dataset performance (1,000 files)
- ⚡ Large dataset performance (5,000+ files)
- ⚡ File finding throughput (files/second)
- ⚡ Content search performance

## 🚀 Running Tests

### Prerequisites

```bash
# Install vexy_glob
pip install -e .

# Ensure test dependencies are available
pip install pytest
```

### Master Test Coordinator

Run all platform tests with comprehensive reporting:

```bash
# Run full test suite
python tests/platform_tests/run_platform_tests.py

# Run specific test categories
python tests/platform_tests/run_platform_tests.py --basic-only
python tests/platform_tests/run_platform_tests.py --platform-only  
python tests/platform_tests/run_platform_tests.py --perf-only

# Don't save detailed JSON results
python tests/platform_tests/run_platform_tests.py --no-save
```

### Platform-Specific Tests

Run tests for your current platform:

```bash
# Windows (must run on Windows)
python tests/platform_tests/windows_ecosystem_test.py

# Linux (must run on Linux)
python tests/platform_tests/linux_distro_test.py

# macOS (must run on macOS)
python tests/platform_tests/macos_integration_test.py
```

### Integration with pytest

```bash
# Run platform tests through pytest
pytest tests/platform_tests/ -v

# Run with coverage
pytest tests/platform_tests/ --cov=vexy_glob --cov-report=html
```

## 📊 Test Reports

### Console Output

The master coordinator produces detailed console reports:

```
🚀 vexy_glob Platform Compatibility Report
============================================================

📋 Environment Information:
  Platform: Darwin 23.5.0
  Machine: arm64
  Python: 3.12.0 (CPython)
  vexy_glob: 1.0.9

🔧 Basic Functionality Tests:
  Success Rate: 100.0%
  File Finding: ✅
  Pattern Matching: ✅
  Content Search: ✅
  Streaming: ✅

🏗️ Darwin-Specific Tests:
  ✅ Platform tests passed

🚀 Performance Benchmarks:
  Small (100 files): 2,500 files/s, 1,200 searches/s
  Medium (1000 files): 3,200 files/s, 980 searches/s
  Large (5000 files): 2,800 files/s, 850 searches/s

🎯 Overall Assessment:
  Test Duration: 45.2 seconds
  Overall Score: 95.0%
  Status: ✅ EXCELLENT - Ready for production
============================================================
```

### JSON Results

Detailed results are saved to timestamped JSON files:

```json
{
  "environment": {
    "platform": "Darwin",
    "python_version": "3.12.0",
    "vexy_glob_version": "1.0.9"
  },
  "basic_tests": {
    "success_rate": 100.0,
    "basic_file_finding": true,
    "pattern_matching": true,
    "content_search": true,
    "streaming": true,
    "errors": []
  },
  "platform_tests": {
    "platform": "Darwin",
    "success": true,
    "stdout": "...",
    "returncode": 0
  },
  "performance_tests": {
    "small_dataset": {
      "files_created": 100,
      "find_rate": 2500.0,
      "search_rate": 1200.0
    }
  }
}
```

## 🔧 Test Development

### Adding New Tests

1. **Platform-Specific Tests**: Add to the appropriate platform test module
2. **Cross-Platform Tests**: Add to the basic functionality tests in `run_platform_tests.py`
3. **Performance Tests**: Extend the benchmark methods

### Test Structure

Each test module follows this pattern:

```python
class PlatformTest(unittest.TestCase):
    def setUp(self):
        # Create test environment
        pass
        
    def tearDown(self):
        # Clean up test environment
        pass
        
    def test_specific_feature(self):
        # Test platform-specific behavior
        pass
```

### Environment Detection

Tests automatically detect:
- Operating system and version
- Available filesystems
- Security features
- Development tools
- Container environments

## 🐛 Troubleshooting

### Common Issues

**Permission Errors**
```bash
# Linux/macOS: Ensure test directories are writable  
chmod -R 755 tests/platform_tests/

# Windows: Run as Administrator for advanced tests
```

**Module Import Errors**
```bash
# Ensure vexy_glob is installed in development mode
pip install -e .

# Check Python path includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Platform Test Skips**
```
# Tests automatically skip on wrong platforms
# Windows tests only run on Windows
# Linux tests only run on Linux  
# macOS tests only run on macOS
```

### Performance Issues

If performance tests fail:

1. **Check system load**: Close other applications
2. **Verify disk speed**: Tests assume reasonable I/O performance
3. **Review memory**: Large datasets require sufficient RAM
4. **Network filesystems**: May have different performance characteristics

### Environment-Specific Issues

**Windows**
- UNC path tests require network shares
- Some tests require Administrator privileges
- Windows Defender may impact performance

**Linux**
- Container tests require Docker/Podman installation
- SELinux/AppArmor tests need security modules enabled
- Distribution detection requires `/etc/os-release`

**macOS**  
- Extended attribute tests use `xattr` command
- Time Machine tests require system integration
- Some tests require Xcode Command Line Tools

## 📈 Performance Expectations

### Baseline Performance Targets

| Dataset Size | Expected Throughput | Acceptable Range |
|--------------|-------------------|------------------|
| Small (100 files) | 2,000+ files/s | 1,000-5,000 files/s |
| Medium (1K files) | 3,000+ files/s | 1,500-6,000 files/s |
| Large (5K files) | 2,500+ files/s | 1,000-5,000 files/s |

### Platform-Specific Considerations

- **Windows**: NTFS performance varies with file attributes
- **Linux**: Performance depends on filesystem type (ext4 vs btrfs vs xfs)
- **macOS**: APFS generally provides consistent performance

## 🤝 Contributing

### Adding Platform Support

To add support for a new platform:

1. Create `{platform}_test.py` module
2. Implement platform-specific test class
3. Add platform detection to `run_platform_tests.py`
4. Update documentation

### Test Quality Guidelines

- **Comprehensive**: Cover all major platform features
- **Isolated**: Tests should not interfere with each other
- **Robust**: Handle missing dependencies gracefully
- **Fast**: Individual tests should complete within seconds
- **Documented**: Clear descriptions of what each test validates

## 📚 References

- [Windows File System Features](https://docs.microsoft.com/en-us/windows/win32/fileio/)
- [Linux Filesystem Hierarchy Standard](https://refspecs.linuxfoundation.org/FHS_3.0/fhs/index.html)
- [macOS File System Programming Guide](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/)

---

**Ready to test?** Start with the master coordinator:

```bash
python tests/platform_tests/run_platform_tests.py
```