# Quickstart

This page walks through one small project so you can see what each call
returns. You need `vexy-glob` installed (see [Installation](installation.md)).

## Set up a sample tree

1. Create a scratch directory with a few files:

    ```bash
    mkdir -p play/src/sub play/.hid
    cd play
    echo "import os" > src/a.py
    echo "TODO x" > src/sub/b.py
    echo "hello" > README.md
    echo "x" > .hid/c.py
    ```

2. Start Python in `play/`:

    ```bash
    python
    ```

## Find files

1. Import the package and list the Python files:

    ```python
    >>> import vexy_glob
    >>> sorted(vexy_glob.find("*.py", as_list=True))
    ['./src/a.py', './src/sub/b.py']
    ```

    Three things happened:

    - `*.py` has no `/`, so the pattern matched file names at any depth.
    - Paths start with `./` because the default `root` is `"."`.
    - `.hid/c.py` is missing, because hidden files and directories are skipped
      by default.

2. Include hidden entries:

    ```python
    >>> sorted(vexy_glob.find("*.py", hidden=True, as_list=True))
    ['./.hid/c.py', './src/a.py', './src/sub/b.py']
    ```

3. Search below a different root. The paths now start with that root:

    ```python
    >>> sorted(vexy_glob.find("*.py", root="src", as_list=True))
    ['src/a.py', 'src/sub/b.py']
    ```

4. Stream instead of collecting. Without `as_list=True`, `find()` returns an
   iterator that yields each path as the walker finds it:

    ```python
    >>> it = vexy_glob.find("*.py")
    >>> for path in it:
    ...     print(path)
    ./src/sub/b.py
    ./src/a.py
    ```

    The order depends on thread scheduling. Use `sort="path"` (which also
    collects the results into a list) when the order matters.

5. Get `pathlib.Path` objects:

    ```python
    >>> vexy_glob.find("README.md", as_path=True, as_list=True)
    [PosixPath('README.md')]
    ```

    On Windows the objects are `WindowsPath`.

## Filter

1. Directories only:

    ```python
    >>> vexy_glob.find("*", file_type="d", sort="path")
    ['.', './src', './src/sub']
    ```

    The root directory itself is part of the walk, so `"."` appears.

2. Files by extension, sorted by file name:

    ```python
    >>> vexy_glob.find("*", extension=["py", "md"], file_type="f", sort="name")
    ['./README.md', './src/a.py', './src/sub/b.py']
    ```

3. Files changed in the last day:

    ```python
    >>> sorted(vexy_glob.find("*.py", mtime_after="-1d", as_list=True))
    ['./src/a.py', './src/sub/b.py']
    ```

## Search contents

1. Search for a regular expression in Python files:

    ```python
    >>> vexy_glob.search("TODO", "*.py", as_list=True)
    [{'path': './src/sub/b.py', 'line_number': 1, 'line_text': 'TODO x\n', 'matches': ['TODO x']}]
    ```

    Each result is a dictionary. `line_text` keeps the line ending.

2. Search with a lowercase pattern. Smart case makes it case-insensitive, so it
   still finds `TODO`:

    ```python
    >>> [r["path"] for r in vexy_glob.search("todo", "*.py")]
    ['./src/sub/b.py']
    ```

## Use the command line

The same searches from a shell:

```bash
vg find "*.py"
vg search "*.py" "TODO" --no-color
```

```text
./src/sub/b.py
./src/a.py
./src/sub/b.py:1:TODO x
```

## Next steps

- [Patterns and case](patterns.md) explains how patterns meet paths.
- [Filters](filters.md) lists every filter and its accepted values.
- [Python API](api.md) is the full reference.
