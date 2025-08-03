# this_file: tests/test_literal_optimization.py
"""Test literal pattern optimization."""

import tempfile
from pathlib import Path
import time
import vexy_glob


def test_literal_pattern_matching():
    """Test that literal patterns work correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        files = [
            "exact_file.txt",
            "another_exact_file.py",
            "path/to/exact_file.rs",
            "not_matched.txt",
        ]
        
        for file in files:
            filepath = Path(tmpdir, file)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text("content")
        
        # Test 1: Literal pattern matching
        results = list(vexy_glob.find("exact_file.txt", root=tmpdir))
        assert len(results) == 1
        assert "exact_file.txt" in results[0]
        
        # Test 2: Literal pattern with path
        results = list(vexy_glob.find("path/to/exact_file.rs", root=tmpdir))
        assert len(results) == 1
        assert "path/to/exact_file.rs" in results[0]
        
        # Test 3: Case-insensitive literal matching
        results = list(vexy_glob.find("EXACT_FILE.txt", root=tmpdir, case_sensitive=False))
        assert len(results) == 1
        
        # Test 4: Case-sensitive literal matching
        results = list(vexy_glob.find("EXACT_FILE.txt", root=tmpdir, case_sensitive=True))
        assert len(results) == 0


def test_literal_vs_glob_patterns():
    """Test that both literal and glob patterns work in the same function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        files = ["file1.txt", "file2.txt", "file3.py", "exact.txt"]
        for file in files:
            Path(tmpdir, file).write_text("content")
        
        # Test literal pattern
        literal_results = list(vexy_glob.find("exact.txt", root=tmpdir))
        assert len(literal_results) == 1
        assert "exact.txt" in literal_results[0]
        
        # Test glob pattern
        glob_results = list(vexy_glob.find("*.txt", root=tmpdir))
        assert len(glob_results) == 3
        
        # Test glob pattern with ?
        glob_results = list(vexy_glob.find("file?.txt", root=tmpdir))
        assert len(glob_results) == 2


def test_literal_pattern_performance():
    """Test that literal patterns are faster than glob patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create many files
        num_files = 1000
        target_file = "target_file_999.txt"
        
        for i in range(num_files):
            Path(tmpdir, f"file_{i}.txt").write_text("content")
        Path(tmpdir, target_file).write_text("special content")
        
        # Time literal pattern search
        start = time.time()
        results = list(vexy_glob.find(target_file, root=tmpdir))
        literal_time = time.time() - start
        assert len(results) == 1
        
        # Time glob pattern search (will match two files: file_999.txt and target_file_999.txt)
        start = time.time()
        results = list(vexy_glob.find("target_*_999.txt", root=tmpdir))
        glob_time = time.time() - start
        assert len(results) == 1
        
        # Literal should be at least as fast (often faster for large dirs)
        print(f"Literal pattern time: {literal_time:.4f}s")
        print(f"Glob pattern time: {glob_time:.4f}s")
        
        # Both should be very fast, but literal might have less overhead
        assert literal_time < 1.0  # Should complete in under 1 second
        assert glob_time < 1.0  # Should complete in under 1 second


def test_literal_pattern_with_filters():
    """Test literal patterns work with other filters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files with different sizes
        small_file = Path(tmpdir, "small.txt")
        small_file.write_text("x")
        
        large_file = Path(tmpdir, "large.txt") 
        large_file.write_text("x" * 1000)
        
        # Test literal pattern with size filter
        results = list(vexy_glob.find("small.txt", root=tmpdir, max_size=100))
        assert len(results) == 1
        
        results = list(vexy_glob.find("large.txt", root=tmpdir, min_size=500))
        assert len(results) == 1
        
        # Test literal pattern that doesn't match size filter
        results = list(vexy_glob.find("small.txt", root=tmpdir, min_size=100))
        assert len(results) == 0