# this_file: tests/test_basic.py
"""Basic tests for vexy_glob functionality."""

import vexy_glob
import pytest
from pathlib import Path
import tempfile
import os


def test_import():
    """Test that the module can be imported."""
    assert hasattr(vexy_glob, "find")
    assert hasattr(vexy_glob, "glob")
    assert hasattr(vexy_glob, "iglob")
    assert hasattr(vexy_glob, "search")


def test_find_in_current_directory():
    """Test finding files in current directory."""
    # Find Python files - use the vexy_glob directory specifically
    results = list(vexy_glob.find("*.py", root="vexy_glob", max_depth=1))
    assert isinstance(results, list)
    # Should at least find __init__.py
    assert any("__init__.py" in r for r in results)


def test_find_returns_strings_by_default():
    """Test that find returns strings by default."""
    results = list(vexy_glob.find("*.py", max_depth=1))
    if results:
        assert all(isinstance(r, str) for r in results)


def test_find_with_path_objects():
    """Test that find can return Path objects."""
    results = list(vexy_glob.find("*.py", max_depth=1, as_path=True))
    if results:
        assert all(isinstance(r, Path) for r in results)


def test_glob_compatibility():
    """Test glob function works like stdlib glob."""
    results = vexy_glob.glob("*.py")
    assert isinstance(results, list)
    assert all(isinstance(r, str) for r in results)


def test_iglob_returns_iterator():
    """Test iglob returns an iterator."""
    result = vexy_glob.iglob("*.py")
    # Should be an iterator, not a list
    assert hasattr(result, "__iter__")
    assert not isinstance(result, list)


def test_pattern_error():
    """Test that invalid patterns raise PatternError."""
    with pytest.raises(vexy_glob.PatternError):
        list(vexy_glob.find("[invalid"))


def test_find_with_file_type():
    """Test filtering by file type."""
    # Find only directories
    dirs = list(vexy_glob.find("*", file_type="d", max_depth=1))
    # Find only files
    files = list(vexy_glob.find("*", file_type="f", max_depth=1))

    # Should have found something
    assert len(dirs) > 0 or len(files) > 0


def test_max_depth():
    """Test max_depth parameter."""
    # Depth 0 should only return the root
    results = list(vexy_glob.find("*", max_depth=0))
    # Depth 1 should return immediate children
    results_depth1 = list(vexy_glob.find("*", max_depth=1))

    # Should have more results with higher depth
    assert len(results_depth1) >= len(results)


def test_extension_filter():
    """Test filtering by extension."""
    results = list(vexy_glob.find("*", extension="py", max_depth=2))
    # All results should end with .py
    assert all(r.endswith(".py") for r in results)


class TestWithTempDir:
    """Tests that create temporary directory structures."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test structure
            base = Path(tmpdir)

            # Create files
            (base / "test.py").touch()
            (base / "test.txt").touch()
            (base / ".hidden.txt").touch()

            # Create subdirectory
            subdir = base / "subdir"
            subdir.mkdir()
            (subdir / "nested.py").touch()

            # Create .gitignore
            (base / ".gitignore").write_text("*.log\n")
            (base / "ignored.log").touch()

            yield base

    def test_find_all_files(self, temp_dir):
        """Test finding all files in temp directory."""
        results = list(vexy_glob.find("*", root=str(temp_dir)))
        assert len(results) > 0

    def test_hidden_files_excluded_by_default(self, temp_dir):
        """Test that hidden files are excluded by default."""
        results = list(vexy_glob.find("*", root=str(temp_dir)))
        assert not any(".hidden" in r for r in results)

        # But can be included with hidden=True
        results_with_hidden = list(vexy_glob.find("*", root=str(temp_dir), hidden=True))
        assert any(".hidden" in r for r in results_with_hidden)

    def test_gitignore_respected_by_default(self, temp_dir):
        """Test that .gitignore is respected by default."""
        # Initialize git repository for gitignore to work
        import subprocess

        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
        subprocess.run(["git", "add", ".gitignore"], cwd=temp_dir, capture_output=True)

        results = list(vexy_glob.find("*", root=str(temp_dir)))
        assert not any("ignored.log" in r for r in results)

        # But can be ignored with ignore_git=True
        results_no_ignore = list(vexy_glob.find("*", root=str(temp_dir), ignore_git=True))
        assert any("ignored.log" in r for r in results_no_ignore)

    def test_recursive_glob(self, temp_dir):
        """Test recursive glob pattern."""
        results = list(vexy_glob.find("**/*.py", root=str(temp_dir)))
        # Should find both test.py and nested.py
        assert len([r for r in results if r.endswith(".py")]) == 2

    def test_streaming_results(self, temp_dir):
        """Test that results stream immediately."""
        # Create many files with unique names
        for i in range(100):
            (temp_dir / f"testfile{i}.txt").touch()

        # Get iterator for text files only
        iterator = vexy_glob.find("*.txt", root=str(temp_dir))

        # Should be able to get first result immediately
        first = next(iterator)
        assert first.endswith(".txt")

        # Can still get remaining results
        remaining = list(iterator)
        # Total should be 100 files (first + remaining)
        total_found = len(remaining) + 1  # +1 for the first result
        # Allow for the case where other .txt files might exist in the temp dir
        assert total_found >= 100, (
            f"Expected at least 100 files, got {total_found} (first + {len(remaining)} remaining)"
        )


def test_content_search_find_function():
    """Test content search using find() function."""
    # Search for imports in Python files
    results = list(vexy_glob.find("*.py", content="import", root="vexy_glob", max_depth=1))

    # Should find search results
    assert len(results) > 0

    # Results should be dictionaries with expected structure
    for result in results:
        assert isinstance(result, dict)
        assert "path" in result
        assert "line_number" in result
        assert "line_text" in result
        assert "matches" in result
        assert isinstance(result["line_number"], int)
        assert isinstance(result["line_text"], str)
        assert isinstance(result["matches"], list)


def test_content_search_dedicated_function():
    """Test content search using dedicated search() function."""
    # Search for function definitions
    results = list(vexy_glob.search("def ", "*.py", root="vexy_glob"))

    # Should find some function definitions
    assert len(results) > 0

    # Check structure of results
    for result in results:
        assert isinstance(result, dict)
        assert "def " in result["line_text"]


def test_content_search_with_path_objects():
    """Test content search returning Path objects."""
    results = list(vexy_glob.search("class ", "*.py", root="vexy_glob", as_path=True))

    if results:  # Only test if results found
        for result in results:
            assert isinstance(result["path"], Path)


def test_content_search_no_matches():
    """Test content search with pattern that matches no content."""
    # Search for a very unlikely string
    results = list(vexy_glob.search("XyZzAbCdEfGhUnlikelyString123", "*.py", root="vexy_glob"))

    # Should return empty list
    assert len(results) == 0


def test_content_search_as_list():
    """Test content search with as_list=True."""
    results = vexy_glob.search("import", "*.py", root="vexy_glob", as_list=True)

    # Should return a list, not an iterator
    assert isinstance(results, list)

    if results:  # Only test structure if results exist
        for result in results:
            assert isinstance(result, dict)


@pytest.fixture
def temp_dir_with_content():
    """Create a temporary directory with files containing searchable content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create Python file with specific content
        python_file = temp_path / "example.py"
        python_file.write_text("""
import os
import sys
from pathlib import Path

def main():
    print("Hello, World!")
    return 0

class ExampleClass:
    def __init__(self):
        self.value = 42
""")

        # Create text file with different content
        text_file = temp_path / "readme.txt"
        text_file.write_text("""
This is a sample text file.
It contains multiple lines.
Some lines have KEYWORDS in them.
Others do not.
""")

        yield temp_path


def test_content_search_in_temp_dir(temp_dir_with_content):
    """Test content search in a controlled temporary directory."""
    temp_dir = temp_dir_with_content

    # Search for imports
    results = list(vexy_glob.search("import", "*.py", root=str(temp_dir)))
    assert len(results) >= 2  # Should find at least 2 import statements

    # Search for class definition
    results = list(vexy_glob.search("class ", "*.py", root=str(temp_dir)))
    assert len(results) >= 1  # Should find the class definition

    # Search in text files
    results = list(vexy_glob.search("KEYWORDS", "*.txt", root=str(temp_dir)))
    assert len(results) >= 1  # Should find the keyword in text file


def test_content_search_regex_patterns(temp_dir_with_content):
    """Test content search with regex patterns."""
    temp_dir = temp_dir_with_content

    # Search for function definitions using regex
    results = list(vexy_glob.search(r"def \w+", "*.py", root=str(temp_dir)))
    assert len(results) >= 2  # Should find main() and __init__()

    # Search for numbers using regex
    results = list(vexy_glob.search(r"\d+", "*.py", root=str(temp_dir)))
    assert len(results) >= 1  # Should find "42"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
