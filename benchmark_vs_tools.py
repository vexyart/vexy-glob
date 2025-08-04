#!/usr/bin/env python
# this_file: benchmark_vs_tools.py
"""
Benchmark vexy_glob against fd and ripgrep for performance comparison.

This script provides a fair comparison between:
- vexy_glob (our tool)
- fd (fast file finder)
- ripgrep/rg (fast content searcher)
"""

import subprocess
import time
import tempfile
import os
import shutil
from pathlib import Path
import vexy_glob
import statistics
import json
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

def check_tool_availability():
    """Check if fd and rg are available."""
    tools = {}
    
    # Check fd
    try:
        result = subprocess.run(['fd', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            tools['fd'] = result.stdout.strip()
        else:
            tools['fd'] = None
    except FileNotFoundError:
        tools['fd'] = None
    
    # Check ripgrep
    try:
        result = subprocess.run(['rg', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            tools['rg'] = result.stdout.strip().split('\n')[0]
        else:
            tools['rg'] = None
    except FileNotFoundError:
        tools['rg'] = None
    
    return tools

def create_test_dataset(base_dir: Path, file_count: int, dir_depth: int = 4):
    """Create a realistic test dataset with nested directories."""
    extensions = ['.py', '.js', '.rs', '.txt', '.md', '.json', '.yaml', '.toml', '.cpp', '.h']
    
    console.print(f"Creating test dataset with {file_count} files...")
    
    # Create directory structure
    dirs_created = 0
    files_created = 0
    
    # Create nested directory structure
    for i in range(dir_depth):
        for j in range(5):  # 5 dirs per level
            dir_path = base_dir
            for level in range(i + 1):
                dir_path = dir_path / f"level{level}" / f"dir{j}"
            dir_path.mkdir(parents=True, exist_ok=True)
            dirs_created += 1
            
            # Create files in this directory
            files_per_dir = max(1, file_count // (dirs_created * 2))
            for k in range(files_per_dir):
                if files_created >= file_count:
                    break
                ext = extensions[files_created % len(extensions)]
                file_path = dir_path / f"file_{files_created}{ext}"
                
                # Write some content
                if ext == '.py':
                    content = f"""#!/usr/bin/env python
# File: {file_path.name}
# TODO: Implement functionality

def function_{k}():
    '''Function docstring'''
    return "result_{k}"

class TestClass_{k}:
    def __init__(self):
        self.value = {k}
"""
                elif ext in ['.js', '.ts']:
                    content = f"""// File: {file_path.name}
// TODO: Add implementation

function processData_{k}() {{
    return "data_{k}";
}}

class Handler_{k} {{
    constructor() {{
        this.id = {k};
    }}
}}
"""
                else:
                    content = f"Test content for {file_path.name}\nLine 2\nLine 3\nTODO: Update this file\n"
                
                file_path.write_text(content)
                files_created += 1
    
    # Create some hidden files and .gitignore
    gitignore_path = base_dir / '.gitignore'
    gitignore_path.write_text("*.tmp\n*.cache\n__pycache__/\nnode_modules/\n")
    
    return files_created

def benchmark_file_finding(base_dir: Path, pattern: str, iterations: int = 5):
    """Benchmark file finding operations."""
    results = {}
    
    # Benchmark vexy_glob
    console.print(f"Benchmarking vexy_glob for pattern '{pattern}'...")
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        vexy_results = list(vexy_glob.find(pattern, root=str(base_dir)))
        end = time.perf_counter()
        times.append(end - start)
    
    results['vexy_glob'] = {
        'times': times,
        'avg': statistics.mean(times),
        'min': min(times),
        'max': max(times),
        'count': len(vexy_results)
    }
    
    # Benchmark fd (if available)
    if shutil.which('fd'):
        console.print(f"Benchmarking fd for pattern '{pattern}'...")
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            result = subprocess.run(
                ['fd', pattern, str(base_dir), '--hidden', '--no-ignore'],
                capture_output=True, text=True
            )
            end = time.perf_counter()
            times.append(end - start)
            fd_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        results['fd'] = {
            'times': times,
            'avg': statistics.mean(times),
            'min': min(times),
            'max': max(times),
            'count': fd_count
        }
    
    # For glob patterns, we can't use ripgrep (it's for content search)
    # But we can compare with Python's glob
    if '*' in pattern:
        import glob as python_glob
        console.print(f"Benchmarking Python glob for pattern '{pattern}'...")
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            glob_results = list(python_glob.glob(f"{base_dir}/**/{pattern}", recursive=True))
            end = time.perf_counter()
            times.append(end - start)
        
        results['python_glob'] = {
            'times': times,
            'avg': statistics.mean(times),
            'min': min(times),
            'max': max(times),
            'count': len(glob_results)
        }
    
    return results

def benchmark_content_search(base_dir: Path, pattern: str, iterations: int = 3):
    """Benchmark content search operations."""
    results = {}
    
    # Benchmark vexy_glob search
    console.print(f"Benchmarking vexy_glob content search for '{pattern}'...")
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        vexy_results = list(vexy_glob.search(pattern, "*", root=str(base_dir)))
        end = time.perf_counter()
        times.append(end - start)
    
    results['vexy_glob'] = {
        'times': times,
        'avg': statistics.mean(times),
        'min': min(times),
        'max': max(times),
        'count': len(vexy_results)
    }
    
    # Benchmark ripgrep (if available)
    if shutil.which('rg'):
        console.print(f"Benchmarking ripgrep for '{pattern}'...")
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            result = subprocess.run(
                ['rg', pattern, str(base_dir), '--count-matches'],
                capture_output=True, text=True
            )
            end = time.perf_counter()
            times.append(end - start)
            # Count matches from ripgrep output
            rg_count = sum(int(line.split(':')[-1]) for line in result.stdout.strip().split('\n') if ':' in line)
        
        results['ripgrep'] = {
            'times': times,
            'avg': statistics.mean(times),
            'min': min(times),
            'max': max(times),
            'count': rg_count
        }
    
    return results

def display_results(title: str, results: dict):
    """Display benchmark results in a table."""
    table = Table(title=title)
    table.add_column("Tool", style="cyan")
    table.add_column("Avg Time (ms)", justify="right", style="green")
    table.add_column("Min Time (ms)", justify="right")
    table.add_column("Max Time (ms)", justify="right")
    table.add_column("Matches", justify="right", style="yellow")
    table.add_column("vs vexy_glob", justify="right", style="bold")
    
    vexy_avg = results.get('vexy_glob', {}).get('avg', 1.0)
    
    for tool, data in results.items():
        speedup = vexy_avg / data['avg'] if data['avg'] > 0 else 1.0
        speedup_str = f"{speedup:.2f}x" if speedup < 1 else f"{1/speedup:.2f}x slower"
        if tool == 'vexy_glob':
            speedup_str = "baseline"
        
        table.add_row(
            tool,
            f"{data['avg'] * 1000:.2f}",
            f"{data['min'] * 1000:.2f}",
            f"{data['max'] * 1000:.2f}",
            str(data['count']),
            speedup_str
        )
    
    console.print(table)

def run_comprehensive_benchmark():
    """Run comprehensive benchmarks."""
    # Check tool availability
    tools = check_tool_availability()
    console.print("[bold]Tool Availability:[/bold]")
    for tool, version in tools.items():
        if version:
            console.print(f"  ✓ {tool}: {version}")
        else:
            console.print(f"  ✗ {tool}: Not installed")
    console.print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        
        # Test different dataset sizes
        test_configs = [
            ("Small dataset", 1000, 3),
            ("Medium dataset", 10000, 4),
            ("Large dataset", 50000, 5),
        ]
        
        for config_name, file_count, dir_depth in test_configs:
            console.print(f"\n[bold blue]{config_name}[/bold blue]")
            
            # Create dataset
            created = create_test_dataset(base_dir, file_count, dir_depth)
            console.print(f"Created {created} files in {sum(1 for _ in base_dir.rglob('*') if _.is_dir())} directories\n")
            
            # File finding benchmarks
            find_patterns = [
                "*.py",
                "*.js",
                "test*",
                "**/level2/**/*.py",
            ]
            
            for pattern in find_patterns:
                console.print(f"\n[yellow]File finding: {pattern}[/yellow]")
                results = benchmark_file_finding(base_dir, pattern)
                display_results(f"Pattern: {pattern}", results)
            
            # Content search benchmarks (only for smaller datasets)
            if file_count <= 10000:
                search_patterns = [
                    "TODO",
                    "function.*\\{",
                    "class\\s+\\w+",
                ]
                
                for pattern in search_patterns:
                    console.print(f"\n[yellow]Content search: {pattern}[/yellow]")
                    results = benchmark_content_search(base_dir, pattern)
                    display_results(f"Search: {pattern}", results)
            
            # Clean up for next iteration
            shutil.rmtree(base_dir)
            base_dir.mkdir()

def test_real_world_performance():
    """Test on real-world directory if available."""
    # Look for common large directories
    test_dirs = [
        Path.home() / ".cargo" / "registry" / "src",  # Rust crates
        Path.home() / "node_modules",  # Node modules
        Path("/usr/local/lib/python3.12/site-packages"),  # Python packages
    ]
    
    for test_dir in test_dirs:
        if test_dir.exists() and test_dir.is_dir():
            file_count = sum(1 for _ in test_dir.rglob('*') if _.is_file())
            if file_count > 1000:
                console.print(f"\n[bold green]Real-world test: {test_dir}[/bold green]")
                console.print(f"Files: {file_count}")
                
                # Quick benchmark
                pattern = "*.py" if "python" in str(test_dir) else "*"
                results = benchmark_file_finding(test_dir, pattern, iterations=3)
                display_results(f"Real-world: {pattern} in {test_dir.name}", results)
                break

if __name__ == "__main__":
    console.print("[bold]Vexy Glob vs fd/ripgrep Performance Comparison[/bold]\n")
    
    run_comprehensive_benchmark()
    test_real_world_performance()
    
    console.print("\n[green]✓ Benchmarking complete![/green]")
    console.print("\n[dim]Note: Results may vary based on filesystem, OS, and system load.[/dim]")