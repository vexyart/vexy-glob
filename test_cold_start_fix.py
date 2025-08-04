#!/usr/bin/env python3
# this_file: test_cold_start_fix.py
#
# Test script to validate that cold start variance has been reduced
# This tests the effectiveness of the global initialization fixes

import time
import statistics
import subprocess
import sys
from pathlib import Path

def test_cold_start_variance():
    """Test variance in cold start performance by running vexy_glob in fresh processes"""
    print("Testing cold start variance after global initialization fixes...")
    
    # Create test script that imports and uses vexy_glob
    test_script = """
import time
import vexy_glob

start_time = time.perf_counter()
results = list(vexy_glob.find('*.py', '.'))
end_time = time.perf_counter()

print(f"{(end_time - start_time) * 1000:.2f}")  # Print time in milliseconds
"""
    
    # Write test script to temp file
    script_path = Path("temp_cold_start_test.py")
    script_path.write_text(test_script)
    
    try:
        # Run multiple cold start tests
        times = []
        for i in range(10):
            print(f"Cold start test {i+1}/10...", end=" ")
            
            # Run in fresh Python process
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                time_ms = float(result.stdout.strip())
                times.append(time_ms)
                print(f"{time_ms:.2f}ms")
            else:
                print(f"ERROR: {result.stderr}")
                return False
        
        # Calculate statistics
        mean = statistics.mean(times)
        stdev = statistics.stdev(times) if len(times) > 1 else 0
        cv = (stdev / mean) * 100 if mean > 0 else 0
        min_time = min(times)
        max_time = max(times)
        range_ratio = max_time / min_time if min_time > 0 else 0
        
        print("\n=== Cold Start Performance Analysis ===")
        print(f"Mean time: {mean:.2f}ms")
        print(f"Std deviation: {stdev:.2f}ms")
        print(f"Coefficient of variance: {cv:.1f}%")
        print(f"Min time: {min_time:.2f}ms")
        print(f"Max time: {max_time:.2f}ms")
        print(f"Range ratio: {range_ratio:.1f}x")
        
        # Compare with baseline from variance analysis
        print("\n=== Comparison with Baseline (from VARIANCE_ANALYSIS.md) ===")
        baseline_cv = 111.0  # Cold start CV from analysis
        baseline_mean = 52.13  # Cold start mean from analysis
        baseline_range_ratio = 7.2  # Range ratio from analysis
        
        cv_improvement = (baseline_cv - cv) / baseline_cv * 100
        mean_improvement = (baseline_mean - mean) / baseline_mean * 100
        range_improvement = (baseline_range_ratio - range_ratio) / baseline_range_ratio * 100
        
        print(f"CV improvement: {cv_improvement:+.1f}% (target: >50% reduction)")
        print(f"Mean time improvement: {mean_improvement:+.1f}%")
        print(f"Range ratio improvement: {range_improvement:+.1f}% (target: >50% reduction)")
        
        # Success criteria
        success = True
        if cv > 55:  # Target: < 55% CV (50% improvement from 111%)
            print(f"❌ CV still too high: {cv:.1f}% > 55%")
            success = False
        else:
            print(f"✅ CV improved sufficiently: {cv:.1f}% ≤ 55%")
            
        if range_ratio > 3.6:  # Target: < 3.6x range (50% improvement from 7.2x)
            print(f"❌ Range ratio still too high: {range_ratio:.1f}x > 3.6x")
            success = False
        else:
            print(f"✅ Range ratio improved sufficiently: {range_ratio:.1f}x ≤ 3.6x")
        
        return success
        
    finally:
        # Cleanup
        if script_path.exists():
            script_path.unlink()

def test_warm_start_performance():
    """Test warm start performance within a single process"""
    print("\n\nTesting warm start performance (within single process)...")
    
    import vexy_glob
    
    # Warm up the system
    list(vexy_glob.find('*.py', '.'))
    
    # Run multiple warm tests
    times = []
    for i in range(10):
        start_time = time.perf_counter()
        results = list(vexy_glob.find('*.py', '.'))
        end_time = time.perf_counter()
        
        time_ms = (end_time - start_time) * 1000
        times.append(time_ms)
        print(f"Warm test {i+1}/10: {time_ms:.2f}ms")
    
    # Calculate statistics
    mean = statistics.mean(times)
    stdev = statistics.stdev(times) if len(times) > 1 else 0
    cv = (stdev / mean) * 100 if mean > 0 else 0
    
    print(f"\nWarm start stats: Mean={mean:.2f}ms, CV={cv:.1f}%")
    
    # Compare with baseline
    baseline_warm_cv = 50.3
    baseline_warm_mean = 28.84
    
    print(f"Baseline warm CV: {baseline_warm_cv:.1f}%")
    print(f"Baseline warm mean: {baseline_warm_mean:.2f}ms")
    
    cv_improvement = (baseline_warm_cv - cv) / baseline_warm_cv * 100
    mean_improvement = (baseline_warm_mean - mean) / baseline_warm_mean * 100
    
    print(f"Warm CV improvement: {cv_improvement:+.1f}%")
    print(f"Warm mean improvement: {mean_improvement:+.1f}%")

if __name__ == "__main__":
    print("🔥 Testing Cold Start Performance Fixes")
    print("=" * 50)
    
    cold_start_success = test_cold_start_variance()
    test_warm_start_performance()
    
    print("\n" + "=" * 50)
    if cold_start_success:
        print("🎉 SUCCESS: Cold start variance has been significantly reduced!")
        print("✅ Global initialization fixes are working effectively")
    else:
        print("⚠️  PARTIAL: Some improvements made but variance still high")
        print("🔧 Additional optimizations may be needed")