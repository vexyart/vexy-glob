# Filters

Every filter is a keyword argument of `find()`, and `search()` passes its extra
keyword arguments on to `find()`. Filters combine with AND: an entry is
returned only if it passes all of them. The walker applies them in the Rust
core, so rejected entries never reach Python.

## File type

`file_type` keeps one kind of entry:

| Value | Keeps |
| --- | --- |
| `"f"` | Regular files |
| `"d"` | Directories |
| `"l"` | Symbolic links |

```python
>>> vexy_glob.find("*", file_type="d", sort="path")
['.', './src', './src/sub']
```

Without `file_type`, results include files, directories and links. Any other
value is ignored and no type filter is applied.

## Extension

`extension` takes one extension or a list, written without the leading dot:

```python
vexy_glob.find("*", extension="py")
vexy_glob.find("*", extension=["py", "pyi"])
```

The comparison is exact and case-sensitive, and it uses the part after the
last dot. Entries without an extension (including most directories) are
dropped. `extension=".py"` matches nothing, because the stored extension is
`py`.

## Exclude patterns

`exclude` takes one glob pattern or a list. An entry whose path matches any of
them is dropped:

```python
vexy_glob.find("*.py", exclude=["*_test.py", "**/build/**"])
```

Exclude patterns follow the same rules as the main pattern (see
[Patterns and case](patterns.md)): a pattern without `/` gets a `**/` prefix,
and the case mode of the main pattern applies. Exclusion removes the matching
entries from the results. It does not stop the walker from entering an
excluded directory, so prefer `.gitignore` or a custom ignore file for large
trees you never want to visit.

## Size

`min_size` and `max_size` are byte counts and both limits are inclusive.
They apply only to regular files; directories and links pass through
unchanged, so combine them with `file_type="f"` to get files only.

```python
# Files from 1 KiB up to 10 MiB
vexy_glob.find("*", file_type="f", min_size=1024, max_size=10 * 1024 * 1024)
```

The [command line](cli.md) accepts sizes such as `10k` or `1M` and converts
them to bytes. The Python API takes integers only.

## Time

Six parameters filter by timestamp:

| Parameter | Timestamp used | Keeps entries |
| --- | --- | --- |
| `mtime_after` | last modification | modified at or after the value |
| `mtime_before` | last modification | modified at or before the value |
| `atime_after` | last access | accessed at or after the value |
| `atime_before` | last access | accessed at or before the value |
| `ctime_after` | creation time | created at or after the value |
| `ctime_before` | creation time | created at or before the value |

`ctime_*` uses the file's creation (birth) time as reported by Rust's
`Metadata::created()`. If a timestamp cannot be read (some Linux file systems
do not record creation time), the entry is kept: the time filter does not
remove it. Access times depend on the mount options of the
file system (for example `noatime` or `relatime` on Linux).

Each value can be:

| Form | Example | Meaning |
| --- | --- | --- |
| `int` or `float` | `1735689600` | Unix timestamp in seconds |
| `datetime` | `datetime(2025, 1, 1)` | Converted with `.timestamp()` |
| ISO date | `"2025-01-01"` | Midnight at the start of that day, local time |
| ISO date and time | `"2025-01-01T12:30:00"` | That moment; a trailing `Z` means UTC |
| Relative | `"-30s"`, `"-15m"`, `"-2h"`, `"-7d"` | That long before now |

Relative values start with `-` and end with `s`, `m`, `h` or `d`. A string
that fits none of these forms raises `ValueError`.

```python
from datetime import datetime

# Modified in the last two hours
vexy_glob.find("*.log", mtime_after="-2h")

# Modified during January 2025
vexy_glob.find("*", mtime_after="2025-01-01", mtime_before="2025-02-01")

# Not accessed since a fixed date
vexy_glob.find("*", file_type="f", atime_before=datetime(2024, 6, 1))
```

## Depth

`max_depth` limits how far the walker descends. The root is depth 0, its
direct children are depth 1, and so on:

```python
>>> vexy_glob.find("*", max_depth=0, as_list=True)
['.']
>>> vexy_glob.find("*.py", max_depth=2, as_list=True)
['./src/a.py']
```

`./src/a.py` is at depth 2 and `./src/sub/b.py` at depth 3, so only the first
is returned.

`find()` also accepts a `min_depth` argument, but the current release does not
pass it to the Rust core, so it has no effect.

## Hidden files

Entries whose name starts with a dot are skipped by default, together with
everything below a hidden directory. Pass `hidden=True` to include them.

## Ignore files

By default the walker honours, like `fd` and `ripgrep`:

- `.gitignore` files, the repository's `.git/info/exclude` and your global
  Git ignore file. The `ignore` crate applies Git rules only inside a Git
  repository.
- `.ignore` files.
- A `.fdignore` file in the root directory, if one exists.

Pass `ignore_git=True` to turn off the `.gitignore`, `.ignore`,
`.git/info/exclude` and `.fdignore` handling. The global Git ignore file is
still read.

`custom_ignore_files` adds more ignore files in gitignore syntax. Give one path
or a list. Paths are checked relative to the current working directory, and
files that do not exist are skipped without an error:

```python
vexy_glob.find("*", custom_ignore_files=[".myignore", "config/search.ignore"])
```

## Symbolic links and file systems

- `follow_symlinks=True` makes the walker descend into directories reached
  through symbolic links. The default is `False`.
- `same_file_system=True` stops the walker from crossing into other mounted
  file systems below the root. The default is `False`.

## Sorting

`sort` collects all results and sorts them before returning a list:

| Value | Order |
| --- | --- |
| `"name"` | File name only (the last path component) |
| `"path"` | Full path string |
| `"size"` | File size, smallest first |
| `"mtime"` | Modification time, oldest first |

Any other value raises `VexyGlobError`. `search()` ignores `sort`.

## Threads

`threads` sets the number of walker threads. `None` (the default) or `0` uses
the number of logical CPUs.
