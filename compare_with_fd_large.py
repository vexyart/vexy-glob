#!/usr/bin/env python3
# this_file: compare_with_fd_large.py
#
# Compare vexy_glob vs fd performance on larger datasets to validate current performance

import time
import subprocess
import tempfile
import os
import statistics
from pathlib import Path
import vexy_glob
import shutil

def create_test_dataset(num_files: int) -> Path:
    """Create a test dataset for comparison"""
    temp_dir = Path(tempfile.mkdtemp(prefix=f"compare_test_{num_files}_"))
    
    print(f"Creating {num_files} files...")
    
    for i in range(num_files):
        # Create nested directory structure
        subdir = temp_dir / f"dir_{i // 1000}"
        subdir.mkdir(exist_ok=True)
        
        # Create different file types
        if i % 3 == 0:
            (subdir / f"file_{i}.py").write_text(f"print({i})")
        elif i % 3 == 1:
            (subdir / f"file_{i}.js").write_text(f"console.log({i});")
        else:
            (subdir / f"file_{i}.txt").write_text(f"Content {i}")
    
    return temp_dir

def benchmark_tool(tool: str, pattern: str, dataset_dir: Path, num_runs: int = 3):
    """Benchmark a specific tool"""
    times = []
    results_counts = []
    
    for run in range(num_runs):
        if tool == "vexy_glob":
            start_time = time.perf_counter()
            results = list(vexy_glob.find(pattern, str(dataset_dir)))  
            end_time = time.perf_counter()
            
            times.append((end_time - start_time) * 1000)
            results_counts.append(len(results))
            
        elif tool == "fd":
            # Convert pattern for fd
            fd_pattern = pattern.replace('*', '')
            
            start_time = time.perf_counter()
            try:
                result = subprocess.run([
                    'fd', fd_pattern, str(dataset_dir)
                ], capture_output=True, text=True, timeout=30)
                end_time = time.perf_counter()
                
                if result.returncode == 0:
                    results = result.stdout.strip().split('\n') if result.stdout.strip() else []
                    times.append((end_time - start_time) * 1000)
                    results_counts.append(len(results))
                else:
                    return None
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return None
    
    if not times:
        return None
        
    return {
        'tool': tool,
        'mean_time': statistics.mean(times),
        'std_time': statistics.stdev(times) if len(times) > 1 else 0,
        'results_count': results_counts[0],
        'throughput': results_counts[0] / (statistics.mean(times) / 1000)
    }

def compare_performance():
    """Compare vexy_glob vs fd on different dataset sizes"""
    print("⚔️  vexy_glob vs fd Performance Comparison")
    print("=" * 50)
    
    dataset_sizes = [5000, 15000, 30000]
    pattern = "*.py"
    
    results = []
    datasets = []
    
    try:
        for size in dataset_sizes:
            print(f"\n--- Comparing on {size:,} files ---")
            
            # Create dataset
            dataset_dir = create_test_dataset(size)
            datasets.append(dataset_dir)
            
            # Benchmark both tools
            vg_result = benchmark_tool("vexy_glob", pattern, dataset_dir)
            fd_result = benchmark_tool("fd", pattern, dataset_dir)
            
            if vg_result:
                print(f"vexy_glob: {vg_result['mean_time']:.0f}ms, {vg_result['results_count']:,} results, {vg_result['throughput']:.0f} files/sec")
            
            if fd_result:
                print(f"fd:        {fd_result['mean_time']:.0f}ms, {fd_result['results_count']:,} results, {fd_result['throughput']:.0f} files/sec")
            
            # Calculate performance ratio
            if vg_result and fd_result:
                speed_ratio = vg_result['mean_time'] / fd_result['mean_time']
                if speed_ratio < 1.0:
                    print(f"🏆 vexy_glob is {1/speed_ratio:.2f}x FASTER than fd")
                else:
                    print(f"⚠️  vexy_glob is {speed_ratio:.2f}x slower than fd")
                    
                result_match = abs(vg_result['results_count'] - fd_result['results_count']) <= 1
                if not result_match:
                    print(f"⚠️  Result count mismatch: {vg_result['results_count']} vs {fd_result['results_count']}")
            
            results.append({
                'size': size,
                'vexy_glob': vg_result,
                'fd': fd_result
            })
        
        # Summary analysis
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 60)
        
        print(f"{'Dataset':<10} {'vexy_glob':<15} {'fd':<15} {'Ratio':<15} {'Winner':<10}")
        print("-" * 70)
        
        vexy_wins = 0
        fd_wins = 0
        
        for result in results:
            size = result['size']
            vg = result['vexy_glob']
            fd = result['fd']
            
            if vg and fd:
                ratio = vg['mean_time'] / fd['mean_time']
                if ratio < 1.0:
                    winner = f"vexy_glob ({1/ratio:.1f}x)"
                    vexy_wins += 1
                else:
                    winner = f"fd ({ratio:.1f}x)"
                    fd_wins += 1
                    
                print(f"{size:<10,} {vg['mean_time']:<15.0f} {fd['mean_time']:<15.0f} {ratio:<15.2f} {winner:<10}")
            else:
                print(f"{size:<10,} {'N/A':<15} {'N/A':<15} {'N/A':<15} {'N/A':<10}")
        
        print(f"\n🏆 FINAL SCORE:")
        print(f"vexy_glob wins: {vexy_wins}")
        print(f"fd wins: {fd_wins}")
        
        if vexy_wins > fd_wins:
            print("✅ vexy_glob is generally FASTER than fd!")
        elif fd_wins > vexy_wins:
            print("⚠️  fd is generally faster than vexy_glob")
        else:
            print("🤝 Performance is roughly equivalent")
    
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        for dataset in datasets:
            if dataset.exists():
                shutil.rmtree(dataset)

if __name__ == "__main__":
    compare_performance()
    print("\n✅ Comparison complete!")