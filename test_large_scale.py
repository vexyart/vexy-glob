#!/usr/bin/env python3
# this_file: test_large_scale.py
#
# Test with larger datasets to find where performance degradation occurs

import time
import tempfile
import os
import statistics
from pathlib import Path
import vexy_glob
import shutil

def create_realistic_dataset(num_files: int) -> Path:
    """Create a more realistic test dataset with varied directory structure"""
    temp_dir = Path(tempfile.mkdtemp(prefix=f"vexy_large_test_{num_files}_"))
    
    print(f"Creating realistic dataset with {num_files} files...")
    
    # Create deeper directory structure like a real project
    for i in range(num_files):
        # Create nested structure like: src/module/submodule/
        level1 = temp_dir / f"src{i // 5000}" 
        level2 = level1 / f"module{i // 1000}"
        level3 = level2 / f"submodule{i // 200}"
        level3.mkdir(parents=True, exist_ok=True)
        
        # Create different file types with realistic names
        if i % 5 == 0:
            (level3 / f"main_{i}.py").write_text(f"# Main file {i}\nimport os\nprint('hello')")
        elif i % 5 == 1:
            (level3 / f"utils_{i}.py").write_text(f"# Utils file {i}\ndef helper():\n    pass")
        elif i % 5 == 2:
            (level3 / f"test_{i}.py").write_text(f"# Test file {i}\nimport unittest")
        elif i % 5 == 3:
            (level3 / f"config_{i}.js").write_text(f"// Config {i}\nmodule.exports = {{}};")
        else:
            (level3 / f"README_{i}.md").write_text(f"# Documentation {i}\nThis is a readme.")
    
    print(f"Created {num_files} files with deep directory structure in {temp_dir}")
    return temp_dir

def benchmark_large_datasets():
    """Test performance on increasingly large datasets"""
    print("🚀 Testing Large Scale Performance")
    print("=" * 50)
    
    # Test progressively larger datasets
    dataset_sizes = [10000, 20000, 40000]
    pattern = "*.py"
    
    results = []
    datasets = []
    
    try:
        for size in dataset_sizes:
            print(f"\n--- Testing {size:,} files ---")
            
            # Create dataset
            dataset_dir = create_realistic_dataset(size)
            datasets.append(dataset_dir)
            
            # Benchmark vexy_glob with warmup
            print("Warming up...")
            _ = list(vexy_glob.find(pattern, str(dataset_dir)))  # Warmup
            
            print("Running benchmark...")
            times = []
            counts = []
            
            for run in range(3):
                start_time = time.perf_counter()
                results_list = list(vexy_glob.find(pattern, str(dataset_dir)))
                end_time = time.perf_counter()
                
                time_ms = (end_time - start_time) * 1000
                times.append(time_ms)
                counts.append(len(results_list))
                
                print(f"  Run {run+1}: {time_ms:.0f}ms, {len(results_list):,} results")
            
            # Calculate statistics
            mean_time = statistics.mean(times)
            files_per_sec = counts[0] / (mean_time / 1000)
            
            result = {
                'size': size,
                'mean_time': mean_time,
                'files_per_sec': files_per_sec,
                'results_count': counts[0]
            }
            results.append(result)
            
            print(f"  Average: {mean_time:.0f}ms, {files_per_sec:.0f} files/sec")
            
            # Check for performance degradation
            if len(results) > 1:
                prev = results[-2]
                curr = results[-1]
                
                size_ratio = curr['size'] / prev['size']
                time_ratio = curr['mean_time'] / prev['mean_time']
                scaling_factor = time_ratio / size_ratio
                
                print(f"  Scaling factor: {scaling_factor:.2f}x")
                
                if scaling_factor > 2.0:
                    print(f"  ⚠️  SEVERE degradation: {scaling_factor:.2f}x worse than linear!")
                    break  # Stop testing larger sizes
                elif scaling_factor > 1.5:
                    print(f"  ⚠️  Performance degradation: {scaling_factor:.2f}x")
                else:
                    print(f"  ✅  Good scaling: {scaling_factor:.2f}x")
        
        # Final analysis
        print("\n" + "=" * 60)
        print("📊 LARGE SCALE PERFORMANCE ANALYSIS")
        print("=" * 60)
        
        print(f"{'Files':<10} {'Time':<12} {'Files/sec':<12} {'Results':<10} {'Scaling':<10}")
        print("-" * 55)
        
        for i, result in enumerate(results):
            scaling = ""
            if i > 0:
                prev = results[i-1]
                size_ratio = result['size'] / prev['size']
                time_ratio = result['mean_time'] / prev['mean_time']
                scaling_factor = time_ratio / size_ratio
                scaling = f"{scaling_factor:.2f}x"
            
            print(f"{result['size']:<10,} {result['mean_time']:<12.0f}ms {result['files_per_sec']:<12.0f} {result['results_count']:<10,} {scaling:<10}")
        
        # Performance analysis
        print(f"\n🎯 PERFORMANCE INSIGHTS:")
        
        # Calculate overall scaling from first to last
        if len(results) >= 2:
            first = results[0]
            last = results[-1]
            
            overall_size_ratio = last['size'] / first['size']
            overall_time_ratio = last['mean_time'] / first['mean_time']
            overall_scaling = overall_time_ratio / overall_size_ratio
            
            print(f"Overall scaling ({first['size']:,} → {last['size']:,} files): {overall_scaling:.2f}x")
            
            # Theoretical performance
            expected_time = first['mean_time'] * overall_size_ratio
            print(f"Expected linear time: {expected_time:.0f}ms")
            print(f"Actual time: {last['mean_time']:.0f}ms")
            print(f"Performance efficiency: {(expected_time / last['mean_time']) * 100:.0f}%")
            
            # Find the largest dataset with good performance
            max_good_size = first['size']
            for result in results:
                max_good_size = result['size']
                
            print(f"Largest tested dataset: {max_good_size:,} files")
            print(f"Peak throughput: {max(r['files_per_sec'] for r in results):.0f} files/sec")
    
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up {len(datasets)} test datasets...")
        for dataset in datasets:
            if dataset.exists():
                shutil.rmtree(dataset)
                print(f"  Removed {dataset.name}")

if __name__ == "__main__":
    benchmark_large_datasets()
    print("\n✅ Large scale testing complete!")