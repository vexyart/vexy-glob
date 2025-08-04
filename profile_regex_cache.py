#!/usr/bin/env python
# this_file: profile_regex_cache.py
"""
Profile regex compilation caching effectiveness in content search operations.

This script measures the performance impact of pattern caching when performing
content searches with various regex patterns.
"""

import time
import tempfile
import os
from pathlib import Path
import vexy_glob
import re
import gc
import statistics
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

# Common regex patterns that should benefit from caching
REGEX_PATTERNS = [
    # Simple patterns
    r"TODO",
    r"FIXME",
    r"BUG",
    r"HACK",
    r"XXX",
    r"NOTE",
    
    # Common programming patterns
    r"import\s+\w+",
    r"from\s+\w+\s+import",
    r"def\s+\w+\s*\(",
    r"class\s+\w+",
    r"function\s+\w+",
    r"const\s+\w+\s*=",
    r"let\s+\w+\s*=",
    r"var\s+\w+\s*=",
    
    # More complex patterns
    r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b",  # CamelCase
    r"\b[a-z]+_[a-z]+(?:_[a-z]+)*\b",   # snake_case
    r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",  # IP addresses
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
    r"https?://[^\s]+",  # URLs
    r"\b(?:0x)?[0-9a-fA-F]{8,}\b",  # Hex numbers
]

def create_test_files(directory: Path, num_files: int = 100) -> None:
    """Create test files with content that matches our patterns."""
    content_templates = [
        """
# TODO: Implement this function
import os
from pathlib import Path

def process_data(input_file):
    # FIXME: Add error handling
    pass

class DataProcessor:
    def __init__(self):
        # NOTE: Consider lazy loading
        self.data = []
    
    def handleRequest(self, request_id):
        # Process camelCase method
        pass
""",
        """
// TODO: Refactor this code
const API_URL = "https://api.example.com/v1/data";
let user_name = "john_doe";
var email_address = "user@example.com";

function fetchData() {
    // BUG: Race condition here
    return fetch(API_URL);
}

class UserManager {
    constructor() {
        // HACK: Temporary workaround
        this.cache = {};
    }
}
""",
        """
# XXX: This needs optimization
import re
from typing import List

IP_ADDRESS = "192.168.1.1"
HEX_VALUE = 0xDEADBEEF

def parse_log_file(log_path: str) -> List[str]:
    # TODO: Add regex pattern caching
    pattern = re.compile(r"\\d+\\.\\d+\\.\\d+\\.\\d+")
    return []

class LogAnalyzer:
    def find_errors(self):
        # FIXME: Memory leak in this method
        pass
"""
    ]
    
    for i in range(num_files):
        file_path = directory / f"test_file_{i}.py"
        content = content_templates[i % len(content_templates)]
        file_path.write_text(content)

def measure_search_performance(directory: Path, pattern: str, iterations: int = 5) -> dict:
    """Measure search performance for a given pattern."""
    times = []
    match_counts = []
    
    for _ in range(iterations):
        gc.collect()
        gc.disable()
        
        start = time.perf_counter()
        results = list(vexy_glob.search(pattern, "*.py", root=str(directory)))
        end = time.perf_counter()
        
        gc.enable()
        
        times.append(end - start)
        match_counts.append(len(results))
    
    return {
        'pattern': pattern,
        'avg_time': statistics.mean(times),
        'min_time': min(times),
        'max_time': max(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
        'matches': match_counts[0],
        'times': times
    }

def run_cache_effectiveness_test():
    """Test cache effectiveness by running patterns multiple times."""
    console.print("[bold blue]Regex Compilation Cache Effectiveness Test[/bold blue]\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        console.print(f"Creating test files in {test_dir}...")
        create_test_files(test_dir, num_files=200)
        
        # First, warm up the cache by running each pattern once
        console.print("\n[yellow]Warming up pattern cache...[/yellow]")
        for pattern in track(REGEX_PATTERNS, description="Cache warming"):
            list(vexy_glob.search(pattern, "*.py", root=str(test_dir)))
        
        # Now measure performance
        console.print("\n[green]Measuring search performance...[/green]")
        results = []
        
        for pattern in track(REGEX_PATTERNS, description="Testing patterns"):
            result = measure_search_performance(test_dir, pattern)
            results.append(result)
        
        # Display results
        table = Table(title="Regex Pattern Search Performance")
        table.add_column("Pattern", style="cyan")
        table.add_column("Avg Time (ms)", justify="right", style="green")
        table.add_column("Min Time (ms)", justify="right")
        table.add_column("Max Time (ms)", justify="right")
        table.add_column("Std Dev (ms)", justify="right")
        table.add_column("Matches", justify="right", style="yellow")
        
        for result in results:
            table.add_row(
                result['pattern'][:30] + "..." if len(result['pattern']) > 30 else result['pattern'],
                f"{result['avg_time'] * 1000:.2f}",
                f"{result['min_time'] * 1000:.2f}",
                f"{result['max_time'] * 1000:.2f}",
                f"{result['std_dev'] * 1000:.2f}",
                str(result['matches'])
            )
        
        console.print("\n", table)
        
        # Test cold vs warm cache
        console.print("\n[bold]Cold vs Warm Cache Comparison[/bold]")
        
        # Pick a few representative patterns
        test_patterns = [REGEX_PATTERNS[0], REGEX_PATTERNS[6], REGEX_PATTERNS[14]]
        
        for pattern in test_patterns:
            # Cold cache (simulate by using a unique pattern variation)
            cold_pattern = pattern + r"(?:UNIQUE_SUFFIX_FOR_COLD_CACHE)?"
            cold_result = measure_search_performance(test_dir, cold_pattern, iterations=1)
            
            # Warm cache (pattern should be cached)
            warm_result = measure_search_performance(test_dir, pattern, iterations=1)
            
            speedup = cold_result['avg_time'] / warm_result['avg_time'] if warm_result['avg_time'] > 0 else 1.0
            
            console.print(f"\nPattern: [cyan]{pattern}[/cyan]")
            console.print(f"  Cold cache: {cold_result['avg_time'] * 1000:.2f}ms")
            console.print(f"  Warm cache: {warm_result['avg_time'] * 1000:.2f}ms")
            console.print(f"  Speedup: [green]{speedup:.2f}x[/green]")

def test_pattern_complexity_scaling():
    """Test how pattern complexity affects caching benefits."""
    console.print("\n[bold blue]Pattern Complexity vs Cache Benefit Analysis[/bold blue]\n")
    
    complexity_patterns = [
        # Simple literal
        ("Simple literal", r"ERROR"),
        # Basic regex
        ("Basic regex", r"import\s+\w+"),
        # Moderate regex
        ("Moderate regex", r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b"),
        # Complex regex
        ("Complex regex", r"(?:https?|ftp)://[^\s/$.?#].[^\s]*"),
        # Very complex regex
        ("Very complex", r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        create_test_files(test_dir, num_files=100)
        
        table = Table(title="Pattern Complexity vs Performance")
        table.add_column("Complexity", style="cyan")
        table.add_column("Pattern", style="dim")
        table.add_column("First Run (ms)", justify="right")
        table.add_column("Cached Run (ms)", justify="right", style="green")
        table.add_column("Cache Benefit", justify="right", style="yellow")
        
        for name, pattern in complexity_patterns:
            # First run (cold)
            gc.collect()
            start = time.perf_counter()
            list(vexy_glob.search(pattern + "_cold", "*.py", root=str(test_dir)))
            cold_time = (time.perf_counter() - start) * 1000
            
            # Warm the cache
            list(vexy_glob.search(pattern, "*.py", root=str(test_dir)))
            
            # Cached run
            gc.collect()
            start = time.perf_counter()
            list(vexy_glob.search(pattern, "*.py", root=str(test_dir)))
            warm_time = (time.perf_counter() - start) * 1000
            
            benefit = ((cold_time - warm_time) / cold_time * 100) if cold_time > 0 else 0
            
            table.add_row(
                name,
                pattern[:40] + "..." if len(pattern) > 40 else pattern,
                f"{cold_time:.2f}",
                f"{warm_time:.2f}",
                f"{benefit:.1f}%"
            )
        
        console.print("\n", table)

if __name__ == "__main__":
    console.print("[bold]Vexy Glob Regex Compilation Cache Profiling[/bold]\n")
    console.print("This script tests the effectiveness of pattern caching in content search.\n")
    
    run_cache_effectiveness_test()
    test_pattern_complexity_scaling()
    
    console.print("\n[green]✓ Profiling complete![/green]")