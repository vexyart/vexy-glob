# this_file: tests/platform_tests/__init__.py
"""
Platform-specific testing framework for vexy_glob

This module provides comprehensive testing across Windows, Linux, and macOS platforms
to ensure vexy_glob works correctly in all supported environments.

Test Modules:
- windows_ecosystem_test.py: Windows-specific testing (UNC paths, NTFS, etc.)
- linux_distro_test.py: Linux distribution matrix testing (Ubuntu, RHEL, Alpine, etc.)
- macos_integration_test.py: macOS integration testing (APFS, xattrs, etc.)
- run_platform_tests.py: Master test coordinator and report generator

Usage:
    # Run all platform tests
    python tests/platform_tests/run_platform_tests.py
    
    # Run platform-specific tests only
    python tests/platform_tests/windows_ecosystem_test.py
    python tests/platform_tests/linux_distro_test.py
    python tests/platform_tests/macos_integration_test.py
    
    # Run specific test categories
    python tests/platform_tests/run_platform_tests.py --basic-only
    python tests/platform_tests/run_platform_tests.py --platform-only
    python tests/platform_tests/run_platform_tests.py --perf-only
"""

__version__ = "1.0.0"
__all__ = [
    "run_platform_tests",
    "windows_ecosystem_test", 
    "linux_distro_test",
    "macos_integration_test"
]