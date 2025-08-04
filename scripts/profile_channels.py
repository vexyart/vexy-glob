#!/usr/bin/env python3
# this_file: scripts/profile_channels.py
"""Profile crossbeam channel overhead and buffer utilization patterns"""

import os
import sys
import time
import threading
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple
import statistics
import queue

# Add parent directory to path for vexy_glob import
sys.path.insert(0, str(Path(__file__).parent.parent))
import vexy_glob

def create_test_files(base_dir: Path, num_files: int) -> None:
    """Create test files for benchmarking"""
    for i in range(num_files):
        dir_depth = i % 5  # Vary directory depth
        path = base_dir
        for d in range(dir_depth):
            path = path / f"dir_{d}"
        path.mkdir(parents=True, exist_ok=True)
        (path / f"file_{i:05d}.txt").touch()

def measure_channel_throughput():
    """Measure the throughput characteristics of the channel"""
    print("\n📊 Channel Throughput Analysis")
    print("   " + "-" * 60)
    
    file_counts = [100, 1000, 5000, 10000]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        results = []
        
        for num_files in file_counts:
            # Clear and recreate test structure
            for item in temp_path.iterdir():
                if item.is_dir():
                    import shutil
                    shutil.rmtree(item)
            
            create_test_files(temp_path, num_files)
            
            # Measure immediate consumption (best case)
            start = time.perf_counter()
            immediate_count = 0
            for _ in vexy_glob.find("**/*.txt", root=str(temp_path)):
                immediate_count += 1
            immediate_time = time.perf_counter() - start
            
            # Measure with artificial delays (worst case)
            start = time.perf_counter()
            delayed_count = 0
            for _ in vexy_glob.find("**/*.txt", root=str(temp_path)):
                delayed_count += 1
                if delayed_count % 50 == 0:
                    time.sleep(0.001)  # 1ms delay every 50 files
            delayed_time = time.perf_counter() - start
            
            results.append({
                'files': num_files,
                'immediate_time': immediate_time,
                'delayed_time': delayed_time,
                'immediate_throughput': num_files / immediate_time,
                'delayed_throughput': num_files / delayed_time,
                'overhead_ratio': delayed_time / immediate_time
            })
            
            print(f"   {num_files:5d} files: {immediate_time:6.3f}s immediate, "
                  f"{delayed_time:6.3f}s delayed (ratio: {delayed_time/immediate_time:.2f}x)")
        
        # Analysis
        print("\n   Throughput Summary:")
        print(f"   {'Files':<10} {'Immediate':<15} {'Delayed':<15} {'Overhead':<10}")
        print("   " + "-" * 60)
        for r in results:
            print(f"   {r['files']:<10} {r['immediate_throughput']:>10.0f}/s   "
                  f"{r['delayed_throughput']:>10.0f}/s   {r['overhead_ratio']:>6.2f}x")

def analyze_buffer_behavior():
    """Analyze how the buffer behaves under different consumption patterns"""
    print("\n🎯 Buffer Behavior Analysis")
    print("   " + "-" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_test_files(temp_path, 5000)
        
        # Test 1: Burst consumption
        print("   Test 1: Burst consumption pattern")
        burst_times = []
        total_files = 0
        
        gen = vexy_glob.find("**/*.txt", root=str(temp_path))
        
        # Consume in bursts
        for burst in range(10):
            time.sleep(0.05)  # 50ms pause between bursts
            
            start = time.perf_counter()
            burst_count = 0
            for _ in range(500):  # Consume 500 at a time
                try:
                    next(gen)
                    burst_count += 1
                except StopIteration:
                    break
            burst_time = time.perf_counter() - start
            
            if burst_count > 0:
                burst_times.append(burst_time / burst_count * 1000)  # ms per file
                total_files += burst_count
        
        if burst_times:
            print(f"     Average time per file in burst: {statistics.mean(burst_times):.3f}ms")
            print(f"     Variation (std dev): {statistics.stdev(burst_times):.3f}ms")
        
        # Test 2: Steady consumption
        print("\n   Test 2: Steady consumption pattern")
        steady_times = []
        
        gen = vexy_glob.find("**/*.txt", root=str(temp_path))
        
        for i in range(1000):
            try:
                start = time.perf_counter()
                next(gen)
                steady_time = (time.perf_counter() - start) * 1000
                steady_times.append(steady_time)
                time.sleep(0.001)  # 1ms between each file
            except StopIteration:
                break
        
        if steady_times:
            print(f"     Average time per file: {statistics.mean(steady_times):.3f}ms")
            print(f"     Min/Max: {min(steady_times):.3f}ms / {max(steady_times):.3f}ms")

def profile_backpressure():
    """Test how the system handles backpressure"""
    print("\n⏸️  Backpressure Analysis")
    print("   " + "-" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_test_files(temp_path, 10000)
        
        # Test with no consumption (maximum backpressure)
        print("   Testing maximum backpressure scenario...")
        
        collected_files = []
        collection_times = []
        
        # Collect files in batches with delays
        gen = vexy_glob.find("**/*.txt", root=str(temp_path))
        
        for batch in range(20):
            batch_start = time.perf_counter()
            batch_files = []
            
            # Collect 500 files
            for _ in range(500):
                try:
                    batch_files.append(next(gen))
                except StopIteration:
                    break
            
            batch_time = time.perf_counter() - batch_start
            
            if batch_files:
                collected_files.extend(batch_files)
                collection_times.append(batch_time)
                
                # Simulate processing delay
                time.sleep(0.1)  # 100ms processing time
            else:
                break
        
        if collection_times:
            print(f"     Total files collected: {len(collected_files)}")
            print(f"     Average batch collection time: {statistics.mean(collection_times)*1000:.1f}ms")
            print(f"     First batch time: {collection_times[0]*1000:.1f}ms")
            print(f"     Last batch time: {collection_times[-1]*1000:.1f}ms")
            
            # Check if there's performance degradation
            if collection_times[-1] > collection_times[0] * 1.5:
                print("     ⚠️  Performance degradation detected under backpressure")
            else:
                print("     ✅ Performance remains stable under backpressure")

def analyze_concurrent_access():
    """Test concurrent access patterns"""
    print("\n🔄 Concurrent Access Analysis")
    print("   " + "-" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_test_files(temp_path, 5000)
        
        # Test multiple concurrent finds
        print("   Testing multiple concurrent find operations...")
        
        def run_find(pattern, results_queue):
            start = time.perf_counter()
            count = len(list(vexy_glob.find(pattern, root=str(temp_path))))
            duration = time.perf_counter() - start
            results_queue.put((pattern, count, duration))
        
        patterns = ["*.txt", "**/*.txt", "**/file_0*.txt", "**/dir_2/*.txt"]
        threads = []
        results_queue = queue.Queue()
        
        # Start all threads simultaneously
        start_all = time.perf_counter()
        for pattern in patterns:
            thread = threading.Thread(target=run_find, args=(pattern, results_queue))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        total_time = time.perf_counter() - start_all
        
        # Collect results
        print(f"\n   Concurrent execution results (total time: {total_time:.3f}s):")
        print(f"   {'Pattern':<20} {'Files':<10} {'Time':<10} {'Files/sec':<15}")
        print("   " + "-" * 60)
        
        while not results_queue.empty():
            pattern, count, duration = results_queue.get()
            throughput = count / duration if duration > 0 else 0
            print(f"   {pattern:<20} {count:<10} {duration:<10.3f} {throughput:>10.0f}/s")

def main():
    print("📡 Crossbeam Channel Performance Analysis")
    print("=" * 80)
    
    # Run all analyses
    measure_channel_throughput()
    analyze_buffer_behavior()
    profile_backpressure()
    analyze_concurrent_access()
    
    print("\n✅ Channel analysis complete!")
    
    # Recommendations
    print("\n💡 Channel Optimization Recommendations:")
    print("   1. Adaptive buffer sizing based on consumption rate")
    print("   2. Consider bounded channel with dynamic capacity adjustment")
    print("   3. Implement backpressure feedback to slow producer if needed")
    print("   4. Optimize for burst consumption patterns (common in practice)")
    print("   5. Consider using crossbeam's array_queue for fixed-size scenarios")

if __name__ == "__main__":
    main()