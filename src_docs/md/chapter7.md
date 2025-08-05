---
# this_file: src_docs/md/chapter7.md
title: Chapter 7 - Integration and Examples
---

# Chapter 7: Integration and Examples

## Real-World Usage Patterns

This chapter provides practical examples and cookbook recipes for integrating vexy_glob into real-world applications, from simple scripts to complex data processing pipelines.

## Development Tools Integration

### Code Analysis and Linting

```python
import vexy_glob
from collections import defaultdict
import re

class CodeAnalyzer:
    """Advanced code analysis using vexy_glob."""
    
    def __init__(self, project_root):
        self.project_root = project_root
        self.patterns = {
            'todo_comments': r'#.*?(?:TODO|FIXME|XXX|HACK).*',
            'function_defs': r'def\s+(\w+)\s*\(',
            'class_defs': r'class\s+(\w+).*:',
            'imports': r'^(?:from\s+\w+\s+)?import\s+([\w,\s]+)',
            'long_lines': r'.{120,}',
            'print_statements': r'print\s*\(',
            'magic_numbers': r'\b(?<![\w.])\d{2,}(?![\w.])\b',
        }
    
    def analyze_project(self):
        """Perform comprehensive project analysis."""
        results = {
            'summary': {},
            'details': defaultdict(list)
        }
        
        # Find all Python files excluding common build/cache directories
        python_files = vexy_glob.find(
            "**/*.py",
            root=self.project_root,
            exclude=[
                "**/__pycache__/**",
                "**/venv/**", 
                "**/.venv/**",
                "**/build/**",
                "**/dist/**"
            ],
            as_list=True
        )
        
        results['summary']['total_files'] = len(python_files)
        
        # Analyze each pattern
        for pattern_name, pattern in self.patterns.items():
            matches = list(vexy_glob.find(
                "**/*.py",
                content=pattern,
                root=self.project_root,
                exclude=[
                    "**/__pycache__/**",
                    "**/venv/**",
                    "**/.venv/**"
                ]
            ))
            
            results['summary'][pattern_name] = len(matches)
            results['details'][pattern_name] = matches[:10]  # First 10 matches
        
        return results
    
    def find_security_issues(self):
        """Find potential security issues in code."""
        security_patterns = {
            'hardcoded_secrets': r'(?i)(password|secret|token|key)\s*=\s*["\'][^"\']+["\']',
            'sql_injection': r'(?i)(query|execute)\s*\(\s*["\'].*%.*["\']',
            'shell_injection': r'(?i)(system|popen|subprocess)\s*\(',
            'eval_usage': r'(?i)eval\s*\(',
            'pickle_usage': r'(?i)pickle\.(loads|load)\s*\(',
        }
        
        issues = {}
        for issue_type, pattern in security_patterns.items():
            matches = list(vexy_glob.find(
                "**/*.py",
                content=pattern,
                root=self.project_root,
                exclude=["**/test/**", "**/tests/**"]
            ))
            if matches:
                issues[issue_type] = matches
        
        return issues
    
    def generate_report(self):
        """Generate a comprehensive analysis report."""
        analysis = self.analyze_project()
        security = self.find_security_issues()
        
        print(f"Code Analysis Report for {self.project_root}")
        print("=" * 50)
        print(f"Total Python files: {analysis['summary']['total_files']}")
        print(f"TODO comments: {analysis['summary']['todo_comments']}")
        print(f"Long lines (>120 chars): {analysis['summary']['long_lines']}")
        print(f"Print statements: {analysis['summary']['print_statements']}")
        print(f"Magic numbers: {analysis['summary']['magic_numbers']}")
        
        if security:
            print("\n⚠️ Security Issues Found:")
            for issue_type, matches in security.items():
                print(f"  {issue_type}: {len(matches)} occurrences")
        else:
            print("\n✅ No obvious security issues found")

# Usage
analyzer = CodeAnalyzer(".")
analyzer.generate_report()
```

### Documentation Generation

```python
import vexy_glob
import os
from pathlib import Path

class DocGenerator:
    """Generate documentation from code using vexy_glob."""
    
    def __init__(self, source_dir, output_dir):
        self.source_dir = source_dir
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def extract_docstrings(self):
        """Extract all docstrings from Python files."""
        docstring_pattern = r'"""([^"]*(?:"[^"]*)*?)"""'
        docstrings = {}
        
        for match in vexy_glob.find(
            "**/*.py",
            content=docstring_pattern,
            root=self.source_dir
        ):
            if match.path not in docstrings:
                docstrings[match.path] = []
            
            docstrings[match.path].append({
                'line': match.line_number,
                'content': match.matches[0] if match.matches else '',
                'context': match.line_text.strip()
            })
        
        return docstrings
    
    def find_public_api(self):
        """Find all public functions and classes."""
        api_elements = {'functions': [], 'classes': []}
        
        # Find public functions (not starting with _)
        for match in vexy_glob.find(
            "**/*.py",
            content=r'^def\s+([a-zA-Z][a-zA-Z0-9_]*)\s*\(',
            root=self.source_dir,
            exclude=["**/test/**", "**/tests/**"]
        ):
            api_elements['functions'].append({
                'name': match.matches[0],
                'file': match.path,
                'line': match.line_number
            })
        
        # Find public classes
        for match in vexy_glob.find(
            "**/*.py", 
            content=r'^class\s+([A-Z][a-zA-Z0-9_]*)\s*[:\(]',
            root=self.source_dir,
            exclude=["**/test/**", "**/tests/**"]
        ):
            api_elements['classes'].append({
                'name': match.matches[0],
                'file': match.path,
                'line': match.line_number
            })
        
        return api_elements
    
    def generate_api_docs(self):
        """Generate API documentation."""
        api = self.find_public_api()
        docstrings = self.extract_docstrings()
        
        with open(self.output_dir / "api.md", "w") as f:
            f.write("# API Documentation\n\n")
            
            f.write("## Classes\n\n")
            for cls in api['classes']:
                f.write(f"### {cls['name']}\n")
                f.write(f"*File: {cls['file']}:{cls['line']}*\n\n")
                
                # Look for docstring near class definition
                if cls['file'] in docstrings:
                    for doc in docstrings[cls['file']]:
                        if abs(doc['line'] - cls['line']) <= 3:
                            f.write(f"{doc['content']}\n\n")
                            break
            
            f.write("## Functions\n\n")
            for func in api['functions']:
                f.write(f"### {func['name']}\n")
                f.write(f"*File: {func['file']}:{func['line']}*\n\n")
                
                # Look for docstring near function definition
                if func['file'] in docstrings:
                    for doc in docstrings[func['file']]:
                        if abs(doc['line'] - func['line']) <= 3:
                            f.write(f"{doc['content']}\n\n")
                            break

# Usage
doc_gen = DocGenerator("src", "docs")
doc_gen.generate_api_docs()
```

## Data Processing Pipelines

### Log Analysis Pipeline

```python
import vexy_glob
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

class LogAnalyzer:
    """Comprehensive log analysis using vexy_glob."""
    
    def __init__(self, log_directory):
        self.log_directory = log_directory
        self.patterns = {
            'timestamp': r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            'log_level': r'(DEBUG|INFO|WARN|ERROR|FATAL|CRITICAL)',
            'ip_address': r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b',
            'http_method': r'(GET|POST|PUT|DELETE|HEAD|OPTIONS)',
            'status_code': r'\s(\d{3})\s',
            'user_agent': r'Mozilla/[^"]+',
            'error_trace': r'(Exception|Error|Traceback)'
        }
    
    def analyze_recent_logs(self, hours=24):
        """Analyze logs from the last N hours."""
        cutoff_time = f"-{hours}h"
        
        # Find recent log files
        recent_logs = list(vexy_glob.find(
            "**/*.log",
            root=self.log_directory,
            mtime_after=cutoff_time,
            min_size=1024  # Skip empty logs
        ))
        
        analysis = {
            'files_analyzed': len(recent_logs),
            'time_range': f"Last {hours} hours",
            'errors': self._analyze_errors(cutoff_time),
            'traffic': self._analyze_traffic(cutoff_time),
            'performance': self._analyze_performance(cutoff_time)
        }
        
        return analysis
    
    def _analyze_errors(self, time_filter):
        """Analyze error patterns in logs."""
        error_analysis = {
            'total_errors': 0,
            'by_level': Counter(),
            'by_file': Counter(),
            'error_patterns': defaultdict(int),
            'recent_errors': []
        }
        
        # Find all error entries
        for match in vexy_glob.find(
            "**/*.log",
            content=self.patterns['log_level'],
            root=self.log_directory,
            mtime_after=time_filter
        ):
            level = match.matches[0]
            if level in ['ERROR', 'FATAL', 'CRITICAL']:
                error_analysis['total_errors'] += 1
                error_analysis['by_level'][level] += 1
                error_analysis['by_file'][match.path] += 1
                
                # Store recent errors (first 100)
                if len(error_analysis['recent_errors']) < 100:
                    error_analysis['recent_errors'].append({
                        'file': match.path,
                        'line': match.line_number,
                        'level': level,
                        'text': match.line_text.strip()
                    })
        
        # Find specific error patterns
        error_patterns = {
            'connection_errors': r'(?i)connection.*(?:refused|timeout|failed)',
            'database_errors': r'(?i)database.*(?:error|failed|timeout)',
            'authentication_errors': r'(?i)auth.*(?:failed|denied|invalid)',
            'permission_errors': r'(?i)permission.*denied',
            'memory_errors': r'(?i)(?:memory|oom).*(?:error|exhausted)',
        }
        
        for pattern_name, pattern in error_patterns.items():
            matches = list(vexy_glob.find(
                "**/*.log",
                content=pattern,
                root=self.log_directory,
                mtime_after=time_filter
            ))
            error_analysis['error_patterns'][pattern_name] = len(matches)
        
        return error_analysis
    
    def _analyze_traffic(self, time_filter):
        """Analyze HTTP traffic patterns."""
        traffic_analysis = {
            'total_requests': 0,
            'by_method': Counter(),
            'by_status': Counter(),
            'top_ips': Counter(),
            'unusual_activity': []
        }
        
        # Analyze HTTP methods
        for match in vexy_glob.find(
            "**/*.log",
            content=self.patterns['http_method'],
            root=self.log_directory,
            mtime_after=time_filter
        ):
            method = match.matches[0]
            traffic_analysis['total_requests'] += 1
            traffic_analysis['by_method'][method] += 1
        
        # Analyze status codes
        for match in vexy_glob.find(
            "**/*.log",
            content=self.patterns['status_code'],
            root=self.log_directory,
            mtime_after=time_filter
        ):
            status = match.matches[0]
            traffic_analysis['by_status'][status] += 1
        
        # Track IP addresses
        for match in vexy_glob.find(
            "**/*.log",
            content=self.patterns['ip_address'],
            root=self.log_directory,
            mtime_after=time_filter
        ):
            ip = match.matches[0]
            traffic_analysis['top_ips'][ip] += 1
        
        # Find unusual activity (high request rates from single IP)
        for ip, count in traffic_analysis['top_ips'].most_common(10):
            if count > 1000:  # Threshold for suspicious activity
                traffic_analysis['unusual_activity'].append({
                    'ip': ip,
                    'request_count': count,
                    'note': 'High request volume'
                })
        
        return traffic_analysis
    
    def _analyze_performance(self, time_filter):
        """Analyze performance metrics from logs."""
        performance = {
            'slow_requests': [],
            'response_times': [],
            'memory_usage': []
        }
        
        # Find slow requests (customize pattern for your log format)
        slow_pattern = r'(?i)(?:slow|timeout|duration).*?(\d+(?:\.\d+)?)\s*(?:ms|sec|seconds)'
        for match in vexy_glob.find(
            "**/*.log",
            content=slow_pattern,
            root=self.log_directory,
            mtime_after=time_filter
        ):
            duration = float(match.matches[0])
            if duration > 1000:  # Slow threshold: 1 second
                performance['slow_requests'].append({
                    'file': match.path,
                    'line': match.line_number,
                    'duration': duration,
                    'text': match.line_text.strip()
                })
        
        return performance
    
    def generate_report(self, hours=24):
        """Generate comprehensive log analysis report."""
        analysis = self.analyze_recent_logs(hours)
        
        print(f"Log Analysis Report - Last {hours} Hours")
        print("=" * 50)
        print(f"Files analyzed: {analysis['files_analyzed']}")
        print(f"Total requests: {analysis['traffic']['total_requests']}")
        print(f"Total errors: {analysis['errors']['total_errors']}")
        
        print(f"\nError Breakdown:")
        for level, count in analysis['errors']['by_level'].most_common():
            print(f"  {level}: {count}")
        
        print(f"\nHTTP Methods:")
        for method, count in analysis['traffic']['by_method'].most_common():
            print(f"  {method}: {count}")
        
        print(f"\nTop Status Codes:")
        for status, count in analysis['traffic']['by_status'].most_common(5):
            print(f"  {status}: {count}")
        
        if analysis['traffic']['unusual_activity']:
            print(f"\n⚠️ Unusual Activity:")
            for activity in analysis['traffic']['unusual_activity']:
                print(f"  IP {activity['ip']}: {activity['request_count']} requests")
        
        return analysis

# Usage
analyzer = LogAnalyzer("/var/log/myapp")
report = analyzer.generate_report(hours=24)
```

### File Organization and Cleanup

```python
import vexy_glob
import os
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

class FileOrganizer:
    """Organize and clean up files using vexy_glob."""
    
    def __init__(self, target_directory):
        self.target_directory = Path(target_directory)
    
    def find_duplicates(self):
        """Find duplicate files by content hash."""
        file_hashes = {}
        duplicates = []
        
        # Process all files
        for path in vexy_glob.find(
            "**/*",
            root=self.target_directory,
            file_type="f",
            exclude=["**/.git/**", "**/__pycache__/**"]
        ):
            file_path = Path(path)
            
            # Calculate hash
            hasher = hashlib.md5()
            try:
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                file_hash = hasher.hexdigest()
                
                if file_hash in file_hashes:
                    # Found duplicate
                    duplicates.append({
                        'original': file_hashes[file_hash],
                        'duplicate': str(file_path),
                        'size': file_path.stat().st_size
                    })
                else:
                    file_hashes[file_hash] = str(file_path)
            except (IOError, OSError):
                continue  # Skip files we can't read
        
        return duplicates
    
    def organize_by_type(self, output_base):
        """Organize files by type into separate directories."""
        output_base = Path(output_base)
        
        file_categories = {
            'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'],
            'documents': ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'],
            'archives': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2'],
            'videos': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv'],
            'audio': ['mp3', 'wav', 'flac', 'aac', 'ogg'],
            'code': ['py', 'js', 'html', 'css', 'java', 'cpp', 'c']
        }
        
        organization_report = {
            'files_processed': 0,
            'categories': {cat: 0 for cat in file_categories.keys()},
            'uncategorized': 0
        }
        
        for path in vexy_glob.find(
            "**/*",
            root=self.target_directory,
            file_type="f"
        ):
            file_path = Path(path)
            extension = file_path.suffix.lower().lstrip('.')
            
            # Find category
            category = None
            for cat, extensions in file_categories.items():
                if extension in extensions:
                    category = cat
                    break
            
            if category:
                # Create category directory
                category_dir = output_base / category
                category_dir.mkdir(parents=True, exist_ok=True)
                
                # Move file
                destination = category_dir / file_path.name
                # Handle name conflicts
                counter = 1
                while destination.exists():
                    stem = file_path.stem
                    suffix = file_path.suffix
                    destination = category_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                shutil.move(str(file_path), str(destination))
                organization_report['categories'][category] += 1
            else:
                organization_report['uncategorized'] += 1
            
            organization_report['files_processed'] += 1
        
        return organization_report
    
    def cleanup_old_files(self, days_old=30, dry_run=True):
        """Clean up old files (with safety dry-run mode)."""
        cutoff_time = f"-{days_old}d"
        
        cleanup_report = {
            'files_found': 0,
            'total_size': 0,
            'by_extension': {},
            'files': []
        }
        
        # Find old files
        for path in vexy_glob.find(
            "**/*",
            root=self.target_directory,
            file_type="f",
            mtime_before=cutoff_time,
            exclude=[
                "**/.git/**",
                "**/important/**",
                "**/backup/**"
            ]
        ):
            file_path = Path(path)
            file_size = file_path.stat().st_size
            extension = file_path.suffix.lower()
            
            cleanup_report['files_found'] += 1
            cleanup_report['total_size'] += file_size
            cleanup_report['files'].append({
                'path': str(file_path),
                'size': file_size,
                'age_days': (datetime.now() - datetime.fromtimestamp(
                    file_path.stat().st_mtime)).days
            })
            
            if extension in cleanup_report['by_extension']:
                cleanup_report['by_extension'][extension]['count'] += 1
                cleanup_report['by_extension'][extension]['size'] += file_size
            else:
                cleanup_report['by_extension'][extension] = {
                    'count': 1,
                    'size': file_size
                }
            
            # Actually delete if not dry run
            if not dry_run:
                file_path.unlink()
        
        return cleanup_report
    
    def find_large_files(self, min_size_mb=100):
        """Find files larger than specified size."""
        min_size_bytes = min_size_mb * 1024 * 1024
        
        large_files = []
        for path in vexy_glob.find(
            "**/*",
            root=self.target_directory,
            file_type="f",
            min_size=min_size_bytes
        ):
            file_path = Path(path)
            size_mb = file_path.stat().st_size / (1024 * 1024)
            
            large_files.append({
                'path': str(file_path),
                'size_mb': round(size_mb, 2),
                'extension': file_path.suffix.lower()
            })
        
        # Sort by size
        large_files.sort(key=lambda x: x['size_mb'], reverse=True)
        return large_files

# Usage
organizer = FileOrganizer("~/Downloads")

# Find duplicates
duplicates = organizer.find_duplicates()
print(f"Found {len(duplicates)} duplicate files")

# Find large files
large_files = organizer.find_large_files(min_size_mb=50)
print(f"Found {len(large_files)} files over 50MB")

# Cleanup old files (dry run first)
cleanup_report = organizer.cleanup_old_files(days_old=30, dry_run=True)
print(f"Would clean up {cleanup_report['files_found']} files "
      f"({cleanup_report['total_size']/1024/1024:.1f} MB)")
```

## Build System Integration

### Dependency Analysis

```python
import vexy_glob
import json
import re
from collections import defaultdict, set

class DependencyAnalyzer:
    """Analyze project dependencies using vexy_glob."""
    
    def __init__(self, project_root):
        self.project_root = project_root
        self.language_patterns = {
            'python': {
                'files': "**/*.py",
                'imports': r'^(?:from\s+(\S+)\s+)?import\s+([\w,\s.]+)',
                'stdlib': self._get_python_stdlib()
            },
            'javascript': {
                'files': "**/*.{js,ts,jsx,tsx}",
                'imports': r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                'require': r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
            },
            'rust': {
                'files': "**/*.rs",
                'extern': r'extern\s+crate\s+(\w+)',
                'use': r'use\s+([\w:]+)'
            }
        }
    
    def _get_python_stdlib(self):
        """Get list of Python standard library modules."""
        # Simplified list - in practice, you'd want a more comprehensive list
        return {
            'os', 'sys', 'json', 'time', 'datetime', 'collections',
            'itertools', 're', 'pathlib', 'urllib', 'http', 'typing',
            'asyncio', 'threading', 'multiprocessing', 'logging'
        }
    
    def analyze_python_dependencies(self):
        """Analyze Python project dependencies."""
        dependencies = {
            'internal': set(),
            'external': set(),
            'stdlib': set(),
            'import_graph': defaultdict(set),
            'unused': set()
        }
        
        # Find all Python files
        python_files = set(vexy_glob.find(
            self.language_patterns['python']['files'],
            root=self.project_root,
            exclude=["**/__pycache__/**", "**/venv/**", "**/.venv/**"],
            as_list=True
        ))
        
        # Extract imports
        all_imports = set()
        for match in vexy_glob.find(
            self.language_patterns['python']['files'],
            content=self.language_patterns['python']['imports'],
            root=self.project_root,
            exclude=["**/__pycache__/**", "**/venv/**", "**/.venv/**"]
        ):
            if match.matches:
                # Handle different import formats
                if len(match.matches) >= 2:
                    module = match.matches[0] or match.matches[1].split(',')[0].strip()
                else:
                    module = match.matches[0]
                
                # Clean module name
                module = module.split('.')[0].strip()
                if module:
                    all_imports.add(module)
                    dependencies['import_graph'][match.path].add(module)
        
        # Categorize dependencies
        stdlib = self.language_patterns['python']['stdlib']
        
        for module in all_imports:
            if module in stdlib:
                dependencies['stdlib'].add(module)
            elif any(module in f for f in python_files):
                dependencies['internal'].add(module)
            else:
                dependencies['external'].add(module)
        
        return dependencies
    
    def find_unused_imports(self):
        """Find potentially unused imports."""
        import_usage = defaultdict(set)
        
        # Find all imports
        for match in vexy_glob.find(
            "**/*.py",
            content=r'^(?:from\s+\S+\s+)?import\s+([\w,\s.]+)',
            root=self.project_root,
            exclude=["**/__pycache__/**", "**/test/**", "**/tests/**"]
        ):
            if match.matches:
                imports = [imp.strip() for imp in match.matches[0].split(',')]
                for imp in imports:
                    if imp:
                        import_usage[match.path].add(imp)
        
        # Check usage in same files
        unused_by_file = {}
        for file_path, imports in import_usage.items():
            # Read file content to check usage
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                unused = []
                for imp in imports:
                    # Simple usage check (can be improved)
                    if imp not in content.replace(f"import {imp}", ""):
                        unused.append(imp)
                
                if unused:
                    unused_by_file[file_path] = unused
            except (IOError, UnicodeDecodeError):
                continue
        
        return unused_by_file
    
    def analyze_circular_dependencies(self):
        """Find circular dependencies in imports."""
        dependencies = self.analyze_python_dependencies()
        import_graph = dependencies['import_graph']
        
        def has_path(graph, start, end, visited=None):
            if visited is None:
                visited = set()
            
            if start == end:
                return True
            
            if start in visited:
                return False
            
            visited.add(start)
            
            for neighbor in graph.get(start, set()):
                if has_path(graph, neighbor, end, visited.copy()):
                    return True
            
            return False
        
        # Build file-to-file dependency graph
        file_graph = defaultdict(set)
        for file_path, modules in import_graph.items():
            for module in modules:
                # Find files that define this module
                for other_file in import_graph.keys():
                    if module in other_file or other_file.endswith(f"{module}.py"):
                        file_graph[file_path].add(other_file)
        
        # Find cycles
        cycles = []
        for file1 in file_graph:
            for file2 in file_graph[file1]:
                if has_path(file_graph, file2, file1):
                    cycles.append((file1, file2))
        
        return cycles
    
    def generate_dependency_report(self):
        """Generate comprehensive dependency report."""
        python_deps = self.analyze_python_dependencies()
        unused = self.find_unused_imports()
        cycles = self.analyze_circular_dependencies()
        
        report = {
            'summary': {
                'total_external_deps': len(python_deps['external']),
                'total_stdlib_usage': len(python_deps['stdlib']),
                'total_internal_modules': len(python_deps['internal']),
                'files_with_unused_imports': len(unused),
                'circular_dependencies': len(cycles)
            },
            'external_dependencies': sorted(python_deps['external']),
            'unused_imports': unused,
            'circular_dependencies': cycles,
            'most_used_stdlib': sorted(python_deps['stdlib'])
        }
        
        return report

# Usage
analyzer = DependencyAnalyzer(".")
report = analyzer.generate_dependency_report()

print("Dependency Analysis Report")
print("=" * 30)
print(f"External dependencies: {report['summary']['total_external_deps']}")
print(f"Standard library modules used: {report['summary']['total_stdlib_usage']}")
print(f"Files with unused imports: {report['summary']['files_with_unused_imports']}")

if report['circular_dependencies']:
    print(f"\n⚠️ Circular dependencies found: {len(report['circular_dependencies'])}")
```

## Testing and Quality Assurance

### Test Discovery and Analysis

```python
import vexy_glob
import re
from pathlib import Path

class TestAnalyzer:
    """Analyze test coverage and patterns using vexy_glob."""
    
    def __init__(self, project_root):
        self.project_root = project_root
        self.test_patterns = {
            'pytest': r'def\s+test_(\w+)',
            'unittest': r'def\s+test(\w+)\s*\(.*TestCase',
            'doctest': r'>>>\s+',
            'fixtures': r'@pytest\.fixture',
            'parametrize': r'@pytest\.mark\.parametrize'
        }
    
    def find_test_files(self):
        """Find all test files in the project."""
        test_files = {
            'pytest_files': [],
            'unittest_files': [],
            'test_directories': set()
        }
        
        # Find files with test patterns
        pytest_files = list(vexy_glob.find(
            "**/test_*.py",
            root=self.project_root,
            as_list=True
        )) + list(vexy_glob.find(
            "**/*_test.py", 
            root=self.project_root,
            as_list=True
        ))
        
        # Find files in test directories
        test_dir_files = list(vexy_glob.find(
            "**/test/**/*.py",
            root=self.project_root,
            as_list=True
        )) + list(vexy_glob.find(
            "**/tests/**/*.py",
            root=self.project_root,
            as_list=True
        ))
        
        test_files['pytest_files'] = pytest_files + test_dir_files
        
        # Extract test directories
        for file_path in test_files['pytest_files']:
            path = Path(file_path)
            if 'test' in path.parts:
                test_idx = None
                for i, part in enumerate(path.parts):
                    if 'test' in part.lower():
                        test_idx = i
                        break
                if test_idx is not None:
                    test_dir = '/'.join(path.parts[:test_idx+1])
                    test_files['test_directories'].add(test_dir)
        
        return test_files
    
    def analyze_test_patterns(self):
        """Analyze test patterns and structure."""
        analysis = {
            'total_tests': 0,
            'by_pattern': {},
            'test_files': [],
            'coverage_gaps': []
        }
        
        test_files = self.find_test_files()['pytest_files']
        
        for pattern_name, pattern in self.test_patterns.items():
            matches = list(vexy_glob.find(
                "**/*.py",
                content=pattern,
                root=self.project_root,
                include_paths=test_files  # Focus on test files
            ))
            
            analysis['by_pattern'][pattern_name] = len(matches)
            analysis['total_tests'] += len(matches)
        
        # Analyze individual test files
        for test_file in test_files:
            file_analysis = self._analyze_test_file(test_file)
            analysis['test_files'].append(file_analysis)
        
        return analysis
    
    def _analyze_test_file(self, file_path):
        """Analyze individual test file."""
        analysis = {
            'path': file_path,
            'test_count': 0,
            'fixture_count': 0,
            'parametrized_tests': 0,
            'imports': [],
            'complexity_score': 0
        }
        
        # Count tests in this file
        test_matches = list(vexy_glob.find(
            file_path,
            content=self.test_patterns['pytest']
        ))
        analysis['test_count'] = len(test_matches)
        
        # Count fixtures
        fixture_matches = list(vexy_glob.find(
            file_path,
            content=self.test_patterns['fixtures']
        ))
        analysis['fixture_count'] = len(fixture_matches)
        
        # Count parametrized tests
        param_matches = list(vexy_glob.find(
            file_path,
            content=self.test_patterns['parametrize']
        ))
        analysis['parametrized_tests'] = len(param_matches)
        
        # Find imports
        import_matches = list(vexy_glob.find(
            file_path,
            content=r'^(?:from\s+\S+\s+)?import\s+([\w,\s.]+)'
        ))
        analysis['imports'] = [m.matches[0] for m in import_matches if m.matches]
        
        # Simple complexity score
        analysis['complexity_score'] = (
            analysis['test_count'] * 1 +
            analysis['fixture_count'] * 2 +
            analysis['parametrized_tests'] * 3
        )
        
        return analysis
    
    def find_untested_files(self):
        """Find source files that might not have corresponding tests."""
        # Find all source files
        source_files = set(vexy_glob.find(
            "**/*.py",
            root=self.project_root,
            exclude=[
                "**/test/**",
                "**/tests/**", 
                "**/*_test.py",
                "**/test_*.py",
                "**/__pycache__/**"
            ],
            as_list=True
        ))
        
        # Find test files
        test_files = set(self.find_test_files()['pytest_files'])
        
        # Check for corresponding tests
        untested = []
        for source_file in source_files:
            source_path = Path(source_file)
            source_name = source_path.stem
            
            # Look for corresponding test files
            has_test = False
            for test_file in test_files:
                test_path = Path(test_file)
                if (source_name in test_path.name or 
                    test_path.name.replace('test_', '').replace('_test', '') == source_name):
                    has_test = True
                    break
            
            if not has_test:
                untested.append(source_file)
        
        return untested
    
    def generate_test_report(self):
        """Generate comprehensive test analysis report."""
        test_analysis = self.analyze_test_patterns()
        untested = self.find_untested_files()
        test_files_info = self.find_test_files()
        
        print("Test Analysis Report")
        print("=" * 25)
        print(f"Total tests found: {test_analysis['total_tests']}")
        print(f"Test files: {len(test_files_info['pytest_files'])}")
        print(f"Test directories: {len(test_files_info['test_directories'])}")
        print(f"Untested source files: {len(untested)}")
        
        print("\nTest patterns:")
        for pattern, count in test_analysis['by_pattern'].items():
            print(f"  {pattern}: {count}")
        
        print("\nTest directories:")
        for test_dir in sorted(test_files_info['test_directories']):
            print(f"  {test_dir}")
        
        if untested:
            print(f"\n⚠️ Files without tests:")
            for file in sorted(untested)[:10]:  # Show first 10
                print(f"  {file}")
            if len(untested) > 10:
                print(f"  ... and {len(untested) - 10} more")

# Usage
test_analyzer = TestAnalyzer(".")
test_analyzer.generate_test_report()
```

## Next Steps

You've now seen comprehensive examples of integrating vexy_glob into real-world applications. Next, learn about troubleshooting and best practices:

→ **[Chapter 8: Troubleshooting and Best Practices](chapter8.md)** - Common issues and solutions

→ **[Chapter 9: Development and Contributing](chapter9.md)** - Development setup and contributing guidelines

---

!!! tip "Integration Best Practice"
    Start with simple patterns and gradually add complexity. Always test your patterns on a small subset before running on large datasets.

!!! note "Performance in Pipelines"
    For data processing pipelines, use streaming results and implement early termination to optimize memory usage and processing time.

!!! warning "Error Handling"
    Always implement proper error handling when integrating with external systems. File permissions, disk space, and network issues can cause failures.