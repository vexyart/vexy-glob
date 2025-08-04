#!/usr/bin/env python3
# this_file: scripts/profile_fs_quick.py
"""Quick filesystem-specific performance profiling for vexy_glob"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
import tracemalloc

# Add parent directory to path for vexy_glob import
sys.path.insert(0, str(Path(__file__).parent.parent))
import vexy_glob

def create_test_structure(base_dir: Path, structure_type: str):
    """Create different filesystem structures for testing"""
    if structure_type == "shallow":
        # 1000 files in a single directory
        for i in range(1000):
            (base_dir / f"file_{i:04d}.txt").touch()
    
    elif structure_type == "deep":
        # 20 levels deep with 5 files per level
        current = base_dir
        for level in range(20):
            current = current / f"level_{level:02d}"
            current.mkdir()
            for i in range(5):
                (current / f"file_{i}.txt").touch()
    
    elif structure_type == "mixed":
        # Realistic project structure
        dirs = [
            "src/components", "src/lib", "src/utils",
            "tests/unit", "tests/integration",
            "docs", "config", ".github/workflows"
        ]
        for d in dirs:
            (base_dir / d).mkdir(parents=True)
            # Add 5-10 files per directory
            for i in range(5):
                (base_dir / d / f"file_{i}.js").touch()
                (base_dir / d / f"test_{i}.py").touch()
    
    elif structure_type == "case_sensitive":
        # Test case sensitivity on APFS
        files = ["test.txt", "Test.txt", "TEST.txt", "TeSt.txt"]
        for f in files:
            (base_dir / f).touch()

def profile_traversal(test_dir: Path, pattern: str, description: str):
    """Profile a specific traversal pattern"""
    print(f"\n📊 {description}")
    print(f"   Directory: {test_dir}")
    print(f"   Pattern: {pattern}")
    print("   " + "-" * 40)
    
    # Warm-up run
    list(vexy_glob.find(pattern, root=str(test_dir)))
    
    # Timed runs
    times = []
    for run in range(3):
        start = time.perf_counter()
        results = list(vexy_glob.find(pattern, root=str(test_dir)))
        end = time.perf_counter()
        times.append(end - start)
    
    avg_time = sum(times) / len(times)
    file_count = len(results)
    
    print(f"   Files found: {file_count}")
    print(f"   Average time: {avg_time:.3f}s")
    print(f"   Throughput: {file_count/avg_time:.0f} files/second")
    print(f"   Individual runs: {[f'{t:.3f}s' for t in times]}")
    
    return {
        "description": description,
        "file_count": file_count,
        "avg_time": avg_time,
        "throughput": file_count / avg_time if avg_time > 0 else 0
    }

def analyze_memory_usage(test_dir: Path, pattern: str):
    """Analyze memory usage during traversal"""
    tracemalloc.start()
    
    # Take initial snapshot
    snapshot1 = tracemalloc.take_snapshot()
    
    # Perform traversal
    results = 0
    for _ in vexy_glob.find(pattern, root=str(test_dir)):
        results += 1
    
    # Take final snapshot
    snapshot2 = tracemalloc.take_snapshot()
    
    # Analyze differences
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    current, peak = tracemalloc.get_traced_memory()
    
    tracemalloc.stop()
    
    return {
        "files_processed": results,
        "current_memory_mb": current / 1024 / 1024,
        "peak_memory_mb": peak / 1024 / 1024,
        "top_allocations": top_stats[:3]
    }

def main():
    print("🔍 Filesystem Performance Analysis for vexy_glob")
    print("=" * 50)
    
    # Get filesystem info
    if sys.platform == "darwin":
        import subprocess
        fs_info = subprocess.check_output(
            ["diskutil", "info", "/"], text=True
        )
        fs_type = "APFS" if "APFS" in fs_info else "Unknown"
        print(f"📁 Filesystem: {fs_type} (macOS)")
    else:
        print(f"📁 Platform: {sys.platform}")
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory(prefix="vexy_glob_fs_test_") as temp_dir:
        temp_path = Path(temp_dir)
        
        results = []
        
        # Test 1: Shallow directory
        print("\n🏗️  Test 1: Shallow directory structure")
        shallow_dir = temp_path / "shallow"
        shallow_dir.mkdir()
        create_test_structure(shallow_dir, "shallow")
        results.append(profile_traversal(
            shallow_dir, "*.txt", 
            "Shallow traversal (1000 files, 1 level)"
        ))
        
        # Test 2: Deep directory
        print("\n🏗️  Test 2: Deep directory structure")
        deep_dir = temp_path / "deep"
        deep_dir.mkdir()
        create_test_structure(deep_dir, "deep")
        results.append(profile_traversal(
            deep_dir, "**/*.txt",
            "Deep traversal (100 files, 20 levels)"
        ))
        
        # Test 3: Mixed project structure
        print("\n🏗️  Test 3: Mixed project structure")
        mixed_dir = temp_path / "mixed"
        mixed_dir.mkdir()
        create_test_structure(mixed_dir, "mixed")
        results.append(profile_traversal(
            mixed_dir, "**/*.js",
            "Project traversal (mixed structure)"
        ))
        
        # Test 4: Case sensitivity (APFS only)
        if sys.platform == "darwin":
            print("\n🏗️  Test 4: Case sensitivity test")
            case_dir = temp_path / "case"
            case_dir.mkdir()
            create_test_structure(case_dir, "case_sensitive")
            
            # Test case-insensitive pattern
            results.append(profile_traversal(
                case_dir, "*est.txt",
                "Case-insensitive pattern matching"
            ))
        
        # Memory analysis
        print("\n💾 Memory Usage Analysis")
        print("   " + "-" * 40)
        mem_stats = analyze_memory_usage(shallow_dir, "*.txt")
        print(f"   Files processed: {mem_stats['files_processed']}")
        print(f"   Peak memory: {mem_stats['peak_memory_mb']:.2f} MB")
        print(f"   Memory per 1K files: {mem_stats['peak_memory_mb'] / (mem_stats['files_processed'] / 1000):.2f} MB")
        
        # Summary
        print("\n📈 Performance Summary")
        print("   " + "-" * 40)
        for result in results:
            print(f"   {result['description']}: {result['throughput']:.0f} files/sec")
        
        # Filesystem-specific insights
        print("\n🔍 Filesystem-Specific Insights")
        print("   " + "-" * 40)
        
        # Compare shallow vs deep performance
        if len(results) >= 2:
            shallow_perf = results[0]['throughput']
            deep_perf = results[1]['throughput']
            ratio = shallow_perf / deep_perf if deep_perf > 0 else 0
            print(f"   Shallow vs Deep performance ratio: {ratio:.1f}x")
            print(f"   → Shallow traversal is {ratio:.1f}x faster")
            
            if ratio > 20:
                print("   ⚠️  High ratio indicates significant overhead for deep hierarchies")
                print("   💡 Consider optimizing for directory depth")

if __name__ == "__main__":
    main()