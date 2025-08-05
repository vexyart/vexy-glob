---
# this_file: src_docs/md/index.md
title: vexy_glob Documentation
---

# vexy_glob - Path Accelerated Finding in Rust

[![PyPI version](https://badge.fury.io/py/vexy_glob.svg)](https://badge.fury.io/py/vexy_glob) [![CI](https://github.com/vexyart/vexy-glob/actions/workflows/ci.yml/badge.svg)](https://github.com/vexyart/vexy-glob/actions/workflows/ci.yml) [![codecov](https://codecov.io/gh/vexyart/vexy-glob/branch/main/graph/badge.svg)](https://codecov.io/gh/vexyart/vexy-glob)

**vexy_glob** is a high-performance Python extension for file system traversal and content searching, built with Rust. It provides a faster and more feature-rich alternative to Python's built-in `glob` (up to 6x faster) and `pathlib` (up to 12x faster) modules.

## TL;DR

**Quick Install:**
```bash
pip install vexy_glob
```

**Quick Usage:**
```python
import vexy_glob

# Find all Python files
for path in vexy_glob.find("**/*.py"):
    print(path)

# Search content within files
for match in vexy_glob.find("**/*.py", content="import asyncio"):
    print(f"{match.path}:{match.line_number}: {match.line_text}")
```

**Key Benefits:**
- 🚀 10-100x faster than standard Python file operations
- ⚡ Streaming results - get first results in milliseconds
- 💾 Constant memory usage regardless of file count
- 🔥 Parallel execution using all CPU cores
- 🔍 Built-in content search with regex support
- 🎯 Rich filtering by size, time, type, and custom patterns
- 🧠 Smart defaults - respects .gitignore automatically

## Documentation Table of Contents

This documentation is organized into 9 comprehensive chapters covering all aspects of vexy_glob:

### Getting Started
- **[Chapter 1: Introduction and Overview](chapter1.md)** - What is vexy_glob, architecture, and key features
- **[Chapter 2: Installation and Setup](chapter2.md)** - Installation methods, system requirements, and first steps

### User Guide  
- **[Chapter 3: Basic Usage and API Reference](chapter3.md)** - Core functions, basic patterns, and essential examples
- **[Chapter 4: Advanced Features and Configuration](chapter4.md)** - Complex filtering, performance tuning, and advanced options
- **[Chapter 5: Performance Optimization and Benchmarks](chapter5.md)** - Performance analysis, benchmarks, and optimization strategies
- **[Chapter 6: Content Search and Filtering](chapter6.md)** - Regex content search, filtering options, and search patterns

### Examples & Integration
- **[Chapter 7: Integration and Examples](chapter7.md)** - Real-world examples, cookbook recipes, and integration patterns

### Advanced Topics
- **[Chapter 8: Troubleshooting and Best Practices](chapter8.md)** - Common issues, debugging, and best practices
- **[Chapter 9: Development and Contributing](chapter9.md)** - Development setup, building from source, and contributing

## What Makes vexy_glob Special?

vexy_glob combines the best of both worlds: the performance of Rust with the convenience of Python. Built on top of battle-tested Rust crates used by tools like `fd` and `ripgrep`, it delivers exceptional performance while maintaining a simple, Pythonic API.

### Architecture Overview

```
┌─────────────────────┐
│   Python API Layer  │  ← Your Python code calls vexy_glob.find()
├─────────────────────┤
│    PyO3 Bindings    │  ← Zero-copy conversions between Python/Rust
├─────────────────────┤
│  Rust Core Engine   │  ← GIL released for true parallelism
│  ┌───────────────┐  │
│  │ ignore crate  │  │  ← Parallel directory traversal
│  │ (from fd)     │  │     Respects .gitignore files
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │ grep-searcher │  │  ← High-speed content search
│  │ (from ripgrep)│  │     SIMD-accelerated regex
│  └───────────────┘  │
├─────────────────────┤
│ Streaming Channel   │  ← Results yielded as found
│ (crossbeam-channel) │     No memory accumulation
└─────────────────────┘
```

## Quick Feature Comparison

| Feature | `glob.glob()` | `pathlib` | `vexy_glob` |
|---------|---------------|-----------|-------------|
| Pattern matching | ✅ Basic | ✅ Basic | ✅ Advanced |
| Recursive search | ✅ Slow | ✅ Slow | ✅ Fast |
| Streaming results | ❌ | ❌ | ✅ |
| Content search | ❌ | ❌ | ✅ |
| .gitignore respect | ❌ | ❌ | ✅ |
| Parallel execution | ❌ | ❌ | ✅ |
| Rich filtering | ❌ | ❌ | ✅ |
| Memory efficiency | ❌ | ❌ | ✅ |

## Ready to Get Started?

Choose your path:

- **New to vexy_glob?** Start with [Chapter 1: Introduction and Overview](chapter1.md)
- **Want to install quickly?** Jump to [Chapter 2: Installation and Setup](chapter2.md)
- **Ready to code?** Go straight to [Chapter 3: Basic Usage and API Reference](chapter3.md)
- **Need specific examples?** Check out [Chapter 7: Integration and Examples](chapter7.md)
- **Having issues?** Visit [Chapter 8: Troubleshooting and Best Practices](chapter8.md)

---

!!! tip "Performance Tip"
    For maximum performance, be specific with your patterns. Instead of `**/*.py`, use `src/**/*.py` when you know the target directory.

!!! info "Community"
    Found a bug or have a feature request? Visit our [GitHub repository](https://github.com/vexyart/vexy-glob) to open an issue or contribute!