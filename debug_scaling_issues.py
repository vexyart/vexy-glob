#!/usr/bin/env python3
# this_file: debug_scaling_issues.py
#
# Debug script to investigate performance scaling issues on larger datasets
# Focus on the 4.5x slower performance vs fd on medium/large datasets

import time
import subprocess
import tempfile
import os
import statistics
from pathlib import Path
import vexy_glob

def create_test_dataset(num_files: int, pattern: str = "test") -> Path:
    """Create a test dataset with specified number of files"""
    temp_dir = Path(tempfile.mkdtemp(prefix=f"vexy_test_{num_files}_"))
    
    print(f"Creating test dataset with {num_files} files in {temp_dir}")
    
    # Create directory structure with files
    for i in range(num_files):
        # Create nested directory structure
        subdir = temp_dir / f"subdir_{i // 100}"
        subdir.mkdir(exist_ok=True)
        
        # Create different file types
        if i % 4 == 0:
            (subdir / f"{pattern}_{i}.py").write_text(f"# Python file {i}\nprint('hello')")
        elif i % 4 == 1:
            (subdir / f"{pattern}_{i}.js").write_text(f"// JavaScript file {i}\nconsole.log('hello');")
        elif i % 4 == 2:
            (subdir / f"{pattern}_{i}.txt").write_text(f"Text file {i}\nHello world!")
        else:
            (subdir / f"other_{i}.rs").write_text(f"// Rust file {i}\nfn main() {{}}")
    
    print(f"Created {num_files} files in {temp_dir}")
    return temp_dir

def benchmark_vexy_glob(dataset_dir: Path, pattern: str, num_runs: int = 3) -> dict:
    """Benchmark vexy_glob performance"""
    print(f"Benchmarking vexy_glob with pattern '{pattern}' on {dataset_dir}")
    
    times = []
    results_counts = []
    
    for run in range(num_runs):
        start_time = time.perf_counter()
        results = list(vexy_glob.find(pattern, str(dataset_dir)))
        end_time = time.perf_counter()
        
        time_ms = (end_time - start_time) * 1000
        times.append(time_ms)
        results_counts.append(len(results))
        
        print(f"  Run {run+1}: {time_ms:.1f}ms, {len(results)} results")
    
    return {
        'tool': 'vexy_glob',
        'pattern': pattern,
        'times': times,
        'mean_time': statistics.mean(times),
        'std_time': statistics.stdev(times) if len(times) > 1 else 0,
        'results_count': results_counts[0],  # Should be consistent
        'files_per_second': results_counts[0] / (statistics.mean(times) / 1000) if statistics.mean(times) > 0 else 0
    }

def benchmark_fd(dataset_dir: Path, pattern: str, num_runs: int = 3) -> dict:
    """Benchmark fd performance"""
    print(f"Benchmarking fd with pattern '{pattern}' on {dataset_dir}")
    
    times = []
    results_counts = []
    
    # Convert glob pattern to fd format
    fd_pattern = pattern.replace('*', '')  # fd uses regex, not glob
    
    for run in range(num_runs):
        start_time = time.perf_counter()
        
        try:
            result = subprocess.run([
                'fd', fd_pattern, str(dataset_dir)
            ], capture_output=True, text=True, timeout=30)
            
            end_time = time.perf_counter()
            
            if result.returncode == 0:
                results = result.stdout.strip().split('\n') if result.stdout.strip() else []
                time_ms = (end_time - start_time) * 1000
                times.append(time_ms)
                results_counts.append(len(results))
                
                print(f"  Run {run+1}: {time_ms:.1f}ms, {len(results)} results")
            else:
                print(f"  Run {run+1}: fd failed with error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"  Run {run+1}: fd timed out")
            return None
        except FileNotFoundError:
            print("  fd not found - skipping fd benchmark")
            return None
    
    return {
        'tool': 'fd',
        'pattern': pattern,
        'times': times,
        'mean_time': statistics.mean(times),
        'std_time': statistics.stdev(times) if len(times) > 1 else 0,
        'results_count': results_counts[0],
        'files_per_second': results_counts[0] / (statistics.mean(times) / 1000) if statistics.mean(times) > 0 else 0
    }

def profile_vexy_glob_scaling():
    """Profile vexy_glob performance across different dataset sizes"""
    print("🔍 Profiling vexy_glob scaling performance")
    print("=" * 60)
    
    dataset_sizes = [1000, 5000, 10000]
    pattern = "*.py"
    
    results = []
    datasets = []
    
    try:
        # Create datasets
        for size in dataset_sizes:
            dataset = create_test_dataset(size)
            datasets.append(dataset)
            
            print(f"\n--- Testing dataset size: {size} files ---")
            
            # Benchmark vexy_glob
            vexy_result = benchmark_vexy_glob(dataset, pattern)
            
            # Benchmark fd if available
            fd_result = benchmark_fd(dataset, pattern)
            
            # Store results
            result_entry = {
                'dataset_size': size,
                'vexy_glob': vexy_result,
                'fd': fd_result
            }
            results.append(result_entry)
            
            # Calculate performance ratio
            if fd_result and vexy_result:
                speed_ratio = vexy_result['mean_time'] / fd_result['mean_time']
                print(f"Performance ratio (vexy_glob/fd): {speed_ratio:.2f}x")
                if speed_ratio > 2.0:
                    print(f"⚠️  WARNING: vexy_glob is {speed_ratio:.1f}x slower than fd")
        
        # Analysis
        print("\n" + "=" * 60)
        print("📊 SCALING ANALYSIS")
        print("=" * 60)
        
        print(f"{'Dataset Size':<12} {'vexy_glob':<15} {'fd':<15} {'Ratio':<10} {'Files/sec (vg)':<15}")
        print("-" * 70)
        
        for result in results:
            size = result['dataset_size']
            vg = result['vexy_glob']
            fd = result['fd']
            
            if fd:
                ratio = vg['mean_time'] / fd['mean_time']
                print(f"{size:<12} {vg['mean_time']:<15.1f}ms {fd['mean_time']:<15.1f}ms {ratio:<10.2f}x {vg['files_per_second']:<15.0f}")
            else:
                print(f"{size:<12} {vg['mean_time']:<15.1f}ms {'N/A':<15} {'N/A':<10} {vg['files_per_second']:<15.0f}")
        
        # Identify scaling issues
        print("\n🔍 SCALING ISSUES DETECTED:")
        vexy_times = [r['vexy_glob']['mean_time'] for r in results]
        
        for i in range(1, len(results)):
            prev_size = results[i-1]['dataset_size']
            curr_size = results[i]['dataset_size']
            prev_time = results[i-1]['vexy_glob']['mean_time']
            curr_time = results[i]['vexy_glob']['mean_time']
            
            size_ratio = curr_size / prev_size
            time_ratio = curr_time / prev_time
            
            expected_linear_time = prev_time * size_ratio
            scaling_factor = time_ratio / size_ratio
            
            print(f"  {prev_size}→{curr_size} files: {scaling_factor:.2f}x scaling factor")
            print(f"    Expected (linear): {expected_linear_time:.1f}ms, Actual: {curr_time:.1f}ms")
            
            if scaling_factor > 1.5:
                print(f"    ⚠️  Poor scaling: {scaling_factor:.2f}x worse than linear")
            elif scaling_factor > 1.2:
                print(f"    ⚠️  Sublinear scaling: {scaling_factor:.2f}x")
            else:
                print(f"    ✅ Good scaling: {scaling_factor:.2f}x")
    
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up test datasets...")
        for dataset in datasets:
            if dataset.exists():
                import shutil
                shutil.rmtree(dataset)
                print(f"  Removed {dataset}")

def profile_memory_usage():
    """Profile memory usage during large dataset processing"""
    print("\n🧠 Memory Usage Profiling")
    print("=" * 40)
    
    import tracemalloc
    
    # Create a medium dataset
    dataset = create_test_dataset(5000)
    
    try:
        # Start memory tracking
        tracemalloc.start()
        
        print("Starting memory profiling...")
        start_snapshot = tracemalloc.take_snapshot()
        
        # Run vexy_glob
        start_time = time.perf_counter()
        results = list(vexy_glob.find("*.py", str(dataset)))
        end_time = time.perf_counter()
        
        end_snapshot = tracemalloc.take_snapshot()
        
        # Calculate memory usage
        top_stats = end_snapshot.compare_to(start_snapshot, 'lineno')
        total_memory = sum(stat.size_diff for stat in top_stats) / 1024 / 1024  # MB
        
        print(f"Time: {(end_time - start_time) * 1000:.1f}ms")
        print(f"Results: {len(results)}")
        print(f"Memory usage: {total_memory:.2f} MB")
        print(f"Memory per result: {total_memory * 1024 / len(results):.2f} KB") 
        
        # Show top memory allocations
        print("\nTop 5 memory allocations:")
        for stat in top_stats[:5]:
            print(f"  {stat.size_diff / 1024:.1f} KB: {stat.traceback.format()[-1]}")
    
    finally:
        import shutil
        shutil.rmtree(dataset)
        tracemalloc.stop()

if __name__ == "__main__":
    print("🐛 Debugging vexy_glob Scaling Issues")
    print("=" * 50)
    
    profile_vexy_glob_scaling()
    profile_memory_usage()
    
    print("\n✅ Analysis complete!")
    print("Check the results above to identify performance bottlenecks.")