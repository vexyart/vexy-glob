# Python API

Everything public is exported from the `vexy_glob` package:

```python
from vexy_glob import (
    find, glob, iglob, search,
    VexyGlobError, PatternError, SearchError, TraversalNotSupportedError,
)
```

`vexy_glob.__version__` holds the installed package version, read from the
package metadata.

## `find()`

```python
find(
    pattern: str = "*",
    root: str | Path = ".",
    *,
    content: str | None = None,
    file_type: str | None = None,
    extension: str | list[str] | None = None,
    exclude: str | list[str] | None = None,
    max_depth: int | None = None,
    min_depth: int = 0,
    min_size: int | None = None,
    max_size: int | None = None,
    mtime_after: float | int | str | datetime | None = None,
    mtime_before: float | int | str | datetime | None = None,
    atime_after: float | int | str | datetime | None = None,
    atime_before: float | int | str | datetime | None = None,
    ctime_after: float | int | str | datetime | None = None,
    ctime_before: float | int | str | datetime | None = None,
    hidden: bool = False,
    ignore_git: bool = False,
    custom_ignore_files: str | list[str] | None = None,
    case_sensitive: bool | None = None,
    follow_symlinks: bool = False,
    same_file_system: bool = False,
    sort: "name" | "path" | "size" | "mtime" | None = None,
    threads: int | None = None,
    as_path: bool = False,
    as_list: bool = False,
)
```

Walks `root`, applies the filters and returns the matching paths. With
`content`, returns search results instead (see [Content search](content-search.md)).

Everything after `root` is keyword-only.

| Parameter | Default | Meaning |
| --- | --- | --- |
| `pattern` | `"*"` | Glob pattern. Without `/` it matches at any depth. See [Patterns and case](patterns.md). |
| `root` | `"."` | Directory to walk. Returned paths start with it. |
| `content` | `None` | Regex to search for inside matching files. |
| `file_type` | `None` | `"f"`, `"d"` or `"l"`. |
| `extension` | `None` | Extension or list of extensions, without the dot. |
| `exclude` | `None` | Glob pattern or list of patterns to drop. |
| `max_depth` | `None` | Deepest level to visit; the root is level 0. |
| `min_depth` | `0` | Accepted but not applied in the current release. |
| `min_size`, `max_size` | `None` | Inclusive size limits in bytes, applied to regular files. |
| `mtime_after`, `mtime_before` | `None` | Modification-time limits. |
| `atime_after`, `atime_before` | `None` | Access-time limits. |
| `ctime_after`, `ctime_before` | `None` | Creation-time limits. |
| `hidden` | `False` | Include entries whose name starts with a dot. |
| `ignore_git` | `False` | Stop honouring `.gitignore`, `.ignore`, `.git/info/exclude` and `.fdignore`. |
| `custom_ignore_files` | `None` | Extra ignore files in gitignore syntax. |
| `case_sensitive` | `None` | `None` is smart case; `True` or `False` forces a mode for glob and regex. |
| `follow_symlinks` | `False` | Descend into linked directories. |
| `same_file_system` | `False` | Do not cross mount points. |
| `sort` | `None` | Sort key; forces a list result. Ignored when `content` is set. |
| `threads` | `None` | Walker threads; `None` or `0` means one per logical CPU. |
| `as_path` | `False` | Return `pathlib.Path` objects instead of strings. |
| `as_list` | `False` | Return a list instead of an iterator. |

Time values accept Unix timestamps, `datetime` objects, ISO date strings and
relative strings such as `"-2h"`. See [Filters](filters.md#time).

**Returns**

| Call | Return value |
| --- | --- |
| no `content`, no `sort`, `as_list=False` | Iterator of `str` (or `Path`) |
| no `content`, `as_list=True` or `sort` set | `list` of `str` (or `Path`) |
| `content` set, `as_list=False` | Iterator of result dictionaries |
| `content` set, `as_list=True` | `list` of result dictionaries |

**Raises**

- `ImportError` if the compiled extension is missing (for example in a source
  checkout before `maturin develop`).
- `PatternError` for a glob or exclude pattern that cannot be parsed.
- `ValueError` for a time string in an unknown format, `TypeError` for a time
  value of another type.
- `VexyGlobError` for other errors reported by the Rust core, such as an
  invalid regex or an unknown `sort` value.

A `root` that does not exist does not raise. The walker reports
`Error during traversal: ... No such file or directory` on standard error
(iterator mode) and the result is empty.

## `glob()`

```python
glob(
    pattern: str,
    *,
    recursive: bool = False,
    root_dir: str | Path | None = None,
    include_hidden: bool = False,
) -> list[str]
```

Accepts the common keyword arguments of `glob.glob()` and returns a list of
strings. It calls `find(pattern, root=root_dir or ".", hidden=include_hidden,
as_list=True)`.

- `recursive=True` puts `**/` in front of the pattern if it contains no `**`.
- `root_dir` sets the directory to search. Returned paths start with it.

Because a pattern without `/` already matches at any depth (see
[Patterns and case](patterns.md)), `glob("*.py")` also returns files in
subdirectories, unlike `glob.glob("*.py")`. Paths start with `./` when
`root_dir` is not given. `.gitignore` rules apply.

## `iglob()`

```python
iglob(
    pattern: str,
    *,
    recursive: bool = False,
    root_dir: str | Path | None = None,
    include_hidden: bool = False,
) -> Iterator[str]
```

Same as `glob()`, but returns an iterator.

## `search()`

```python
search(
    content_regex: str,
    pattern: str = "*",
    root: str | Path = ".",
    **kwargs,
)
```

Searches file contents. Equivalent to
`find(pattern=pattern, root=root, content=content_regex, **kwargs)`, after
removing `sort` from `kwargs`. Returns an iterator of result dictionaries, or a
list with `as_list=True`.

Each result dictionary has the keys `path`, `line_number`, `line_text` and
`matches`. See [Content search](content-search.md#the-result-dictionary).

## Exceptions

```text
Exception
└── VexyGlobError
    ├── PatternError          (also a ValueError)
    ├── SearchError           (also an IOError / OSError)
    └── TraversalNotSupportedError  (also a NotImplementedError)
```

| Exception | When |
| --- | --- |
| `VexyGlobError` | Base class. Also raised for Rust-side errors that fit no subclass. |
| `PatternError` | A glob or exclude pattern is invalid. The `pattern` attribute holds the main `pattern` argument, even when the bad pattern was in `exclude`; the message names the bad one. |
| `SearchError` | An error message from the Rust core mentions permissions or I/O. |
| `TraversalNotSupportedError` | Defined for API compatibility; the current code does not raise it. |

Catch `VexyGlobError` to handle all of them in one place:

```python
try:
    files = vexy_glob.find(user_pattern, as_list=True)
except vexy_glob.PatternError as e:
    print(f"Bad pattern {e.pattern!r}")
except vexy_glob.VexyGlobError as e:
    print(f"Search failed: {e}")
```

## The extension module

The compiled module is `vexy_glob._vexy_glob`. It exposes lower-level `find()`
and `search()` functions that the Python layer calls. They take a list of
root paths, Unix timestamps as floats and pre-computed case flags. Treat them
as internal: their signatures can change between releases.
