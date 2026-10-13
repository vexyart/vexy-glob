# Content search

Content search reads the files that pass the path filters and reports every
line that matches a regular expression. It uses the `grep-searcher` and
`grep-regex` crates from `ripgrep`.

## Two ways to call it

`search()` takes the regex first:

```python
vexy_glob.search(content_regex, pattern="*", root=".", **kwargs)
```

`find()` with `content=` does the same thing:

```python
vexy_glob.find(pattern, root=".", content=content_regex, ...)
```

`search()` removes a `sort` argument if you pass one and then calls `find()`.
All other keyword arguments (filters, `hidden`, `as_list` and so on) work the
same way as for `find()`.

## What happens to one file

Take `src/sub/b.py` containing the single line `TODO x`, and the call
`search("TODO", "*.py", root="src")`:

1. The walker reaches `src/sub/b.py`.
2. The path filters run: `*.py` matches, there are no other filters.
3. The entry is a regular file, so the searcher opens it. (Directories and
   links never reach the searcher.)
4. The searcher runs the regex over the file line by line and records one
   result for each matching line.
5. When the file is done, its results are sent to Python in order.

The result is:

```python
{'path': 'src/sub/b.py', 'line_number': 1, 'line_text': 'TODO x\n', 'matches': ['TODO x']}
```

Results from one file arrive in line order. Results from different files can
interleave, because files are searched on several threads.

## The result dictionary

| Key | Type | Content |
| --- | --- | --- |
| `path` | `str`, or `pathlib.Path` with `as_path=True` | Path of the file, starting with `root` |
| `line_number` | `int` | 1-based line number |
| `line_text` | `str` | The whole line, including its line ending |
| `matches` | `list[str]` | In the current release, one item: the line with surrounding whitespace removed |

`matches` does not yet contain the individual regex matches. To find the
matched substrings, run Python's `re` on `line_text`:

```python
import re

rx = re.compile(r"TODO\s*(\w+)")
for hit in vexy_glob.search(r"TODO", "*.py"):
    for m in rx.finditer(hit["line_text"]):
        print(hit["path"], hit["line_number"], m.group(1))
```

A line that matches several times still produces one result.

Lines that are not valid UTF-8 are decoded with replacement characters
(`U+FFFD`).

## Regex syntax

The regex is compiled by the Rust `regex` engine through `grep-regex`. Its
syntax is close to Python's `re`, with these differences that matter in
practice:

- No look-around (`(?=...)`, `(?!...)`, `(?<=...)`, `(?<!...)`) and no
  backreferences. Patterns that use them raise an error.
- Matching is line-oriented: each line is searched on its own, so a regex
  cannot match across a line break.
- `\b`, `\d`, `\w`, `\s`, character classes, alternation and repetition work as
  expected. Write patterns as raw strings in Python (`r"fn\s+\w+"`).

Case follows smart case (see [Patterns and case](patterns.md#letter-case)): a
regex without uppercase letters is case-insensitive. `case_sensitive=True` or
`False` overrides it for both the glob and the regex.

An invalid regex raises `VexyGlobError`:

```python
>>> vexy_glob.search("(", "*.py", as_list=True)
Traceback (most recent call last):
  ...
vexy_glob.VexyGlobError: Invalid content regex: regex parse error:
    (?:()
    ^
error: unclosed group
```

## Streaming versus lists

Like `find()`, `search()` returns an iterator unless you pass `as_list=True`.
The iterator lets you stop early:

```python
first = next(iter(vexy_glob.search("def main", "*.py")), None)
```

## Narrowing the search

Path filters run before any file is opened, so they reduce the amount of data
read from disk. Useful combinations:

```python
# Only Python sources, skip tests, skip files over 1 MiB
vexy_glob.search(
    r"import\s+asyncio",
    "*.py",
    root="src",
    exclude="*test*",
    max_size=1024 * 1024,
)

# Only recently changed Markdown files
vexy_glob.search("FIXME", "*.md", mtime_after="-7d")
```

## Errors while searching

If a file cannot be opened or read, the error is reported and the search goes
on:

- With an iterator, the message is printed to standard error, prefixed with
  `Error during traversal:`, and iteration continues with the next result.
- With `as_list=True`, such errors are dropped silently.
