# Command line

Installing the package adds a `vg` command with two subcommands, `find` and
`search`. The CLI is built with Python Fire (`vexy_glob/__main__.py`), and each
subcommand calls the matching Python function.

## `vg find`

Prints one path per line.

```bash
vg find [PATTERN] [options]
```

`PATTERN` defaults to `*`. Quote it so the shell does not expand it.

| Option | Short | Value | Python argument |
| --- | --- | --- | --- |
| `--root` | `-r` | Directory to start in (default `.`) | `root` |
| `--min-size` | | Size string, see below | `min_size` |
| `--max-size` | | Size string, see below | `max_size` |
| `--mtime-after` | | Time string, e.g. `-2d`, `2025-01-01` | `mtime_after` |
| `--mtime-before` | | Time string | `mtime_before` |
| `--no-gitignore` | `-n` | Flag | `ignore_git=True` |
| `--hidden` | `-h` | Flag | `hidden=True` |
| `--case-sensitive` | `-c` | Flag, or `False` | `case_sensitive` |
| `--type` | `-t` | `f`, `d` or `l` | `file_type` |
| `--extension` | `-e` | Extension without the dot | `extension` |
| `--depth` | `-d` | Integer | `max_depth` |

Fire accepts both `--min-size` and `--min_size`. Note that `-h` means
`--hidden`; to see help, run `vg find --help`.

Examples:

```bash
# Python files anywhere below the current directory
vg find "*.py"

# Markdown files of at least 10 KiB
vg find "*.md" --min-size 10k

# Log files changed in the last two days
vg find "*.log" --mtime-after -2d

# Directories, one level deep
vg find "*" --type d --depth 1

# Search another directory and include hidden files
vg find "*.toml" --root ~/projects --hidden
```

The CLI exposes a subset of the API. Filters such as `exclude`, `atime_*`,
`ctime_*`, `follow_symlinks` and `sort` are available from Python only.

## `vg search`

Prints one line per match in the form `path:line_number:line_text`.

```bash
vg search PATTERN CONTENT_PATTERN [options]
```

- `PATTERN` is the glob for the files to search.
- `CONTENT_PATTERN` is the regular expression to look for.

`vg search` accepts every option of `vg find` plus:

| Option | Value | Effect |
| --- | --- | --- |
| `--no-color` | Flag | Plain text. Without it, the path is printed in magenta and the line number in green. |

Examples:

```bash
vg search "*.py" "import asyncio"
vg search "*.rs" "fn\s+main" --root src
vg search "*.md" "TODO" --no-color | cut -d: -f1 | sort -u
```

```text
./src/sub/b.py:1:TODO x
```

The trailing line ending of each match is removed before printing.

## Size strings

`--min-size` and `--max-size` take a number followed by an optional unit:

| Unit | Multiplier |
| --- | --- |
| none or `b` | 1 |
| `k` | 1,024 |
| `M` | 1,048,576 |
| `G` | 1,073,741,824 |
| `T` | 1,099,511,627,776 |

Units are case-insensitive and may be followed by `b` or `B` (`10kb`,
`1MB`). Decimals are allowed (`1.5M`).

Give the size with a unit. Fire turns a bare number such as `500` into an
integer, and the size parser then fails with
`Error: 'int' object has no attribute 'strip'`. Write `500b` instead.

## Output and exit codes

- Results are written to standard output as they are found.
- Errors are printed to standard output as `Error: <message>`, and the command
  exits with status 1.
- Ctrl+C exits with status 130.
- A closed pipe (for example `vg find "*" | head -1`) stops the command without
  an error message. In the current release the exit status is then 1, which
  matters only if your shell uses `set -o pipefail`.

## Running without the entry point

`python -m vexy_glob` runs the same CLI:

```bash
python -m vexy_glob find "*.py"
```
