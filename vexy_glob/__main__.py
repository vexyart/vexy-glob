#!/usr/bin/env python3
# this_file: vexy_glob/__main__.py
"""
Command-line interface for vexy_glob using fire library.

Provides 'vexy_glob find' and 'vexy_glob search' commands with full feature parity
to the Python API while offering a user-friendly CLI experience.
"""

import sys
import re
from pathlib import Path
from typing import Optional, Union, List
import fire
from rich.console import Console
from rich.text import Text
from rich import print as rprint
import vexy_glob


class VexyGlobCLI:
    """Command-line interface for vexy_glob - Path Accelerated Finding in Rust."""

    def __init__(self):
        self.console = Console()

    def _parse_size(self, size_str: str) -> int:
        """Parse human-readable size strings like '10k', '1M', '500G'."""
        if not size_str:
            return 0

        size_str = size_str.lower().strip()

        # Extract number and unit
        match = re.match(r"^(\d+(?:\.\d+)?)\s*([kmgt]?)b?$", size_str)
        if not match:
            raise ValueError(
                f"Invalid size format: {size_str}. Use formats like '10k', '1M', '500G'"
            )

        number, unit = match.groups()
        number = float(number)

        multipliers = {
            "": 1,
            "k": 1024,
            "m": 1024 * 1024,
            "g": 1024 * 1024 * 1024,
            "t": 1024 * 1024 * 1024 * 1024,
        }

        return int(number * multipliers[unit])

    def _format_search_result(self, result: dict, no_color: bool = False) -> str:
        """Format search results similar to grep output with optional coloring."""
        path = result["path"]
        line_number = result["line_number"]
        line_text = result["line_text"].rstrip()

        if no_color:
            return f"{path}:{line_number}:{line_text}"

        # Create colored output using rich
        path_text = Text(str(path), style="cyan")
        line_num_text = Text(str(line_number), style="green")

        # Highlight matches in the line text
        # For now, just show the line without highlighting specific matches
        # TODO: Implement match highlighting based on regex pattern
        line_content = Text(line_text)

        return f"{path_text}:{line_num_text}:{line_content}"

    def find(
        self,
        pattern: str = "*",
        root: str = ".",
        min_size: Optional[str] = None,
        max_size: Optional[str] = None,
        mtime_after: Optional[str] = None,
        mtime_before: Optional[str] = None,
        atime_after: Optional[str] = None,
        atime_before: Optional[str] = None,
        ctime_after: Optional[str] = None,
        ctime_before: Optional[str] = None,
        no_gitignore: bool = False,
        hidden: bool = False,
        case_sensitive: bool = False,
        type: Optional[str] = None,
        extension: Optional[str] = None,
        exclude: Optional[str] = None,
        depth: Optional[int] = None,
        follow_symlinks: bool = False,
        custom_ignore_files: Optional[str] = None,
    ):
        """
        Find files matching a glob pattern and optional filters.

        Args:
            pattern: Glob pattern to search for (e.g., "**/*.py")
            root: Root directory to start search from
            min_size: Minimum file size (e.g., "10k", "1M")
            max_size: Maximum file size (e.g., "10k", "1M")
            mtime_after: Files modified after this time (-1d, -2h, ISO dates, timestamps)
            mtime_before: Files modified before this time
            atime_after: Files accessed after this time
            atime_before: Files accessed before this time
            ctime_after: Files created after this time
            ctime_before: Files created before this time
            no_gitignore: Don't respect .gitignore files
            hidden: Include hidden files and directories
            case_sensitive: Make search case-sensitive
            type: Filter by type ('f' for file, 'd' for directory, 'l' for symlink)
            extension: Filter by file extension (e.g., "py", "md")
            exclude: Exclude pattern (e.g., "*.log")
            depth: Maximum search depth
            follow_symlinks: Follow symbolic links
            custom_ignore_files: Custom ignore files to use

        Examples:
            vexy_glob find "**/*.py"
            vexy_glob find "**/*.md" --min-size 10k
            vexy_glob find "*.log" --mtime-after -2d
            vexy_glob find "*" --type f --exclude "*.tmp"
        """
        try:
            # Parse size parameters
            min_size_bytes = self._parse_size(min_size) if min_size else None
            max_size_bytes = self._parse_size(max_size) if max_size else None

            # Convert exclude to list if provided
            exclude_list = [exclude] if exclude else None

            # Convert custom ignore files to list if provided
            custom_ignore_list = [custom_ignore_files] if custom_ignore_files else None

            # Call vexy_glob.find with all parameters
            results = vexy_glob.find(
                pattern=pattern,
                root=root,
                min_size=min_size_bytes,
                max_size=max_size_bytes,
                mtime_after=mtime_after,
                mtime_before=mtime_before,
                atime_after=atime_after,
                atime_before=atime_before,
                ctime_after=ctime_after,
                ctime_before=ctime_before,
                hidden=hidden,
                ignore_git=no_gitignore,
                case_sensitive=case_sensitive if case_sensitive else None,
                file_type=type,
                extension=extension,
                exclude=exclude_list,
                max_depth=depth,
                follow_symlinks=follow_symlinks,
                custom_ignore_files=custom_ignore_list,
                as_path=False,  # Return strings for CLI
                as_list=False,  # Stream results
            )

            # Print results
            try:
                for path in results:
                    print(path)
            except BrokenPipeError:
                # Handle broken pipe gracefully for Unix pipelines
                sys.stderr.close()
                sys.exit(0)

        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    def search(
        self,
        pattern: str,
        content_pattern: str,
        root: str = ".",
        min_size: Optional[str] = None,
        max_size: Optional[str] = None,
        mtime_after: Optional[str] = None,
        mtime_before: Optional[str] = None,
        atime_after: Optional[str] = None,
        atime_before: Optional[str] = None,
        ctime_after: Optional[str] = None,
        ctime_before: Optional[str] = None,
        no_gitignore: bool = False,
        hidden: bool = False,
        case_sensitive: bool = False,
        type: Optional[str] = None,
        extension: Optional[str] = None,
        exclude: Optional[str] = None,
        depth: Optional[int] = None,
        follow_symlinks: bool = False,
        custom_ignore_files: Optional[str] = None,
        no_color: bool = False,
    ):
        """
        Search for content within files using regex patterns.

        Args:
            pattern: Glob pattern for files to search within
            content_pattern: Regex pattern to search for in file contents
            root: Root directory to start search from
            min_size: Minimum file size (e.g., "10k", "1M")
            max_size: Maximum file size (e.g., "10k", "1M")
            mtime_after: Files modified after this time
            mtime_before: Files modified before this time
            atime_after: Files accessed after this time
            atime_before: Files accessed before this time
            ctime_after: Files created after this time
            ctime_before: Files created before this time
            no_gitignore: Don't respect .gitignore files
            hidden: Include hidden files and directories
            case_sensitive: Make search case-sensitive
            type: Filter by type ('f' for file, 'd' for directory, 'l' for symlink)
            extension: Filter by file extension
            exclude: Exclude pattern
            depth: Maximum search depth
            follow_symlinks: Follow symbolic links
            custom_ignore_files: Custom ignore files to use
            no_color: Disable colored output

        Examples:
            vexy_glob search "**/*.py" "import asyncio"
            vexy_glob search "src/**/*.rs" "fn\\s+my_function"
            vexy_glob search "**/*.md" "TODO|FIXME" --no-color
        """
        try:
            # Parse size parameters
            min_size_bytes = self._parse_size(min_size) if min_size else None
            max_size_bytes = self._parse_size(max_size) if max_size else None

            # Convert exclude to list if provided
            exclude_list = [exclude] if exclude else None

            # Convert custom ignore files to list if provided
            custom_ignore_list = [custom_ignore_files] if custom_ignore_files else None

            # Call vexy_glob.search with all parameters
            results = vexy_glob.search(
                content_regex=content_pattern,
                pattern=pattern,
                root=root,
                min_size=min_size_bytes,
                max_size=max_size_bytes,
                mtime_after=mtime_after,
                mtime_before=mtime_before,
                atime_after=atime_after,
                atime_before=atime_before,
                ctime_after=ctime_after,
                ctime_before=ctime_before,
                hidden=hidden,
                ignore_git=no_gitignore,
                case_sensitive=case_sensitive if case_sensitive else None,
                file_type=type,
                extension=extension,
                exclude=exclude_list,
                max_depth=depth,
                follow_symlinks=follow_symlinks,
                custom_ignore_files=custom_ignore_list,
                as_path=False,  # Return strings for CLI
                as_list=False,  # Stream results
            )

            # Print formatted results
            try:
                for result in results:
                    if no_color:
                        output = self._format_search_result(result, no_color=True)
                        print(output)
                    else:
                        # Use rich for colored output
                        path = result["path"]
                        line_number = result["line_number"]
                        line_text = result["line_text"].rstrip()

                        self.console.print(
                            f"[cyan]{path}[/cyan]:[green]{line_number}[/green]:{line_text}"
                        )
            except BrokenPipeError:
                # Handle broken pipe gracefully for Unix pipelines
                sys.stderr.close()
                sys.exit(0)

        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    """Main entry point for the CLI."""
    fire.Fire(VexyGlobCLI)


if __name__ == "__main__":
    main()
