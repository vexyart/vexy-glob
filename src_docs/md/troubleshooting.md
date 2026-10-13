# Troubleshooting

## A call with `as_list=True` never returns

**Symptom.** With vexy-glob 1.0.9 or earlier, `find(..., as_list=True)`,
`find(..., sort=...)`, `glob()` or `search(..., as_list=True)` hangs on a large
tree, while the same call without `as_list` finishes quickly.

**Cause.** In those releases the list path waited for the walker to finish
before it read results from the internal channel. When the number of results
exceeded the channel capacity, the walker blocked and the call waited forever.
The capacity is 1,000 results by default, 500 matching lines for content
search, 10,000 with `sort`, and 1,000 × `threads` (at most 8,000) when you pass
`threads`. See [Architecture](architecture.md#streaming-results-to-python).

**Fix.** Upgrade to vexy-glob 1.0.11 or later, where the list path drains the
channel while the walker runs:

```bash
uv pip install --upgrade vexy-glob
```

**Workaround for older releases.** Use the iterator and build the list in Python:

```python
paths = list(vexy_glob.find("**/*.txt"))           # instead of as_list=True
paths = sorted(vexy_glob.find("**/*.txt"))         # instead of sort="path"
hits = list(vexy_glob.search("TODO", "*.py"))      # instead of as_list=True
paths = list(vexy_glob.iglob("*.py"))              # instead of glob()
```

## `ImportError: vexy_glob extension module not built`

The Python files were imported without the compiled module
`vexy_glob/_vexy_glob.*`. This happens when you run Python from the root of a
source checkout, where the local `vexy_glob/` directory shadows the installed
package.

- In a source checkout, build the extension: `maturin develop`.
- Otherwise, run your script from another directory, or install the package
  (`uv pip install vexy-glob`).

## No results, or fewer than expected

Work through these causes in order:

1. **The pattern contains `/`.** Such patterns must match the whole path,
   which starts with the root (`./` by default). `src/*.py` matches nothing;
   use `**/src/*.py`, `./src/*.py` or `find("*.py", root="src")`. See
   [Patterns and case](patterns.md#patterns-with-are-matched-against-the-full-path).
2. **Case.** A pattern with an uppercase letter is case-sensitive:
   `Readme.md` does not match `README.md`. Pass `case_sensitive=False`.
3. **Hidden files.** Names starting with a dot, and everything inside hidden
   directories, are skipped. Pass `hidden=True`.
4. **Ignore files.** `.gitignore`, `.ignore`, `.git/info/exclude`, the global
   Git ignore file and a root `.fdignore` can hide entries. Pass
   `ignore_git=True` to switch off all but the global Git ignore file.
5. **Extension written with a dot.** `extension=".py"` matches nothing; use
   `extension="py"`.
6. **Depth.** With `max_depth`, the root is level 0. A file in `./src/` is at
   level 2.
7. **Wrong root.** A root that does not exist gives an empty result and, in
   iterator mode, a line on standard error:
   `Error during traversal: nope: No such file or directory (os error 2)`.

## More results than expected

- A pattern without `/` matches at every depth: `*.py` is treated as
  `**/*.py`. Use `max_depth` to stay near the root.
- `*` also matches `/`, so `./src/*.py` includes files in `./src/sub/`.
- `vexy_glob.glob("*.py")` searches subdirectories too, unlike
  `glob.glob("*.py")`.
- Without `file_type`, directories and links are returned along with files.
  `find("*")` also returns the root itself (`.`).

## `PatternError` or `VexyGlobError` on a regex

- `PatternError: Invalid glob pattern: ...` means the glob (or an `exclude`
  entry) has a syntax error, often an unclosed `[` or `{`.
- `VexyGlobError: Invalid content regex: ...` means the content regex does not
  compile. The Rust `regex` engine has no look-around and no backreferences;
  rewrite the pattern without them, or filter `line_text` in Python with `re`.

## `ValueError: Invalid time format`

A time argument is a string the parser does not recognise. Accepted strings
are ISO dates (`2025-01-01`), ISO date-times (`2025-01-01T12:00:00`, optional
`Z`) and relative values `-<number><unit>` with unit `s`, `m`, `h` or `d`.
Weeks (`-1w`) are not supported; write `-7d`.

## `vg`: `Error: 'int' object has no attribute 'strip'`

`--min-size` or `--max-size` received a bare number. Add a unit:
`--min-size 500b`, `--min-size 10k`. See [Command line](cli.md#size-strings).

## `vg -h` does not show help

`-h` is the short form of `--hidden`. Use `vg --help`, `vg find --help` or
`vg search --help`.

## `matches` contains the whole line

In the current release, the `matches` list of a search result holds the
trimmed line, not the individual regex matches. Run Python's `re.finditer()`
on `line_text` to get the matched substrings. See
[Content search](content-search.md#the-result-dictionary).

## Messages on standard error during iteration

Lines such as `Error during traversal: ...: Permission denied` come from the
walker. The walk continues past the entry that failed. To skip a directory
you cannot read, add it to an ignore file or to `exclude`.

## Installing fails with a Rust or `cargo` error

`pip` found no wheel for your platform and is building from source. Install a
Rust toolchain from <https://rustup.rs/> and run the install again. See
[Installation](installation.md#wheels-and-source-builds).
