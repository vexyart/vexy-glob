---
# this_file: src_docs/md/chapter2.md
title: Chapter 2 - Installation and Setup
---

# Chapter 2: Installation and Setup

## Quick Installation

The easiest way to install vexy_glob is using pip:

```bash
pip install vexy_glob
```

That's it! vexy_glob comes as pre-built wheels for all major platforms, so no compilation is required.

## System Requirements

### Supported Platforms

vexy_glob provides pre-built wheels for:

=== "Linux"
    - **x86_64** (Intel/AMD 64-bit)
    - **aarch64** (ARM 64-bit)
    - **i686** (32-bit, limited support)
    - Most distributions (Ubuntu, CentOS, Alpine, etc.)

=== "macOS"
    - **x86_64** (Intel Macs)
    - **arm64** (Apple Silicon M1/M2/M3)
    - macOS 10.12+ (Sierra and later)

=== "Windows"
    - **x86_64** (64-bit Windows)
    - **i686** (32-bit Windows)
    - Windows 7+ (all versions)

### Python Version Support

- **Python 3.8+** (recommended: Python 3.10+)
- **PyPy 3.8+** (with some performance limitations)

### Runtime Dependencies

vexy_glob has **zero runtime dependencies** - everything is compiled into the binary wheel.

## Installation Methods

### 1. Standard pip Installation

```bash
# Latest stable version
pip install vexy_glob

# Specific version
pip install vexy_glob==1.0.9

# Upgrade to latest
pip install --upgrade vexy_glob
```

### 2. Development Installation

For the latest features (potentially unstable):

```bash
# Install from GitHub main branch
pip install git+https://github.com/vexyart/vexy-glob.git

# Install specific branch or tag
pip install git+https://github.com/vexyart/vexy-glob.git@v1.0.9
```

### 3. Editable Development Installation

For contributors and developers:

```bash
# Clone repository
git clone https://github.com/vexyart/vexy-glob.git
cd vexy-glob

# Install in development mode
pip install -e .

# Or using maturin for Rust development
pip install maturin
maturin develop
```

### 4. Alternative Package Managers

=== "uv (Recommended)"
    ```bash
    # Fast installation with uv
    uv add vexy_glob
    
    # Or in a script
    # /// script
    # dependencies = ["vexy_glob"]
    # ///
    ```

=== "poetry"
    ```bash
    poetry add vexy_glob
    ```

=== "pipenv"
    ```bash
    pipenv install vexy_glob
    ```

=== "conda/mamba"
    ```bash
    # Not yet available on conda-forge
    # Use pip within conda environment
    conda install pip
    pip install vexy_glob
    ```

## Verification

### Test Installation

Verify your installation works correctly:

```python
import vexy_glob

# Basic functionality test
files = list(vexy_glob.find("*.py"))
print(f"Found {len(files)} Python files")

# Version check
print(f"vexy_glob version: {vexy_glob.__version__}")

# Performance test
import time
start = time.time()
count = sum(1 for _ in vexy_glob.find("**/*"))
end = time.time()
print(f"Found {count} files in {end-start:.3f} seconds")
```

### Command-Line Interface

Test the CLI functionality:

```bash
# Basic file finding
python -m vexy_glob find "*.py"

# Help information
python -m vexy_glob --help

# Version information
python -m vexy_glob --version
```

## First Steps

### Your First Search

Let's start with a simple file search:

```python
import vexy_glob

# Find all Python files in current directory and subdirectories
for path in vexy_glob.find("**/*.py"):
    print(path)
```

### Your First Content Search

Now let's search for content within files:

```python
import vexy_glob

# Find TODO comments in Python files
for match in vexy_glob.find("**/*.py", content="TODO"):
    print(f"{match.path}:{match.line_number}: {match.line_text.strip()}")
```

### Performance Comparison

See the difference for yourself:

```python
import time
import glob
import vexy_glob

# Standard library approach
start = time.time()
stdlib_files = glob.glob("**/*.py", recursive=True)
stdlib_time = time.time() - start

# vexy_glob approach  
start = time.time()
vexy_files = list(vexy_glob.find("**/*.py"))
vexy_time = time.time() - start

print(f"Standard library: {len(stdlib_files)} files in {stdlib_time:.3f}s")
print(f"vexy_glob: {len(vexy_files)} files in {vexy_time:.3f}s")
print(f"Speedup: {stdlib_time/vexy_time:.1f}x faster")
```

## Environment Setup

### Virtual Environment (Recommended)

Always use virtual environments for Python projects:

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install vexy_glob

# Using uv (faster)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv add vexy_glob
```

### IDE Configuration

#### VS Code

Add to your `settings.json` for better IntelliSense:

```json
{
    "python.analysis.typeCheckingMode": "strict",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true
}
```

#### PyCharm

vexy_glob includes comprehensive type hints that work automatically with PyCharm.

#### Jupyter Notebooks

Install in your notebook environment:

```bash
# If using conda
conda activate your-env
pip install vexy_glob

# If using pip
pip install vexy_glob ipython
```

## Building from Source

### Prerequisites

If you need to build from source (e.g., for unsupported platforms):

1. **Rust toolchain** (1.70+):
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Python development headers**:
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-dev
   
   # CentOS/RHEL
   sudo yum install python3-devel
   
   # macOS (via Xcode command line tools)
   xcode-select --install
   ```

3. **maturin** (build tool):
   ```bash
   pip install maturin
   ```

### Build Process

```bash
# Clone repository
git clone https://github.com/vexyart/vexy-glob.git
cd vexy-glob

# Development build
maturin develop

# Release build
maturin build --release

# Install locally
pip install target/wheels/vexy_glob-*.whl
```

### Build Configuration

The build can be customized via environment variables:

```bash
# Enable CPU-specific optimizations
export RUSTFLAGS="-C target-cpu=native"
maturin build --release

# Debug build with symbols
maturin develop --profile=dev

# Cross-compilation (advanced)
rustup target add x86_64-unknown-linux-musl
maturin build --target x86_64-unknown-linux-musl
```

## Troubleshooting Installation

### Common Issues

#### 1. No Wheel Available

If you see "No matching distribution found":

```bash
# Update pip and try again
pip install --upgrade pip setuptools wheel
pip install vexy_glob

# Or build from source
pip install maturin
pip install vexy_glob --no-binary=vexy_glob
```

#### 2. Import Errors

If `import vexy_glob` fails:

```python
# Check installation
import sys
print(sys.path)

# Reinstall
import subprocess
subprocess.run([sys.executable, "-m", "pip", "install", "--force-reinstall", "vexy_glob"])
```

#### 3. Permission Errors

On some systems you might need:

```bash
# User installation
pip install --user vexy_glob

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install vexy_glob
```

#### 4. Platform-Specific Issues

=== "Windows"
    ```bash
    # If you get "Microsoft Visual C++ 14.0 is required"
    # Either install Visual Studio Build Tools or use pre-built wheels
    pip install --only-binary=vexy_glob vexy_glob
    ```

=== "macOS"
    ```bash
    # If you get "command line tools" errors
    xcode-select --install
    
    # For Apple Silicon Macs, ensure you're using arm64 Python
    python -c "import platform; print(platform.machine())"
    ```

=== "Linux"
    ```bash
    # If you get "GLIBC version" errors
    # You may need a newer Linux distribution or build from source
    
    # For Alpine Linux
    apk add musl-dev gcc
    pip install vexy_glob
    ```

### Debug Information

Collect debug info for support:

```python
import sys
import platform
import vexy_glob

print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Architecture: {platform.machine()}")
print(f"vexy_glob: {vexy_glob.__version__}")

# Test basic functionality
try:
    list(vexy_glob.find("*.py"))
    print("Basic functionality: OK")
except Exception as e:
    print(f"Basic functionality: ERROR - {e}")
```

## Configuration

### Environment Variables

vexy_glob respects these environment variables:

```bash
# Control default thread count
export VEXY_GLOB_THREADS=4

# Control default buffer sizes
export VEXY_GLOB_BUFFER_SIZE=8192

# Enable debug logging
export VEXY_GLOB_DEBUG=1
```

### Global Settings

Configure defaults in your application:

```python
import vexy_glob

# Set global defaults (if supported in future versions)
vexy_glob.set_default_threads(4)
vexy_glob.set_default_hidden(False)
```

## Next Steps

Now that you have vexy_glob installed and verified, you're ready to explore its capabilities:

→ **[Chapter 3: Basic Usage and API Reference](chapter3.md)** - Learn the core functions and patterns

→ **[Chapter 7: Integration and Examples](chapter7.md)** - See real-world usage examples

---

!!! tip "Performance Tip"
    For maximum performance, ensure you're using the latest version of vexy_glob, as each release includes performance improvements.

!!! warning "Development Builds"
    Development versions from GitHub may be unstable. Use tagged releases for production environments.

!!! info "Support"
    If you encounter installation issues not covered here, please check our [GitHub issues](https://github.com/vexyart/vexy-glob/issues) or open a new issue with your debug information.