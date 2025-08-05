---
# this_file: src_docs/md/chapter6.md
title: Chapter 6 - Content Search and Filtering
---

# Chapter 6: Content Search and Filtering

## Content Search Overview

vexy_glob's content search capability is powered by the same high-performance `grep-searcher` crate that powers `ripgrep`, providing blazing-fast regex-based text search within files. This integration makes vexy_glob a powerful tool for code analysis, log processing, and text mining.

### Key Features

- **High-performance regex engine** with SIMD optimizations
- **Streaming results** - process matches as they're found
- **Smart case detection** - automatic case sensitivity
- **Binary file detection** - automatically skips binary files
- **Rich match information** - line numbers, text, and captured groups

## Basic Content Search

### Simple Text Search

```python
import vexy_glob

# Find all TODO comments in Python files
for match in vexy_glob.find("**/*.py", content="TODO"):
    print(f"{match.path}:{match.line_number}: {match.line_text.strip()}")

# Find import statements
for match in vexy_glob.find("**/*.py", content="import"):
    print(f"Import in {match.path}: {match.line_text.strip()}")

# Case-insensitive search
for match in vexy_glob.find("**/*.md", content="python", case_sensitive=False):
    print(f"Python mention: {match.path}:{match.line_number}")
```

### SearchResult Object

The `SearchResult` object provides detailed information about each match:

```python
class SearchResult(TypedDict):
    path: Union[str, Path]      # File path containing the match
    line_number: int            # Line number (1-indexed)
    line_text: str              # Complete line text
    matches: List[str]          # List of matched strings/groups
```

#### Working with SearchResult

```python
# Access all match information
for match in vexy_glob.find("**/*.py", content=r"def (\w+)"):
    print(f"File: {match.path}")
    print(f"Line: {match.line_number}")
    print(f"Text: {match.line_text.strip()}")
    print(f"Function name: {match.matches[0]}")  # Captured group
    print("---")
```

## Regular Expression Patterns

### Basic Regex Syntax

vexy_glob uses standard regex syntax for content search:

| Pattern | Description | Example |
|---------|-------------|---------|
| `.` | Any character | `f.r` matches `for`, `far` |
| `*` | Zero or more | `ab*` matches `a`, `ab`, `abb` |
| `+` | One or more | `ab+` matches `ab`, `abb` |
| `?` | Zero or one | `ab?` matches `a`, `ab` |
| `^` | Start of line | `^import` matches imports at line start |
| `$` | End of line | `);$` matches lines ending with `);` |
| `\b` | Word boundary | `\bclass\b` matches `class` but not `subclass` |
| `\d` | Any digit | `\d+` matches `123`, `456` |
| `\w` | Word character | `\w+` matches `hello`, `world123` |
| `\s` | Whitespace | `\s+` matches spaces, tabs, newlines |

### Common Search Patterns

#### Programming Language Patterns

```python
# Python-specific patterns
patterns = {
    "function_definitions": r"def\s+(\w+)\s*\(",
    "class_definitions": r"class\s+(\w+).*:",
    "import_statements": r"^(from\s+\w+\s+)?import\s+([\w,\s]+)",
    "decorators": r"@\w+",
    "string_literals": r'"[^"]*"|\'[^\']*\'',
    "comments": r"#.*$",
    "todo_comments": r"#.*TODO.*$",
    "async_functions": r"async\s+def\s+(\w+)",
    "error_handling": r"except\s+(\w+):"
}

# Usage examples
for match in vexy_glob.find("**/*.py", content=patterns["function_definitions"]):
    print(f"Function '{match.matches[0]}' in {match.path}:{match.line_number}")

for match in vexy_glob.find("**/*.py", content=patterns["import_statements"]):
    print(f"Import: {match.line_text.strip()}")
```

#### Web Development Patterns

```python
# JavaScript/TypeScript patterns
js_patterns = {
    "function_declarations": r"function\s+(\w+)\s*\(",
    "arrow_functions": r"(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>",
    "react_components": r"(?:const|function)\s+([A-Z]\w*)\s*[:=]",
    "imports": r"import\s+.*from\s+['\"]([^'\"]+)['\"]",
    "console_logs": r"console\.(log|error|warn|info)\s*\(",
    "api_calls": r"(?:fetch|axios)\s*\(",
    "event_listeners": r"addEventListener\s*\(\s*['\"](\w+)['\"]"
}

# Find React components
for match in vexy_glob.find("**/*.{js,jsx,ts,tsx}", content=js_patterns["react_components"]):
    print(f"Component: {match.matches[0]} in {match.path}")
```

#### Configuration and Data Patterns

```python
# Configuration file patterns
config_patterns = {
    "yaml_keys": r"^(\w+):\s*",
    "json_properties": r'"(\w+)"\s*:\s*',
    "env_variables": r"^([A-Z_]+)=",
    "urls": r"https?://[^\s<>\"'`]+",
    "email_addresses": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "ip_addresses": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "version_numbers": r"\bv?\d+\.\d+\.\d+\b"
}

# Find configuration keys
for match in vexy_glob.find("**/*.yml", content=config_patterns["yaml_keys"]):
    print(f"Config key: {match.matches[0]}")
```

### Advanced Regex Features

#### Capture Groups

```python
# Named capture groups
pattern = r"(?P<method>GET|POST|PUT|DELETE)\s+(?P<path>/\S+)"
for match in vexy_glob.find("**/*.log", content=pattern):
    print(f"HTTP {match.matches[0]} {match.matches[1]}")

# Multiple capture groups
pattern = r"([A-Z]+)\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})"
for match in vexy_glob.find("**/*.log", content=pattern):
    level, date, time = match.matches
    print(f"Log entry: {level} at {date} {time}")
```

#### Lookahead and Lookbehind

```python
# Positive lookahead - find TODO not followed by DONE
todo_pattern = r"TODO(?!\s+DONE)"
for match in vexy_glob.find("**/*.py", content=todo_pattern):
    print(f"Open TODO: {match.path}:{match.line_number}")

# Negative lookbehind - find function calls not preceded by def
call_pattern = r"(?<!def\s)\w+\s*\("
for match in vexy_glob.find("**/*.py", content=call_pattern):
    print(f"Function call: {match.path}:{match.line_number}")
```

#### Word Boundaries and Anchors

```python
# Exact word matching
word_pattern = r"\bclass\b"  # Matches "class" but not "subclass"
for match in vexy_glob.find("**/*.py", content=word_pattern):
    print(f"Class keyword: {match.path}:{match.line_number}")

# Line anchors
start_pattern = r"^def\s+"  # Functions at start of line only
end_pattern = r";\s*$"      # Lines ending with semicolon

# Multi-line patterns (when supported)
block_pattern = r"try:.*?except:"  # Try-except blocks
```

## Content Search with File Filtering

### Combining Content and File Filters

```python
# Search in specific file types only
for match in vexy_glob.find(
    "**/*",
    content="password",
    extension=["py", "js", "java", "cpp"],
    exclude=["**/test/**", "**/vendor/**"]
):
    print(f"Security concern: {match.path}:{match.line_number}")

# Search in recently modified files
for match in vexy_glob.find(
    "**/*.py",
    content=r"TODO|FIXME|XXX",
    mtime_after="-7d",  # Last week only
    min_size=100        # Skip very small files
):
    print(f"Recent action item: {match.path}:{match.line_number}")

# Search in large files only
for match in vexy_glob.find(
    "**/*.log",
    content="ERROR",
    min_size=1024*1024,  # 1MB+
    max_size=100*1024*1024  # <100MB
):
    print(f"Error in large log: {match.path}:{match.line_number}")
```

### Performance-Optimized Searches

```python
# Efficient pattern for specific directories
for match in vexy_glob.find(
    "src/**/*.py",  # Specific location
    content=r"def\s+test_",  # Test functions
    max_depth=3,    # Limit recursion
    exclude=["**/__pycache__/**"]
):
    print(f"Test function: {match.path}:{match.line_number}")

# Time-bounded search for analysis
import time

def search_with_timeout(pattern, content_pattern, timeout=30):
    start_time = time.time()
    matches = []
    
    for match in vexy_glob.find(pattern, content=content_pattern):
        matches.append(match)
        if time.time() - start_time > timeout:
            print(f"Search timeout reached, found {len(matches)} matches")
            break
    
    return matches
```

## Advanced Content Search Techniques

### Multi-Pattern Searches

```python
# OR patterns - find any of multiple patterns
security_patterns = r"password|secret|token|api_key|private_key|auth"
for match in vexy_glob.find("**/*.py", content=security_patterns):
    print(f"Security keyword: {match.path}:{match.line_number}")

# AND simulation - find files containing multiple patterns
def find_files_with_all_patterns(file_pattern, content_patterns):
    """Find files that contain ALL specified patterns."""
    file_matches = {}
    
    # Search for each pattern
    for pattern in content_patterns:
        for match in vexy_glob.find(file_pattern, content=pattern):
            if match.path not in file_matches:
                file_matches[match.path] = set()
            file_matches[match.path].add(pattern)
    
    # Return files that match ALL patterns
    return [path for path, patterns in file_matches.items() 
            if len(patterns) == len(content_patterns)]

# Usage
files_with_auth = find_files_with_all_patterns(
    "**/*.py", 
    ["import", "password", "login"]
)
```

### Context-Aware Searching

```python
# Search within specific code blocks
class_method_pattern = r"(?<=class\s+\w+.*?:).*?def\s+(\w+)"
for match in vexy_glob.find("**/*.py", content=class_method_pattern):
    print(f"Method: {match.matches[0]}")

# Search for patterns near other patterns
def find_nearby_patterns(file_pattern, target_pattern, context_pattern, max_distance=5):
    """Find target patterns near context patterns."""
    results = []
    
    # Get all target matches
    target_matches = {}
    for match in vexy_glob.find(file_pattern, content=target_pattern):
        if match.path not in target_matches:
            target_matches[match.path] = []
        target_matches[match.path].append(match.line_number)
    
    # Get all context matches
    for match in vexy_glob.find(file_pattern, content=context_pattern):
        if match.path in target_matches:
            # Check if any target is within max_distance
            for target_line in target_matches[match.path]:
                if abs(target_line - match.line_number) <= max_distance:
                    results.append({
                        'path': match.path,
                        'target_line': target_line,
                        'context_line': match.line_number,
                        'distance': abs(target_line - match.line_number)
                    })
    
    return results

# Find TODO comments near function definitions
nearby_todos = find_nearby_patterns("**/*.py", "TODO", r"def\s+\w+", max_distance=3)
```

### Code Analysis Patterns

```python
# Detect code smells and patterns
code_analysis_patterns = {
    "long_lines": r".{120,}",  # Lines over 120 characters
    "multiple_returns": r"return\s+.*",  # Count returns per function
    "nested_loops": r"\s+(for|while)\s+.*:\s*\n\s+(for|while)",
    "magic_numbers": r"\b\d{2,}\b",  # Numbers with 2+ digits
    "print_debugging": r"print\s*\(",
    "commented_code": r"#\s*(def|class|if|for|while)",
    "long_parameter_lists": r"def\s+\w+\s*\([^)]{50,}\)",
    "duplicate_strings": r'"[^"]{10,}"',  # Long string literals
}

def analyze_code_quality(directory):
    """Analyze code quality metrics."""
    metrics = {}
    
    for name, pattern in code_analysis_patterns.items():
        matches = list(vexy_glob.find(
            "**/*.py", 
            content=pattern,
            root=directory,
            exclude=["**/test/**", "**/vendor/**"]
        ))
        metrics[name] = len(matches)
        
        if name == "long_lines":
            print(f"Long lines found: {len(matches)}")
            for match in matches[:5]:  # Show first 5
                print(f"  {match.path}:{match.line_number}")
    
    return metrics
```

### Log Analysis Patterns

```python
# Log file analysis patterns
log_patterns = {
    "error_levels": r"(ERROR|FATAL|CRITICAL)",
    "timestamps": r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}",
    "ip_addresses": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "http_methods": r"(GET|POST|PUT|DELETE|HEAD|OPTIONS)\s+",
    "status_codes": r"\s(2\d{2}|3\d{2}|4\d{2}|5\d{2})\s",
    "user_agents": r"Mozilla/[^\"]+",
    "sql_queries": r"(SELECT|INSERT|UPDATE|DELETE)\s+",
    "stack_traces": r"Traceback|Exception|Error:",
}

def analyze_logs(log_directory, time_range="-1d"):
    """Analyze log files for patterns and anomalies."""
    analysis = {}
    
    # Find recent error logs
    error_matches = vexy_glob.find(
        "**/*.log",
        content=log_patterns["error_levels"],
        root=log_directory,
        mtime_after=time_range,
        as_list=True
    )
    
    # Group errors by type and file
    error_summary = {}
    for match in error_matches:
        key = f"{match.path}:{match.matches[0]}"
        error_summary[key] = error_summary.get(key, 0) + 1
    
    # Find unusual status codes
    bad_status = vexy_glob.find(
        "**/*.log",
        content=r"\s(4\d{2}|5\d{2})\s",
        root=log_directory,
        mtime_after=time_range,
        as_list=True
    )
    
    return {
        'total_errors': len(error_matches),
        'error_breakdown': error_summary,
        'bad_requests': len(bad_status),
        'files_analyzed': len(set(m.path for m in error_matches + bad_status))
    }
```

## Content Search Best Practices

### Performance Optimization

```python
# ✅ Efficient: Specific file patterns
vexy_glob.find("src/**/*.py", content="pattern")

# ❌ Inefficient: Too broad
vexy_glob.find("**/*", content="pattern")

# ✅ Efficient: Use file type filtering
vexy_glob.find("**/*", content="pattern", extension=["py", "js"])

# ❌ Inefficient: Search all files
vexy_glob.find("**/*", content="pattern")

# ✅ Efficient: Exclude large directories
vexy_glob.find("**/*.py", content="pattern", exclude=["**/venv/**"])

# ✅ Efficient: Use time filters for large datasets
vexy_glob.find("**/*.log", content="ERROR", mtime_after="-1d")
```

### Pattern Design

```python
# ✅ Good: Specific patterns
r"def\s+\w+\s*\("  # Function definitions

# ❌ Bad: Too greedy
r".*def.*"  # Matches too much

# ✅ Good: Use anchors when appropriate
r"^import\s+\w+"  # Imports at line start

# ✅ Good: Use word boundaries
r"\bclass\b"  # Exact word "class"

# ❌ Bad: No boundaries
r"class"  # Matches "subclass", "classes", etc.
```

### Error Handling

```python
import vexy_glob
from vexy_glob import VexyGlobError, PatternError

def safe_content_search(pattern, content, **kwargs):
    """Safely perform content search with error handling."""
    try:
        return list(vexy_glob.find(pattern, content=content, **kwargs))
    except PatternError as e:
        print(f"Invalid pattern: {e}")
        return []
    except VexyGlobError as e:
        print(f"Search error: {e}")
        return []

# Test regex pattern before using
import re

def validate_regex(pattern):
    """Validate regex pattern before using in search."""
    try:
        re.compile(pattern)
        return True
    except re.error as e:
        print(f"Invalid regex: {e}")
        return False

if validate_regex(r"def\s+(\w+)"):
    matches = vexy_glob.find("**/*.py", content=r"def\s+(\w+)")
```

## Next Steps

Now that you understand content search and filtering, explore real-world integration examples:

→ **[Chapter 7: Integration and Examples](chapter7.md)** - Practical recipes and integration patterns

→ **[Chapter 8: Troubleshooting and Best Practices](chapter8.md)** - Common issues and solutions

---

!!! tip "Regex Performance"
    Simple literal patterns are fastest. Use anchors (`^`, `$`) and word boundaries (`\b`) to make patterns more specific and improve performance.

!!! note "Binary Files"
    vexy_glob automatically detects and skips binary files during content search. This prevents false matches and improves performance.

!!! warning "Complex Patterns"
    Very complex regex patterns may be slower than simple ones. Consider breaking complex searches into multiple simpler searches when performance is critical.