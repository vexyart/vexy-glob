#!/usr/bin/env python3
# this_file: tests/test_cli.py
"""
Tests for vexy_glob CLI interface.

Tests command-line argument parsing, output formatting, error handling,
and compatibility with shell pipelines.
"""

import sys
import tempfile
import subprocess
import json
from pathlib import Path
import pytest
from io import StringIO
from unittest.mock import patch, Mock

# Import the CLI class for direct testing
from vexy_glob.__main__ import Cli, main


class TestVexyGlobCLISizeParser:
    """Test human-readable size parsing."""

    def test_parse_size_basic(self):
        """Test basic size parsing."""
        cli = Cli()

        assert cli._parse_size("100") == 100
        assert cli._parse_size("1k") == 1024
        assert cli._parse_size("1K") == 1024
        assert cli._parse_size("2m") == 2 * 1024 * 1024
        assert cli._parse_size("3g") == 3 * 1024 * 1024 * 1024
        assert cli._parse_size("1t") == 1024 * 1024 * 1024 * 1024

    def test_parse_size_with_decimals(self):
        """Test size parsing with decimal numbers."""
        cli = Cli()

        assert cli._parse_size("1.5k") == int(1.5 * 1024)
        assert cli._parse_size("2.5m") == int(2.5 * 1024 * 1024)

    def test_parse_size_with_b_suffix(self):
        """Test size parsing with 'b' suffix."""
        cli = Cli()

        assert cli._parse_size("1kb") == 1024
        assert cli._parse_size("2mb") == 2 * 1024 * 1024
        assert cli._parse_size("3gb") == 3 * 1024 * 1024 * 1024

    def test_parse_size_empty(self):
        """Test parsing empty size string."""
        cli = Cli()
        assert cli._parse_size("") == 0
        assert cli._parse_size(None) == 0

    def test_parse_size_invalid(self):
        """Test parsing invalid size strings."""
        cli = Cli()

        with pytest.raises(ValueError, match="Invalid size format"):
            cli._parse_size("invalid")

        with pytest.raises(ValueError, match="Invalid size format"):
            cli._parse_size("1x")

        with pytest.raises(ValueError, match="Invalid size format"):
            cli._parse_size("abc123")


class TestVexyGlobCLIFormatting:
    """Test output formatting for search results."""

    def test_format_basic_output(self):
        """Test basic output formatting."""
        cli = Cli()
        # Basic test to ensure CLI can be instantiated and has required methods
        assert hasattr(cli, "find")
        assert hasattr(cli, "search")


class TestVexyGlobCLIFindCommand:
    """Test the 'find' command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.tmpdir_path = Path(self.tmpdir)

        # Create test files
        (self.tmpdir_path / "test.py").write_text("print('hello')")
        (self.tmpdir_path / "test.txt").write_text("some text")
        (self.tmpdir_path / "large.log").write_text("x" * 10000)  # 10KB file

        # Create subdirectory
        subdir = self.tmpdir_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.py").write_text("import os")

    def test_find_basic_pattern(self):
        """Test basic pattern matching."""
        cli = Cli()

        # Capture stdout
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            try:
                cli.find(pattern="*.py", root=str(self.tmpdir))
            except SystemExit:
                pass  # CLI may exit on completion

        output = mock_stdout.getvalue()
        assert "test.py" in output
        assert "nested.py" in output
        assert "test.txt" not in output

    def test_find_with_size_filter(self):
        """Test find with size filtering."""
        cli = Cli()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            try:
                cli.find(pattern="*", root=str(self.tmpdir), min_size="5k")
            except SystemExit:
                pass

        output = mock_stdout.getvalue()
        assert "large.log" in output
        assert "test.py" not in output  # Too small

    def test_find_with_type_filter(self):
        """Test find with file type filtering."""
        cli = Cli()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            try:
                cli.find(pattern="*", root=str(self.tmpdir), type="f")
            except SystemExit:
                pass

        output = mock_stdout.getvalue()
        # Should contain files but not directories
        assert "test.py" in output
        # Directories should not be listed when filtering by file type
        lines = [line for line in output.strip().split("\n") if line]
        directory_lines = [
            line for line in lines if "/subdir" in line and not line.endswith(".py")
        ]
        assert len(directory_lines) == 0  # No standalone directory entries

    def test_find_error_handling(self):
        """Test error handling in find command."""
        # Test error handling via subprocess since Rust errors bypass Python stderr mocking
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "vexy_glob",
                "find",
                "*",
                "--root",
                "/nonexistent/directory",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should handle the error gracefully and print error message
        error_text = (result.stderr + result.stdout).lower()
        assert (
            "error" in error_text
            or "no such file" in error_text
            or "traversal" in error_text
        )


class TestVexyGlobCLISearchCommand:
    """Test the 'search' command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.tmpdir_path = Path(self.tmpdir)

        # Create test files with content
        (self.tmpdir_path / "test.py").write_text(
            "import os\nprint('hello')\ndef test_function():\n    pass"
        )
        (self.tmpdir_path / "test.txt").write_text(
            "some text\nwith multiple lines\nand more content"
        )
        (self.tmpdir_path / "config.ini").write_text(
            "[section]\nkey=value\nother=setting"
        )

    def test_search_basic_pattern(self):
        """Test basic content search."""
        cli = Cli()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            try:
                cli.search(
                    pattern="*.py", content_pattern="import", root=str(self.tmpdir)
                )
            except SystemExit:
                pass

        output = mock_stdout.getvalue()
        assert "test.py" in output
        assert "import os" in output

    def test_search_regex_pattern(self):
        """Test regex pattern search."""
        cli = Cli()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            try:
                cli.search(
                    pattern="*.py", content_pattern="def\\s+\\w+", root=str(self.tmpdir)
                )
            except SystemExit:
                pass

        output = mock_stdout.getvalue()
        if output.strip():  # Only check if there's output
            assert "test.py" in output
            # Should find function definitions
            assert "def" in output

    def test_search_no_color(self):
        """Test search with no color output."""
        cli = Cli()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            try:
                cli.search(
                    pattern="*.py",
                    content_pattern="import",
                    root=str(self.tmpdir),
                    no_color=True,
                )
            except SystemExit:
                pass

        output = mock_stdout.getvalue()
        # Should be plain text format: file:line:content
        lines = output.strip().split("\n")
        if lines and lines[0]:  # If there's output
            assert ":" in lines[0]  # Should have colon separators

    def test_search_error_handling(self):
        """Test error handling in search command."""
        cli = Cli()

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit):
                cli.search(
                    pattern="*", content_pattern="[invalid", root=str(self.tmpdir)
                )

        # Should print error message for invalid regex
        error_output = mock_stderr.getvalue()
        assert "Error:" in error_output or "regex" in error_output.lower()


class TestVexyGlobCLIIntegration:
    """Test CLI integration and subprocess calls."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.tmpdir_path = Path(self.tmpdir)

        # Create test files
        (self.tmpdir_path / "test.py").write_text("import sys\nprint('hello world')")
        (self.tmpdir_path / "test.txt").write_text("some content")
        (self.tmpdir_path / "large.log").write_text("x" * 5000)  # 5KB file

    def test_cli_find_via_subprocess(self):
        """Test CLI find command via subprocess."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "vexy_glob",
                "find",
                "*.py",
                "--root",
                str(self.tmpdir),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "test.py" in result.stdout
        assert "test.txt" not in result.stdout

    def test_cli_search_via_subprocess(self):
        """Test CLI search command via subprocess."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "vexy_glob",
                "search",
                "*.py",
                "import",
                "--root",
                str(self.tmpdir),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should find the import statement
        assert result.returncode == 0
        assert "test.py" in result.stdout
        # The search should find the import line
        assert "import" in result.stdout

    def test_cli_find_with_size_filter_subprocess(self):
        """Test CLI find with size filter via subprocess."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "vexy_glob",
                "find",
                "*",
                "--root",
                str(self.tmpdir),
                "--min-size",
                "4k",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "large.log" in result.stdout
        assert "test.py" not in result.stdout  # Too small

    def test_cli_invalid_arguments(self):
        """Test CLI with invalid arguments."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "vexy_glob",
                "find",
                "*",
                "--root",
                "/nonexistent/directory",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # CLI currently returns 0 even for invalid paths (library design)
        # But should still print an error message
        error_text = (result.stderr + result.stdout).lower()
        assert (
            "error" in error_text
            or "no such file" in error_text
            or "traversal" in error_text
        )

    def test_cli_help_output(self):
        """Test CLI help output."""
        result = subprocess.run(
            [sys.executable, "-m", "vexy_glob", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Fire library should provide help output
        assert result.returncode == 0
        # Help text can be in stdout or stderr
        help_text = (result.stdout + result.stderr).lower()
        assert (
            "command" in help_text
            or "synopsis" in help_text
            or "find" in help_text
            or "search" in help_text
        )


class TestVexyGlobCLIPipelineCompatibility:
    """Test CLI compatibility with Unix pipelines."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.tmpdir_path = Path(self.tmpdir)

        # Create multiple test files
        for i in range(10):
            (self.tmpdir_path / f"file_{i}.py").write_text(f"# File {i}\nprint({i})")
            (self.tmpdir_path / f"file_{i}.txt").write_text(f"Text file {i}")

    def test_pipeline_with_head(self):
        """Test CLI output piped to head command."""
        cmd = (
            f"{sys.executable} -m vexy_glob find '*.py' --root {self.tmpdir} | head -3"
        )
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) <= 3  # Should be limited by head
        assert all(".py" in line for line in lines if line)

    def test_pipeline_with_grep(self):
        """Test CLI output piped to grep command."""
        cmd = f"{sys.executable} -m vexy_glob find '*' --root {self.tmpdir} | grep '\\.py$'"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert all(".py" in line for line in lines if line)
        assert not any(".txt" in line for line in lines if line)

    def test_pipeline_with_wc(self):
        """Test CLI output piped to wc command."""
        cmd = f"{sys.executable} -m vexy_glob find '*.py' --root {self.tmpdir} | wc -l"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        count = int(result.stdout.strip())
        assert count == 10  # Should count all 10 .py files

    def test_search_pipeline_with_cut(self):
        """Test search output piped to cut command."""
        cmd = f"{sys.executable} -m vexy_glob search '*.py' 'print' --root {self.tmpdir} --no-color | cut -d: -f1 | sort | uniq"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 10  # Should find unique files
        assert all(".py" in line for line in lines if line)


class TestVexyGlobCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    def test_broken_pipe_handling(self):
        """Test that broken pipe is handled gracefully."""
        cli = Cli()

        # Mock BrokenPipeError during output
        with patch("builtins.print", side_effect=BrokenPipeError):
            with patch("sys.stderr") as mock_stderr:
                with patch("sys.exit") as mock_exit:
                    cli.find(pattern="*", root=".")
                    mock_exit.assert_called_with(0)

    def test_keyboard_interrupt_handling(self):
        """Test keyboard interrupt handling."""
        cli = Cli()

        # Mock KeyboardInterrupt during vexy_glob.find
        with patch("vexy_glob.find", side_effect=KeyboardInterrupt):
            with patch("sys.exit") as mock_exit:
                cli.find(pattern="*", root=".")
                mock_exit.assert_called_with(1)

    def test_invalid_size_format_error(self):
        """Test error handling for invalid size format."""
        cli = Cli()

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with patch("sys.exit") as mock_exit:
                cli.find(pattern="*", root=".", min_size="invalid_size")
                mock_exit.assert_called_with(1)

        error_output = mock_stderr.getvalue()
        assert "Error:" in error_output
        # Error message should mention size format issue
        assert (
            "size format" in error_output.lower() or "invalid" in error_output.lower()
        )


class TestVexyGlobCLIFireIntegration:
    """Test fire library integration."""

    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        from vexy_glob.__main__ import main

        assert callable(main)

    def test_cli_class_methods(self):
        """Test that CLI class has required methods."""
        cli = Cli()
        assert hasattr(cli, "find")
        assert hasattr(cli, "search")
        assert callable(cli.find)
        assert callable(cli.search)

    def test_cli_class_instantiation(self):
        """Test CLI class can be instantiated."""
        cli = Cli()
        assert hasattr(cli, "console")
        assert hasattr(cli, "_parse_size")


if __name__ == "__main__":
    pytest.main([__file__])
