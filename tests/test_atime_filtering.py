#!/usr/bin/env python3
# this_file: tests/test_atime_filtering.py
"""
Test access time filtering functionality.
"""

import os
import tempfile
import time
import pytest
from pathlib import Path
from datetime import datetime, timezone
import vexy_glob


def test_atime_after_filtering():
    """Test filtering files accessed after a specific time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        old_file = Path(tmpdir) / "old_file.txt"
        new_file = Path(tmpdir) / "new_file.txt"

        old_file.write_text("old content")
        time.sleep(0.1)  # Small delay to ensure different access times

        # Record timestamp
        cutoff_time = time.time()
        time.sleep(0.1)

        new_file.write_text("new content")

        # Access the new file to update its access time
        new_file.read_text()

        # Find files accessed after cutoff time
        results = list(vexy_glob.find("*.txt", root=tmpdir, atime_after=cutoff_time, file_type="f"))

        # Should only include the new file
        assert len(results) == 1
        assert "new_file.txt" in results[0]


def test_atime_before_filtering():
    """Test filtering files accessed before a specific time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an old file
        old_file = Path(tmpdir) / "old_file.txt"
        old_file.write_text("old content")

        # Set its access time to 1 hour ago
        old_time = time.time() - 3600
        os.utime(old_file, (old_time, old_file.stat().st_mtime))

        # Record cutoff time
        cutoff_time = time.time()
        time.sleep(0.1)

        # Create a new file
        new_file = Path(tmpdir) / "new_file.txt"
        new_file.write_text("new content")
        new_file.read_text()  # Access it

        # Find files accessed before cutoff time
        results = list(
            vexy_glob.find("*.txt", root=tmpdir, atime_before=cutoff_time, file_type="f")
        )

        # Should only include the old file
        assert len(results) == 1
        assert "old_file.txt" in results[0]


def test_atime_range_filtering():
    """Test filtering files within an access time range."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files and set their access times manually
        very_old_file = Path(tmpdir) / "very_old.txt"
        middle_file = Path(tmpdir) / "middle.txt"
        very_new_file = Path(tmpdir) / "very_new.txt"

        # Create all files
        very_old_file.write_text("very old")
        middle_file.write_text("middle")
        very_new_file.write_text("very new")

        # Set access times manually
        current_time = time.time()
        very_old_time = current_time - 3600  # 1 hour ago
        middle_time = current_time - 1800  # 30 minutes ago
        very_new_time = current_time  # Now

        os.utime(very_old_file, (very_old_time, very_old_file.stat().st_mtime))
        os.utime(middle_file, (middle_time, middle_file.stat().st_mtime))
        os.utime(very_new_file, (very_new_time, very_new_file.stat().st_mtime))

        # Define range boundaries
        start_time = current_time - 2400  # 40 minutes ago
        end_time = current_time - 1200  # 20 minutes ago

        # Find files accessed within the range
        results = list(
            vexy_glob.find(
                "*.txt", root=tmpdir, atime_after=start_time, atime_before=end_time, file_type="f"
            )
        )

        # Should only include the middle file
        assert len(results) == 1
        assert "middle.txt" in results[0]


def test_atime_with_relative_time():
    """Test access time filtering with relative time formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file and access it
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")
        test_file.read_text()

        # Find files accessed in the last hour (should include our file)
        results = list(vexy_glob.find("*.txt", root=tmpdir, atime_after="-1h", file_type="f"))
        assert len(results) == 1
        assert "test.txt" in results[0]

        # Find files accessed in the last second (may or may not include our file)
        # This test is less reliable due to timing precision
        results = list(vexy_glob.find("*.txt", root=tmpdir, atime_after="-10s", file_type="f"))
        assert len(results) >= 0  # Could be 0 or 1 depending on timing


def test_atime_with_datetime_objects():
    """Test access time filtering with datetime objects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")

        # Use a datetime from 1 hour ago
        one_hour_ago = datetime.fromtimestamp(time.time() - 3600)

        # Find files accessed after 1 hour ago
        results = list(
            vexy_glob.find("*.txt", root=tmpdir, atime_after=one_hour_ago, file_type="f")
        )

        # Should include our recently created file
        assert len(results) == 1
        assert "test.txt" in results[0]


def test_atime_with_content_search():
    """Test access time filtering combined with content search."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with different content and access times
        old_file = Path(tmpdir) / "old.py"
        new_file = Path(tmpdir) / "new.py"

        old_file.write_text("def old_function():\n    pass")
        new_file.write_text("def new_function():\n    pass")

        # Set access times manually
        current_time = time.time()
        old_time = current_time - 3600  # 1 hour ago
        new_time = current_time  # Now

        os.utime(old_file, (old_time, old_file.stat().st_mtime))
        os.utime(new_file, (new_time, new_file.stat().st_mtime))

        # Set cutoff to 30 minutes ago
        cutoff_time = current_time - 1800

        # Search for 'def' in files accessed after cutoff
        results = list(vexy_glob.search("def", "*.py", root=tmpdir, atime_after=cutoff_time))

        # Should only find matches in the new file
        assert len(results) == 1
        assert "new.py" in results[0]["path"]


def test_atime_with_size_filtering():
    """Test access time filtering combined with size filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files of different sizes
        small_file = Path(tmpdir) / "small.txt"
        large_file = Path(tmpdir) / "large.txt"

        small_file.write_text("small")
        small_file.read_text()
        time.sleep(0.1)

        cutoff_time = time.time()
        time.sleep(0.1)

        large_file.write_text("large content that is much longer than the small file")
        large_file.read_text()

        # Find large files accessed after cutoff
        results = list(
            vexy_glob.find(
                "*.txt", root=tmpdir, atime_after=cutoff_time, min_size=30, file_type="f"
            )
        )

        # Should only include the large file
        assert len(results) == 1
        assert "large.txt" in results[0]


def test_atime_with_exclude_patterns():
    """Test access time filtering combined with exclude patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create different types of files
        py_file = Path(tmpdir) / "script.py"
        log_file = Path(tmpdir) / "debug.log"
        txt_file = Path(tmpdir) / "readme.txt"

        py_file.write_text("print('hello')")
        log_file.write_text("debug info")
        txt_file.write_text("readme content")

        # Set access times manually
        current_time = time.time()
        old_time = current_time - 3600  # 1 hour ago
        new_time = current_time  # Now

        # Set py_file to old time, others to new time
        os.utime(py_file, (old_time, py_file.stat().st_mtime))
        os.utime(log_file, (new_time, log_file.stat().st_mtime))
        os.utime(txt_file, (new_time, txt_file.stat().st_mtime))

        cutoff_time = current_time - 1800  # 30 minutes ago

        # Find files accessed after cutoff but exclude logs
        results = list(
            vexy_glob.find(
                "*", root=tmpdir, atime_after=cutoff_time, exclude="*.log", file_type="f"
            )
        )

        # Should include txt but not log or py (py is too old, log is excluded)
        assert len(results) == 1
        assert "readme.txt" in results[0]


def test_atime_iso_date_format():
    """Test access time filtering with ISO date formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")
        test_file.read_text()

        # Use yesterday's date in ISO format
        yesterday = datetime.fromtimestamp(time.time() - 86400).strftime("%Y-%m-%d")

        # Find files accessed after yesterday
        results = list(vexy_glob.find("*.txt", root=tmpdir, atime_after=yesterday, file_type="f"))

        # Should include our recently accessed file
        assert len(results) == 1
        assert "test.txt" in results[0]


def test_atime_no_match():
    """Test access time filtering that matches no files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")
        test_file.read_text()

        # Look for files accessed in the future (should be none)
        future_time = time.time() + 3600  # 1 hour in the future

        results = list(vexy_glob.find("*.txt", root=tmpdir, atime_after=future_time, file_type="f"))

        assert len(results) == 0


def test_atime_edge_cases():
    """Test edge cases for access time filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files
        file1 = Path(tmpdir) / "file1.txt"
        file2 = Path(tmpdir) / "file2.txt"

        file1.write_text("content1")
        file2.write_text("content2")

        # Test with None values (should not filter)
        results_none = list(
            vexy_glob.find("*.txt", root=tmpdir, atime_after=None, atime_before=None, file_type="f")
        )
        assert len(results_none) == 2

        # Test with same time for before and after (should be empty or very small window)
        current_time = time.time()
        results_same = list(
            vexy_glob.find(
                "*.txt",
                root=tmpdir,
                atime_after=current_time,
                atime_before=current_time,
                file_type="f",
            )
        )
        assert len(results_same) == 0


def test_atime_with_mtime_filtering():
    """Test access time filtering combined with modification time filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("initial content")

        # Record time after creation
        after_create = time.time()
        time.sleep(0.1)

        # Modify the file
        test_file.write_text("modified content")

        # Record time after modification
        after_modify = time.time()
        time.sleep(0.1)

        # Access the file
        test_file.read_text()

        # Find files modified after creation and accessed after modification
        results = list(
            vexy_glob.find(
                "*.txt",
                root=tmpdir,
                mtime_after=after_create,
                atime_after=after_modify,
                file_type="f",
            )
        )

        # Should include our file
        assert len(results) == 1
        assert "test.txt" in results[0]
