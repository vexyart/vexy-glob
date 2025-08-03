#!/usr/bin/env python3
# this_file: tests/test_custom_ignore.py
"""
Test custom ignore file functionality (.ignore, .fdignore, custom files).
"""

import os
import subprocess
import tempfile
import pytest
from pathlib import Path
import vexy_glob


def test_custom_ignore_file():
    """Test custom ignore file functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files
        (tmpdir_path / "keep.txt").write_text("keep me")
        (tmpdir_path / "ignore_me.log").write_text("ignore me")
        (tmpdir_path / "also_keep.py").write_text("keep me too")

        # Create a custom ignore file
        custom_ignore = tmpdir_path / "custom.ignore"
        custom_ignore.write_text("*.log\n")

        # Test without custom ignore - should find all files (including ignore file)
        results_without = list(vexy_glob.find("*", root=tmpdir, file_type="f"))
        assert len(results_without) == 4  # Includes custom.ignore file

        # Test with custom ignore - should exclude .log files but include ignore file
        results_with = list(
            vexy_glob.find(
                "*", root=tmpdir, custom_ignore_files=[str(custom_ignore)], file_type="f"
            )
        )
        assert len(results_with) == 3  # Excludes .log file but includes ignore file
        assert not any("ignore_me.log" in r for r in results_with)
        assert any("keep.txt" in r for r in results_with)
        assert any("also_keep.py" in r for r in results_with)
        assert any("custom.ignore" in r for r in results_with)


def test_multiple_custom_ignore_files():
    """Test multiple custom ignore files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files
        (tmpdir_path / "keep.txt").write_text("keep me")
        (tmpdir_path / "ignore1.log").write_text("ignore me")
        (tmpdir_path / "ignore2.tmp").write_text("ignore me too")
        (tmpdir_path / "also_keep.py").write_text("keep me too")

        # Create custom ignore files
        ignore1 = tmpdir_path / "ignore1.ignore"
        ignore1.write_text("*.log\n")

        ignore2 = tmpdir_path / "ignore2.ignore"
        ignore2.write_text("*.tmp\n")

        # Test with multiple custom ignore files
        results = list(
            vexy_glob.find(
                "*", root=tmpdir, custom_ignore_files=[str(ignore1), str(ignore2)], file_type="f"
            )
        )

        assert len(results) == 4  # Includes both ignore files
        assert not any("ignore1.log" in r for r in results)
        assert not any("ignore2.tmp" in r for r in results)
        assert any("keep.txt" in r for r in results)
        assert any("also_keep.py" in r for r in results)
        assert any("ignore1.ignore" in r for r in results)
        assert any("ignore2.ignore" in r for r in results)


def test_fdignore_file_auto_detection():
    """Test automatic detection of .fdignore files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files
        (tmpdir_path / "keep.txt").write_text("keep me")
        (tmpdir_path / "ignore_me.log").write_text("ignore me")
        (tmpdir_path / "also_keep.py").write_text("keep me too")

        # Create .fdignore file
        fdignore = tmpdir_path / ".fdignore"
        fdignore.write_text("*.log\n")

        # Test with .fdignore auto-detection (ignore_git=False by default)
        results = list(vexy_glob.find("*", root=tmpdir, file_type="f"))
        assert len(results) == 2
        assert not any("ignore_me.log" in r for r in results)
        assert any("keep.txt" in r for r in results)
        assert any("also_keep.py" in r for r in results)


def test_fdignore_disabled_with_ignore_git():
    """Test that .fdignore files are ignored when ignore_git=True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files
        (tmpdir_path / "keep.txt").write_text("keep me")
        (tmpdir_path / "ignore_me.log").write_text("ignore me")

        # Create .fdignore file
        fdignore = tmpdir_path / ".fdignore"
        fdignore.write_text("*.log\n")

        # Test with ignore_git=True - should not respect .fdignore
        results = list(vexy_glob.find("*", root=tmpdir, ignore_git=True, file_type="f"))
        assert len(results) == 2  # Should include the .log file
        assert any("ignore_me.log" in r for r in results)


def test_custom_ignore_with_string_parameter():
    """Test custom ignore file with string parameter (not list)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files
        (tmpdir_path / "keep.txt").write_text("keep me")
        (tmpdir_path / "ignore_me.log").write_text("ignore me")

        # Create custom ignore file
        custom_ignore = tmpdir_path / "custom.ignore"
        custom_ignore.write_text("*.log\n")

        # Test with string parameter (not list)
        results = list(
            vexy_glob.find("*", root=tmpdir, custom_ignore_files=str(custom_ignore), file_type="f")
        )

        assert len(results) == 2  # Includes ignore file itself
        assert not any("ignore_me.log" in r for r in results)
        assert any("keep.txt" in r for r in results)
        assert any("custom.ignore" in r for r in results)


def test_nonexistent_custom_ignore_file():
    """Test behavior with non-existent custom ignore files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files
        (tmpdir_path / "keep.txt").write_text("keep me")
        (tmpdir_path / "also_keep.log").write_text("keep me too")

        # Reference non-existent ignore file
        nonexistent_ignore = tmpdir_path / "nonexistent.ignore"

        # Should not error and should include all files
        results = list(
            vexy_glob.find(
                "*", root=tmpdir, custom_ignore_files=[str(nonexistent_ignore)], file_type="f"
            )
        )

        assert len(results) == 2
        assert any("keep.txt" in r for r in results)
        assert any("also_keep.log" in r for r in results)


def test_custom_ignore_with_subdirectories():
    """Test custom ignore files with subdirectories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create subdirectory and files
        subdir = tmpdir_path / "subdir"
        subdir.mkdir()

        (tmpdir_path / "root_keep.txt").write_text("keep")
        (tmpdir_path / "root_ignore.log").write_text("ignore")
        (subdir / "sub_keep.py").write_text("keep")
        (subdir / "sub_ignore.log").write_text("ignore")

        # Create custom ignore file
        custom_ignore = tmpdir_path / "custom.ignore"
        custom_ignore.write_text("*.log\n")

        # Test - should ignore .log files in all directories
        results = list(
            vexy_glob.find(
                "*", root=tmpdir, custom_ignore_files=[str(custom_ignore)], file_type="f"
            )
        )

        assert len(results) == 3  # Includes ignore file itself
        assert any("root_keep.txt" in r for r in results)
        assert any("sub_keep.py" in r for r in results)
        assert any("custom.ignore" in r for r in results)
        assert not any("root_ignore.log" in r for r in results)
        assert not any("sub_ignore.log" in r for r in results)


def test_custom_ignore_with_content_search():
    """Test custom ignore files combined with content search."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files with content
        (tmpdir_path / "match_keep.py").write_text("def test_function():\n    pass")
        (tmpdir_path / "match_ignore.log").write_text("def test_function():\n    pass")
        (tmpdir_path / "no_match.py").write_text("print('hello')")

        # Create custom ignore file
        custom_ignore = tmpdir_path / "custom.ignore"
        custom_ignore.write_text("*.log\n")

        # Test content search with custom ignore
        results = list(
            vexy_glob.search(
                "test_function", "*", root=tmpdir, custom_ignore_files=[str(custom_ignore)]
            )
        )

        # Should find content match in .py file but not .log file
        assert len(results) == 1
        assert any("match_keep.py" in r["path"] for r in results)
        assert not any("match_ignore.log" in r["path"] for r in results)


def test_custom_ignore_complex_patterns():
    """Test custom ignore files with complex patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files and directories
        (tmpdir_path / "file.txt").write_text("keep")
        (tmpdir_path / "build.log").write_text("ignore")
        (tmpdir_path / "temp_file.tmp").write_text("ignore")

        # Create subdirectories
        build_dir = tmpdir_path / "build"
        build_dir.mkdir()
        (build_dir / "output.txt").write_text("ignore")

        temp_dir = tmpdir_path / "temp"
        temp_dir.mkdir()
        (temp_dir / "cache.dat").write_text("ignore")

        # Create custom ignore file with complex patterns
        custom_ignore = tmpdir_path / "complex.ignore"
        custom_ignore.write_text("""
# Ignore log files
*.log

# Ignore temp files and directories
*.tmp
temp/
temp/*

# Ignore build directory
build/
""")

        # Test with complex ignore patterns
        results = list(vexy_glob.find("*", root=tmpdir, custom_ignore_files=[str(custom_ignore)]))

        # Should only include the main file.txt
        result_names = [Path(r).name for r in results]
        assert "file.txt" in result_names
        assert "build.log" not in result_names
        assert "temp_file.tmp" not in result_names
        # Note: Directory filtering depends on the ignore crate implementation


def test_custom_ignore_with_other_filters():
    """Test custom ignore files combined with other filtering options."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create test files with different sizes
        (tmpdir_path / "small.txt").write_text("small")  # 5 bytes
        (tmpdir_path / "medium.py").write_text("medium content here")  # ~18 bytes
        (tmpdir_path / "large.log").write_text("large content " * 10)  # ~140 bytes
        (tmpdir_path / "huge.txt").write_text("huge content " * 20)  # ~260 bytes

        # Create custom ignore file
        custom_ignore = tmpdir_path / "size.ignore"
        custom_ignore.write_text("*.log\n")

        # Test custom ignore combined with size filtering
        results = list(
            vexy_glob.find(
                "*",
                root=tmpdir,
                custom_ignore_files=[str(custom_ignore)],
                min_size=10,  # Exclude small.txt (5 bytes)
                max_size=200,  # Exclude huge.txt (260 bytes)
                file_type="f",
            )
        )

        # Should include only medium.py (large.log ignored, small.txt too small, huge.txt too large)
        assert len(results) == 1
        assert any("medium.py" in r for r in results)
        assert not any("small.txt" in r for r in results)
        assert not any("large.log" in r for r in results)
        assert not any("huge.txt" in r for r in results)


def test_custom_ignore_precedence():
    """Test precedence of custom ignore vs other ignore files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Initialize git repository for .gitignore to work
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True, check=True)

        # Create test files
        (tmpdir_path / "keep.txt").write_text("keep")
        (tmpdir_path / "python_file.py").write_text("python")
        (tmpdir_path / "log_file.log").write_text("log")

        # Create .gitignore that ignores .py files
        gitignore = tmpdir_path / ".gitignore"
        gitignore.write_text("*.py\n")

        # Create custom ignore that ignores .log files
        custom_ignore = tmpdir_path / "custom.ignore"
        custom_ignore.write_text("*.log\n")

        # Test with both ignore files active
        results = list(
            vexy_glob.find(
                "*", root=tmpdir, custom_ignore_files=[str(custom_ignore)], file_type="f"
            )
        )

        # Should respect both ignore files
        assert len(results) == 2  # keep.txt and custom.ignore
        assert any("keep.txt" in r for r in results)
        assert any("custom.ignore" in r for r in results)
        assert not any("python_file.py" in r for r in results)  # Ignored by .gitignore
        assert not any("log_file.log" in r for r in results)  # Ignored by custom ignore
