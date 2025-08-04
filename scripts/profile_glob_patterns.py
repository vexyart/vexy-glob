#!/usr/bin/env python3
# this_file: scripts/profile_glob_patterns.py
"""Profile glob pattern compilation and matching performance"""

import os
import sys
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple
import statistics

# Add parent directory to path for vexy_glob import
sys.path.insert(0, str(Path(__file__).parent.parent))
import vexy_glob

# Test patterns of varying complexity
PATTERN_TESTS = [
    # (pattern, description, expected_complexity)
    ("*.txt", "Simple extension match", "low"),
    ("file_*.txt", "Literal prefix + wildcard", "low"),
    ("**/file.txt", "Recursive exact filename", "medium"),
    ("**/*.py", "Recursive extension match", "medium"),
    ("src/**/*.{js,ts,jsx,tsx}", "Multiple extensions with brace expansion", "high"),
    ("**/test_*.{py,js}", "Recursive prefix + multiple extensions", "high"),
    ("{src,lib,test}/**/*.{py,js,ts}", "Multiple roots + extensions", "very_high"),
    ("**/{test,spec}_*.{js,ts,py}", "Complex nested patterns", "very_high"),
]

def create_test_files(base_dir: Path, num_files: int = 1000) -> List[Path]:
    """Create a realistic file structure for testing"""
    extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.txt', '.md', '.json']
    prefixes = ['test_', 'spec_', 'file_', 'index_', 'main_', '']
    dirs = [
        'src', 'lib', 'test', 'tests', 'spec', 'docs',
        'src/components', 'src/utils', 'lib/helpers',
        'test/unit', 'test/integration'
    ]
    
    # Create directories
    for d in dirs:
        (base_dir / d).mkdir(parents=True, exist_ok=True)
    
    # Create files
    files = []
    for i in range(num_files):
        dir_idx = i % len(dirs)
        ext_idx = i % len(extensions)
        prefix_idx = i % len(prefixes)
        
        filename = f"{prefixes[prefix_idx]}file_{i:04d}{extensions[ext_idx]}"
        filepath = base_dir / dirs[dir_idx] / filename
        filepath.touch()
        files.append(filepath)
    
    return files

def benchmark_pattern(pattern: str, test_dir: Path, warmup_runs: int = 3, test_runs: int = 10) -> Dict:
    """Benchmark a single glob pattern"""
    # Warmup runs
    for _ in range(warmup_runs):
        list(vexy_glob.find(pattern, root=str(test_dir)))
    
    # Test runs
    times = []
    file_counts = []
    
    for _ in range(test_runs):
        start = time.perf_counter()
        results = list(vexy_glob.find(pattern, root=str(test_dir)))
        end = time.perf_counter()
        
        times.append(end - start)
        file_counts.append(len(results))
    
    # Calculate statistics
    avg_time = statistics.mean(times)
    std_time = statistics.stdev(times) if len(times) > 1 else 0
    min_time = min(times)
    max_time = max(times)
    file_count = file_counts[0]  # Should be consistent
    
    return {
        'pattern': pattern,
        'avg_time': avg_time,
        'std_time': std_time,
        'min_time': min_time,
        'max_time': max_time,
        'file_count': file_count,
        'throughput': file_count / avg_time if avg_time > 0 else 0,
        'times': times
    }

def analyze_pattern_compilation():
    """Analyze pattern compilation overhead by testing with empty directories"""
    print("\n🔬 Pattern Compilation Analysis")
    print("   Testing compilation overhead with empty directory...")
    print("   " + "-" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        results = []
        
        for pattern, description, complexity in PATTERN_TESTS:
            # Test with empty directory to isolate compilation time
            start = time.perf_counter()
            list(vexy_glob.find(pattern, root=temp_dir))
            end = time.perf_counter()
            
            compilation_time = (end - start) * 1000  # Convert to ms
            results.append((pattern, description, complexity, compilation_time))
        
        # Sort by compilation time
        results.sort(key=lambda x: x[3])
        
        print(f"   {'Pattern':<35} {'Complexity':<12} {'Time (ms)':<10}")
        print("   " + "-" * 60)
        for pattern, desc, complexity, comp_time in results:
            print(f"   {pattern:<35} {complexity:<12} {comp_time:>8.3f}")
        
        # Analysis
        simple_times = [r[3] for r in results if r[2] == "low"]
        complex_times = [r[3] for r in results if r[2] in ["high", "very_high"]]
        
        if simple_times and complex_times:
            overhead_ratio = statistics.mean(complex_times) / statistics.mean(simple_times)
            print(f"\n   💡 Complex patterns take {overhead_ratio:.1f}x longer to compile")

def analyze_matching_performance():
    """Analyze pattern matching performance with real files"""
    print("\n🏃 Pattern Matching Performance")
    print("   Testing with 1000 files in realistic directory structure...")
    print("   " + "-" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files
        print("   Creating test files...", end='', flush=True)
        create_test_files(temp_path, 1000)
        print(" done!")
        
        results = []
        
        # Benchmark each pattern
        for pattern, description, complexity in PATTERN_TESTS:
            print(f"   Testing: {pattern:<35}", end='', flush=True)
            result = benchmark_pattern(pattern, temp_path)
            result['description'] = description
            result['complexity'] = complexity
            results.append(result)
            print(f" {result['file_count']:>4} files, {result['avg_time']*1000:>6.1f}ms")
        
        # Summary table
        print("\n   📊 Performance Summary")
        print("   " + "-" * 80)
        print(f"   {'Pattern':<35} {'Files':<8} {'Avg(ms)':<10} {'Throughput':<15}")
        print("   " + "-" * 80)
        
        for r in results:
            print(f"   {r['pattern']:<35} {r['file_count']:<8} "
                  f"{r['avg_time']*1000:<10.1f} {r['throughput']:>10.0f} files/s")
        
        # Complexity analysis
        print("\n   📈 Complexity Impact Analysis")
        print("   " + "-" * 80)
        
        complexity_groups = {}
        for r in results:
            if r['complexity'] not in complexity_groups:
                complexity_groups[r['complexity']] = []
            complexity_groups[r['complexity']].append(r['throughput'])
        
        for complexity in ['low', 'medium', 'high', 'very_high']:
            if complexity in complexity_groups:
                avg_throughput = statistics.mean(complexity_groups[complexity])
                print(f"   {complexity.capitalize():<15} complexity: {avg_throughput:>10.0f} files/s average")

def analyze_pattern_caching():
    """Test if patterns are cached effectively"""
    print("\n🗄️  Pattern Caching Analysis")
    print("   Testing repeated pattern usage...")
    print("   " + "-" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_test_files(temp_path, 100)  # Smaller dataset for caching test
        
        pattern = "**/*.py"
        
        # First run times
        first_runs = []
        for i in range(5):
            start = time.perf_counter()
            list(vexy_glob.find(pattern, root=str(temp_path)))
            end = time.perf_counter()
            first_runs.append((end - start) * 1000)
            time.sleep(0.01)  # Small delay between runs
        
        # Repeated run times (should benefit from caching)
        repeated_runs = []
        for i in range(20):
            start = time.perf_counter()
            list(vexy_glob.find(pattern, root=str(temp_path)))
            end = time.perf_counter()
            repeated_runs.append((end - start) * 1000)
        
        avg_first = statistics.mean(first_runs)
        avg_repeated = statistics.mean(repeated_runs)
        improvement = ((avg_first - avg_repeated) / avg_first) * 100 if avg_first > 0 else 0
        
        print(f"   First 5 runs average: {avg_first:.2f}ms")
        print(f"   Next 20 runs average: {avg_repeated:.2f}ms")
        print(f"   Performance improvement: {improvement:.1f}%")
        
        if improvement > 10:
            print("   ✅ Pattern caching appears to be effective")
        else:
            print("   ⚠️  No significant caching benefit detected")

def main():
    print("🔍 Glob Pattern Performance Analysis")
    print("=" * 80)
    
    # Run all analyses
    analyze_pattern_compilation()
    print()
    analyze_matching_performance()
    print()
    analyze_pattern_caching()
    
    print("\n✅ Pattern analysis complete!")
    
    # Recommendations
    print("\n💡 Optimization Recommendations:")
    print("   1. Consider pre-compiling frequently used patterns")
    print("   2. Optimize brace expansion parsing for complex patterns")
    print("   3. Implement pattern complexity detection for adaptive optimization")
    print("   4. Cache compiled patterns with LRU eviction")

if __name__ == "__main__":
    main()