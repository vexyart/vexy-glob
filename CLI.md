# `vexy_glob` CLI Documentation and Specification

This document outlines the design and specification for a command-line interface (CLI) for the `vexy_glob` library, to be implemented in a `__main__.py` file using the `fire` library.

## Overview

The `vexy_glob` CLI provides the full power of the `vexy_glob` library to the command line, allowing for fast, efficient file finding and content searching directly from your terminal.

## Installation

The CLI is included with the `vexy_glob` package. Once `vexy_glob` is installed, the CLI will be available as `vexy_glob`.

```bash
pip install vexy_glob
```

## Usage

The CLI is structured into two main commands:

- `vexy_glob find`: Find files based on various criteria.
- `vexy_glob search`: Search for content within files.

### `vexy_glob find`

Finds files matching a glob pattern and other filters.

**Usage:**

```bash
vexy_glob find [OPTIONS] <pattern>
```

**Arguments:**

- `<pattern>`: The glob pattern to search for (e.g., `"**/*.py"`).

**Options:**

- `--root <directory>`: The root directory to start the search from. Defaults to the current directory.
- `--min-size <size>`: Minimum file size (e.g., `10k`, `1M`, `1G`).
- `--max-size <size>`: Maximum file size.
- `--mtime-after <time>`: Find files modified after a specific time. Accepts relative times (`-1d`, `-2h`), ISO dates, or Unix timestamps.
- `--mtime-before <time>`: Find files modified before a specific time.
- `--no-gitignore`: Don't respect `.gitignore` files.
- `--hidden`: Include hidden files and directories.
- `--case-sensitive`: Make the search case-sensitive.
- `--type <file_type>`: Filter by file type (`f` for file, `d` for directory, `l` for symlink).
- `--extension <ext>`: Filter by file extension (e.g., `py`, `md`).
- `--depth <max_depth>`: The maximum depth to search.

**Examples:**

Find all Python files:

```bash
vexy_glob find "**/*.py"
```

Find all Markdown files larger than 10KB:

```bash
vexy_glob find "**/*.md" --min-size 10k
```

Find all log files modified in the last 2 days:

```bash
vexy_glob find "*.log" --mtime-after -2d
```

### `vexy_glob search`

Searches for a regex pattern within files.

**Usage:**

```bash
vexy_glob search [OPTIONS] <pattern> <content_pattern>
```

**Arguments:**

- `<pattern>`: The glob pattern for files to search within.
- `<content_pattern>`: The regex pattern to search for within the files.

**Options:**

- All the options from `vexy_glob find` are also available for `vexy_glob search`.
- `--no-color`: Disable colored output.

**Output Format:**

The output is similar to `grep`, with the file path, line number, and the matching line. Matches are highlighted.

```
path/to/file.py:123:import this
```

**Examples:**

Search for "import asyncio" in all Python files:

```bash
vexy_glob search "**/*.py" "import asyncio"
```

Search for a specific function definition in the `src` directory:

```bash
vexy_glob search "src/**/*.rs" "fn\s+my_function"
```

## Implementation with `fire`

The `__main__.py` file will use `fire.Fire` to expose the `find` and `search` functions from a class or a dictionary.

```python
# __main__.py
import fire
import vexy_glob
from rich import print

class Cli:
    def find(self, pattern, root=".", min_size=None, max_size=None, mtime_after=None, mtime_before=None, no_gitignore=False, hidden=False, case_sensitive=False, type=None, extension=None, depth=None):
        # ... implementation using vexy_glob.find ...
        for path in vexy_glob.find(...):
            print(path)

    def search(self, pattern, content_pattern, root=".", min_size=None, max_size=None, mtime_after=None, mtime_before=None, no_gitignore=False, hidden=False, case_sensitive=False, type=None, extension=None, depth=None, no_color=False):
        # ... implementation using vexy_glob.find with content ...
        for match in vexy_glob.find(content=content_pattern, ...):
            # ... print formatted and colored output using rich ...
            pass

if __name__ == '__main__':
    fire.Fire(Cli)

```

This structure will automatically generate the CLI with the specified commands and options, providing a seamless interface to the `vexy_glob` library's functionality.
