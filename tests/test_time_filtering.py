# this_file: tests/test_time_filtering.py
"""Test modification time filtering functionality."""

import os
import time
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import pytest
import vexy_glob


def create_test_files_with_times(base_dir):
    """Create test files with specific modification times."""
    files = []
    now = time.time()

    # File modified 1 hour ago
    old_file = base_dir / "old.txt"
    old_file.write_text("old content")
    old_time = now - 3600  # 1 hour ago
    os.utime(old_file, (old_time, old_time))
    files.append(("old.txt", old_time))

    # File modified 5 minutes ago
    recent_file = base_dir / "recent.txt"
    recent_file.write_text("recent content")
    recent_time = now - 300  # 5 minutes ago
    os.utime(recent_file, (recent_time, recent_time))
    files.append(("recent.txt", recent_time))

    # File modified now
    new_file = base_dir / "new.txt"
    new_file.write_text("new content")
    files.append(("new.txt", now))

    # File modified yesterday
    yesterday_file = base_dir / "yesterday.txt"
    yesterday_file.write_text("yesterday content")
    yesterday_time = now - 86400  # 24 hours ago
    os.utime(yesterday_file, (yesterday_time, yesterday_time))
    files.append(("yesterday.txt", yesterday_time))

    # Create a directory (should be affected by time filtering)
    subdir = base_dir / "subdir"
    subdir.mkdir()

    return files, now


def test_mtime_after_filtering():
    """Test filtering files modified after a specific time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        files, now = create_test_files_with_times(base_dir)

        # Find files modified in the last 30 minutes
        thirty_min_ago = now - 1800
        results = list(vexy_glob.find("*.txt", root=tmpdir, mtime_after=thirty_min_ago))
        names = [Path(r).name for r in results]

        assert len(results) == 2
        assert "recent.txt" in names
        assert "new.txt" in names
        assert "old.txt" not in names
        assert "yesterday.txt" not in names


def test_mtime_before_filtering():
    """Test filtering files modified before a specific time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        files, now = create_test_files_with_times(base_dir)

        # Find files modified more than 30 minutes ago
        thirty_min_ago = now - 1800
        results = list(vexy_glob.find("*.txt", root=tmpdir, mtime_before=thirty_min_ago))
        names = [Path(r).name for r in results]

        assert len(results) == 2
        assert "old.txt" in names
        assert "yesterday.txt" in names
        assert "recent.txt" not in names
        assert "new.txt" not in names


def test_mtime_range_filtering():
    """Test filtering files modified within a time range."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        files, now = create_test_files_with_times(base_dir)

        # Find files modified between 2 hours ago and 10 minutes ago
        two_hours_ago = now - 7200
        ten_min_ago = now - 600
        results = list(
            vexy_glob.find(
                "*.txt", root=tmpdir, mtime_after=two_hours_ago, mtime_before=ten_min_ago
            )
        )
        names = [Path(r).name for r in results]

        assert len(results) == 1
        assert "old.txt" in names
        assert "recent.txt" not in names  # Too recent
        assert "new.txt" not in names  # Too recent
        assert "yesterday.txt" not in names  # Too old


def test_mtime_with_directories():
    """Test that modification time filtering applies to directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        now = time.time()

        # Create old directory
        old_dir = base_dir / "old_dir"
        old_dir.mkdir()
        old_time = now - 3600
        os.utime(old_dir, (old_time, old_time))

        # Create new directory
        new_dir = base_dir / "new_dir"
        new_dir.mkdir()

        # Find directories modified in the last 30 minutes
        thirty_min_ago = now - 1800
        results = list(
            vexy_glob.find("*_dir", root=tmpdir, mtime_after=thirty_min_ago, file_type="d")
        )
        names = [Path(r).name for r in results]

        assert len(results) == 1
        assert "new_dir" in names
        assert "old_dir" not in names


def test_mtime_with_content_search():
    """Test that time filtering works with content search."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        now = time.time()

        # Create old Python file
        old_file = base_dir / "old.py"
        old_file.write_text("import os\nprint('old')")
        old_time = now - 3600
        os.utime(old_file, (old_time, old_time))

        # Create new Python file
        new_file = base_dir / "new.py"
        new_file.write_text("import os\nprint('new')")

        # Search for content in files modified in the last 30 minutes
        thirty_min_ago = now - 1800
        results = list(
            vexy_glob.find("*.py", root=tmpdir, content="import", mtime_after=thirty_min_ago)
        )

        # Should only find matches in new.py
        assert len(results) == 1
        assert results[0]["path"].endswith("new.py")
        assert "import" in results[0]["line_text"]


def test_mtime_with_size_filtering():
    """Test combining time and size filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        now = time.time()

        # Create small old file
        small_old = base_dir / "small_old.txt"
        small_old.write_text("x" * 100)
        old_time = now - 3600
        os.utime(small_old, (old_time, old_time))

        # Create large old file
        large_old = base_dir / "large_old.txt"
        large_old.write_text("y" * 1000)
        os.utime(large_old, (old_time, old_time))

        # Create small new file
        small_new = base_dir / "small_new.txt"
        small_new.write_text("z" * 100)

        # Create large new file
        large_new = base_dir / "large_new.txt"
        large_new.write_text("w" * 1000)

        # Find large files modified in the last 30 minutes
        thirty_min_ago = now - 1800
        results = list(
            vexy_glob.find("*.txt", root=tmpdir, min_size=500, mtime_after=thirty_min_ago)
        )
        names = [Path(r).name for r in results]

        assert len(results) == 1
        assert "large_new.txt" in names
        assert "large_old.txt" not in names  # Too old
        assert "small_new.txt" not in names  # Too small
        assert "small_old.txt" not in names  # Too old and too small


def test_mtime_with_zero_timestamp():
    """Test handling of zero/negative timestamps."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create a file
        test_file = base_dir / "test.txt"
        test_file.write_text("test")

        # Should find all files when mtime_after is 0
        results = list(vexy_glob.find("*.txt", root=tmpdir, mtime_after=0))
        assert len(results) == 1

        # Should find no files when mtime_before is 0
        results = list(vexy_glob.find("*.txt", root=tmpdir, mtime_before=0))
        assert len(results) == 0


def test_datetime_to_timestamp_conversion():
    """Test that datetime objects work (via float conversion)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        now = datetime.now()

        # Create test file
        test_file = base_dir / "test.txt"
        test_file.write_text("test")

        # Use datetime objects (they should be converted to timestamps)
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        # Convert to timestamps
        yesterday_ts = yesterday.timestamp()
        tomorrow_ts = tomorrow.timestamp()

        # Should find files between yesterday and tomorrow
        results = list(
            vexy_glob.find("*.txt", root=tmpdir, mtime_after=yesterday_ts, mtime_before=tomorrow_ts)
        )
        assert len(results) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
