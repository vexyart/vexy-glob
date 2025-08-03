# this_file: tests/test_same_file_system.py
"""Test same_file_system option to prevent crossing mount points."""

import os
import tempfile
from pathlib import Path
import pytest
import vexy_glob


def test_same_file_system_basic():
    """Test that same_file_system option is accepted."""
    # We can't easily test actual mount point crossing in unit tests
    # but we can verify the option is accepted without errors
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        base = Path(tmpdir)
        (base / "file1.txt").write_text("content1")
        (base / "subdir").mkdir()
        (base / "subdir" / "file2.txt").write_text("content2")
        
        # Test with same_file_system=True
        results = list(vexy_glob.find("**/*.txt", root=tmpdir, same_file_system=True))
        assert len(results) == 2
        
        # Test with same_file_system=False (default)
        results = list(vexy_glob.find("**/*.txt", root=tmpdir, same_file_system=False))
        assert len(results) == 2


def test_same_file_system_with_search():
    """Test that same_file_system works with content search."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        base = Path(tmpdir)
        (base / "test.txt").write_text("hello world")
        
        # Test with same_file_system=True
        results = list(vexy_glob.search(
            "hello", 
            "*.txt", 
            root=tmpdir, 
            same_file_system=True
        ))
        assert len(results) == 1
        assert results[0]["line_text"].strip() == "hello world"