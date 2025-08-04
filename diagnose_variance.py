#!/usr/bin/env python
# this_file: diagnose_variance.py
"""
Diagnose high variance in initial file finding runs.

This script helps identify why the first few runs show extreme variance
(50ms min to 10,387ms max) in performance.
"""

import time
import tempfile
import os
import gc
from pathlib import Path
import vexy_glob
import statistics
import psutil
import resource
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

console = Console()

def get_memory_info():
    """Get current memory usage."""
    process = psutil.Process(os.getpid())
    return {
        'rss': process.memory_info().rss / 1024 / 1024,  # MB
        'vms': process.memory_info().vms / 1024 / 1024,  # MB
        'available': psutil.virtual_memory().available / 1024 / 1024 / 1024,  # GB
    }

def measure_with_details(pattern: str, root: str, iterations: int = 10):
    """Measure performance with detailed timing for each iteration."""
    times = []
    memory_before = []
    memory_after = []
    result_counts = []
    
    console.print(f"\n[bold]Measuring pattern: {pattern}[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task("Running iterations...", total=iterations)
        
        for i in range(iterations):
            # Force garbage collection
            gc.collect()
            gc.disable()
            
            # Memory before
            mem_before = get_memory_info()
            memory_before.append(mem_before['rss'])
            
            # Time the operation
            start = time.perf_counter()
            results = list(vexy_glob.find(pattern, root=root))
            end = time.perf_counter()
            
            # Memory after
            mem_after = get_memory_info()
            memory_after.append(mem_after['rss'])
            
            gc.enable()
            
            elapsed = end - start
            times.append(elapsed)
            result_counts.append(len(results))
            
            # Show details for first few runs and any outliers
            if i < 3 or elapsed > statistics.mean(times) * 2 if len(times) > 3 else True:
                console.print(f"  Run {i+1}: {elapsed*1000:.2f}ms, "
                            f"Memory: {mem_before['rss']:.1f}→{mem_after['rss']:.1f}MB, "
                            f"Results: {len(results)}")
            
            progress.update(task, advance=1)
    
    return {
        'times': times,
        'memory_before': memory_before,
        'memory_after': memory_after,
        'result_counts': result_counts
    }

def analyze_variance(times):
    """Analyze variance in timing data."""
    if len(times) < 2:
        return {}
    
    mean = statistics.mean(times)
    stdev = statistics.stdev(times)
    cv = (stdev / mean) * 100 if mean > 0 else 0
    
    # Identify outliers (>2 std dev from mean)
    outliers = [t for t in times if abs(t - mean) > 2 * stdev]
    
    return {
        'mean': mean,
        'stdev': stdev,
        'cv': cv,
        'min': min(times),
        'max': max(times),
        'range_ratio': max(times) / min(times) if min(times) > 0 else float('inf'),
        'outliers': outliers,
        'outlier_count': len(outliers)
    }

def test_cold_vs_warm_start():
    """Test cold start vs warm start performance."""
    console.print("\n[bold blue]Cold vs Warm Start Analysis[/bold blue]")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        
        # Create test files
        console.print("Creating test dataset...")
        for i in range(1000):
            (test_dir / f"test_{i}.py").write_text(f"# Test file {i}\n")
        
        # Test 1: Cold start (new process simulation)
        console.print("\n[yellow]Test 1: Cold Start (Fresh State)[/yellow]")
        
        # Clear filesystem cache if possible (requires root on Linux/macOS)
        try:
            if os.name != 'nt':  # Unix-like
                os.system("sync && echo 3 > /proc/sys/vm/drop_caches 2>/dev/null")
        except:
            pass
        
        cold_results = measure_with_details("*.py", str(test_dir), iterations=5)
        
        # Test 2: Warm start (immediate repeat)
        console.print("\n[yellow]Test 2: Warm Start (Cached State)[/yellow]")
        warm_results = measure_with_details("*.py", str(test_dir), iterations=5)
        
        # Analyze
        cold_analysis = analyze_variance(cold_results['times'])
        warm_analysis = analyze_variance(warm_results['times'])
        
        # Display comparison
        table = Table(title="Cold vs Warm Start Comparison")
        table.add_column("Metric", style="cyan")
        table.add_column("Cold Start", justify="right")
        table.add_column("Warm Start", justify="right", style="green")
        table.add_column("Improvement", justify="right", style="yellow")
        
        metrics = [
            ("Mean Time", f"{cold_analysis['mean']*1000:.2f}ms", 
             f"{warm_analysis['mean']*1000:.2f}ms",
             f"{cold_analysis['mean']/warm_analysis['mean']:.2f}x"),
            ("Std Dev", f"{cold_analysis['stdev']*1000:.2f}ms",
             f"{warm_analysis['stdev']*1000:.2f}ms", "-"),
            ("CV%", f"{cold_analysis['cv']:.1f}%",
             f"{warm_analysis['cv']:.1f}%", "-"),
            ("Min Time", f"{cold_analysis['min']*1000:.2f}ms",
             f"{warm_analysis['min']*1000:.2f}ms", "-"),
            ("Max Time", f"{cold_analysis['max']*1000:.2f}ms",
             f"{warm_analysis['max']*1000:.2f}ms", "-"),
            ("Range Ratio", f"{cold_analysis['range_ratio']:.1f}x",
             f"{warm_analysis['range_ratio']:.1f}x", "-"),
        ]
        
        for row in metrics:
            table.add_row(*row)
        
        console.print("\n", table)

def test_pattern_complexity_variance():
    """Test how pattern complexity affects variance."""
    console.print("\n[bold blue]Pattern Complexity vs Variance Analysis[/bold blue]")
    
    patterns = [
        ("Simple literal", "test.py"),
        ("Simple glob", "*.py"),
        ("Nested glob", "**/*.py"),
        ("Complex glob", "**/test_*_[0-9]*.py"),
        ("Multiple globs", "**/{src,test,lib}/**/*.{py,rs,js}"),
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        
        # Create nested structure
        console.print("Creating nested test structure...")
        for depth in range(3):
            for i in range(10):
                dir_path = test_dir
                for d in range(depth + 1):
                    dir_path = dir_path / f"level{d}"
                dir_path.mkdir(parents=True, exist_ok=True)
                
                # Create files
                (dir_path / f"test_{i}.py").write_text(f"# Test\n")
                (dir_path / f"test_data_{i}.py").write_text(f"# Data\n")
                (dir_path / f"lib_{i}.js").write_text(f"// JS\n")
        
        results_table = Table(title="Pattern Complexity vs Performance Variance")
        results_table.add_column("Pattern Type", style="cyan")
        results_table.add_column("Pattern", style="dim")
        results_table.add_column("Mean (ms)", justify="right")
        results_table.add_column("CV%", justify="right", style="yellow")
        results_table.add_column("Range Ratio", justify="right", style="red")
        
        for pattern_type, pattern in patterns:
            results = measure_with_details(pattern, str(test_dir), iterations=10)
            analysis = analyze_variance(results['times'])
            
            results_table.add_row(
                pattern_type,
                pattern[:30] + "..." if len(pattern) > 30 else pattern,
                f"{analysis['mean']*1000:.2f}",
                f"{analysis['cv']:.1f}",
                f"{analysis['range_ratio']:.1f}x"
            )
        
        console.print("\n", results_table)

def test_thread_pool_warmup():
    """Test if thread pool warmup affects variance."""
    console.print("\n[bold blue]Thread Pool Warmup Analysis[/bold blue]")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir)
        
        # Create files
        for i in range(5000):
            (test_dir / f"file_{i}.txt").write_text(f"Content {i}\n")
        
        # Test without warmup
        console.print("\n[yellow]Without Thread Pool Warmup[/yellow]")
        gc.collect()
        without_warmup = measure_with_details("*.txt", str(test_dir), iterations=5)
        
        # Test with warmup
        console.print("\n[yellow]With Thread Pool Warmup[/yellow]")
        # Warmup: run a few operations first
        for _ in range(3):
            list(vexy_glob.find("warmup_*.txt", root=str(test_dir)))
        
        with_warmup = measure_with_details("*.txt", str(test_dir), iterations=5)
        
        # Compare first run times
        console.print("\n[bold]First Run Comparison:[/bold]")
        console.print(f"Without warmup: {without_warmup['times'][0]*1000:.2f}ms")
        console.print(f"With warmup: {with_warmup['times'][0]*1000:.2f}ms")
        console.print(f"Improvement: {without_warmup['times'][0]/with_warmup['times'][0]:.2f}x")

def main():
    console.print("[bold]Vexy Glob Performance Variance Diagnostic[/bold]\n")
    console.print("This tool diagnoses the cause of high variance in initial runs.\n")
    
    # Show system info
    console.print("[dim]System Information:[/dim]")
    console.print(f"CPU Count: {psutil.cpu_count()}")
    console.print(f"Memory: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}GB")
    console.print(f"Python: {os.sys.version.split()[0]}")
    
    # Run tests
    test_cold_vs_warm_start()
    test_pattern_complexity_variance()
    test_thread_pool_warmup()
    
    # Recommendations
    console.print("\n[bold green]Recommendations:[/bold green]")
    console.print("1. Implement thread pool pre-warming in library initialization")
    console.print("2. Add pattern compilation cache warming for common patterns")
    console.print("3. Consider lazy initialization with proper synchronization")
    console.print("4. Document expected variance for first-run scenarios")

if __name__ == "__main__":
    main()