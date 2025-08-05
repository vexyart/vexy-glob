---
# this_file: src_docs/md/chapter3.md
title: Chapter 3 - Basic Usage and API Reference
---

# Chapter 3: Basic Usage and API Reference

## Core Functions

vexy_glob provides several functions for file operations, with `find()` being the primary and most powerful function.

### The `find()` Function

The `find()` function is the heart of vexy_glob, providing both file discovery and content search capabilities.

#### Basic Syntax

```python
import vexy_glob

def find(
    pattern: str = "*",
    root: Union[str, Path] = ".",
    *,
    content: Optional[str] = None,
    file_type: Optional[str] = None,
    extension: Optional[Union[str, List[str]]] = None,
    exclude: Optional[Union[str, List[str]]] = None,
    max_depth: Optional[int] = None,
    min_depth: int = 0,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    mtime_after: Optional[Union[float, int, str, datetime]] = None,
    mtime_before: Optional[Union[float, int, str, datetime]] = None,
    atime_after: Optional[Union[float, int, str, datetime]] = None,
    atime_before: Optional[Union[float, int, str, datetime]] = None,
    ctime_after: Optional[Union[float, int, str, datetime]] = None,
    ctime_before: Optional[Union[float, int, str, datetime]] = None,
    hidden: bool = False,
    ignore_git: bool = False,
    case_sensitive: Optional[bool] = None,
    follow_symlinks: bool = False,
    threads: Optional[int] = None,
    as_path: bool = False,
    as_list: bool = False,
) -> Union[Iterator[Union[str, Path, SearchResult]], List[Union[str, Path, SearchResult]]]:
```

#### Parameters

=== "Basic Parameters"
    - **`pattern`** (str): Glob pattern to match files (default: "*")
    - **`root`** (str | Path): Starting directory (default: current directory)
    - **`content`** (str, optional): Regex pattern to search within files
    - **`as_path`** (bool): Return Path objects instead of strings
    - **`as_list`** (bool): Return list instead of iterator

=== "Filtering Parameters"
    - **`file_type`** (str, optional): Filter by 'f' (files), 'd' (directories), 'l' (symlinks)
    - **`extension`** (str | List[str], optional): Filter by file extension(s)
    - **`exclude`** (str | List[str], optional): Patterns to exclude
    - **`min_size`** (int, optional): Minimum file size in bytes
    - **`max_size`** (int, optional): Maximum file size in bytes

=== "Time Parameters"
    - **`mtime_after`** / **`mtime_before`**: Modified time filters
    - **`atime_after`** / **`atime_before`**: Access time filters  
    - **`ctime_after`** / **`ctime_before`**: Creation time filters
    
    Time formats: Unix timestamp, datetime object, ISO date, relative time (-1d, -2h, etc.)

=== "Behavior Parameters"
    - **`max_depth`** (int, optional): Maximum directory depth
    - **`min_depth`** (int): Minimum directory depth (default: 0)
    - **`hidden`** (bool): Include hidden files (default: False)
    - **`ignore_git`** (bool): Ignore .gitignore rules (default: False)
    - **`case_sensitive`** (bool, optional): Case sensitivity (None = smart case)
    - **`follow_symlinks`** (bool): Follow symbolic links (default: False)
    - **`threads`** (int, optional): Number of threads (None = auto)

## Basic Examples

### Simple File Finding

```python
import vexy_glob

# Find all files in current directory
for path in vexy_glob.find():
    print(path)

# Find all Python files
for path in vexy_glob.find("*.py"):
    print(path)

# Find all Python files recursively
for path in vexy_glob.find("**/*.py"):
    print(path)

# Get results as a list
python_files = vexy_glob.find("**/*.py", as_list=True)
print(f"Found {len(python_files)} Python files")
```

### Working with Path Objects

```python
from pathlib import Path
import vexy_glob

# Get Path objects instead of strings
for path in vexy_glob.find("**/*.py", as_path=True):
    print(f"File: {path.name}, Size: {path.stat().st_size} bytes")
    print(f"Parent: {path.parent}")
```

### Directory-Specific Searches

```python
# Search in specific directory
for path in vexy_glob.find("*.py", root="src"):
    print(path)

# Search multiple extensions
for path in vexy_glob.find("**/*.{py,js,ts}"):
    print(path)

# Using extension parameter (more efficient)
for path in vexy_glob.find("**/*", extension=["py", "js", "ts"]):
    print(path)
```

## Pattern Matching

### Glob Pattern Syntax

vexy_glob supports advanced glob patterns:

| Pattern | Description | Example |
|---------|-------------|---------|
| `*` | Matches any characters except `/` | `*.py` → `test.py` |
| `**` | Matches any characters including `/` | `**/*.py` → `src/lib/test.py` |
| `?` | Matches exactly one character | `test?.py` → `test1.py` |
| `[seq]` | Matches any character in sequence | `test[123].py` → `test2.py` |
| `[!seq]` | Matches any character not in sequence | `test[!0].py` → `test1.py` |
| `{a,b}` | Matches either pattern a or b | `*.{py,js}` → both `.py` and `.js` |

### Pattern Examples

```python
import vexy_glob

# Complex patterns
vexy_glob.find("src/**/*.{py,pyi,pyx}")        # Multiple extensions
vexy_glob.find("**/test_*.py")                 # Prefix matching  
vexy_glob.find("**/*[0-9].log")               # Numbered log files
vexy_glob.find("docs/**/*.{md,rst}")          # Documentation files
vexy_glob.find("{src,tests}/**/*.py")         # Multiple directories

# Character classes
vexy_glob.find("**/*[0-9][0-9].txt")          # Two-digit numbers
vexy_glob.find("**/*[a-z].py")                # Ending with lowercase
vexy_glob.find("**/[A-Z]*.py")                # Starting with uppercase
```

### Smart Case Detection

By default, vexy_glob uses smart case sensitivity:

```python
# Case-insensitive (no uppercase in pattern)
vexy_glob.find("readme.md")      # Finds README.md, readme.md, ReadMe.md

# Case-sensitive (contains uppercase)  
vexy_glob.find("README.md")      # Only finds exact match README.md

# Force case sensitivity
vexy_glob.find("readme.md", case_sensitive=True)   # Only finds readme.md
vexy_glob.find("readme.md", case_sensitive=False)  # Case-insensitive
```

## File Type and Extension Filtering

### File Type Filtering

```python
import vexy_glob

# Only files
for path in vexy_glob.find("**/*", file_type="f"):
    print(f"File: {path}")

# Only directories
for path in vexy_glob.find("**/*", file_type="d"):
    print(f"Directory: {path}")

# Only symbolic links
for path in vexy_glob.find("**/*", file_type="l"):
    print(f"Symlink: {path}")
```

### Extension Filtering

```python
# Single extension
vexy_glob.find("**/*", extension="py")

# Multiple extensions
vexy_glob.find("**/*", extension=["py", "pyi", "pyx"])

# Case-insensitive extensions
vexy_glob.find("**/*", extension=["jpg", "JPEG", "png"], case_sensitive=False)
```

## Content Search

When you provide a `content` parameter, `find()` searches within files and returns `SearchResult` objects.

### SearchResult Object

```python
class SearchResult(TypedDict):
    path: Union[str, Path]      # Path to the file
    line_number: int            # Line number (1-indexed) 
    line_text: str              # Full line text
    matches: List[str]          # Matched strings
```

### Basic Content Search

```python
import vexy_glob

# Find TODO comments
for match in vexy_glob.find("**/*.py", content="TODO"):
    print(f"{match.path}:{match.line_number}: {match.line_text.strip()}")

# Find function definitions
for match in vexy_glob.find("**/*.py", content=r"def \w+\("):
    print(f"Function at {match.path}:{match.line_number}")

# Find import statements
for match in vexy_glob.find("**/*.py", content=r"^import \w+"):
    print(f"Import: {match.matches[0]} in {match.path}")
```

### Advanced Content Search

```python
# Search with OR patterns
for match in vexy_glob.find("**/*.py", content=r"TODO|FIXME|XXX"):
    print(f"Action item: {match.path}:{match.line_number}")

# Search for patterns with capture groups
for match in vexy_glob.find("**/*.py", content=r"class (\w+)"):
    print(f"Class {match.matches[0]} in {match.path}")

# Case-insensitive content search
for match in vexy_glob.find("**/*.md", content="python", case_sensitive=False):
    print(f"Python mention: {match.path}")
```

## Exclusion Patterns

### Basic Exclusions

```python
import vexy_glob

# Exclude single pattern
vexy_glob.find("**/*.py", exclude="*test*")

# Exclude multiple patterns
exclusions = [
    "**/__pycache__/**",
    "**/node_modules/**", 
    "**/.git/**",
    "**/build/**",
    "**/dist/**"
]
vexy_glob.find("**/*", exclude=exclusions)
```

### Common Exclusion Patterns

```python
# Python project exclusions
PYTHON_EXCLUDES = [
    "**/__pycache__/**",
    "**/*.pyc",
    "**/.pytest_cache/**",
    "**/.mypy_cache/**",
    "**/venv/**",
    "**/.venv/**",
    "**/build/**",
    "**/dist/**"
]

# Web project exclusions  
WEB_EXCLUDES = [
    "**/node_modules/**",
    "**/build/**",
    "**/dist/**",
    "**/.next/**",
    "**/coverage/**"
]

# Find clean source files
for path in vexy_glob.find("**/*.py", exclude=PYTHON_EXCLUDES):
    print(path)
```

## Drop-in Replacements

### `glob()` and `iglob()`

vexy_glob provides drop-in replacements for standard library functions:

```python
import vexy_glob

# Instead of: import glob
# Use:        import vexy_glob as glob

# glob.glob() replacement
files = vexy_glob.glob("**/*.py", recursive=True)

# glob.iglob() replacement  
for path in vexy_glob.iglob("**/*.py", recursive=True):
    print(path)

# With additional options
files = vexy_glob.glob("*.py", include_hidden=True)
```

### Migration Example

```python
# OLD: Standard library
import glob
files = glob.glob("**/*.py", recursive=True)

# NEW: Just change the import!
import vexy_glob as glob  
files = glob.glob("**/*.py", recursive=True)  # 10-100x faster!
```

## Iterator vs List Results

### Streaming (Default)

By default, `find()` returns an iterator that streams results:

```python
# Memory efficient - processes one result at a time
for path in vexy_glob.find("**/*.py"):
    process_file(path)  # Process immediately
    
# Can break early to save time
for path in vexy_glob.find("**/*.py"):
    if path.endswith("target.py"):
        print(f"Found target: {path}")
        break  # Stops search immediately
```

### List Results

Use `as_list=True` when you need all results at once:

```python
# Get all results as a list
all_files = vexy_glob.find("**/*.py", as_list=True)
print(f"Found {len(all_files)} files")

# Useful for sorting, counting, or multiple iterations
files = vexy_glob.find("**/*.py", as_list=True)
files.sort()  # Sort alphabetically
for i, path in enumerate(files):
    print(f"{i+1}: {path}")
```

## Performance Tips

### Optimize Your Patterns

```python
# Slow: Too broad
vexy_glob.find("**/*.py")

# Fast: Be specific
vexy_glob.find("src/**/*.py")

# Faster: Limit depth when possible
vexy_glob.find("src/**/*.py", max_depth=3)
```

### Use Built-in Filtering

```python
# Slow: Filter after finding
files = []
for path in vexy_glob.find("**/*"):
    if path.endswith('.py') and os.path.getsize(path) > 1024:
        files.append(path)

# Fast: Use built-in filtering
files = vexy_glob.find("**/*.py", min_size=1024, as_list=True)
```

### Leverage Exclusions

```python
# Include exclusions to skip large directories
vexy_glob.find(
    "**/*.py",
    exclude=["**/node_modules/**", "**/.git/**", "**/venv/**"]
)
```

## Error Handling

### Exception Hierarchy

```python
from vexy_glob import VexyGlobError, PatternError, SearchError

try:
    results = vexy_glob.find("[invalid pattern")
except PatternError as e:
    print(f"Invalid pattern: {e}")
except SearchError as e:
    print(f"Search failed: {e}")
except VexyGlobError as e:
    print(f"General error: {e}")
```

### Common Error Scenarios

```python
import vexy_glob

# Handle invalid patterns
try:
    vexy_glob.find("[unclosed")
except vexy_glob.PatternError:
    print("Pattern syntax error")

# Handle permission errors
try:
    vexy_glob.find("**/*", root="/root")
except vexy_glob.SearchError:
    print("Permission denied or I/O error")

# Handle invalid regex in content search
try:
    vexy_glob.find("**/*.py", content="[invalid regex")
except vexy_glob.PatternError:
    print("Invalid regex pattern")
```

## Working with Different File Systems

### Symbolic Links

```python
# By default, symlinks are not followed
vexy_glob.find("**/*")

# Follow symlinks (be careful with loops)
vexy_glob.find("**/*", follow_symlinks=True)
```

### Hidden Files

```python
# Exclude hidden files (default)
vexy_glob.find("**/*")

# Include hidden files
vexy_glob.find("**/*", hidden=True)

# Find only hidden files
vexy_glob.find("**/.*", hidden=True)
```

### Git Integration

```python
# Respect .gitignore (default)
vexy_glob.find("**/*")

# Ignore .gitignore rules
vexy_glob.find("**/*", ignore_git=True)

# Find gitignored files specifically
all_files = set(vexy_glob.find("**/*", ignore_git=True, as_list=True))
tracked_files = set(vexy_glob.find("**/*", as_list=True))
gitignored_files = all_files - tracked_files
```

## Next Steps

Now that you understand the basic API, explore more advanced features:

→ **[Chapter 4: Advanced Features and Configuration](chapter4.md)** - Complex filtering and performance tuning

→ **[Chapter 5: Performance Optimization and Benchmarks](chapter5.md)** - Performance analysis and optimization

→ **[Chapter 6: Content Search and Filtering](chapter6.md)** - Advanced regex search and filtering

---

!!! tip "Best Practice"
    Always use the most specific pattern possible. `src/**/*.py` is much faster than `**/*.py` when you know the target directory.

!!! note "Memory Usage"
    Use iterators (default) for large result sets to maintain constant memory usage. Only use `as_list=True` when you need to access all results multiple times.

!!! warning "Pattern Syntax"
    vexy_glob uses standard glob patterns, not regular expressions. For content search, use the `content` parameter with regex patterns.