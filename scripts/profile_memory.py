#!/usr/bin/env python3
# this_file: scripts/profile_memory.py
"""Profile memory allocations and identify hotspots in vexy_glob"""

import os
import sys
import time
import tempfile
import tracemalloc
import gc
from pathlib import Path
from typing import List, Dict, Tuple
import statistics

# Add parent directory to path for vexy_glob import
sys.path.insert(0, str(Path(__file__).parent.parent))
import vexy_glob

def create_large_test_structure(base_dir: Path, num_files: int = 10000) -> None:
    """Create a large test structure to stress memory allocation"""
    # Create nested directories
    dirs = []
    for i in range(10):
        for j in range(10):
            dir_path = base_dir / f"dir_{i:02d}" / f"subdir_{j:02d}"
            dir_path.mkdir(parents=True, exist_ok=True)
            dirs.append(dir_path)
    
    # Distribute files across directories
    for i in range(num_files):
        dir_idx = i % len(dirs)
        file_path = dirs[dir_idx] / f"file_{i:05d}.txt"
        file_path.write_text(f"Content of file {i}")

def profile_memory_basic():
    """Basic memory profiling using tracemalloc"""
    print("\n📊 Basic Memory Allocation Analysis")
    print("   " + "-" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test structure
        print("   Creating test structure (10,000 files)...", end='', flush=True)
        create_large_test_structure(temp_path, 10000)
        print(" done!")
        
        # Start memory profiling
        tracemalloc.start()
        gc.collect()
        
        # Take baseline snapshot
        snapshot_start = tracemalloc.take_snapshot()
        
        # Test 1: Iterator mode (streaming)
        print("\n   Test 1: Iterator mode (streaming)")
        file_count = 0
        for file_path in vexy_glob.find("**/*.txt", root=str(temp_path)):
            file_count += 1
        
        snapshot_iter = tracemalloc.take_snapshot()
        
        # Test 2: List mode (collecting all results)
        gc.collect()
        print("   Test 2: List mode (collecting all)")
        all_files = list(vexy_glob.find("**/*.txt", root=str(temp_path)))
        
        snapshot_list = tracemalloc.take_snapshot()
        
        # Analyze memory usage
        print("\n   Memory Usage Analysis:")
        print("   " + "-" * 60)
        
        # Iterator mode statistics
        stats_iter = snapshot_iter.compare_to(snapshot_start, 'lineno')
        current_iter, peak_iter = snapshot_iter.statistics('traceback')[0].size, snapshot_iter.statistics('traceback')[0].count
        
        print(f"   Iterator mode:")
        print(f"     Files processed: {file_count}")
        print(f"     Memory per 1K files: {peak_iter / (file_count / 1000):.2f} bytes")
        
        # List mode statistics
        stats_list = snapshot_list.compare_to(snapshot_iter, 'lineno')
        
        print(f"\n   List mode:")
        print(f"     Files collected: {len(all_files)}")
        
        # Top allocations
        print("\n   Top Memory Allocations (List mode):")
        for stat in stats_list[:5]:
            print(f"     {stat}")
        
        tracemalloc.stop()

def profile_allocation_patterns():
    """Profile specific allocation patterns"""
    print("\n🔬 Allocation Pattern Analysis")
    print("   " + "-" * 60)
    
    patterns = [
        ("Simple glob", "*.txt", 1000),
        ("Recursive glob", "**/*.txt", 10000),
        ("Complex pattern", "**/{test,spec}_*.{py,js,txt}", 5000),
        ("Deep recursion", "**/deep/**/file.txt", 5000),
    ]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_large_test_structure(temp_path, 10000)
        
        results = []
        
        for name, pattern, expected_files in patterns:
            gc.collect()
            tracemalloc.start()
            
            # Measure allocation during traversal
            start_memory = tracemalloc.get_traced_memory()[0]
            
            file_count = 0
            start_time = time.perf_counter()
            
            for _ in vexy_glob.find(pattern, root=str(temp_path)):
                file_count += 1
            
            end_time = time.perf_counter()
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            
            tracemalloc.stop()
            
            # Calculate metrics
            memory_used = peak_memory - start_memory
            duration = end_time - start_time
            memory_per_file = memory_used / file_count if file_count > 0 else 0
            
            results.append({
                'name': name,
                'pattern': pattern,
                'files': file_count,
                'memory_kb': memory_used / 1024,
                'duration_ms': duration * 1000,
                'bytes_per_file': memory_per_file
            })
        
        # Display results
        print(f"\n   {'Pattern Type':<20} {'Files':<10} {'Memory (KB)':<15} {'Bytes/File':<15}")
        print("   " + "-" * 60)
        
        for r in results:
            print(f"   {r['name']:<20} {r['files']:<10} {r['memory_kb']:<15.1f} {r['bytes_per_file']:<15.1f}")

def profile_channel_memory():
    """Profile crossbeam channel memory usage"""
    print("\n📡 Channel Buffer Memory Analysis")
    print("   " + "-" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_large_test_structure(temp_path, 5000)
        
        # Test different consumption rates
        print("   Testing different consumption patterns...")
        
        # Fast consumption (normal case)
        gc.collect()
        tracemalloc.start()
        
        fast_count = 0
        for _ in vexy_glob.find("**/*.txt", root=str(temp_path)):
            fast_count += 1
        
        fast_current, fast_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Slow consumption (simulate processing delay)
        gc.collect()
        tracemalloc.start()
        
        slow_count = 0
        for _ in vexy_glob.find("**/*.txt", root=str(temp_path)):
            slow_count += 1
            if slow_count % 100 == 0:
                time.sleep(0.001)  # Simulate processing
        
        slow_current, slow_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\n   Fast consumption:")
        print(f"     Files: {fast_count}")
        print(f"     Peak memory: {fast_peak / 1024:.1f} KB")
        
        print(f"\n   Slow consumption (with delays):")
        print(f"     Files: {slow_count}")
        print(f"     Peak memory: {slow_peak / 1024:.1f} KB")
        print(f"     Memory overhead: {((slow_peak - fast_peak) / fast_peak * 100):.1f}%")

def analyze_string_allocations():
    """Analyze string/path allocations specifically"""
    print("\n🔤 String/Path Allocation Analysis")
    print("   " + "-" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create files with varying path lengths
        for depth in [1, 5, 10, 20]:
            path = temp_path
            for i in range(depth):
                path = path / f"level_{i:02d}"
            path.mkdir(parents=True, exist_ok=True)
            
            # Create files at this depth
            for j in range(10):
                (path / f"file_{j:02d}.txt").touch()
        
        # Profile different path return modes
        print("   Comparing string vs Path object returns...")
        
        # String mode
        gc.collect()
        tracemalloc.start()
        string_results = list(vexy_glob.find("**/*.txt", root=str(temp_path), as_path=False))
        string_current, string_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Path mode
        gc.collect()
        tracemalloc.start()
        path_results = list(vexy_glob.find("**/*.txt", root=str(temp_path), as_path=True))
        path_current, path_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\n   String mode:")
        print(f"     Files: {len(string_results)}")
        print(f"     Memory: {string_peak / 1024:.1f} KB")
        print(f"     Per file: {string_peak / len(string_results):.1f} bytes")
        
        print(f"\n   Path object mode:")
        print(f"     Files: {len(path_results)}")
        print(f"     Memory: {path_peak / 1024:.1f} KB")
        print(f"     Per file: {path_peak / len(path_results):.1f} bytes")
        print(f"     Overhead: {((path_peak - string_peak) / string_peak * 100):.1f}%")

def main():
    print("💾 Memory Allocation Profiling for vexy_glob")
    print("=" * 80)
    
    # Run all profiling analyses
    profile_memory_basic()
    profile_allocation_patterns()
    profile_channel_memory()
    analyze_string_allocations()
    
    print("\n✅ Memory profiling complete!")
    
    # Recommendations
    print("\n💡 Memory Optimization Opportunities:")
    print("   1. String interning for repeated path components")
    print("   2. Object pooling for path objects in traversal")
    print("   3. Adaptive channel buffer sizing based on consumption rate")
    print("   4. Lazy path object creation (only when needed)")
    print("   5. Consider using Cow<str> for path components")

if __name__ == "__main__":
    main()