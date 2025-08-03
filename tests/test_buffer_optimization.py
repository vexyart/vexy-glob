# this_file: tests/test_buffer_optimization.py
"""Test buffer configuration optimization."""

import tempfile
from pathlib import Path
import time
import vexy_glob


def test_sorting_workload_performance():
    """Test that sorting workload is optimized differently."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create many files for sorting test
        num_files = 1000
        for i in range(num_files):
            Path(tmpdir, f"file_{i:04d}.txt").write_text("content")
        
        # Test sorting performance (should use larger channel buffer)
        start = time.time()
        results = list(vexy_glob.find("*.txt", root=tmpdir, sort="name"))
        sort_time = time.time() - start
        
        assert len(results) == num_files
        # Verify sorting works
        assert "file_0000.txt" in results[0]
        assert "file_0999.txt" in results[-1]
        
        # Should complete reasonably quickly with optimized buffers
        assert sort_time < 5.0  # Should be much faster than this
        print(f"Sorted {num_files} files in {sort_time:.3f}s")


def test_content_search_performance():
    """Test that content search workload is optimized."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with searchable content
        num_files = 100
        for i in range(num_files):
            if i % 10 == 0:
                Path(tmpdir, f"file_{i}.txt").write_text("target content here")
            else:
                Path(tmpdir, f"file_{i}.txt").write_text("other content")
        
        # Test content search performance (should use smaller channel buffer)
        start = time.time()
        results = list(vexy_glob.search("target", "*.txt", root=tmpdir))
        search_time = time.time() - start
        
        assert len(results) == 10  # Should find 10 files with target content
        
        # Should complete reasonably quickly
        assert search_time < 2.0
        print(f"Content search in {num_files} files took {search_time:.3f}s")


def test_standard_find_performance():
    """Test standard file finding performance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create directory structure
        for subdir in ["src", "tests", "docs"]:
            subdir_path = Path(tmpdir, subdir)
            subdir_path.mkdir()
            for i in range(50):
                (subdir_path / f"file_{i}.py").write_text("print('hello')")
        
        # Test standard find performance
        start = time.time()
        results = list(vexy_glob.find("*.py", root=tmpdir))
        find_time = time.time() - start
        
        assert len(results) == 150  # 3 subdirs * 50 files each
        
        # Should complete very quickly for standard finding
        assert find_time < 1.0
        print(f"Found {len(results)} files in {find_time:.3f}s")


def test_threading_scaling():
    """Test that buffer sizes scale with thread count."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files in many subdirectories
        for i in range(10):
            subdir = Path(tmpdir, f"dir_{i}")
            subdir.mkdir()
            for j in range(10):
                (subdir / f"file_{j}.txt").write_text("content")
        
        # Test with different thread counts
        for threads in [1, 2, 4]:
            start = time.time()
            results = list(vexy_glob.find("*.txt", root=tmpdir, threads=threads))
            duration = time.time() - start
            
            assert len(results) == 100
            print(f"With {threads} threads: {duration:.3f}s")
            
            # More threads should generally be faster (or at least not much slower)
            # This is a rough test - actual performance depends on many factors
            assert duration < 2.0


def test_memory_usage_stable():
    """Test that buffer optimizations don't cause memory issues."""
    import tracemalloc
    
    tracemalloc.start()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create many files
        for i in range(500):
            Path(tmpdir, f"file_{i}.txt").write_text("x" * 100)
        
        # Run various operations
        list(vexy_glob.find("*.txt", root=tmpdir))
        list(vexy_glob.find("*.txt", root=tmpdir, sort="name"))
        list(vexy_glob.search("x", "*.txt", root=tmpdir))
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory should be reasonable (less than 50MB for this test)
        assert peak < 50 * 1024 * 1024  # 50MB
        print(f"Peak memory usage: {peak / 1024 / 1024:.1f}MB")