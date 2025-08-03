#!/usr/bin/env python3
# this_file: demo.py
"""
Demo script showing vexy_glob capabilities.
"""

import vexy_glob
from pathlib import Path
import time


def demo_basic_usage():
    """Demonstrate basic vexy_glob usage."""
    print("=== Basic Usage Demo ===\n")

    print("1. Finding all Python files in the project:")
    for path in vexy_glob.find("**/*.py", max_depth=3):
        print(f"  {path}")

    print("\n2. Finding files in specific directory with extension filter:")
    for path in vexy_glob.find("*", root="vexy_glob", extension="py"):
        print(f"  {path}")

    print("\n3. Using as drop-in glob replacement:")
    py_files = vexy_glob.glob("**/*.py", recursive=True)
    print(f"  Found {len(py_files)} Python files")

    print("\n4. Getting Path objects instead of strings:")
    for path in vexy_glob.find("*.md", as_path=True, max_depth=1):
        print(f"  {path} (size: {path.stat().st_size} bytes)")


def demo_streaming():
    """Demonstrate streaming capabilities."""
    print("\n=== Streaming Demo ===\n")

    print("Finding files with streaming (results appear immediately):")
    iterator = vexy_glob.find("**/*", max_depth=2)

    count = 0
    start_time = time.time()

    for path in iterator:
        count += 1
        if count <= 5:
            elapsed = (time.time() - start_time) * 1000
            print(f"  Result {count}: {Path(path).name} (after {elapsed:.1f}ms)")
        elif count == 6:
            print("  ...")

        if count >= 10:  # Stop after 10 for demo
            break

    total_time = (time.time() - start_time) * 1000
    print(f"\nStreamed {count} results in {total_time:.1f}ms")


def demo_filters():
    """Demonstrate filtering capabilities."""
    print("\n=== Filtering Demo ===\n")

    print("1. Finding only directories:")
    dirs = list(vexy_glob.find("*", file_type="d", max_depth=2))
    print(f"  Found {len(dirs)} directories")

    print("\n2. Finding only files (no directories):")
    files = list(vexy_glob.find("*", file_type="f", max_depth=1))
    print(f"  Found {len(files)} files in root")

    print("\n3. Finding with max depth control:")
    shallow = list(vexy_glob.find("**/*", max_depth=1))
    deep = list(vexy_glob.find("**/*", max_depth=3))
    print(f"  Depth 1: {len(shallow)} items")
    print(f"  Depth 3: {len(deep)} items")


def demo_performance():
    """Demonstrate performance compared to stdlib."""
    print("\n=== Performance Demo ===\n")

    import glob

    pattern = "**/*.py"
    root = "."

    # Time stdlib glob
    start = time.perf_counter()
    stdlib_results = glob.glob(f"{root}/{pattern}", recursive=True)
    stdlib_time = time.perf_counter() - start

    # Time vexy_glob
    start = time.perf_counter()
    vexy_glob_results = list(vexy_glob.find(pattern, root=root))
    vexy_glob_time = time.perf_counter() - start

    print(f"Finding Python files:")
    print(f"  stdlib glob: {stdlib_time:.4f}s ({len(stdlib_results)} files)")
    print(f"  vexy_glob:        {vexy_glob_time:.4f}s ({len(vexy_glob_results)} files)")

    if vexy_glob_time > 0:
        speedup = stdlib_time / vexy_glob_time
        print(f"  Speedup:     {speedup:.1f}x")

    # Time to first result
    print(f"\nTime to first result:")

    start = time.perf_counter()
    stdlib_first = glob.glob(f"{root}/{pattern}", recursive=True)[0]
    stdlib_first_time = time.perf_counter() - start

    start = time.perf_counter()
    vexy_glob_first = next(vexy_glob.find(pattern, root=root))
    vexy_glob_first_time = time.perf_counter() - start

    print(f"  stdlib glob: {stdlib_first_time:.6f}s (complete search required)")
    print(f"  vexy_glob:        {vexy_glob_first_time:.6f}s (streaming)")

    if vexy_glob_first_time > 0:
        speedup = stdlib_first_time / vexy_glob_first_time
        print(f"  Speedup:     {speedup:.0f}x faster")


def main():
    """Run all demos."""
    print("🚀 vexy_glob - Path Accelerated Finding in Rust")
    print("High-performance file finding for Python\n")

    try:
        demo_basic_usage()
        demo_streaming()
        demo_filters()
        demo_performance()

        print("\n" + "=" * 50)
        print("✨ Demo complete! Try running the benchmark:")
        print("   python benchmarks/compare_stdlib.py")
        print("=" * 50)

    except Exception as e:
        print(f"Demo error: {e}")
        print("Make sure to build the extension with: maturin develop")


if __name__ == "__main__":
    main()
