# Patterns and case

The `pattern` argument of `find()`, `glob()`, `iglob()` and `search()` is a glob
pattern compiled by the Rust `globset` crate. This page explains which part of
each path the pattern is compared with, and how letter case is handled.

## What the pattern is compared with

The walker produces paths that start with the `root` you passed: `./src/a.py`
for the default root `"."`, `src/a.py` for `root="src"`, `/home/me/a.py` for
an absolute root. The pattern is tested against that whole string, but the
tool first rewrites patterns that contain no path separator.

### Patterns without `/` match at any depth

If the pattern contains neither `/` nor `\`, the tool puts `**/` in front of
it. So `*.py` becomes `**/*.py`, which matches a `.py` file in any directory
below the root.

| Pattern you pass | Pattern that is matched | Matches `./src/sub/b.py`? |
| --- | --- | --- |
| `*.py` | `**/*.py` | yes |
| `b.py` | literal file-name comparison | yes |
| `src/*.py` | `src/*.py` | no |
| `**/src/*.py` | `**/src/*.py` | yes |
| `./src/*.py` | `./src/*.py` | yes |

This is the main difference from Python's `glob.glob()`, where `*.py` only
looks in one directory. To limit the depth, use `max_depth` (see
[Filters](filters.md#depth)).

### Patterns with `/` are matched against the full path

A pattern with a separator is used as is, so it has to describe the path from
its first character. With the default root, paths start with `./`:

```python
>>> vexy_glob.find("src/*.py", as_list=True)
[]
>>> sorted(vexy_glob.find("./src/*.py", as_list=True))
['./src/a.py', './src/sub/b.py']
```

Two ways to avoid the `./` prefix problem:

- Start the pattern with `**/`, for example `**/src/*.py`.
- Pass the directory as `root` and keep the pattern short:
  `find("*.py", root="src")`.

### `*` also matches `/`

`globset` is used without its "literal separator" option, so `*` can match
across directory separators. In the example above, `./src/*.py` matched
`./src/sub/b.py`. Use `max_depth` or an `exclude` pattern when you need to stop
at one level.

## Pattern syntax

| Syntax | Meaning | Example |
| --- | --- | --- |
| `*` | Any run of characters, including `/` | `*.md` |
| `?` | Any single character | `file?.txt` |
| `**` | Any number of directories | `**/tests/*.py` |
| `[abc]`, `[a-z]` | One character from a set or range | `img[0-9].png` |
| `[!abc]` | One character not in the set | `[!_]*.py` |
| `{a,b}` | Either alternative | `*.{py,pyi}` |

A pattern without any of `* ? [ ] { }` is a literal. Literals take a faster
path:

- A literal without `/` is compared with the file name only: `README.md`
  matches `./README.md` and `./docs/README.md`.
- A literal with `/` matches any path that ends with it: `sub/b.py` matches
  `./src/sub/b.py`.

## Letter case

### Smart case (the default)

`case_sensitive` defaults to `None`, which selects smart case:

- The glob pattern is case-sensitive if it contains an uppercase letter, and
  case-insensitive otherwise.
- The content regex (for `search()` or `content=`) follows the same rule on its
  own: a regex with an uppercase letter is case-sensitive.

```python
>>> vexy_glob.find("readme.md", as_list=True)   # no uppercase: insensitive
['./README.md']
>>> vexy_glob.find("Readme.md", as_list=True)   # uppercase: sensitive
[]
```

### Forcing a mode

Pass `case_sensitive=True` or `case_sensitive=False`. The value then applies
to both the glob pattern and the content regex:

```python
>>> sorted(vexy_glob.find("*.PY", case_sensitive=False, as_list=True))
['./src/a.py', './src/sub/b.py']
```

`exclude` patterns use the same case mode as the main pattern.

## Invalid patterns

A pattern that `globset` cannot parse raises `PatternError`:

```python
>>> vexy_glob.find("[", as_list=True)
Traceback (most recent call last):
  ...
vexy_glob.PatternError: Invalid glob pattern: error parsing glob '**/[': unclosed character class; missing ']': '['
```

The message shows the rewritten pattern (`**/[`), which tells you that the
`**/` prefix was added.
