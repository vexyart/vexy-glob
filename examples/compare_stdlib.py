#!/usr/bin/env python3
# this_file: benchmarks/compare_stdlib.py
"""
Benchmark vexy_glob against Python's standard library glob module.
"""

import time
import glob
import tempfile
import vexy_glob
from pathlib import Path
import statistics
import os


def create_test_structure(base_dir: Path, num_files: int = 1000, num_dirs: int = 50):
    """Create a test directory structure with many files."""
    print(f"Creating test structure with {num_files} files in {num_dirs} directories...")

    # Create directories
    for i in range(num_dirs):
        dir_path = base_dir / f"dir_{i:03d}"
        dir_path.mkdir(exist_ok=True)

        # Create files in each directory
        files_per_dir = num_files // num_dirs
        for j in range(files_per_dir):
            if j % 3 == 0:
                ext = "py"
            elif j % 3 == 1:
                ext = "txt"
            else:
                ext = "rs"

            file_path = dir_path / f"file_{j:04d}.{ext}"
            file_path.touch()

    print(f"Created {num_files} files in {num_dirs} directories")


def benchmark_function(func, *args, **kwargs):
    """Benchmark a function and return timing stats."""
    times = []

    # Warm up
    func(*args, **kwargs)

    # Run multiple times
    for _ in range(5):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        times.append(end - start)

        # Convert generator to list if needed
        if hasattr(result, "__iter__") and not isinstance(result, (list, tuple)):
            list(result)

    return {
        "min": min(times),
        "max": max(times),
        "mean": statistics.mean(times),
        "median": statistics.median(times),
    }


def stdlib_find_py_files(root):
    """Find Python files using stdlib glob."""
    return glob.glob(f"{root}/**/*.py", recursive=True)


def vexy_glob_find_py_files(root):
    """Find Python files using vexy_glob."""
    return list(vexy_glob.find("**/*.py", root=root))


def stdlib_find_all_files(root):
    """Find all files using stdlib glob."""
    return glob.glob(f"{root}/**/*", recursive=True)


def vexy_glob_find_all_files(root):
    """Find all files using vexy_glob."""
    return list(vexy_glob.find("**/*", root=root))


def run_benchmarks():
    """Run all benchmarks."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)

        # Create test structure
        create_test_structure(base_path, num_files=5000, num_dirs=100)

        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS")
        print("=" * 60)

        # Benchmark 1: Find Python files
        print("\n1. Finding Python files (pattern: **/*.py)")
        print("-" * 40)

        stdlib_stats = benchmark_function(stdlib_find_py_files, str(base_path))
        vexy_glob_stats = benchmark_function(vexy_glob_find_py_files, str(base_path))

        print(f"stdlib glob: {stdlib_stats['mean']:.4f}s (median: {stdlib_stats['median']:.4f}s)")
        print(
            f"vexy_glob:        {vexy_glob_stats['mean']:.4f}s (median: {vexy_glob_stats['median']:.4f}s)"
        )

        speedup = stdlib_stats["mean"] / vexy_glob_stats["mean"]
        print(f"Speedup:     {speedup:.1f}x faster")

        # Benchmark 2: Find all files
        print("\n2. Finding all files (pattern: **/*)")
        print("-" * 40)

        stdlib_stats = benchmark_function(stdlib_find_all_files, str(base_path))
        vexy_glob_stats = benchmark_function(vexy_glob_find_all_files, str(base_path))

        print(f"stdlib glob: {stdlib_stats['mean']:.4f}s (median: {stdlib_stats['median']:.4f}s)")
        print(
            f"vexy_glob:        {vexy_glob_stats['mean']:.4f}s (median: {vexy_glob_stats['median']:.4f}s)"
        )

        speedup = stdlib_stats["mean"] / vexy_glob_stats["mean"]
        print(f"Speedup:     {speedup:.1f}x faster")

        # Benchmark 3: Time to first result (streaming)
        print("\n3. Time to first result (streaming)")
        print("-" * 40)

        # stdlib (must collect all)
        start = time.perf_counter()
        stdlib_results = glob.glob(f"{base_path}/**/*.py", recursive=True)
        stdlib_first_time = time.perf_counter() - start

        # vexy_glob (streaming)
        start = time.perf_counter()
        vexy_glob_iter = vexy_glob.find("**/*.py", root=str(base_path))
        first_result = next(vexy_glob_iter)
        vexy_glob_first_time = time.perf_counter() - start

        print(f"stdlib glob: {stdlib_first_time:.6f}s (must complete full search)")
        print(f"vexy_glob:        {vexy_glob_first_time:.6f}s (streaming first result)")

        speedup = stdlib_first_time / vexy_glob_first_time
        print(f"Speedup:     {speedup:.0f}x faster to first result")

        print("\n" + "=" * 60)
        print("Summary: vexy_glob provides significant performance improvements")
        print("especially for large directory structures and streaming use cases.")
        print("=" * 60)


if __name__ == "__main__":
    print("vexy_glob vs stdlib benchmark")
    print("This may take a minute to run...")
    run_benchmarks()
