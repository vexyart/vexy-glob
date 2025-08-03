# this_file: tests/test_sorting.py
"""Test result sorting functionality."""

import os
import tempfile
import time
from pathlib import Path
import pytest
import vexy_glob


def test_sort_by_name():
    """Test sorting results by filename."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with different names
        files = ["zebra.txt", "apple.txt", "banana.txt", "cherry.txt"]
        for filename in files:
            Path(tmpdir, filename).write_text("content")
        
        # Test sorting by name
        results = list(vexy_glob.find("*.txt", root=tmpdir, sort="name"))
        basenames = [os.path.basename(r) for r in results]
        assert basenames == ["apple.txt", "banana.txt", "cherry.txt", "zebra.txt"]


def test_sort_by_path():
    """Test sorting results by full path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create nested structure
        base = Path(tmpdir)
        (base / "b_dir").mkdir()
        (base / "a_dir").mkdir()
        (base / "c_dir").mkdir()
        
        (base / "b_dir" / "file.txt").write_text("b")
        (base / "a_dir" / "file.txt").write_text("a")
        (base / "c_dir" / "file.txt").write_text("c")
        (base / "root.txt").write_text("root")
        
        # Test sorting by path
        results = list(vexy_glob.find("**/*.txt", root=tmpdir, sort="path"))
        # Extract relative paths
        rel_paths = [os.path.relpath(r, tmpdir) for r in results]
        
        # Should be sorted alphabetically by full path
        expected = ["a_dir/file.txt", "b_dir/file.txt", "c_dir/file.txt", "root.txt"]
        assert rel_paths == expected


def test_sort_by_size():
    """Test sorting results by file size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with different sizes
        files = [
            ("small.txt", "a"),
            ("medium.txt", "b" * 100),
            ("large.txt", "c" * 1000),
            ("tiny.txt", ""),
        ]
        
        for filename, content in files:
            Path(tmpdir, filename).write_text(content)
        
        # Test sorting by size
        results = list(vexy_glob.find("*.txt", root=tmpdir, sort="size"))
        basenames = [os.path.basename(r) for r in results]
        # Should be sorted by size (ascending)
        assert basenames == ["tiny.txt", "small.txt", "medium.txt", "large.txt"]


def test_sort_by_mtime():
    """Test sorting results by modification time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with different mtimes
        files = ["first.txt", "second.txt", "third.txt", "fourth.txt"]
        
        for i, filename in enumerate(files):
            path = Path(tmpdir, filename)
            path.write_text("content")
            # Add small delay to ensure different mtimes
            time.sleep(0.01)
        
        # Test sorting by mtime
        results = list(vexy_glob.find("*.txt", root=tmpdir, sort="mtime"))
        basenames = [os.path.basename(r) for r in results]
        # Should be sorted by mtime (oldest first)
        assert basenames == files


def test_sort_forces_collection():
    """Test that sorting forces collection (returns list not iterator)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        for i in range(5):
            Path(tmpdir, f"file{i}.txt").write_text("content")
        
        # Without sort and as_list=False, should return iterator
        results_iter = vexy_glob.find("*.txt", root=tmpdir)
        assert hasattr(results_iter, "__next__")
        
        # With sort, should return list even if as_list=False
        results_sorted = vexy_glob.find("*.txt", root=tmpdir, sort="name")
        assert isinstance(results_sorted, list)


def test_sort_with_as_path():
    """Test sorting with Path objects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        files = ["zebra.txt", "apple.txt", "banana.txt"]
        for filename in files:
            Path(tmpdir, filename).write_text("content")
        
        # Test sorting with as_path=True
        results = vexy_glob.find("*.txt", root=tmpdir, sort="name", as_path=True)
        assert all(isinstance(p, Path) for p in results)
        
        # Check order
        basenames = [p.name for p in results]
        assert basenames == ["apple.txt", "banana.txt", "zebra.txt"]


def test_invalid_sort_option():
    """Test that invalid sort option raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "test.txt").write_text("content")
        
        # Invalid sort option should raise VexyGlobError
        with pytest.raises(vexy_glob.VexyGlobError, match="Invalid sort option"):
            list(vexy_glob.find("*.txt", root=tmpdir, sort="invalid"))


def test_sort_empty_results():
    """Test sorting with no matching files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # No files created
        results = vexy_glob.find("*.txt", root=tmpdir, sort="name")
        assert results == []


def test_sort_mixed_types():
    """Test sorting with mixed file types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files and directories
        Path(tmpdir, "file1.txt").write_text("content")
        Path(tmpdir, "dir1").mkdir()
        Path(tmpdir, "file2.txt").write_text("content")
        Path(tmpdir, "dir2").mkdir()
        
        # Sort all entries by name (excluding hidden files)
        results = vexy_glob.find("*", root=tmpdir, sort="name")
        basenames = [os.path.basename(r) for r in results]
        # Filter out the temp directory itself if it appears
        basenames = [b for b in basenames if b.startswith(("file", "dir"))]
        assert basenames == ["dir1", "dir2", "file1.txt", "file2.txt"]