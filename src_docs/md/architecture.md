# Architecture

`vexy-glob` has two layers: a thin Python package that normalises arguments,
and a Rust extension module that walks the file system, filters entries and
searches file contents.

```text
vexy_glob/__init__.py      Python API: find, glob, iglob, search, exceptions
vexy_glob/__main__.py      CLI (Fire): vg find, vg search
src/lib.rs                 PyO3 module vexy_glob._vexy_glob: walker, filters, search
src/pattern_cache.rs       Compiled glob cache (LRU, 1000 entries)
src/global_init.rs         One-time initialisation when the module is imported
src/zero_copy_path.rs      Path helpers prepared for later use (not called yet)
src/simd_string.rs         String helpers prepared for later use (not called yet)
```

## Python layer

`vexy_glob.find()` does no file-system work itself. It:

1. Converts a `Path` root to `str`.
2. Works out the case mode. With `case_sensitive=None`, the glob is
   case-sensitive if it contains an uppercase letter, and the content regex is
   checked the same way on its own.
3. Turns single strings for `extension`, `exclude` and `custom_ignore_files`
   into one-element lists.
4. Converts every time argument to a Unix timestamp (`float`). Relative values
   such as `"-2h"` are resolved against `time.time()` at this point.
5. Calls `_vexy_glob.find()` or, when `content` is set, `_vexy_glob.search()`.
6. Maps errors from the Rust side to `PatternError`, `SearchError` or
   `VexyGlobError` by looking at the error message.

`glob()`, `iglob()` and `search()` are small wrappers around `find()`.

## Rust core

### Walking

The core builds an `ignore::WalkBuilder` for the root and configures it from
the arguments:

| Builder setting | Set from |
| --- | --- |
| `hidden(!hidden)` | `hidden` |
| `ignore`, `git_ignore`, `git_exclude` | `not ignore_git` |
| `git_global(true)` | always on |
| `follow_links` | `follow_symlinks` |
| `same_file_system` | `same_file_system` |
| `max_depth` | `max_depth` |
| `threads` | `threads`, or the CPU count when 0 |
| `add_ignore(path)` | each existing file in `custom_ignore_files`, and `<root>/.fdignore` unless `ignore_git` |

It then starts the parallel walker (`build_parallel()`) on a separate thread
and returns to Python.

### Filtering

Each walker thread runs every entry through one function,
`should_include_entry()`, which checks in this order: glob pattern, exclude
patterns, file type, extension, size, modification time, access time and
creation time. The first failed check rejects the entry. Size and time checks
read the entry's metadata only when such a filter is set.

Glob patterns are compiled once and kept in a process-wide cache keyed by
pattern and case mode. A pattern with no wildcard characters skips `globset`
and is compared as a plain string.

### Streaming results to Python

Accepted paths go into a bounded `crossbeam-channel` channel. Its capacity
depends on the job:

| Job | Channel capacity |
| --- | --- |
| Content search | 500 |
| Path search with `sort` | 10,000 |
| Path search, `threads` not set | 1,000 |
| Path search, `threads=n` | 1,000 × n, at most 8,000 |

When Python asks for an iterator, the core wraps the receiving end of the
channel in a `VexyGlobIterator` object. Each `next()` call takes one result
from the channel and converts it to a `str`, a `pathlib.Path` or, for content
search, a `dict`. If Python reads slower than the walker produces, the channel
fills up and the walker threads wait, so memory use stays bounded.

When Python asks for a list (`as_list=True` or `sort`), the core releases the
GIL, drains the channel while the walker runs, then joins the walker thread,
sorts if requested, and builds a Python list. Releases up to 1.0.9 joined the
walker first and could hang on large result sets; see
[Troubleshooting](troubleshooting.md#a-call-with-as_listtrue-never-returns).

### Content search

For `search()`, entries that pass `should_include_entry()` and are regular
files are opened and scanned with a `grep_searcher::Searcher` and a
`grep_regex::RegexMatcher`. A custom sink collects one record per matching
line (path, line number, line text) and sends the records for a file to the
channel after the file is finished.

### Errors during the walk

Walker errors (unreadable directories, a missing root) and file-open errors
travel through the same channel as error records. The iterator prints them to
standard error with the prefix `Error during traversal:` and moves on. The
list path discards them.

## Build and packaging

The project is a maturin "mixed" layout (`python-source = "."` in
`pyproject.toml`): maturin compiles the crate in `src/` into
`vexy_glob/_vexy_glob.*.so` (or `.pyd` on Windows) and packages it together
with the Python files in `vexy_glob/`. PyO3 is built with the `abi3-py38`
feature, so one wheel per platform works on CPython 3.8 and newer.

The release profile in `Cargo.toml` uses `opt-level = 3`, LTO, one codegen
unit, `panic = "abort"` and stripped symbols.

The package version is the `version` in `Cargo.toml`; `pyproject.toml`
declares it as dynamic. See [Contributing](contributing.md#releasing) for how a
release keeps the git tag and `Cargo.toml` in step.
