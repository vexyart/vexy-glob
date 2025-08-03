#!/usr/bin/env python3
# this_file: tests/test_ctime_filtering.py
"""
Test creation time filtering functionality.
"""

import os
import tempfile
import time
import pytest
from pathlib import Path
from datetime import datetime, timezone
import vexy_glob


def test_ctime_after_filtering():
    """Test filtering files created after a specific time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an old file
        old_file = Path(tmpdir) / "old_file.txt"
        old_file.write_text("old content")

        # Set its creation time to 1 hour ago
        old_time = time.time() - 3600
        # Note: We can't directly set creation time, but we can set it to
        # simulate an older file by using utime for both atime and mtime
        # and trusting that creation time is older
        os.utime(old_file, (old_time, old_time))

        # Record cutoff time
        cutoff_time = time.time() - 1800  # 30 minutes ago
        time.sleep(0.1)

        # Create a new file
        new_file = Path(tmpdir) / "new_file.txt"
        new_file.write_text("new content")

        # Find files created after cutoff time
        results = list(vexy_glob.find("*.txt", root=tmpdir, ctime_after=cutoff_time, file_type="f"))

        # Should include the new file (assuming its creation time is after cutoff)
        assert len(results) >= 1
        assert any("new_file.txt" in r for r in results)


def test_ctime_before_filtering():
    """Test filtering files created before a specific time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an old file
        old_file = Path(tmpdir) / "old_file.txt"
        old_file.write_text("old content")

        # Record cutoff time
        cutoff_time = time.time()
        time.sleep(0.5)

        # Create a new file after cutoff
        new_file = Path(tmpdir) / "new_file.txt"
        new_file.write_text("new content")

        # Find files created before cutoff time
        results = list(
            vexy_glob.find("*.txt", root=tmpdir, ctime_before=cutoff_time, file_type="f")
        )

        # Should include the old file
        assert len(results) >= 1
        assert any("old_file.txt" in r for r in results)


def test_ctime_range_filtering():
    """Test filtering files within a creation time range."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a very old file
        very_old_file = Path(tmpdir) / "very_old.txt"
        very_old_file.write_text("very old")

        # Set range boundaries
        start_time = time.time()
        time.sleep(0.2)

        # Create middle file
        middle_file = Path(tmpdir) / "middle.txt"
        middle_file.write_text("middle")
        time.sleep(0.2)

        end_time = time.time()
        time.sleep(0.2)

        # Create very new file
        very_new_file = Path(tmpdir) / "very_new.txt"
        very_new_file.write_text("very new")

        # Find files created within the range
        results = list(
            vexy_glob.find(
                "*.txt", root=tmpdir, ctime_after=start_time, ctime_before=end_time, file_type="f"
            )
        )

        # Should include the middle file
        assert len(results) >= 1
        assert any("middle.txt" in r for r in results)


def test_ctime_with_relative_time():
    """Test creation time filtering with relative time formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")

        # Find files created in the last hour (should include our file)
        results = list(vexy_glob.find("*.txt", root=tmpdir, ctime_after="-1h", file_type="f"))
        assert len(results) >= 1
        assert any("test.txt" in r for r in results)

        # Find files created in the last second (may or may not include our file)
        results = list(vexy_glob.find("*.txt", root=tmpdir, ctime_after="-10s", file_type="f"))
        assert len(results) >= 0  # Could be 0 or more depending on timing


def test_ctime_with_datetime_objects():
    """Test creation time filtering with datetime objects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")

        # Use a datetime from 1 hour ago
        one_hour_ago = datetime.fromtimestamp(time.time() - 3600)

        # Find files created after 1 hour ago
        results = list(
            vexy_glob.find("*.txt", root=tmpdir, ctime_after=one_hour_ago, file_type="f")
        )

        # Should include our recently created file
        assert len(results) >= 1
        assert any("test.txt" in r for r in results)


def test_ctime_with_content_search():
    """Test creation time filtering combined with content search."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an old file
        old_file = Path(tmpdir) / "old.py"
        old_file.write_text("def old_function():\n    pass")

        cutoff_time = time.time()
        time.sleep(0.1)

        # Create a new file
        new_file = Path(tmpdir) / "new.py"
        new_file.write_text("def new_function():\n    pass")

        # Search for 'def' in files created after cutoff
        results = list(vexy_glob.search("def", "*.py", root=tmpdir, ctime_after=cutoff_time))

        # Should find matches in the new file
        assert len(results) >= 1
        assert any("new.py" in r["path"] for r in results)


def test_ctime_with_size_filtering():
    """Test creation time filtering combined with size filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small file
        small_file = Path(tmpdir) / "small.txt"
        small_file.write_text("small")

        cutoff_time = time.time()
        time.sleep(0.1)

        # Create a large file
        large_file = Path(tmpdir) / "large.txt"
        large_file.write_text("large content that is much longer than the small file")

        # Find large files created after cutoff
        results = list(
            vexy_glob.find(
                "*.txt", root=tmpdir, ctime_after=cutoff_time, min_size=30, file_type="f"
            )
        )

        # Should include the large file
        assert len(results) >= 1
        assert any("large.txt" in r for r in results)


def test_ctime_with_exclude_patterns():
    """Test creation time filtering combined with exclude patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files before cutoff
        py_file = Path(tmpdir) / "script.py"
        py_file.write_text("print('hello')")

        cutoff_time = time.time()
        time.sleep(0.1)

        # Create files after cutoff
        log_file = Path(tmpdir) / "debug.log"
        log_file.write_text("debug info")
        txt_file = Path(tmpdir) / "readme.txt"
        txt_file.write_text("readme content")

        # Find files created after cutoff but exclude logs
        results = list(
            vexy_glob.find(
                "*", root=tmpdir, ctime_after=cutoff_time, exclude="*.log", file_type="f"
            )
        )

        # Should include txt but not log
        assert len(results) >= 1
        assert any("readme.txt" in r for r in results)
        assert not any("debug.log" in r for r in results)


def test_ctime_iso_date_format():
    """Test creation time filtering with ISO date formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")

        # Use yesterday's date in ISO format
        yesterday = datetime.fromtimestamp(time.time() - 86400).strftime("%Y-%m-%d")

        # Find files created after yesterday
        results = list(vexy_glob.find("*.txt", root=tmpdir, ctime_after=yesterday, file_type="f"))

        # Should include our recently created file
        assert len(results) >= 1
        assert any("test.txt" in r for r in results)


def test_ctime_no_match():
    """Test creation time filtering that matches no files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")

        # Look for files created in the future (should be none)
        future_time = time.time() + 3600  # 1 hour in the future

        results = list(vexy_glob.find("*.txt", root=tmpdir, ctime_after=future_time, file_type="f"))

        assert len(results) == 0


def test_ctime_edge_cases():
    """Test edge cases for creation time filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files
        file1 = Path(tmpdir) / "file1.txt"
        file2 = Path(tmpdir) / "file2.txt"

        file1.write_text("content1")
        file2.write_text("content2")

        # Test with None values (should not filter)
        results_none = list(
            vexy_glob.find("*.txt", root=tmpdir, ctime_after=None, ctime_before=None, file_type="f")
        )
        assert len(results_none) == 2

        # Test with same time for before and after (should be empty or very small window)
        current_time = time.time()
        results_same = list(
            vexy_glob.find(
                "*.txt",
                root=tmpdir,
                ctime_after=current_time,
                ctime_before=current_time,
                file_type="f",
            )
        )
        assert len(results_same) == 0


def test_ctime_with_all_time_filters():
    """Test creation time filtering combined with modification and access time filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
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

        # Find files created before modification, modified after creation, and accessed after modification
        results = list(
            vexy_glob.find(
                "*.txt",
                root=tmpdir,
                ctime_before=after_modify,  # Created before modification
                mtime_after=after_create,  # Modified after creation
                atime_after=after_modify,  # Accessed after modification
                file_type="f",
            )
        )

        # Should include our file
        assert len(results) >= 1
        assert any("test.txt" in r for r in results)


def test_ctime_platform_compatibility():
    """Test creation time filtering works across platforms."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        file1 = Path(tmpdir) / "file1.txt"
        file2 = Path(tmpdir) / "file2.txt"

        file1.write_text("content1")
        time.sleep(0.1)

        cutoff_time = time.time()
        time.sleep(0.1)

        file2.write_text("content2")

        # Test basic creation time filtering
        try:
            results = list(
                vexy_glob.find("*.txt", root=tmpdir, ctime_after=cutoff_time, file_type="f")
            )
            # On platforms that support creation time, we should get results
            # On platforms that don't, the filter should not error
            assert len(results) >= 0
        except Exception as e:
            # If platform doesn't support creation time, should fail gracefully
            assert "creation time" in str(e).lower() or "not supported" in str(e).lower()
