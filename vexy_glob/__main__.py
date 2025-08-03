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


class Cli:
    """vexy_glob - Path Accelerated Finding in Rust
    
    A high-performance file finding and content searching tool built with Rust.
    """

    def __init__(self):
        self.console = Console()

    def _parse_size(self, size_str: str) -> int:
        """Parse human-readable size strings like '10k', '1M', '500G'."""
        if not size_str:
            return 0

        size_str = size_str.strip()

        # Extract number and unit
        match = re.match(r"^(\d+(?:\.\d+)?)\s*([kKmMgGtT]?)([bB]?)$", size_str)
        if not match:
            raise ValueError(
                f"Invalid size format: {size_str}. Use formats like '10k', '1M', '500G'"
            )

        number = float(match.group(1))
        unit = match.group(2).upper() if match.group(2) else ''

        multipliers = {
            "": 1,
            "K": 1024,
            "M": 1024 * 1024,
            "G": 1024 * 1024 * 1024,
            "T": 1024 * 1024 * 1024 * 1024,
        }

        return int(number * multipliers.get(unit, 1))

    def find(
        self,
        pattern: str = "*",
        root: str = ".",
        min_size: Optional[str] = None,
        max_size: Optional[str] = None,
        mtime_after: Optional[str] = None,
        mtime_before: Optional[str] = None,
        no_gitignore: bool = False,
        hidden: bool = False,
        case_sensitive: Optional[bool] = None,
        type: Optional[str] = None,
        extension: Optional[Union[str, List[str]]] = None,
        depth: Optional[int] = None,
    ):
        """Find files matching a glob pattern.

        Arguments:
            pattern: The glob pattern to search for (e.g., "**/*.py")

        Options:
            --root: The root directory to start the search from (default: current directory)
            --min-size: Minimum file size (e.g., "10k", "1M", "1G")
            --max-size: Maximum file size
            --mtime-after: Find files modified after a specific time (e.g., "-1d", "-2h", ISO dates)
            --mtime-before: Find files modified before a specific time
            --no-gitignore: Don't respect .gitignore files
            --hidden: Include hidden files and directories
            --case-sensitive: Make the search case-sensitive
            --type: Filter by file type ("f" for file, "d" for directory, "l" for symlink)
            --extension: Filter by file extension (e.g., "py", "md")
            --depth: The maximum depth to search

        Examples:
            vexy_glob find "**/*.py"
            vexy_glob find "**/*.md" --min-size 10k
            vexy_glob find "*.log" --mtime-after -2d
        """
        try:
            # Parse size parameters
            min_size_bytes = self._parse_size(min_size) if min_size else None
            max_size_bytes = self._parse_size(max_size) if max_size else None

            # Call vexy_glob.find with all parameters
            results = vexy_glob.find(
                pattern=pattern,
                root=root,
                min_size=min_size_bytes,
                max_size=max_size_bytes,
                mtime_after=mtime_after,
                mtime_before=mtime_before,
                hidden=hidden,
                ignore_git=no_gitignore,
                case_sensitive=case_sensitive,
                file_type=type,
                extension=extension,
                max_depth=depth,
                as_path=False,  # Return strings for CLI
                as_list=False,  # Stream results
            )

            # Print results
            try:
                for path in results:
                    rprint(path)
            except BrokenPipeError:
                # Handle broken pipe gracefully for Unix pipelines
                sys.stderr.close()
                sys.exit(0)

        except KeyboardInterrupt:
            sys.exit(130)  # Standard exit code for Ctrl+C
        except Exception as e:
            self.console.print(f"[red]Error:[/red] {e}")
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
        no_gitignore: bool = False,
        hidden: bool = False,
        case_sensitive: Optional[bool] = None,
        type: Optional[str] = None,
        extension: Optional[Union[str, List[str]]] = None,
        depth: Optional[int] = None,
        no_color: bool = False,
    ):
        """Search for content within files.

        Arguments:
            pattern: The glob pattern for files to search within
            content_pattern: The regex pattern to search for within the files

        Options:
            All options from 'find' command, plus:
            --no-color: Disable colored output

        Output Format:
            path/to/file.py:123:import this

        Examples:
            vexy_glob search "**/*.py" "import asyncio"
            vexy_glob search "src/**/*.rs" "fn\\s+my_function"
        """
        try:
            # Parse size parameters
            min_size_bytes = self._parse_size(min_size) if min_size else None
            max_size_bytes = self._parse_size(max_size) if max_size else None

            # Call vexy_glob.search with all parameters
            results = vexy_glob.search(
                content_regex=content_pattern,
                pattern=pattern,
                root=root,
                min_size=min_size_bytes,
                max_size=max_size_bytes,
                mtime_after=mtime_after,
                mtime_before=mtime_before,
                hidden=hidden,
                ignore_git=no_gitignore,
                case_sensitive=case_sensitive,
                file_type=type,
                extension=extension,
                max_depth=depth,
                as_path=False,  # Return strings for CLI
                as_list=False,  # Stream results
            )

            # Print formatted results
            try:
                for result in results:
                    # Handle both dict and object access patterns
                    if isinstance(result, dict):
                        path = result["path"]
                        line_number = result["line_number"]
                        line_text = result["line_text"].rstrip()
                        matches = result.get("matches", [])
                    else:
                        path = result.path
                        line_number = result.line_number
                        line_text = result.line_text.rstrip()
                        matches = getattr(result, "matches", [])
                    
                    if no_color:
                        # Plain output
                        print(f"{path}:{line_number}:{line_text}")
                    else:
                        # Colored output with highlighted matches
                        text = Text()
                        
                        # Add path in magenta
                        text.append(str(path), style="magenta")
                        text.append(":")
                        
                        # Add line number in green
                        text.append(str(line_number), style="green")
                        text.append(":")
                        
                        # Add line text - matches field contains matched strings, not positions
                        # For now, just show the line without highlighting specific matches
                        # TODO: Implement proper match highlighting using regex to find positions
                        text.append(line_text)
                        
                        self.console.print(text)
                        
            except BrokenPipeError:
                # Handle broken pipe gracefully for Unix pipelines
                sys.stderr.close()
                sys.exit(0)

        except KeyboardInterrupt:
            sys.exit(130)  # Standard exit code for Ctrl+C
        except Exception as e:
            self.console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)


def main():
    """Main entry point for the CLI."""
    fire.Fire(Cli)


if __name__ == "__main__":
    main()
