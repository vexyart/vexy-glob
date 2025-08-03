# this_file: tests/test_size_filtering.py
"""Test file size filtering functionality."""

import os
import tempfile
from pathlib import Path
import pytest
import vexy_glob


def create_test_files_with_sizes(base_dir):
    """Create test files with specific sizes."""
    files = []

    # Small file (100 bytes)
    small_file = base_dir / "small.txt"
    small_file.write_text("x" * 100)
    files.append(("small.txt", 100))

    # Medium file (1000 bytes)
    medium_file = base_dir / "medium.txt"
    medium_file.write_text("y" * 1000)
    files.append(("medium.txt", 1000))

    # Large file (10000 bytes)
    large_file = base_dir / "large.txt"
    large_file.write_text("z" * 10000)
    files.append(("large.txt", 10000))

    # Empty file (0 bytes)
    empty_file = base_dir / "empty.txt"
    empty_file.touch()
    files.append(("empty.txt", 0))

    # Create a directory (should not be affected by size filtering)
    subdir = base_dir / "subdir"
    subdir.mkdir()

    return files


def test_min_size_filtering():
    """Test filtering files by minimum size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        create_test_files_with_sizes(base_dir)

        # Find files >= 500 bytes
        results = list(vexy_glob.find("*.txt", root=tmpdir, min_size=500))
        names = [Path(r).name for r in results]

        assert len(results) == 2
        assert "medium.txt" in names
        assert "large.txt" in names
        assert "small.txt" not in names
        assert "empty.txt" not in names


def test_max_size_filtering():
    """Test filtering files by maximum size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        create_test_files_with_sizes(base_dir)

        # Find files <= 500 bytes
        results = list(vexy_glob.find("*.txt", root=tmpdir, max_size=500))
        names = [Path(r).name for r in results]

        assert len(results) == 2
        assert "small.txt" in names
        assert "empty.txt" in names
        assert "medium.txt" not in names
        assert "large.txt" not in names


def test_size_range_filtering():
    """Test filtering files by size range."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        create_test_files_with_sizes(base_dir)

        # Find files between 100 and 5000 bytes
        results = list(vexy_glob.find("*.txt", root=tmpdir, min_size=100, max_size=5000))
        names = [Path(r).name for r in results]

        assert len(results) == 2
        assert "small.txt" in names
        assert "medium.txt" in names
        assert "empty.txt" not in names
        assert "large.txt" not in names


def test_size_filtering_with_directories():
    """Test that size filtering only applies to files, not directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        create_test_files_with_sizes(base_dir)

        # Find all entries including directories, with size filter
        results = list(vexy_glob.find("*", root=tmpdir, min_size=1))
        names = [Path(r).name for r in results]

        # Should include directory despite size filter
        assert "subdir" in names
        # Should include files >= 1 byte
        assert "small.txt" in names
        assert "medium.txt" in names
        assert "large.txt" in names
        # Should exclude empty file
        assert "empty.txt" not in names


def test_size_filtering_with_content_search():
    """Test that size filtering works with content search."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create files with searchable content
        small_file = base_dir / "small.py"
        small_file.write_text("import os\n" * 10)  # ~100 bytes

        large_file = base_dir / "large.py"
        large_file.write_text("import os\n" * 1000)  # ~10000 bytes

        # Search for content in files >= 1000 bytes
        results = list(vexy_glob.find("*.py", root=tmpdir, content="import", min_size=1000))

        # Should return 1000 lines from large.py, none from small.py
        assert len(results) == 1000
        assert all(r["path"].endswith("large.py") for r in results)
        assert all("import" in r["line_text"] for r in results)

        # Verify small file was excluded
        paths = set(r["path"] for r in results)
        assert len(paths) == 1  # Only one file
        assert not any(p.endswith("small.py") for p in paths)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
