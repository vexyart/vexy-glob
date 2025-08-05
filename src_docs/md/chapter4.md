---
# this_file: src_docs/md/chapter4.md
title: Chapter 4 - Advanced Features and Configuration
---

# Chapter 4: Advanced Features and Configuration

## Advanced Filtering

### Size-Based Filtering

vexy_glob supports human-readable size formats for easy filtering:

```python
import vexy_glob

# Find large files (over 10MB)
for path in vexy_glob.find("**/*", min_size=10 * 1024 * 1024):
    print(f"Large file: {path}")

# More convenient with size parsing utility
# (Note: This would require a parse_size helper function)
for path in vexy_glob.find("**/*", min_size=10485760):  # 10MB in bytes
    print(f"Large file: {path}")

# Find files in specific size range
for path in vexy_glob.find(
    "**/*.log",
    min_size=1024 * 1024,      # 1MB minimum
    max_size=100 * 1024 * 1024  # 100MB maximum
):
    print(f"Log file: {path}")
```

#### Size Format Examples

```python
# Common size calculations
SIZES = {
    "1KB": 1024,
    "1MB": 1024 * 1024,
    "1GB": 1024 * 1024 * 1024,
    "10MB": 10 * 1024 * 1024,
    "100MB": 100 * 1024 * 1024,
}

# Find files by category
small_files = vexy_glob.find("**/*", max_size=SIZES["1MB"], as_list=True)
large_files = vexy_glob.find("**/*", min_size=SIZES["100MB"], as_list=True)
```

### Time-Based Filtering

vexy_glob supports multiple time formats for flexible filtering:

#### Relative Time Formats

```python
import vexy_glob

# Files modified in the last 24 hours
recent_files = vexy_glob.find("**/*", mtime_after="-1d")

# Files accessed in the last hour
active_files = vexy_glob.find("**/*", atime_after="-1h")

# Files created in the last week
new_files = vexy_glob.find("**/*", ctime_after="-7d")

# Supported time units
examples = {
    "-30s": "30 seconds ago",
    "-5m": "5 minutes ago", 
    "-2h": "2 hours ago",
    "-7d": "7 days ago",
    "-2w": "2 weeks ago",
    "-1mo": "1 month ago (30 days)",
    "-1y": "1 year ago (365 days)"
}
```

#### Absolute Time Formats

```python
from datetime import datetime, timedelta
import time

# Using datetime objects
week_ago = datetime.now() - timedelta(weeks=1)
recent_files = vexy_glob.find("**/*", mtime_after=week_ago)

# Using Unix timestamps
hour_ago = time.time() - 3600
active_files = vexy_glob.find("**/*", atime_after=hour_ago)

# Using ISO date strings
files_since_2024 = vexy_glob.find("**/*", mtime_after="2024-01-01")
files_this_month = vexy_glob.find("**/*", mtime_after="2024-12-01")
```

#### Complex Time Filtering

```python
# Files modified between specific dates
for path in vexy_glob.find(
    "**/*.py",
    mtime_after="2024-01-01",
    mtime_before="2024-12-31"
):
    print(f"Modified in 2024: {path}")

# Files accessed recently but not modified (read-only usage)
for path in vexy_glob.find(
    "**/*",
    atime_after="-1d",     # Accessed in last day
    mtime_before="-7d"     # But not modified in last week
):
    print(f"Recently read: {path}")

# Old files that haven't been accessed (candidates for cleanup)
for path in vexy_glob.find(
    "**/*",
    mtime_before="-30d",   # Old files
    atime_before="-30d"    # Not accessed recently
):
    print(f"Cleanup candidate: {path}")
```

### Depth Control

Control how deep the search goes into directory structures:

```python
import vexy_glob

# Shallow search - only immediate subdirectories
shallow_files = vexy_glob.find("**/*.py", max_depth=2)

# Skip root directory - start from subdirectories
deep_files = vexy_glob.find("**/*.py", min_depth=1)

# Specific depth range
mid_level_files = vexy_glob.find("**/*.py", min_depth=2, max_depth=4)

# Example: Find configuration files in common locations
config_files = vexy_glob.find(
    "**/config.*",
    max_depth=3,  # Don't go too deep
    extension=["yml", "yaml", "json", "toml"]
)
```

### Advanced Pattern Combinations

#### Multiple Extension Patterns

```python
# Method 1: Using extension parameter (most efficient)
source_files = vexy_glob.find("**/*", extension=["py", "js", "ts", "rs"])

# Method 2: Using glob braces
source_files = vexy_glob.find("**/*.{py,js,ts,rs}")

# Method 3: Multiple patterns with OR logic
patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.rs"]
source_files = []
for pattern in patterns:
    source_files.extend(vexy_glob.find(pattern, as_list=True))
```

#### Complex Directory Patterns

```python
# Multiple source directories
src_files = vexy_glob.find("{src,lib,app}/**/*.py")

# Exclude test directories but include nested source
production_code = vexy_glob.find(
    "**/*.py",
    exclude=["**/test/**", "**/tests/**", "**/*_test.py", "**/test_*.py"]
)

# Find files in specific subdirectory patterns
component_files = vexy_glob.find("**/components/**/*.{js,ts,tsx}")
```

## Performance Optimization

### Thread Configuration

vexy_glob automatically optimizes thread usage, but you can tune it for specific scenarios:

```python
import os
import vexy_glob

# Auto-detection (default - recommended)
files = vexy_glob.find("**/*.py")

# Explicit thread control
cpu_count = os.cpu_count() or 4

# I/O bound operations: More threads than CPUs
for path in vexy_glob.find("**/*", threads=cpu_count * 2):
    pass

# CPU bound operations: Match CPU count
for match in vexy_glob.find("**/*.py", content="complex.*regex", threads=cpu_count):
    pass

# Single-threaded for debugging or specific requirements
for path in vexy_glob.find("**/*", threads=1):
    pass
```

### Memory Management

#### Streaming vs Batch Processing

```python
# Memory efficient: Process results as they arrive
def process_large_directory():
    for path in vexy_glob.find("**/*"):
        # Process one file at a time
        result = process_file(path)
        yield result

# Memory intensive: Load all results first
def batch_process_directory():
    all_files = vexy_glob.find("**/*", as_list=True)  # Uses more memory
    return [process_file(path) for path in all_files]

# Hybrid approach: Process in chunks
def chunked_process_directory(chunk_size=1000):
    files = vexy_glob.find("**/*")
    chunk = []
    
    for path in files:
        chunk.append(path)
        if len(chunk) >= chunk_size:
            yield process_chunk(chunk)
            chunk = []
    
    if chunk:  # Process remaining files
        yield process_chunk(chunk)
```

#### Early Termination

```python
# Stop search when condition is met
def find_first_large_file():
    for path in vexy_glob.find("**/*", min_size=100 * 1024 * 1024):
        return path  # Return immediately on first match
    return None

# Find a specific number of matches
def find_n_python_files(n=10):
    count = 0
    results = []
    for path in vexy_glob.find("**/*.py"):
        results.append(path)
        count += 1
        if count >= n:
            break
    return results
```

### Caching and Reuse

#### Pattern Optimization

```python
# Cache common exclusion patterns
COMMON_EXCLUDES = [
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/.git/**",
    "**/build/**",
    "**/dist/**",
    "**/.venv/**",
    "**/venv/**"
]

# Reuse compiled patterns
def find_source_files(root=".", language="python"):
    language_patterns = {
        "python": "**/*.py",
        "javascript": "**/*.{js,ts,jsx,tsx}",
        "rust": "**/*.rs",
        "go": "**/*.go"
    }
    
    return vexy_glob.find(
        language_patterns[language],
        root=root,
        exclude=COMMON_EXCLUDES,
        as_list=True
    )
```

## Advanced Content Search Features

### Multi-Pattern Content Search

```python
# Search for multiple patterns with OR logic
security_patterns = r"password|secret|token|api_key|private_key"
for match in vexy_glob.find("**/*.py", content=security_patterns):
    print(f"Security concern: {match.path}:{match.line_number}")

# Search for function definitions and class definitions
definitions = r"(def|class)\s+\w+"
for match in vexy_glob.find("**/*.py", content=definitions):
    print(f"Definition: {match.path}:{match.line_number}")
```

### Content Search with File Filtering

```python
# Search in specific file types only
for match in vexy_glob.find(
    "**/*", 
    content="TODO",
    extension=["py", "js", "rs", "go"]
):
    print(f"TODO in {match.path}:{match.line_number}")

# Search in recently modified files only
for match in vexy_glob.find(
    "**/*.py",
    content=r"import\s+\w+",
    mtime_after="-7d"
):
    print(f"Recent import: {match.path}")

# Search excluding certain directories
for match in vexy_glob.find(
    "**/*.py",
    content="deprecated",
    exclude=["**/tests/**", "**/vendor/**"]
):
    print(f"Deprecated code: {match.path}")
```

### Advanced Regex Patterns

```python
# Function definitions with parameters
func_pattern = r"def\s+(\w+)\s*\([^)]*\):"
for match in vexy_glob.find("**/*.py", content=func_pattern):
    print(f"Function: {match.matches[0]} in {match.path}")

# Import statements
import_pattern = r"^(from\s+\w+\s+)?import\s+([\w,\s]+)"
for match in vexy_glob.find("**/*.py", content=import_pattern):
    print(f"Import: {match.line_text.strip()}")

# URL patterns
url_pattern = r"https?://[^\s<>\"'`]+"
for match in vexy_glob.find("**/*.{py,js,md}", content=url_pattern):
    print(f"URL found: {match.path}:{match.line_number}")

# Configuration keys
config_pattern = r"^\s*([A-Z_]+)\s*=\s*"
for match in vexy_glob.find("**/*.py", content=config_pattern):
    print(f"Config: {match.matches[0]} in {match.path}")
```

## Custom Ignore Files

### Using .fdignore and Custom Ignore Files

```python
# vexy_glob automatically respects .gitignore, .fdignore, and .ignore files

# Add custom ignore files
for path in vexy_glob.find(
    "**/*",
    custom_ignore_files=[".myignore", "project.ignore"]
):
    print(path)

# Multiple custom ignore files
ignore_files = [
    ".dockerignore",
    ".eslintignore", 
    ".prettierignore",
    "custom.ignore"
]

for path in vexy_glob.find("**/*", custom_ignore_files=ignore_files):
    print(path)
```

### Creating Custom Ignore Patterns

```python
# Example .myignore file content:
"""
# Ignore build artifacts
build/
dist/
*.egg-info/

# Ignore logs
*.log
logs/

# Ignore temporary files  
*.tmp
*.temp
.DS_Store
Thumbs.db

# Ignore IDE files
.vscode/
.idea/
*.swp
*.swo

# Ignore OS files
.Spotlight-V100
.Trashes
"""

# Use with vexy_glob
clean_files = vexy_glob.find("**/*", custom_ignore_files=[".myignore"])
```

## Sorting and Organization

### Built-in Sorting Options

```python
# Sort by filename
files_by_name = vexy_glob.find("**/*.py", sort="name", as_list=True)

# Sort by full path
files_by_path = vexy_glob.find("**/*.py", sort="path", as_list=True) 

# Sort by file size
files_by_size = vexy_glob.find("**/*.py", sort="size", as_list=True)

# Sort by modification time
files_by_mtime = vexy_glob.find("**/*.py", sort="mtime", as_list=True)
```

### Custom Sorting

```python
# Custom sorting after retrieval
files = vexy_glob.find("**/*.py", as_list=True)

# Sort by extension
files_by_ext = sorted(files, key=lambda p: os.path.splitext(p)[1])

# Sort by directory depth
files_by_depth = sorted(files, key=lambda p: p.count(os.sep))

# Sort by file size (requires stat calls)
import os
files_by_size = sorted(files, key=lambda p: os.path.getsize(p))
```

## Cross-Platform Considerations

### Path Handling

```python
import os
from pathlib import Path

# Cross-platform path construction
def find_in_subdir(subdir, pattern="*"):
    # Works on all platforms
    root = Path(subdir)
    return vexy_glob.find(pattern, root=root, as_path=True)

# Handle different path separators
def normalize_excludes(excludes):
    """Normalize exclude patterns for current platform."""
    if os.name == 'nt':  # Windows
        return [pattern.replace('/', '\\') for pattern in excludes]
    return excludes

# Platform-specific patterns
if os.name == 'nt':  # Windows
    system_files = vexy_glob.find("**/*.{dll,exe,sys}")
else:  # Unix-like
    system_files = vexy_glob.find("**/*.{so,dylib}")
```

### Case Sensitivity

```python
# Handle platform differences in case sensitivity
import platform

def case_aware_search(pattern, **kwargs):
    """Search with appropriate case sensitivity for platform."""
    system = platform.system().lower()
    
    if system == 'darwin':  # macOS - usually case-insensitive
        kwargs.setdefault('case_sensitive', False)
    elif system == 'windows':  # Windows - case-insensitive
        kwargs.setdefault('case_sensitive', False)
    else:  # Linux and others - case-sensitive
        kwargs.setdefault('case_sensitive', True)
    
    return vexy_glob.find(pattern, **kwargs)
```

## Integration Patterns

### Database Integration

```python
import sqlite3
from pathlib import Path

def index_files_to_database(root_dir):
    """Index file metadata into SQLite database."""
    conn = sqlite3.connect('file_index.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            size INTEGER,
            mtime REAL,
            extension TEXT
        )
    ''')
    
    for path in vexy_glob.find("**/*", root=root_dir, file_type="f", as_path=True):
        stat = path.stat()
        conn.execute(
            'INSERT OR REPLACE INTO files VALUES (?, ?, ?, ?)',
            (str(path), stat.st_size, stat.st_mtime, path.suffix)
        )
    
    conn.commit()
    conn.close()
```

### Configuration Management

```python
import json
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class SearchConfig:
    """Configuration for common search patterns."""
    name: str
    pattern: str
    exclude: Optional[List[str]] = None
    extension: Optional[List[str]] = None
    max_depth: Optional[int] = None
    
    def search(self, root=".", **kwargs):
        """Execute search with this configuration."""
        params = {
            'pattern': self.pattern,
            'root': root,
            'exclude': self.exclude,
            'extension': self.extension,
            'max_depth': self.max_depth,
            **kwargs
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        return vexy_glob.find(**params)

# Predefined configurations
SEARCH_CONFIGS = {
    'python_source': SearchConfig(
        name='Python Source Files',
        pattern='**/*.py',
        exclude=['**/__pycache__/**', '**/venv/**', '**/.venv/**']
    ),
    'web_assets': SearchConfig(
        name='Web Assets',
        pattern='**/*',
        extension=['js', 'css', 'html', 'tsx', 'jsx'],
        exclude=['**/node_modules/**', '**/build/**']
    ),
    'config_files': SearchConfig(
        name='Configuration Files',
        pattern='**/*',
        extension=['yml', 'yaml', 'json', 'toml', 'ini'],
        max_depth=3
    )
}

# Usage
python_files = SEARCH_CONFIGS['python_source'].search('.')
```

## Next Steps

Now that you understand advanced features, explore performance optimization and real-world examples:

→ **[Chapter 5: Performance Optimization and Benchmarks](chapter5.md)** - Deep dive into performance

→ **[Chapter 6: Content Search and Filtering](chapter6.md)** - Advanced regex patterns and search techniques

→ **[Chapter 7: Integration and Examples](chapter7.md)** - Real-world usage patterns and cookbook recipes

---

!!! tip "Performance Tip"
    Use built-in filtering (extension, size, time) instead of filtering results afterwards. This allows vexy_glob to skip files early in the process.

!!! note "Thread Tuning"
    For I/O-heavy operations (large directories), use more threads than CPU cores. For CPU-heavy operations (complex regex), match thread count to CPU cores.

!!! warning "Memory Usage"
    When using `sort` parameter, results must be collected before sorting, which uses more memory. Use streaming for large result sets when possible.