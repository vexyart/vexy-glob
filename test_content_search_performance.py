#!/usr/bin/env python3
# this_file: test_content_search_performance.py
#
# Test content search performance vs ripgrep to identify optimization opportunities

import time
import subprocess
import tempfile
import os
import statistics
from pathlib import Path
import vexy_glob
import shutil

def create_content_dataset(num_files: int) -> Path:
    """Create a dataset with realistic content for search testing"""
    temp_dir = Path(tempfile.mkdtemp(prefix=f"content_test_{num_files}_"))
    
    print(f"Creating {num_files} files with realistic content...")
    
    # Create various file types with searchable content
    for i in range(num_files):
        subdir = temp_dir / f"module_{i // 100}"
        subdir.mkdir(exist_ok=True)
        
        if i % 4 == 0:
            # Python files with classes and functions
            content = f"""# Python file {i}
import os
import sys

class UserManager{i}:
    def __init__(self):
        self.users = []
        
    def add_user(self, name):
        # TODO: validate user name
        self.users.append(name)
        
    class InnerClass:
        pass

def helper_function_{i}():
    # TODO: implement this
    return "helper"

class DatabaseManager{i}(object):
    '''Database management class'''
    def __init__(self):
        super().__init__()
"""
            (subdir / f"python_{i}.py").write_text(content)
            
        elif i % 4 == 1:
            # JavaScript files
            content = f"""// JavaScript file {i}
const express = require('express');

class APIController{i} {{
    constructor() {{
        this.routes = [];
    }}
    
    // TODO: add error handling
    setupRoutes() {{
        // class setup code here
        console.log('Setting up routes');
    }}
}}

class DatabaseHelper{i} extends BaseHelper {{
    connect() {{
        // TODO: connection logic
        return true;
    }}
}}

export {{ APIController{i}, DatabaseHelper{i} }};
"""
            (subdir / f"javascript_{i}.js").write_text(content)
            
        elif i % 4 == 2:
            # Text files with various patterns
            content = f"""Document {i}

This is a test document with various patterns.
TODO: Review this document
FIXME: Update the content

Some class references:
- UserManager class is used for users
- DatabaseManager class handles data
- class inheritance patterns

Email: user{i}@example.com
Phone: +1-555-{i:04d}

Notes:
TODO: Add more examples
class validation is important
"""
            (subdir / f"document_{i}.txt").write_text(content)
            
        else:
            # Code with mixed patterns
            content = f"""/* Mixed content file {i} */

// TODO: optimize this code
struct DataStructure{i} {{
    int value;
    char name[100];
}};

class ProcessorUnit{i} {{
public:
    ProcessorUnit{i}();
    ~ProcessorUnit{i}();
    
    // TODO: implement methods
    void process();
private:
    int data;
}};

// class factory pattern
template<class T>
class Factory{i} {{
    T* create() {{ return new T(); }}
}};
"""
            (subdir / f"mixed_{i}.cpp").write_text(content)
    
    return temp_dir

def benchmark_content_search(tool: str, pattern: str, dataset_dir: Path, file_pattern: str = "*", num_runs: int = 3):
    """Benchmark content search performance"""
    times = []
    results_counts = []
    
    for run in range(num_runs):
        if tool == "vexy_glob":
            start_time = time.perf_counter()
            # Use vexy_glob's search function
            results = list(vexy_glob.search(pattern, "*", str(dataset_dir)))
            end_time = time.perf_counter()
            
            times.append((end_time - start_time) * 1000)
            results_counts.append(len(results))
            
        elif tool == "ripgrep":
            start_time = time.perf_counter()
            try:
                result = subprocess.run([
                    'rg', pattern, str(dataset_dir), '--count-matches'
                ], capture_output=True, text=True, timeout=30)
                end_time = time.perf_counter()
                
                if result.returncode == 0:
                    # Count total matches from ripgrep output
                    lines = result.stdout.strip().split('\n')
                    total_matches = sum(int(line.split(':')[-1]) for line in lines if ':' in line)
                    times.append((end_time - start_time) * 1000)
                    results_counts.append(total_matches)
                else:
                    return None
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return None
    
    if not times:
        return None
        
    return {
        'tool': tool,
        'pattern': pattern,
        'mean_time': statistics.mean(times),
        'std_time': statistics.stdev(times) if len(times) > 1 else 0,
        'results_count': results_counts[0],
        'matches_per_second': results_counts[0] / (statistics.mean(times) / 1000) if statistics.mean(times) > 0 else 0
    }

def test_regex_patterns():
    """Test various regex patterns against ripgrep"""
    print("🔍 Testing Content Search Performance vs ripgrep")
    print("=" * 55)
    
    # Create test dataset
    dataset_size = 5000
    dataset_dir = create_content_dataset(dataset_size)
    
    # Test patterns from simple to complex
    test_patterns = [
        ("TODO", "Simple literal pattern"),
        ("class", "Simple word pattern"),
        ("class\\s+\\w+", "Complex regex: class followed by identifier"),
        ("\\b[A-Z]\\w*Manager\\d*", "Complex regex: Manager classes with numbers"),
        ("TODO.*implement", "Complex regex: TODO comments with implement"),
        ("class\\s+\\w+\\s*\\{", "Complex regex: class definitions with braces"),
        ("def\\s+\\w+\\(|function\\s+\\w+\\(", "Complex regex: function definitions")
    ]
    
    results = []
    
    try:
        for pattern, description in test_patterns:
            print(f"\n--- Testing: {description} ---")
            print(f"Pattern: {pattern}")
            
            # Test both tools
            vg_result = benchmark_content_search("vexy_glob", pattern, dataset_dir)
            rg_result = benchmark_content_search("ripgrep", pattern, dataset_dir)
            
            if vg_result:
                print(f"vexy_glob: {vg_result['mean_time']:.0f}ms, {vg_result['results_count']:,} matches")
            
            if rg_result:
                print(f"ripgrep:   {rg_result['mean_time']:.0f}ms, {rg_result['results_count']:,} matches")
            
            # Compare performance
            if vg_result and rg_result:
                speed_ratio = vg_result['mean_time'] / rg_result['mean_time']
                if speed_ratio < 1.0:
                    print(f"🏆 vexy_glob is {1/speed_ratio:.2f}x FASTER")
                else:
                    print(f"⚠️  vexy_glob is {speed_ratio:.2f}x slower")
                    
                # Check if result counts are similar (within 10%)
                count_diff = abs(vg_result['results_count'] - rg_result['results_count'])
                count_ratio = count_diff / max(vg_result['results_count'], rg_result['results_count'], 1)
                if count_ratio > 0.1:
                    print(f"⚠️  Significant result count difference: {count_ratio:.1%}")
            
            results.append({
                'pattern': pattern,
                'description': description,
                'vexy_glob': vg_result,
                'ripgrep': rg_result
            })
        
        # Summary analysis
        print("\n" + "=" * 70)
        print("📊 CONTENT SEARCH PERFORMANCE SUMMARY")
        print("=" * 70)
        
        print(f"{'Pattern':<25} {'vexy_glob':<12} {'ripgrep':<12} {'Ratio':<10} {'Winner':<15}")
        print("-" * 75)
        
        vexy_wins = 0
        rg_wins = 0
        performance_issues = []
        
        for result in results:
            pattern = result['pattern'][:24]  # Truncate for display
            vg = result['vexy_glob']
            rg = result['ripgrep']
            
            if vg and rg:
                ratio = vg['mean_time'] / rg['mean_time']
                if ratio < 1.0:
                    winner = f"vexy_glob {1/ratio:.1f}x"
                    vexy_wins += 1
                else:
                    winner = f"ripgrep {ratio:.1f}x"
                    rg_wins += 1
                    if ratio > 2.0:
                        performance_issues.append((result['description'], ratio))
                        
                print(f"{pattern:<25} {vg['mean_time']:<12.0f} {rg['mean_time']:<12.0f} {ratio:<10.2f} {winner:<15}")
            else:
                print(f"{pattern:<25} {'N/A':<12} {'N/A':<12} {'N/A':<10} {'N/A':<15}")
        
        print(f"\n🏆 FINAL SCORE:")
        print(f"vexy_glob wins: {vexy_wins}")
        print(f"ripgrep wins: {rg_wins}")
        
        if performance_issues:
            print(f"\n⚠️  PERFORMANCE ISSUES DETECTED:")
            for desc, ratio in performance_issues:
                print(f"  - {desc}: {ratio:.1f}x slower than ripgrep")
        
        # Overall assessment
        if vexy_wins > rg_wins:
            print("\n✅ vexy_glob content search is generally faster than ripgrep!")
        elif rg_wins > vexy_wins:
            print(f"\n⚠️  ripgrep is generally faster than vexy_glob content search")
            if performance_issues:
                print("📋 Optimization opportunities identified above")
        else:
            print("\n🤝 Performance is roughly equivalent")
    
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up test dataset...")
        if dataset_dir.exists():
            shutil.rmtree(dataset_dir)

if __name__ == "__main__":
    test_regex_patterns()
    print("\n✅ Content search performance analysis complete!")