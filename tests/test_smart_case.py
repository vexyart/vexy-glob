# this_file: tests/test_smart_case.py
"""Test smart-case matching functionality."""

import tempfile
from pathlib import Path
import pytest
import vexy_glob


def test_smart_case_lowercase_pattern():
    """Test that lowercase patterns match case-insensitively."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with different cases but unique names to avoid filesystem conflicts
        Path(tmpdir, "test_lower.txt").write_text("content")
        Path(tmpdir, "Test_title.txt").write_text("content")
        Path(tmpdir, "TEST_upper.txt").write_text("content")
        Path(tmpdir, "TeSt_mixed.txt").write_text("content")
        
        # Lowercase pattern should match all variations when case-insensitive
        results = list(vexy_glob.find("*test*.txt", root=tmpdir, case_sensitive=None))
        # Since pattern is lowercase, it should be case-insensitive and match all
        assert len(results) == 4
        
        # Verify with explicit case-insensitive
        results = list(vexy_glob.find("*test*.txt", root=tmpdir, case_sensitive=False))
        assert len(results) == 4


def test_smart_case_uppercase_pattern():
    """Test that patterns with uppercase match case-sensitively."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with different cases but unique names
        Path(tmpdir, "test_lower.txt").write_text("content")
        Path(tmpdir, "Test_title.txt").write_text("content")
        Path(tmpdir, "TEST_upper.txt").write_text("content")
        Path(tmpdir, "TeSt_mixed.txt").write_text("content")
        
        # Pattern with uppercase should be case-sensitive
        results = list(vexy_glob.find("*Test*.txt", root=tmpdir, case_sensitive=None))
        assert len(results) == 1
        assert "Test_title.txt" in results[0]
        
        # Different uppercase pattern
        results = list(vexy_glob.find("*TEST*.txt", root=tmpdir, case_sensitive=None))
        assert len(results) == 1
        assert "TEST_upper.txt" in results[0]


def test_smart_case_mixed_pattern():
    """Test mixed case patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with unique names
        Path(tmpdir, "ReadMe_mixed.md").write_text("content")
        Path(tmpdir, "readme_lower.md").write_text("content")
        Path(tmpdir, "README_upper.md").write_text("content")
        
        # Mixed case pattern should be case-sensitive
        results = list(vexy_glob.find("*ReadMe*.md", root=tmpdir, case_sensitive=None))
        assert len(results) == 1
        assert "ReadMe_mixed.md" in results[0]


def test_smart_case_with_wildcards():
    """Test smart case with wildcard patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with unique names
        Path(tmpdir, "setup_lower.py").write_text("content")
        Path(tmpdir, "Setup_title.py").write_text("content")
        Path(tmpdir, "SETUP_upper.py").write_text("content")
        Path(tmpdir, "test_lower.py").write_text("content")
        Path(tmpdir, "Test_title.py").write_text("content")
        
        # Lowercase wildcard pattern - case insensitive
        results = list(vexy_glob.find("*.py", root=tmpdir, case_sensitive=None))
        assert len(results) == 5
        
        # Pattern with uppercase - case sensitive
        results = list(vexy_glob.find("*S*.py", root=tmpdir, case_sensitive=None))
        assert len(results) == 2  # Setup_title.py and SETUP_upper.py
        # Check that we got the files with uppercase S
        basenames = [Path(r).name for r in results]
        assert "Setup_title.py" in basenames
        assert "SETUP_upper.py" in basenames


def test_smart_case_explicit_sensitive():
    """Test explicit case_sensitive=True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "test_lower.txt").write_text("content")
        Path(tmpdir, "Test_title.txt").write_text("content")
        
        # Explicit case sensitive
        results = list(vexy_glob.find("*test*.txt", root=tmpdir, case_sensitive=True))
        assert len(results) == 1
        assert "test_lower.txt" in results[0]


def test_smart_case_explicit_insensitive():
    """Test explicit case_sensitive=False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "test_lower.txt").write_text("content")
        Path(tmpdir, "Test_title.txt").write_text("content")
        Path(tmpdir, "TEST_upper.txt").write_text("content")
        
        # Explicit case insensitive - even with uppercase pattern
        results = list(vexy_glob.find("*TEST*.txt", root=tmpdir, case_sensitive=False))
        assert len(results) == 3


def test_smart_case_content_search():
    """Test smart case with content search."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with different content cases
        Path(tmpdir, "file1.txt").write_text("hello world")
        Path(tmpdir, "file2.txt").write_text("Hello World")
        Path(tmpdir, "file3.txt").write_text("HELLO WORLD")
        
        # Lowercase content pattern - case insensitive
        results = list(vexy_glob.search("hello", "*.txt", root=tmpdir, case_sensitive=None))
        assert len(results) == 3
        
        # Uppercase content pattern - case sensitive
        results = list(vexy_glob.search("Hello", "*.txt", root=tmpdir, case_sensitive=None))
        assert len(results) == 1
        assert "file2.txt" in results[0]["path"]


def test_smart_case_both_patterns():
    """Test smart case with both glob and content patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with unique names
        Path(tmpdir, "test_lower.txt").write_text("hello world")
        Path(tmpdir, "Test_title.txt").write_text("Hello World")
        Path(tmpdir, "TEST_upper.txt").write_text("HELLO WORLD")
        
        # Both patterns lowercase - case insensitive for both
        results = list(vexy_glob.search("hello", "*test*.txt", root=tmpdir, case_sensitive=None))
        assert len(results) == 3
        
        # Glob uppercase, content lowercase
        # Glob is case-sensitive (matches only Test_title.txt)
        # Content is case-insensitive (matches "Hello World")
        results = list(vexy_glob.search("hello", "*Test*.txt", root=tmpdir, case_sensitive=None))
        assert len(results) == 1  # Test_title.txt matches because content search is case-insensitive
        assert "Test_title.txt" in results[0]["path"]
        
        # Glob lowercase, content uppercase - case sensitive due to content
        results = list(vexy_glob.search("HELLO", "*test*.txt", root=tmpdir, case_sensitive=None))
        assert len(results) == 1
        assert "TEST_upper.txt" in results[0]["path"]