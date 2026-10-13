# vexy-glob

`vexy-glob` finds files and searches their contents from Python. The work
happens in a Rust extension module built on the `ignore` crate (the directory
walker behind `fd`) and the `grep-searcher` crate (the search engine behind
`ripgrep`). Python receives the matching paths as they are found, through an
iterator, so the first results arrive before the walk finishes.

The import name is `vexy_glob`. The PyPI package name is `vexy-glob`. The
command-line tool is `vg`.

## What it does

You give it a glob pattern, a starting directory and optional filters. It walks
the directory tree on several threads, skips what `.gitignore` and hidden-file
rules exclude, applies your filters, and yields each path that passes.

```python
import vexy_glob

for path in vexy_glob.find("*.py", root="src"):
    print(path)
```

With a project that contains `src/a.py` and `src/sub/b.py`, this prints:

```text
src/a.py
src/sub/b.py
```

The order can differ from run to run, because several threads walk the tree at
once. Pass `sort="path"` when you need a stable order.

Add a regular expression with `content=` (or call `search()`) and the tool reads
each matching file and yields one dictionary per matching line:

```python
for hit in vexy_glob.search("TODO", "*.py", root="src"):
    print(f"{hit['path']}:{hit['line_number']}:{hit['line_text'].rstrip()}")
```

```text
src/sub/b.py:1:TODO x
```

## Main features

- **Streaming results.** `find()` returns an iterator by default. Pass
  `as_list=True` to get a list.
- **Ignore rules.** `.gitignore`, `.ignore`, `.git/info/exclude` and a root
  `.fdignore` file are honoured unless you pass `ignore_git=True`.
- **Filters.** File type, extension, exclude patterns, size, modification time,
  access time, creation time and depth.
- **Smart case.** A pattern without uppercase letters matches case-insensitively.
  A pattern with an uppercase letter matches case-sensitively.
- **Content search.** Regular expressions in Rust `regex` syntax, run only on
  files that pass the path filters.
- **`glob` replacements.** `vexy_glob.glob()` and `vexy_glob.iglob()` accept the
  common arguments of `glob.glob()` and `glob.iglob()`.
- **CLI.** `vg find` and `vg search` expose the same engine in the terminal.

## Where to go next

| Page | What it covers |
| --- | --- |
| [Installation](installation.md) | Installing from PyPI and from source |
| [Quickstart](quickstart.md) | A first session, step by step |
| [Patterns and case](patterns.md) | How glob patterns are matched against paths |
| [Filters](filters.md) | Type, extension, exclude, size, time, depth, ignore files |
| [Content search](content-search.md) | Regex search inside files and the result format |
| [Command line](cli.md) | The `vg find` and `vg search` commands |
| [Python API](api.md) | Every function, parameter and exception |
| [Architecture](architecture.md) | How the Rust core and the Python layer fit together |
| [Troubleshooting](troubleshooting.md) | Empty results, errors and surprises |
| [Contributing](contributing.md) | Building, testing and releasing |
