# this_file: tests/test_time_formats.py
"""Test human-readable time format support."""

import os
import time
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytest
import vexy_glob


def test_relative_time_formats():
    """Test relative time format support (-1d, -2h, etc)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        now = time.time()

        # Create files with different ages
        old_file = base_dir / "old.txt"
        old_file.write_text("old")
        os.utime(old_file, (now - 7200, now - 7200))  # 2 hours old

        recent_file = base_dir / "recent.txt"
        recent_file.write_text("recent")
        os.utime(recent_file, (now - 600, now - 600))  # 10 minutes old

        new_file = base_dir / "new.txt"
        new_file.write_text("new")

        # Test various relative formats

        # Files from last 30 minutes
        results = list(vexy_glob.find("*.txt", root=tmpdir, mtime_after="-30m"))
        names = [Path(r).name for r in results]
        assert len(results) == 2
        assert "recent.txt" in names
        assert "new.txt" in names

        # Files from last hour
        results = list(vexy_glob.find("*.txt", root=tmpdir, mtime_after="-1h"))
        names = [Path(r).name for r in results]
        assert len(results) == 2
        assert "recent.txt" in names
        assert "new.txt" in names

        # Files from last 3 hours
        results = list(vexy_glob.find("*.txt", root=tmpdir, mtime_after="-3h"))
        names = [Path(r).name for r in results]
        assert len(results) == 3  # All files

        # Files older than 1 hour
        results = list(vexy_glob.find("*.txt", root=tmpdir, mtime_before="-1h"))
        names = [Path(r).name for r in results]
        assert len(results) == 1
        assert "old.txt" in names


def test_iso_date_formats():
    """Test ISO date format support."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        now = time.time()

        # Create a test file with known modification time
        test_file = base_dir / "test.txt"
        test_file.write_text("test")
        os.utime(test_file, (now, now))

        # Test date-only format
        yesterday = (datetime.now() - timedelta(days=1)).date()
        tomorrow = (datetime.now() + timedelta(days=1)).date()

        results = list(
            vexy_glob.find(
                "*.txt", root=tmpdir, mtime_after=str(yesterday), mtime_before=str(tomorrow)
            )
        )
        assert len(results) == 1

        # Test datetime format with specific timestamp
        test_file2 = base_dir / "test2.txt"
        test_file2.write_text("test2")
        specific_time = now - 1800  # 30 minutes ago
        os.utime(test_file2, (specific_time, specific_time))

        an_hour_ago = datetime.now() - timedelta(hours=1)
        results = list(vexy_glob.find("*2.txt", root=tmpdir, mtime_after=an_hour_ago.isoformat()))
        assert len(results) == 1


def test_datetime_object_support():
    """Test that datetime objects are handled correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create test file
        test_file = base_dir / "test.txt"
        test_file.write_text("test")

        # Use datetime objects directly
        yesterday = datetime.now() - timedelta(days=1)
        tomorrow = datetime.now() + timedelta(days=1)

        results = list(
            vexy_glob.find("*.txt", root=tmpdir, mtime_after=yesterday, mtime_before=tomorrow)
        )
        assert len(results) == 1


def test_mixed_time_formats():
    """Test mixing different time format types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        now = time.time()

        # Create old file
        old_file = base_dir / "old.txt"
        old_file.write_text("old")
        os.utime(old_file, (now - 86400, now - 86400))  # 1 day old

        # Create new file
        new_file = base_dir / "new.txt"
        new_file.write_text("new")

        # Mix relative time and datetime
        yesterday = datetime.now() - timedelta(days=1, hours=1)
        results = list(
            vexy_glob.find("*.txt", root=tmpdir, mtime_after=yesterday, mtime_before="-30m")
        )
        names = [Path(r).name for r in results]
        assert len(results) == 1
        assert "old.txt" in names

        # Mix timestamp and relative time
        results = list(
            vexy_glob.find(
                "*.txt",
                root=tmpdir,
                mtime_after=now - 3600,  # timestamp
                mtime_before="-5m",
            )
        )  # relative
        assert len(results) == 0  # No files in this range


def test_invalid_time_formats():
    """Test that invalid time formats raise appropriate errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Invalid relative format
        with pytest.raises(ValueError, match="Invalid time format"):
            list(vexy_glob.find("*", root=tmpdir, mtime_after="-2x"))

        # Invalid ISO format
        with pytest.raises(ValueError, match="Invalid time format"):
            list(vexy_glob.find("*", root=tmpdir, mtime_after="not-a-date"))

        # Invalid type
        with pytest.raises(TypeError, match="Unsupported time type"):
            list(vexy_glob.find("*", root=tmpdir, mtime_after=[]))


def test_timezone_handling():
    """Test that timezone-aware dates work correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create test file
        test_file = base_dir / "test.txt"
        test_file.write_text("test")

        # Use timezone-aware datetime
        utc_now = datetime.now(timezone.utc)
        yesterday_utc = utc_now - timedelta(days=1)
        tomorrow_utc = utc_now + timedelta(days=1)

        results = list(
            vexy_glob.find(
                "*.txt",
                root=tmpdir,
                mtime_after=yesterday_utc.isoformat(),
                mtime_before=tomorrow_utc.isoformat(),
            )
        )
        assert len(results) == 1


def test_relative_seconds_and_days():
    """Test edge cases for relative time units."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        now = time.time()

        # Create files with specific ages
        files = []
        for i, age in enumerate([10, 300, 3600, 86400]):  # 10s, 5m, 1h, 1d
            f = base_dir / f"file_{i}.txt"
            f.write_text(f"content_{i}")
            os.utime(f, (now - age, now - age))
            files.append((f.name, age))

        # Test seconds
        results = list(vexy_glob.find("*.txt", root=tmpdir, mtime_after="-30s"))
        assert len(results) == 1  # Only file_0

        # Test fractional hours
        results = list(vexy_glob.find("*.txt", root=tmpdir, mtime_after="-0.5h"))
        assert len(results) == 2  # file_0 and file_1

        # Test days
        results = list(vexy_glob.find("*.txt", root=tmpdir, mtime_after="-2d"))
        assert len(results) == 4  # All files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
