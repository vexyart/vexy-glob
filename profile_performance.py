#!/usr/bin/env python
# this_file: profile_performance.py
"""Profile vexy_glob performance to identify hot paths."""

import cProfile
import tempfile
from pathlib import Path
import vexy_glob


def create_test_environment():
    """Create a large test environment for profiling."""
    print("Creating test environment...")
    tmpdir = tempfile.mkdtemp()
    
    # Create a realistic file structure
    for i in range(20):  # 20 top-level dirs
        main_dir = Path(tmpdir, f"project_{i}")
        main_dir.mkdir()
        
        # Create subdirectories
        for subdir in ["src", "tests", "docs", "build", ".git"]:
            sub_path = main_dir / subdir
            sub_path.mkdir()
            
            # Create files in each subdirectory
            for j in range(50):  # 50 files per subdir
                if subdir == "src":
                    (sub_path / f"module_{j}.py").write_text(f"def function_{j}(): pass\n# target content\n")
                elif subdir == "tests":
                    (sub_path / f"test_{j}.py").write_text(f"def test_{j}(): assert True\n")
                elif subdir == "docs":
                    (sub_path / f"doc_{j}.md").write_text(f"# Documentation {j}\ntarget content here\n")
                else:
                    (sub_path / f"file_{j}.txt").write_text("some content\n")
    
    print(f"Created test environment at {tmpdir}")
    print(f"Total structure: 20 dirs × 5 subdirs × 50 files = 5000 files")
    return tmpdir


def profile_file_finding(tmpdir):
    """Profile file finding operations."""
    print("\n=== Profiling File Finding ===")
    
    def find_python_files():
        results = list(vexy_glob.find("*.py", root=tmpdir))
        print(f"Found {len(results)} Python files")
        return results
    
    pr = cProfile.Profile()
    pr.enable()
    find_python_files()
    pr.disable()
    
    print("Top 10 hottest paths for file finding:")
    import pstats
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats(10)


def profile_content_search(tmpdir):
    """Profile content search operations."""
    print("\n=== Profiling Content Search ===")
    
    def search_target_content():
        results = list(vexy_glob.search("target", "*.py", root=tmpdir))
        print(f"Found {len(results)} files with target content")
        return results
    
    pr = cProfile.Profile()
    pr.enable()
    search_target_content()
    pr.disable()
    
    print("Top 10 hottest paths for content search:")
    import pstats
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats(10)


def profile_sorting_operations(tmpdir):
    """Profile sorting operations."""
    print("\n=== Profiling Sorting Operations ===")
    
    def sort_by_name():
        results = list(vexy_glob.find("*.txt", root=tmpdir, sort="name"))
        print(f"Sorted {len(results)} files by name")
        return results
    
    pr = cProfile.Profile()
    pr.enable()
    sort_by_name()
    pr.disable()
    
    print("Top 10 hottest paths for sorting:")
    import pstats
    stats = pstats.Stats(pr)
    stats.sort_stats('cumulative')
    stats.print_stats(10)


def benchmark_operations(tmpdir):
    """Benchmark different operations for comparison."""
    import time
    
    print("\n=== Performance Benchmarks ===")
    
    # Benchmark file finding
    start = time.time()
    py_results = list(vexy_glob.find("*.py", root=tmpdir))
    py_time = time.time() - start
    
    start = time.time()
    txt_results = list(vexy_glob.find("*.txt", root=tmpdir))
    txt_time = time.time() - start
    
    start = time.time()
    sorted_results = list(vexy_glob.find("*.py", root=tmpdir, sort="name"))
    sort_time = time.time() - start
    
    start = time.time()
    search_results = list(vexy_glob.search("target", "*.py", root=tmpdir))
    search_time = time.time() - start
    
    print(f"File finding (*.py): {len(py_results)} files in {py_time:.3f}s")
    print(f"File finding (*.txt): {len(txt_results)} files in {txt_time:.3f}s")
    print(f"Sorted finding: {len(sorted_results)} files in {sort_time:.3f}s")
    print(f"Content search: {len(search_results)} matches in {search_time:.3f}s")
    
    # Calculate throughput
    total_files_scanned = 5000  # From our test structure
    print(f"\nThroughput:")
    print(f"File finding: {total_files_scanned / py_time:.0f} files/sec")
    print(f"Content search: {total_files_scanned / search_time:.0f} files/sec")


if __name__ == "__main__":
    tmpdir = create_test_environment()
    
    try:
        # Run benchmarks first to get baseline numbers
        benchmark_operations(tmpdir)
        
        # Profile individual operations
        profile_file_finding(tmpdir)
        profile_content_search(tmpdir)
        profile_sorting_operations(tmpdir)
        
        print(f"\nTest environment preserved at: {tmpdir}")
        print("You can manually clean it up when done.")
        
    except Exception as e:
        print(f"Error during profiling: {e}")
        import shutil
        shutil.rmtree(tmpdir)
        raise