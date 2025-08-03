# this_file: vexy_glob/__init__.py
"""
vexy_glob - Path Accelerated Finding in Rust

A high-performance Python extension for file system traversal and searching.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union, List, Iterator, Optional, Literal, TYPE_CHECKING
from datetime import datetime, timezone
import time

# Import the Rust extension module
try:
    from . import _vexy_glob
except ImportError:
    # Development mode - module not built yet
    _vexy_glob = None

if TYPE_CHECKING:
    from typing import TypedDict

    class SearchResult(TypedDict):
        """Result from content search."""

        path: Union[str, Path]
        line_number: int
        line_text: str
        matches: List[str]


__version__ = "0.1.0"
__all__ = [
    "find",
    "glob",
    "iglob",
    "search",
    "VexyGlobError",
    "PatternError",
    "SearchError",
    "TraversalNotSupportedError",
]


# Custom exceptions
class VexyGlobError(Exception):
    """Base exception for all vexy_glob errors."""

    pass


class PatternError(VexyGlobError, ValueError):
    """Raised when a provided glob or regex pattern is invalid."""

    def __init__(self, message: str, pattern: str):
        self.pattern = pattern
        super().__init__(f"{message}: '{pattern}'")


class SearchError(VexyGlobError, IOError):
    """Raised for non-recoverable I/O or traversal errors."""

    pass


class TraversalNotSupportedError(VexyGlobError, NotImplementedError):
    """Raised when an unsupported traversal strategy is requested."""

    pass


def _parse_time_param(value: Union[float, int, str, datetime, None]) -> Optional[float]:
    """
    Convert various time formats to Unix timestamp.

    Supports:
    - float/int: Unix timestamp (returned as-is)
    - datetime: Python datetime object
    - str: ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    - str: Relative time (-1d, -2h, -30m, -45s)
    - None: Returns None
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, datetime):
        return value.timestamp()

    if isinstance(value, str):
        # Try relative time format first
        if value.startswith("-"):
            try:
                amount = float(value[1:-1])
                unit = value[-1].lower()

                if unit == "s":
                    return time.time() - amount
                elif unit == "m":
                    return time.time() - (amount * 60)
                elif unit == "h":
                    return time.time() - (amount * 3600)
                elif unit == "d":
                    return time.time() - (amount * 86400)
                else:
                    raise ValueError(f"Unknown time unit: {unit}")
            except (ValueError, IndexError):
                pass

        # Try ISO date format
        try:
            # Handle date-only format
            if "T" not in value and len(value) == 10:
                value += "T00:00:00"

            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.timestamp()
        except ValueError:
            raise ValueError(
                f"Invalid time format: {value}. "
                "Use Unix timestamp, datetime object, ISO format (YYYY-MM-DD), "
                "or relative time (-1d, -2h, -30m, -45s)"
            )

    raise TypeError(f"Unsupported time type: {type(value)}")


def find(
    pattern: str = "*",
    root: Union[str, Path] = ".",
    *,
    content: Optional[str] = None,
    file_type: Optional[str] = None,
    extension: Optional[Union[str, List[str]]] = None,
    exclude: Optional[Union[str, List[str]]] = None,
    max_depth: Optional[int] = None,
    min_depth: int = 0,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    mtime_after: Optional[Union[float, int, str, datetime]] = None,
    mtime_before: Optional[Union[float, int, str, datetime]] = None,
    atime_after: Optional[Union[float, int, str, datetime]] = None,
    atime_before: Optional[Union[float, int, str, datetime]] = None,
    ctime_after: Optional[Union[float, int, str, datetime]] = None,
    ctime_before: Optional[Union[float, int, str, datetime]] = None,
    hidden: bool = False,
    ignore_git: bool = False,
    custom_ignore_files: Optional[Union[str, List[str]]] = None,
    case_sensitive: Optional[bool] = None,  # None = smart case
    follow_symlinks: bool = False,
    threads: Optional[int] = None,
    as_path: bool = False,
    as_list: bool = False,
) -> Union[Iterator[Union[str, Path]], List[Union[str, Path]]]:
    """
    Find files and directories with high performance.

    Args:
        pattern: Glob pattern to match against file paths (default: "*")
        root: Starting directory for search (default: current directory)
        content: Optional regex pattern to search within file contents
        file_type: Filter by type: 'f' (files), 'd' (directories), 'l' (symlinks)
        extension: Filter by file extension(s), e.g. "py" or ["py", "pyx"]
        exclude: Glob pattern(s) to exclude from results, e.g. "*.log" or ["*.tmp", "*.cache"]
        max_depth: Maximum depth to recurse into directories
        min_depth: Minimum depth before yielding results (default: 0)
        min_size: Minimum file size in bytes (only applies to files)
        max_size: Maximum file size in bytes (only applies to files)
        mtime_after: Only include files modified after this time
                    Accepts: Unix timestamp, datetime, ISO date (YYYY-MM-DD),
                    or relative time (-1d, -2h, -30m, -45s)
        mtime_before: Only include files modified before this time
                     Accepts: Unix timestamp, datetime, ISO date (YYYY-MM-DD),
                     or relative time (-1d, -2h, -30m, -45s)
        atime_after: Only include files accessed after this time
                    Accepts: Unix timestamp, datetime, ISO date (YYYY-MM-DD),
                    or relative time (-1d, -2h, -30m, -45s)
        atime_before: Only include files accessed before this time
                     Accepts: Unix timestamp, datetime, ISO date (YYYY-MM-DD),
                     or relative time (-1d, -2h, -30m, -45s)
        ctime_after: Only include files created after this time
                    Accepts: Unix timestamp, datetime, ISO date (YYYY-MM-DD),
                    or relative time (-1d, -2h, -30m, -45s)
        ctime_before: Only include files created before this time
                     Accepts: Unix timestamp, datetime, ISO date (YYYY-MM-DD),
                     or relative time (-1d, -2h, -30m, -45s)
        hidden: Include hidden files and directories (default: False)
        ignore_git: Ignore .gitignore rules (default: False)
        custom_ignore_files: List of custom ignore files to process (e.g., [".myignore", "custom.ignore"])
                            Files will be processed if they exist. .fdignore files are automatically
                            detected and processed when ignore_git=False.
        case_sensitive: Case sensitivity for patterns (None = smart case)
        follow_symlinks: Follow symbolic links (default: False)
        threads: Number of parallel threads (None = auto-detect)
        as_path: Return pathlib.Path objects instead of strings
        as_list: Return a list instead of an iterator

    Returns:
        Iterator or list of matching paths (strings or Path objects)

    Raises:
        PatternError: If the pattern is invalid
        SearchError: If a non-recoverable I/O error occurs
    """
    if _vexy_glob is None:
        raise ImportError(
            "vexy_glob extension module not built. Run 'maturin develop' first."
        )

    # Convert root to string if Path
    if isinstance(root, Path):
        root = str(root)

    # Convert extension to list if string
    if isinstance(extension, str):
        extension = [extension]

    # Convert exclude to list if string
    if isinstance(exclude, str):
        exclude = [exclude]

    # Convert custom_ignore_files to list if string
    if isinstance(custom_ignore_files, str):
        custom_ignore_files = [custom_ignore_files]

    # Parse time parameters to Unix timestamps
    mtime_after = _parse_time_param(mtime_after)
    mtime_before = _parse_time_param(mtime_before)
    atime_after = _parse_time_param(atime_after)
    atime_before = _parse_time_param(atime_before)
    ctime_after = _parse_time_param(ctime_after)
    ctime_before = _parse_time_param(ctime_before)

    # Validate traversal method is depth-first only
    # (This is implicit - we don't expose traversal option in public API)

    # Call Rust implementation
    try:
        if content is not None:
            # Content search mode
            results = _vexy_glob.search(
                content_regex=content,
                paths=[root],
                glob=pattern,
                file_type=file_type,
                extension=extension,
                exclude=exclude,
                max_depth=max_depth,
                min_size=min_size,
                max_size=max_size,
                mtime_after=mtime_after,
                mtime_before=mtime_before,
                atime_after=atime_after,
                atime_before=atime_before,
                ctime_after=ctime_after,
                ctime_before=ctime_before,
                hidden=hidden,
                no_ignore=ignore_git,
                custom_ignore_files=custom_ignore_files,
                follow_symlinks=follow_symlinks,
                case_sensitive_glob=case_sensitive is not False,
                _case_sensitive_content=case_sensitive is not False,
                as_path_objects=as_path,
                yield_results=not as_list,
                _multiline=False,
                threads=threads or 0,
            )
        else:
            # Path-only search mode
            results = _vexy_glob.find(
                paths=[root],
                glob=pattern,
                file_type=file_type,
                extension=extension,
                exclude=exclude,
                max_depth=max_depth,
                min_size=min_size,
                max_size=max_size,
                mtime_after=mtime_after,
                mtime_before=mtime_before,
                atime_after=atime_after,
                atime_before=atime_before,
                ctime_after=ctime_after,
                ctime_before=ctime_before,
                hidden=hidden,
                no_ignore=ignore_git,
                custom_ignore_files=custom_ignore_files,
                follow_symlinks=follow_symlinks,
                case_sensitive_glob=case_sensitive is not False,
                as_path_objects=as_path,
                yield_results=not as_list,
                threads=threads or 0,
            )
    except Exception as e:
        # Convert Rust errors to Python exceptions
        error_msg = str(e).lower()
        if "invalid" in error_msg and ("pattern" in error_msg or "glob" in error_msg):
            raise PatternError(str(e), pattern)
        elif "permission" in error_msg or "i/o error" in error_msg:
            raise SearchError(str(e))
        else:
            raise VexyGlobError(str(e))

    return results


def glob(
    pattern: str,
    *,
    recursive: bool = False,
    root_dir: Optional[Union[str, Path]] = None,
    include_hidden: bool = False,
) -> List[str]:
    """
    Drop-in replacement for glob.glob() with massive performance improvements.

    Args:
        pattern: Glob pattern to match
        recursive: Allow ** to match any number of directories
        root_dir: Directory to search in (default: current directory)
        include_hidden: Include hidden files in results

    Returns:
        List of matching file paths as strings
    """
    # Handle recursive flag by modifying pattern if needed
    if recursive and "**" not in pattern:
        pattern = f"**/{pattern}"

    root = root_dir or "."

    return find(
        pattern=pattern,
        root=root,
        hidden=include_hidden,
        as_list=True,
        as_path=False,
    )


def iglob(
    pattern: str,
    *,
    recursive: bool = False,
    root_dir: Optional[Union[str, Path]] = None,
    include_hidden: bool = False,
) -> Iterator[str]:
    """
    Drop-in replacement for glob.iglob() with streaming results.

    Args:
        pattern: Glob pattern to match
        recursive: Allow ** to match any number of directories
        root_dir: Directory to search in (default: current directory)
        include_hidden: Include hidden files in results

    Returns:
        Iterator of matching file paths as strings
    """
    # Handle recursive flag by modifying pattern if needed
    if recursive and "**" not in pattern:
        pattern = f"**/{pattern}"

    root = root_dir or "."

    return find(
        pattern=pattern,
        root=root,
        hidden=include_hidden,
        as_list=False,
        as_path=False,
    )


def search(
    content_regex: str,
    pattern: str = "*",
    root: Union[str, Path] = ".",
    **kwargs,
) -> Union[Iterator["SearchResult"], List["SearchResult"]]:
    """
    Search for content within files, similar to ripgrep.

    Args:
        content_regex: Regular expression to search for in file contents
        pattern: Glob pattern for files to search in
        root: Starting directory for search
        **kwargs: Additional arguments passed to find()

    Returns:
        Iterator or list of SearchResult dictionaries
    """
    return find(pattern=pattern, root=root, content=content_regex, **kwargs)
