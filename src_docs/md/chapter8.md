---
# this_file: src_docs/md/chapter8.md
title: Chapter 8 - Troubleshooting and Best Practices
---

# Chapter 8: Troubleshooting and Best Practices

## Common Issues and Solutions

### Installation and Import Issues

#### Problem: Import Error

```python
>>> import vexy_glob
ImportError: vexy_glob extension module not built. Run 'maturin develop' first.
```

**Solutions:**

=== "Pre-built Wheel Issue"
    ```bash
    # Update pip and reinstall
    pip install --upgrade pip setuptools wheel
    pip install --force-reinstall vexy_glob
    
    # Check platform compatibility
    pip debug --verbose
    ```

=== "Development Setup"
    ```bash
    # For development installations
    cd vexy-glob
    maturin develop
    
    # Or build and install wheel
    maturin build --release
    pip install target/wheels/vexy_glob-*.whl
    ```

=== "Virtual Environment"
    ```bash
    # Ensure you're in the correct environment
    which python
    pip list | grep vexy_glob
    
    # Reinstall in correct environment
    pip install vexy_glob
    ```

#### Problem: Module Not Found in Script

```python
# Script runs in different environment
ModuleNotFoundError: No module named 'vexy_glob'
```

**Solutions:**

```python
# Check Python path in script
import sys
print("Python executable:", sys.executable)
print("Python path:", sys.path)

# Install in correct Python environment
import subprocess
subprocess.run([sys.executable, "-m", "pip", "install", "vexy_glob"])
```

### Pattern Matching Issues

#### Problem: No Results Found

```python
# Pattern doesn't match expected files
files = list(vexy_glob.find("*.py"))
print(f"Found: {len(files)} files")  # Output: Found: 0 files
```

**Debugging Steps:**

```python
import vexy_glob
import os

# 1. Check current directory
print("Current directory:", os.getcwd())
print("Files in directory:", os.listdir("."))

# 2. Try broader pattern
files = list(vexy_glob.find("*"))
print(f"All files: {files}")

# 3. Check if files are hidden
hidden_files = list(vexy_glob.find("*", hidden=True))
print(f"Including hidden: {len(hidden_files)} files")

# 4. Check if .gitignore is excluding files
all_files = list(vexy_glob.find("*", ignore_git=True))
print(f"Ignoring .gitignore: {len(all_files)} files")

# 5. Use recursive pattern
recursive_files = list(vexy_glob.find("**/*.py"))
print(f"Recursive search: {len(recursive_files)} files")
```

#### Problem: Pattern Syntax Errors

```python
# Invalid glob pattern
vexy_glob.find("[unclosed")
# Raises: PatternError: Invalid pattern: '[unclosed'
```

**Solutions:**

```python
from vexy_glob import PatternError

def safe_find(pattern, **kwargs):
    """Safely execute find with pattern validation."""
    try:
        return list(vexy_glob.find(pattern, **kwargs))
    except PatternError as e:
        print(f"Invalid pattern '{pattern}': {e}")
        return []

# Test patterns before using
patterns = ["*.py", "**/*.{py,js}", "[unclosed"]
for pattern in patterns:
    result = safe_find(pattern)
    print(f"Pattern '{pattern}': {len(result)} files")
```

#### Problem: Case Sensitivity Issues

```python
# Looking for README.md but only finding readme.md
files = list(vexy_glob.find("README.md"))
print(f"Found: {files}")  # May be empty on case-insensitive systems
```

**Solutions:**

```python
# Explicit case sensitivity control
case_sensitive_files = list(vexy_glob.find("README.md", case_sensitive=True))
case_insensitive_files = list(vexy_glob.find("README.md", case_sensitive=False))

print(f"Case sensitive: {case_sensitive_files}")
print(f"Case insensitive: {case_insensitive_files}")

# Use smart case (default behavior)
smart_case_files = list(vexy_glob.find("readme.md"))  # Case insensitive
smart_case_exact = list(vexy_glob.find("README.md"))  # Case sensitive
```

### Performance Issues

#### Problem: Slow First Run

```python
import time

# First run is slow
start = time.time()
files1 = list(vexy_glob.find("**/*.py"))
time1 = time.time() - start

# Second run is faster
start = time.time()
files2 = list(vexy_glob.find("**/*.py"))
time2 = time.time() - start

print(f"First run: {time1:.3f}s, Second run: {time2:.3f}s")
```

**Solutions:**

```python
def benchmark_with_warmup(pattern, warmup_runs=1, **kwargs):
    """Benchmark with filesystem warmup."""
    # Warmup runs
    for _ in range(warmup_runs):
        list(vexy_glob.find(pattern, **kwargs))
    
    # Actual benchmark
    start = time.time()
    result = list(vexy_glob.find(pattern, **kwargs))
    duration = time.time() - start
    
    return result, duration

# Usage
files, duration = benchmark_with_warmup("**/*.py", warmup_runs=2)
print(f"Found {len(files)} files in {duration:.3f}s (after warmup)")
```

#### Problem: High Memory Usage

```python
# Loading too many results into memory
all_files = vexy_glob.find("**/*", as_list=True)  # Potential memory issue
```

**Solutions:**

```python
import psutil
import os

def memory_efficient_processing():
    """Process files with constant memory usage."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Stream processing
    count = 0
    for path in vexy_glob.find("**/*"):
        # Process one file at a time
        process_file(path)
        count += 1
        
        # Check memory periodically
        if count % 1000 == 0:
            current_memory = process.memory_info().rss
            memory_delta = (current_memory - initial_memory) / 1024 / 1024
            print(f"Processed {count} files, memory delta: {memory_delta:.1f}MB")
    
    return count

def process_file(path):
    """Example file processing function."""
    pass  # Your processing logic here

# Chunked processing for when you need lists
def chunked_processing(pattern, chunk_size=1000, **kwargs):
    """Process results in chunks to limit memory usage."""
    chunk = []
    for path in vexy_glob.find(pattern, **kwargs):
        chunk.append(path)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    
    if chunk:  # Process remaining items
        yield chunk

# Usage
for chunk in chunked_processing("**/*.py", chunk_size=500):
    print(f"Processing chunk of {len(chunk)} files")
    # Process chunk...
```

### Content Search Issues

#### Problem: Regex Pattern Errors

```python
# Invalid regex in content search
vexy_glob.find("**/*.py", content="[invalid regex")
# May raise PatternError or return unexpected results
```

**Solutions:**

```python
import re
from vexy_glob import PatternError

def validate_regex(pattern):
    """Validate regex pattern before using."""
    try:
        re.compile(pattern)
        return True
    except re.error as e:
        print(f"Invalid regex pattern: {e}")
        return False

def safe_content_search(file_pattern, content_pattern, **kwargs):
    """Safely perform content search with validation."""
    if not validate_regex(content_pattern):
        return []
    
    try:
        return list(vexy_glob.find(file_pattern, content=content_pattern, **kwargs))
    except PatternError as e:
        print(f"Search error: {e}")
        return []

# Test regex patterns
test_patterns = [
    r"def\s+\w+\(",     # Valid
    r"[unclosed",       # Invalid
    r"(?P<name>\w+)",   # Valid named group
]

for pattern in test_patterns:
    if validate_regex(pattern):
        print(f"✅ Pattern '{pattern}' is valid")
    else:
        print(f"❌ Pattern '{pattern}' is invalid")
```

#### Problem: No Content Search Results

```python
# Expected matches but got none
matches = list(vexy_glob.find("**/*.py", content="TODO"))
print(f"Found: {len(matches)} matches")  # Output: Found: 0 matches
```

**Debugging Steps:**

```python
# 1. Check if files exist
files = list(vexy_glob.find("**/*.py"))
print(f"Python files found: {len(files)}")

# 2. Check file content manually
if files:
    sample_file = files[0]
    try:
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "TODO" in content:
                print(f"✅ Found 'TODO' in {sample_file}")
            else:
                print(f"❌ No 'TODO' in {sample_file}")
    except UnicodeDecodeError:
        print(f"⚠️ Cannot read {sample_file} as text (binary file?)")

# 3. Try case-insensitive search
case_insensitive = list(vexy_glob.find("**/*.py", content="TODO", case_sensitive=False))
print(f"Case-insensitive matches: {len(case_insensitive)}")

# 4. Try broader pattern
broader_matches = list(vexy_glob.find("**/*.py", content=".*TODO.*"))
print(f"Broader pattern matches: {len(broader_matches)}")

# 5. Check specific file types
all_text_files = list(vexy_glob.find("**/*", content="TODO", 
                                    extension=["py", "txt", "md", "js"]))
print(f"All text files with TODO: {len(all_text_files)}")
```

### File System Issues

#### Problem: Permission Denied

```python
# Searching in restricted directories
vexy_glob.find("**/*", root="/root")
# May raise SearchError: Permission denied
```

**Solutions:**

```python
from vexy_glob import SearchError
import os

def safe_search_with_permissions(pattern, root=".", **kwargs):
    """Search with permission error handling."""
    try:
        return list(vexy_glob.find(pattern, root=root, **kwargs))
    except SearchError as e:
        if "permission" in str(e).lower():
            print(f"Permission denied for {root}")
            # Try with current user's directories only
            if root != ".":
                print("Falling back to current directory")
                return list(vexy_glob.find(pattern, root=".", **kwargs))
        else:
            print(f"Search error: {e}")
        return []

# Check directory permissions before searching
def check_directory_access(directory):
    """Check if directory is accessible."""
    try:
        os.listdir(directory)
        return True
    except PermissionError:
        return False

# Usage
test_dirs = ["/root", "/etc", "/home", "."]
for directory in test_dirs:
    if check_directory_access(directory):
        print(f"✅ Can access {directory}")
        files = safe_search_with_permissions("*", root=directory)
        print(f"  Found {len(files)} files")
    else:
        print(f"❌ Cannot access {directory}")
```

#### Problem: Symbolic Link Issues

```python
# Unexpected behavior with symbolic links
files = list(vexy_glob.find("**/*"))
# May not include files behind symlinks
```

**Solutions:**

```python
# Control symlink behavior explicitly
def compare_symlink_behavior(pattern):
    """Compare results with and without following symlinks."""
    no_symlinks = list(vexy_glob.find(pattern, follow_symlinks=False))
    with_symlinks = list(vexy_glob.find(pattern, follow_symlinks=True))
    
    print(f"Without following symlinks: {len(no_symlinks)} files")
    print(f"With following symlinks: {len(with_symlinks)} files")
    
    # Find the difference
    symlink_files = set(with_symlinks) - set(no_symlinks)
    if symlink_files:
        print(f"Files found via symlinks: {len(symlink_files)}")
        for f in list(symlink_files)[:5]:  # Show first 5
            print(f"  {f}")
    
    return no_symlinks, with_symlinks

# Check for broken symlinks
import os
from pathlib import Path

def find_broken_symlinks(root="."):
    """Find broken symbolic links."""
    broken_links = []
    for path in vexy_glob.find("**/*", root=root, follow_symlinks=False):
        path_obj = Path(path)
        if path_obj.is_symlink() and not path_obj.exists():
            broken_links.append(str(path_obj))
    
    return broken_links

broken = find_broken_symlinks()
if broken:
    print(f"Found {len(broken)} broken symlinks:")
    for link in broken:
        print(f"  {link}")
```

### Cross-Platform Issues

#### Problem: Path Separator Issues

```python
# Pattern works on Linux but not Windows
pattern = "src/**/*.py"  # Works everywhere
pattern_win = "src\\**\\*.py"  # Windows-specific, may not work
```

**Solutions:**

```python
import os
from pathlib import Path

def create_cross_platform_pattern(base_dir, file_pattern):
    """Create cross-platform glob patterns."""
    # Use forward slashes - vexy_glob handles conversion
    if isinstance(base_dir, Path):
        base_dir = str(base_dir).replace(os.sep, '/')
    
    return f"{base_dir}/**/{file_pattern}"

# Test cross-platform patterns
patterns = {
    'unix_style': "src/**/*.py",
    'windows_style': "src\\**\\*.py",
    'pathlib_based': create_cross_platform_pattern(Path("src"), "*.py")
}

for name, pattern in patterns.items():
    try:
        files = list(vexy_glob.find(pattern))
        print(f"{name}: {len(files)} files")
    except Exception as e:
        print(f"{name}: Error - {e}")
```

#### Problem: Case Sensitivity Differences

```python
# Behavior differs between Windows/macOS (case-insensitive) and Linux (case-sensitive)
files = list(vexy_glob.find("README.md"))
```

**Solutions:**

```python
import platform

def platform_aware_search(pattern, **kwargs):
    """Adjust search behavior based on platform."""
    system = platform.system().lower()
    
    # Set default case sensitivity based on platform
    if 'case_sensitive' not in kwargs:
        if system in ['windows', 'darwin']:  # Windows or macOS
            kwargs['case_sensitive'] = False
        else:  # Linux and others
            kwargs['case_sensitive'] = True
    
    return vexy_glob.find(pattern, **kwargs)

# Find files regardless of platform case sensitivity
def find_case_variants(base_pattern):
    """Find files with different case variants."""
    results = {}
    
    # Try exact pattern
    results['exact'] = list(vexy_glob.find(base_pattern, case_sensitive=True))
    
    # Try case-insensitive
    results['case_insensitive'] = list(vexy_glob.find(base_pattern, case_sensitive=False))
    
    # Try common variants for README
    if 'readme' in base_pattern.lower():
        variants = ['README.md', 'readme.md', 'ReadMe.md', 'README.MD']
        results['variants'] = []
        for variant in variants:
            files = list(vexy_glob.find(variant, case_sensitive=True))
            results['variants'].extend(files)
    
    return results

# Usage
readme_files = find_case_variants("README.md")
for variant, files in readme_files.items():
    print(f"{variant}: {files}")
```

## Best Practices

### Pattern Design Best Practices

#### 1. Specificity is Key

```python
# ❌ Too broad - searches everything
files = vexy_glob.find("**/*")

# ✅ Specific location
files = vexy_glob.find("src/**/*.py")

# ✅ Even more specific with constraints
files = vexy_glob.find(
    "src/**/*.py",
    exclude=["**/test/**"],
    max_depth=5
)
```

#### 2. Use Built-in Filtering

```python
# ❌ Post-process filtering
all_files = vexy_glob.find("**/*", as_list=True)
py_files = [f for f in all_files if f.endswith('.py')]
large_files = [f for f in py_files if os.path.getsize(f) > 1024]

# ✅ Built-in filtering
large_py_files = vexy_glob.find(
    "**/*.py",
    min_size=1024,
    as_list=True
)
```

#### 3. Smart Exclusions

```python
# Define reusable exclusion patterns
COMMON_EXCLUDES = [
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/.git/**",
    "**/build/**",
    "**/dist/**",
    "**/.venv/**",
    "**/venv/**"
]

DEVELOPMENT_EXCLUDES = COMMON_EXCLUDES + [
    "**/.pytest_cache/**",
    "**/.mypy_cache/**",
    "**/coverage/**"
]

# Use appropriate exclusion set
production_files = vexy_glob.find("**/*.py", exclude=COMMON_EXCLUDES)
clean_files = vexy_glob.find("**/*.py", exclude=DEVELOPMENT_EXCLUDES)
```

### Performance Best Practices

#### 1. Choose the Right Data Structure

```python
# For single-pass processing
def process_streaming():
    for path in vexy_glob.find("**/*.py"):
        process_file(path)  # Process immediately

# For multiple operations on same dataset
def process_with_list():
    files = vexy_glob.find("**/*.py", as_list=True)
    
    # Multiple operations on same data
    count = len(files)
    sorted_files = sorted(files)
    first_ten = files[:10]
    
    return count, sorted_files, first_ten

# For early termination
def find_first_match():
    for path in vexy_glob.find("**/*.py"):
        if "important" in path:
            return path
    return None
```

#### 2. Optimize Thread Usage

```python
import os

def get_optimal_threads(operation_type="mixed"):
    """Get optimal thread count based on operation type."""
    cpu_count = os.cpu_count() or 4
    
    thread_configs = {
        "io_heavy": cpu_count * 2,      # File finding, directory traversal
        "cpu_heavy": cpu_count,         # Complex regex, content processing
        "mixed": cpu_count,             # General purpose
        "memory_limited": max(1, cpu_count // 2),  # When memory is tight
        "single": 1                     # For debugging or specific requirements
    }
    
    return thread_configs.get(operation_type, cpu_count)

# Usage examples
fast_find = vexy_glob.find("**/*", threads=get_optimal_threads("io_heavy"))
complex_search = vexy_glob.find("**/*.py", content=r"complex.*regex", 
                                threads=get_optimal_threads("cpu_heavy"))
```

#### 3. Efficient Content Search

```python
# ✅ Efficient: Specific file types first
def efficient_content_search():
    return vexy_glob.find(
        "**/*",
        content="search_term",
        extension=["py", "js", "md"],  # Limit to text files
        exclude=["**/vendor/**"],     # Skip large directories
        max_depth=10                  # Reasonable depth limit
    )

# ❌ Inefficient: Search all files
def inefficient_content_search():
    return vexy_glob.find("**/*", content="search_term")

# ✅ Progressive search - start specific, then broaden
def progressive_search(term):
    """Search with increasing scope."""
    
    # Start specific
    results = list(vexy_glob.find("src/**/*.py", content=term))
    if results:
        return results
    
    # Broaden to all Python
    results = list(vexy_glob.find("**/*.py", content=term))
    if results:
        return results
    
    # Broaden to all text files
    return list(vexy_glob.find("**/*", content=term, 
                              extension=["py", "js", "md", "txt"]))
```

### Error Handling Best Practices

#### 1. Graceful Degradation

```python
from vexy_glob import VexyGlobError, PatternError, SearchError

def robust_file_search(pattern, **kwargs):
    """Robust file search with graceful error handling."""
    try:
        return list(vexy_glob.find(pattern, **kwargs))
    
    except PatternError as e:
        print(f"Invalid pattern '{pattern}': {e}")
        # Try a simpler fallback pattern
        try:
            fallback = pattern.replace("{", "").replace("}", "")
            print(f"Trying fallback pattern: {fallback}")
            return list(vexy_glob.find(fallback, **kwargs))
        except:
            return []
    
    except SearchError as e:
        print(f"Search error: {e}")
        # Try with reduced scope
        if 'root' in kwargs and kwargs['root'] != '.':
            print("Falling back to current directory")
            kwargs['root'] = '.'
            return robust_file_search(pattern, **kwargs)
        return []
    
    except VexyGlobError as e:
        print(f"General vexy_glob error: {e}")
        return []
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []
```

#### 2. Input Validation

```python
import re
from pathlib import Path

def validate_search_params(pattern, root=None, content=None, **kwargs):
    """Validate search parameters before execution."""
    errors = []
    
    # Validate pattern
    try:
        # Test if it's a valid glob pattern by checking common issues
        if pattern.count('[') != pattern.count(']'):
            errors.append("Unmatched brackets in pattern")
        if pattern.count('{') != pattern.count('}'):
            errors.append("Unmatched braces in pattern")
    except:
        errors.append("Invalid pattern syntax")
    
    # Validate root directory
    if root and not Path(root).exists():
        errors.append(f"Root directory does not exist: {root}")
    
    # Validate regex content pattern
    if content:
        try:
            re.compile(content)
        except re.error as e:
            errors.append(f"Invalid regex in content: {e}")
    
    # Validate size parameters
    for size_param in ['min_size', 'max_size']:
        if size_param in kwargs:
            value = kwargs[size_param]
            if not isinstance(value, (int, float)) or value < 0:
                errors.append(f"Invalid {size_param}: must be non-negative number")
    
    # Validate depth parameters
    for depth_param in ['min_depth', 'max_depth']:
        if depth_param in kwargs:
            value = kwargs[depth_param]
            if not isinstance(value, int) or value < 0:
                errors.append(f"Invalid {depth_param}: must be non-negative integer")
    
    return errors

def safe_search(pattern, **kwargs):
    """Perform search with validation."""
    errors = validate_search_params(pattern, **kwargs)
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return []
    
    return robust_file_search(pattern, **kwargs)
```

### Security Best Practices

#### 1. Path Traversal Protection

```python
import os
from pathlib import Path

def secure_path_search(pattern, root=".", **kwargs):
    """Secure search that prevents path traversal attacks."""
    
    # Normalize and validate root path
    root_path = Path(root).resolve()
    
    # Ensure root is within allowed directories
    allowed_roots = [
        Path.cwd(),
        Path.home(),
        Path("/tmp"),  # Adjust based on your security requirements
    ]
    
    allowed = any(
        root_path == allowed_root or 
        root_path.is_relative_to(allowed_root)
        for allowed_root in allowed_roots
    )
    
    if not allowed:
        raise PermissionError(f"Access denied to directory: {root}")
    
    # Perform search
    results = []
    for path in vexy_glob.find(pattern, root=str(root_path), **kwargs):
        # Double-check each result is within allowed area
        result_path = Path(path).resolve()
        if result_path.is_relative_to(root_path):
            results.append(path)
        else:
            print(f"Warning: Filtered out suspicious path: {path}")
    
    return results
```

#### 2. Content Search Safety

```python
def safe_content_search(pattern, content_pattern, max_results=1000, **kwargs):
    """Safe content search with limits and sanitization."""
    
    # Validate content pattern for safety
    dangerous_patterns = [
        r'.*\.{100,}.*',  # Catastrophic backtracking
        r'(.*)*',         # Nested quantifiers
        r'(.+)+',         # More nested quantifiers
    ]
    
    for dangerous in dangerous_patterns:
        try:
            if re.match(dangerous, content_pattern):
                raise ValueError(f"Potentially dangerous regex pattern detected")
        except re.error:
            continue
    
    # Limit file types for security
    safe_extensions = ['py', 'js', 'ts', 'txt', 'md', 'yml', 'yaml', 'json']
    kwargs['extension'] = kwargs.get('extension', safe_extensions)
    
    # Exclude sensitive directories
    sensitive_excludes = [
        "**/.git/**",
        "**/.ssh/**", 
        "**/passwords/**",
        "**/secrets/**",
        "**/private/**"
    ]
    
    existing_excludes = kwargs.get('exclude', [])
    if isinstance(existing_excludes, str):
        existing_excludes = [existing_excludes]
    
    kwargs['exclude'] = existing_excludes + sensitive_excludes
    
    # Perform limited search
    results = []
    for match in vexy_glob.find(pattern, content=content_pattern, **kwargs):
        results.append(match)
        if len(results) >= max_results:
            print(f"Warning: Result limit ({max_results}) reached")
            break
    
    return results
```

### Testing Best Practices

#### 1. Test Pattern Validation

```python
import unittest
import tempfile
import os
from pathlib import Path

class TestVexyGlobPatterns(unittest.TestCase):
    """Test cases for vexy_glob pattern validation."""
    
    def setUp(self):
        """Create temporary test directory structure."""
        self.test_dir = tempfile.mkdtemp()
        self.test_files = [
            "test.py",
            "README.md", 
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            ".hidden_file",
            "data/file.json"
        ]
        
        # Create test files
        for file_path in self.test_files:
            full_path = Path(self.test_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"Content of {file_path}")
    
    def tearDown(self):
        """Clean up test directory."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_basic_patterns(self):
        """Test basic glob patterns."""
        # Test simple pattern
        py_files = list(vexy_glob.find("*.py", root=self.test_dir))
        self.assertEqual(len(py_files), 1)  # Only test.py in root
        
        # Test recursive pattern
        all_py_files = list(vexy_glob.find("**/*.py", root=self.test_dir))
        self.assertEqual(len(all_py_files), 4)  # All .py files
    
    def test_exclusion_patterns(self):
        """Test exclusion functionality."""
        # Exclude test files
        non_test_py = list(vexy_glob.find(
            "**/*.py", 
            root=self.test_dir,
            exclude=["**/test*"]
        ))
        # Should exclude tests/test_main.py but include others
        self.assertEqual(len(non_test_py), 3)
    
    def test_content_search(self):
        """Test content search functionality."""
        # Search for files containing specific text
        matches = list(vexy_glob.find(
            "**/*",
            content="Content of",
            root=self.test_dir
        ))
        # All files contain "Content of"
        self.assertGreater(len(matches), 0)

if __name__ == "__main__":
    unittest.main()
```

#### 2. Performance Testing

```python
import time
import statistics

def performance_test_suite():
    """Comprehensive performance testing."""
    
    test_scenarios = [
        {
            'name': 'Small directory',
            'pattern': '*.py',
            'setup': lambda: create_test_files(100)
        },
        {
            'name': 'Large directory',
            'pattern': '**/*.py', 
            'setup': lambda: create_test_files(10000)
        },
        {
            'name': 'Content search',
            'pattern': '**/*.py',
            'content': 'def ',
            'setup': lambda: create_test_files(1000)
        }
    ]
    
    results = {}
    
    for scenario in test_scenarios:
        print(f"Testing: {scenario['name']}")
        
        # Setup
        test_dir = scenario['setup']()
        
        # Run multiple iterations
        times = []
        for i in range(5):
            start = time.perf_counter()
            
            if 'content' in scenario:
                list(vexy_glob.find(
                    scenario['pattern'],
                    content=scenario['content'],
                    root=test_dir
                ))
            else:
                list(vexy_glob.find(scenario['pattern'], root=test_dir))
            
            duration = time.perf_counter() - start
            times.append(duration)
        
        # Calculate statistics
        results[scenario['name']] = {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'min': min(times),
            'max': max(times)
        }
        
        # Cleanup
        cleanup_test_files(test_dir)
    
    # Print results
    print("\nPerformance Results:")
    print("-" * 50)
    for name, stats in results.items():
        print(f"{name}:")
        print(f"  Mean: {stats['mean']:.3f}s")
        print(f"  Median: {stats['median']:.3f}s")
        print(f"  Std Dev: {stats['stdev']:.3f}s")
        print(f"  Range: {stats['min']:.3f}s - {stats['max']:.3f}s")

def create_test_files(count):
    """Create test directory with specified number of files."""
    # Implementation depends on your testing needs
    pass

def cleanup_test_files(test_dir):
    """Clean up test directory."""
    # Implementation for cleanup
    pass
```

## Next Steps

You've learned how to troubleshoot common issues and implement best practices. The final chapter covers development and contributing:

→ **[Chapter 9: Development and Contributing](chapter9.md)** - Development setup, building from source, and contributing guidelines

---

!!! tip "Debugging Strategy"
    When encountering issues, start with the simplest possible case and gradually add complexity until you identify the problem.

!!! note "Performance Monitoring"
    Regularly monitor performance in your production environment. File system characteristics can change over time.

!!! warning "Security Considerations"
    Always validate patterns and paths when accepting user input. Malicious patterns can cause performance issues or access restricted areas.