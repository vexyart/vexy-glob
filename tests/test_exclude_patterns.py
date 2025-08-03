#!/usr/bin/env python3
# this_file: tests/test_exclude_patterns.py
"""
Test exclude patterns functionality.
"""

import os
import tempfile
import pytest
from pathlib import Path
import vexy_glob


def test_single_exclude_pattern():
    """Test excluding files with a single pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test structure
        (Path(tmpdir) / "include.py").write_text("print('include')")
        (Path(tmpdir) / "exclude.log").write_text("log data")
        (Path(tmpdir) / "data.txt").write_text("text data")
        (Path(tmpdir) / "debug.log").write_text("debug data")

        # Find all files excluding *.log
        results = list(vexy_glob.find("*", root=tmpdir, exclude="*.log", file_type="f"))

        assert len(results) == 2
        basenames = {os.path.basename(p) for p in results}
        assert "include.py" in basenames
        assert "data.txt" in basenames
        assert "exclude.log" not in basenames
        assert "debug.log" not in basenames


def test_multiple_exclude_patterns():
    """Test excluding files with multiple patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test structure
        (Path(tmpdir) / "main.py").write_text("main")
        (Path(tmpdir) / "test.py").write_text("test")
        (Path(tmpdir) / "config.json").write_text("{}")
        (Path(tmpdir) / "data.csv").write_text("data")
        (Path(tmpdir) / "temp.tmp").write_text("temp")
        (Path(tmpdir) / "cache.cache").write_text("cache")

        # Exclude multiple patterns
        results = list(
            vexy_glob.find("*", root=tmpdir, exclude=["*.tmp", "*.cache", "*.csv"], file_type="f")
        )

        assert len(results) == 3
        basenames = {os.path.basename(p) for p in results}
        assert "main.py" in basenames
        assert "test.py" in basenames
        assert "config.json" in basenames
        assert "temp.tmp" not in basenames
        assert "cache.cache" not in basenames
        assert "data.csv" not in basenames


def test_exclude_with_directories():
    """Test excluding directories and their contents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test structure with directories
        os.makedirs(Path(tmpdir) / "src")
        os.makedirs(Path(tmpdir) / "build")
        os.makedirs(Path(tmpdir) / "node_modules")

        (Path(tmpdir) / "src" / "main.py").write_text("main")
        (Path(tmpdir) / "build" / "output.js").write_text("output")
        (Path(tmpdir) / "node_modules" / "package.json").write_text("{}")
        (Path(tmpdir) / "README.md").write_text("readme")

        # Exclude build and node_modules directories
        results = list(
            vexy_glob.find("**/*", root=tmpdir, exclude=["**/build/**", "**/node_modules/**"])
        )

        basenames = [os.path.relpath(p, tmpdir) for p in results]
        assert "src/main.py" in basenames
        assert "README.md" in basenames
        assert "build/output.js" not in basenames
        assert "node_modules/package.json" not in basenames


def test_exclude_with_glob_pattern():
    """Test exclude patterns work with glob patterns in find."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test structure
        os.makedirs(Path(tmpdir) / "src")
        os.makedirs(Path(tmpdir) / "tests")

        (Path(tmpdir) / "src" / "main.py").write_text("main")
        (Path(tmpdir) / "src" / "main.pyc").write_text("compiled")
        (Path(tmpdir) / "tests" / "test_main.py").write_text("test")
        (Path(tmpdir) / "tests" / "test_main.pyc").write_text("compiled")

        # Find all .py files but exclude .pyc files (redundant but tests interaction)
        results = list(vexy_glob.find("**/*.py*", root=tmpdir, exclude="**/*.pyc"))

        assert len(results) == 2
        basenames = [os.path.relpath(p, tmpdir) for p in results]
        assert "src/main.py" in basenames
        assert "tests/test_main.py" in basenames
        assert "src/main.pyc" not in basenames
        assert "tests/test_main.pyc" not in basenames


def test_exclude_with_content_search():
    """Test exclude patterns work with content search."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        (Path(tmpdir) / "main.py").write_text("def main():\n    print('hello')")
        (Path(tmpdir) / "test.py").write_text("def test():\n    print('test')")
        (Path(tmpdir) / "debug.log").write_text("def debug():\n    print('debug')")
        (Path(tmpdir) / "error.log").write_text("def error():\n    print('error')")

        # Search for 'def' but exclude log files
        results = list(vexy_glob.search("def", "**/*", root=tmpdir, exclude="*.log"))

        assert len(results) == 2
        paths = {r["path"] for r in results}
        assert any("main.py" in p for p in paths)
        assert any("test.py" in p for p in paths)
        assert not any("debug.log" in p for p in paths)
        assert not any("error.log" in p for p in paths)


def test_exclude_case_sensitivity():
    """Test exclude pattern case sensitivity."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with different extensions (not case variants of same file)
        # to work on case-insensitive filesystems
        (Path(tmpdir) / "document.TXT").write_text("uppercase ext")
        (Path(tmpdir) / "readme.txt").write_text("lowercase ext")
        (Path(tmpdir) / "config.Txt").write_text("mixed case ext")
        (Path(tmpdir) / "script.py").write_text("python")

        # Test case sensitive exclude - should only exclude exact *.txt matches
        results_sensitive = list(
            vexy_glob.find("*", root=tmpdir, exclude="*.txt", case_sensitive=True, file_type="f")
        )
        basenames = {os.path.basename(p) for p in results_sensitive}

        # In case sensitive mode, only lowercase .txt should be excluded
        assert "document.TXT" in basenames  # Not excluded (uppercase)
        assert "readme.txt" not in basenames  # Excluded (exact match)
        assert "config.Txt" in basenames  # Not excluded (mixed case)
        assert "script.py" in basenames  # Not excluded (different extension)

        # Test case insensitive exclude - should exclude all .txt variants
        results_insensitive = list(
            vexy_glob.find("*", root=tmpdir, exclude="*.txt", case_sensitive=False, file_type="f")
        )
        basenames_insensitive = {os.path.basename(p) for p in results_insensitive}

        # In case insensitive mode, all .txt variants should be excluded
        assert "document.TXT" not in basenames_insensitive  # Excluded
        assert "readme.txt" not in basenames_insensitive  # Excluded
        assert "config.Txt" not in basenames_insensitive  # Excluded
        assert "script.py" in basenames_insensitive  # Not excluded


def test_exclude_hidden_files():
    """Test exclude patterns with hidden files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create hidden and regular files
        (Path(tmpdir) / ".hidden.py").write_text("hidden")
        (Path(tmpdir) / ".config.json").write_text("{}")
        (Path(tmpdir) / "visible.py").write_text("visible")
        (Path(tmpdir) / "data.json").write_text("{}")

        # Include hidden files but exclude .json
        results = list(
            vexy_glob.find("*", root=tmpdir, hidden=True, exclude="*.json", file_type="f")
        )

        assert len(results) == 2
        basenames = {os.path.basename(p) for p in results}
        assert ".hidden.py" in basenames
        assert "visible.py" in basenames
        assert ".config.json" not in basenames
        assert "data.json" not in basenames


def test_exclude_with_size_filtering():
    """Test exclude patterns combined with size filtering."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files of different sizes
        (Path(tmpdir) / "small.txt").write_text("a" * 10)
        (Path(tmpdir) / "small.log").write_text("b" * 10)
        (Path(tmpdir) / "large.txt").write_text("c" * 1000)
        (Path(tmpdir) / "large.log").write_text("d" * 1000)

        # Find large files but exclude logs
        results = list(
            vexy_glob.find("*", root=tmpdir, min_size=100, exclude="*.log", file_type="f")
        )

        assert len(results) == 1
        assert "large.txt" in results[0]


def test_exclude_empty_list():
    """Test that empty exclude list doesn't filter anything."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        (Path(tmpdir) / "file1.txt").write_text("test1")
        (Path(tmpdir) / "file2.log").write_text("test2")

        # Empty exclude list should not filter
        results_empty = list(vexy_glob.find("*", root=tmpdir, exclude=[], file_type="f"))
        results_none = list(vexy_glob.find("*", root=tmpdir, exclude=None, file_type="f"))

        assert len(results_empty) == 2
        assert len(results_none) == 2


def test_exclude_pattern_priority():
    """Test that exclude patterns take priority over include patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test structure
        os.makedirs(Path(tmpdir) / "src")
        (Path(tmpdir) / "src" / "main.py").write_text("main")
        (Path(tmpdir) / "src" / "main_test.py").write_text("test")
        (Path(tmpdir) / "src" / "util.py").write_text("util")
        (Path(tmpdir) / "src" / "util_test.py").write_text("test")

        # Find all Python files but exclude tests
        results = list(vexy_glob.find("**/*.py", root=tmpdir, exclude="**/*_test.py"))

        assert len(results) == 2
        basenames = [os.path.basename(p) for p in results]
        assert "main.py" in basenames
        assert "util.py" in basenames
        assert "main_test.py" not in basenames
        assert "util_test.py" not in basenames


def test_complex_exclude_patterns():
    """Test complex exclude pattern scenarios."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create complex directory structure
        os.makedirs(Path(tmpdir) / "project" / "src")
        os.makedirs(Path(tmpdir) / "project" / "tests")
        os.makedirs(Path(tmpdir) / "project" / ".git")
        os.makedirs(Path(tmpdir) / "project" / "build" / "dist")

        (Path(tmpdir) / "project" / "src" / "app.py").write_text("app")
        (Path(tmpdir) / "project" / "src" / "__pycache__" / "app.pyc").parent.mkdir(exist_ok=True)
        (Path(tmpdir) / "project" / "src" / "__pycache__" / "app.pyc").write_text("cache")
        (Path(tmpdir) / "project" / "tests" / "test_app.py").write_text("test")
        (Path(tmpdir) / "project" / ".git" / "config").write_text("config")
        (Path(tmpdir) / "project" / "build" / "dist" / "app.whl").write_text("wheel")
        (Path(tmpdir) / "project" / "README.md").write_text("readme")

        # Exclude multiple common patterns
        exclude_patterns = ["**/__pycache__/**", "**/.git/**", "**/build/**", "**/*.pyc"]

        results = list(vexy_glob.find("**/*", root=tmpdir, exclude=exclude_patterns))

        # Convert to relative paths for easier checking
        rel_paths = [os.path.relpath(p, tmpdir) for p in results]

        # Should include
        assert "project/src/app.py" in rel_paths
        assert "project/tests/test_app.py" in rel_paths
        assert "project/README.md" in rel_paths

        # Should exclude
        assert "project/src/__pycache__/app.pyc" not in rel_paths
        assert "project/.git/config" not in rel_paths
        assert "project/build/dist/app.whl" not in rel_paths
