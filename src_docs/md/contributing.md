# Contributing

The source lives at <https://github.com/vexyart/vexy-glob>. Bug reports and
pull requests go to the GitHub issue tracker and pull request queue.

## Prerequisites

- Python 3.8 or newer (3.12 is used in the examples)
- A Rust toolchain from <https://rustup.rs/>, with `rustfmt` and `clippy`
- [`uv`](https://docs.astral.sh/uv/)

## Set up a development build

1. Clone the repository and enter it:

    ```bash
    git clone https://github.com/vexyart/vexy-glob.git
    cd vexy-glob
    ```

2. Create and activate a virtual environment:

    ```bash
    uv venv --python 3.12
    source .venv/bin/activate
    ```

3. Install the build and test tools:

    ```bash
    uv pip install maturin pytest pytest-benchmark fire rich
    ```

4. Compile the extension into the environment:

    ```bash
    maturin develop
    ```

    Repeat this step after every change to a `.rs` file. Python-only changes in
    `vexy_glob/` take effect without rebuilding.

## Run the tests

| Command | What it runs |
| --- | --- |
| `python -m pytest tests/ -v` | Python test suite (`tests/test_*.py`) |
| `cargo test` | Rust unit tests in `src/` |
| `cargo bench` | Criterion benchmarks in `benches/` |

The `tests/platform_tests/` directory holds platform-specific checks with
their own runner, `tests/platform_tests/run_platform_tests.py`.

## Code style

Python:

```bash
uvx ruff check vexy_glob/ tests/
uvx ruff format vexy_glob/ tests/
```

`pyproject.toml` sets `target-version = "py38"` and a line length of 100.
Keep the code importable on Python 3.8.

Rust:

```bash
cargo fmt
cargo clippy -- -D warnings
```

The CI workflow runs `cargo fmt -- --check` and `cargo clippy -- -D warnings`.

## Build the documentation

The documentation sources are the Markdown files in `src_docs/md/`, and the
configuration is `src_docs/mkdocs.yml`. The site is built with ProperDocs and
the MaterialX theme into `docs/`, which GitHub Pages serves at
<https://vexy.dev/vexy-glob/>.

1. Preview with live reload:

    ```bash
    src_docs/build.sh serve
    ```

    Open <http://127.0.0.1:8000>.

2. Build the site in strict mode:

    ```bash
    src_docs/build.sh
    ```

    Any warning, such as a broken link between pages, stops the build.

You do not need to commit `docs/` by hand. The `Docs` workflow
(`.github/workflows/docs.yml`) rebuilds it on every push to `main` that
changes `src_docs/`, and commits the result.

## Build the package

```bash
./build.sh package
```

This deletes `dist/`, runs `uv build` (source distribution plus one wheel for
the current machine, built by maturin from the source distribution) and runs
`twine check` on the results. `./build.sh` with no argument builds the
documentation as well; `./build.sh docs` builds only the documentation.

## Releasing

### Why the version needs care

maturin writes the `version` from `Cargo.toml` into every wheel and the source
distribution. It does not read git tags. A tag `v1.2.3` on a commit whose
`Cargo.toml` says `1.2.2` would publish files labelled `1.2.2`. Also, a local
build produces a wheel for one platform only, so the published wheels must come
from CI.

### The release procedure

Prerequisites: push access to `vexyart/vexy-glob`, `uv` on your `PATH`, and a
working tree whose uncommitted changes you are ready to release, because the
script commits all of them.

1. Add a section for the new version to `CHANGELOG.md`, headed
   `## [X.Y.Z]`. The GitHub release takes its notes from that section.

2. Run the release script from the repository root:

    ```bash
    ./publish.sh
    ```

    The script:

    1. fetches tags from `origin` and stops if your branch is behind its
       upstream;
    2. finds the highest `vX.Y.Z` tag and adds 1 to the patch number, the same
       rule `gitnextver` uses (`v1.0.10` becomes `v1.0.11`);
    3. stops if that tag already exists;
    4. writes the new version into `Cargo.toml`;
    5. runs `./build.sh package` as a check that the package still builds;
    6. runs `uvx gitnextver`, which commits all pending changes with the tag
       name as the message, creates the tag and pushes the branch and the tags;
    7. checks that `HEAD` carries the tag it computed in step 2.

    Nothing is uploaded from your machine.

3. Watch the `Release` workflow in the repository's **Actions** tab. On the
   tag push it:

    1. fails early if the tag does not equal the `Cargo.toml` version;
    2. builds wheels for Linux (`x86_64`, `aarch64`), macOS (`x86_64`,
       `arm64`) and Windows (`x64`), and the source distribution, with
       `PyO3/maturin-action`;
    3. uploads all files to PyPI with `uv publish`, skipping files that are
       already there;
    4. creates the GitHub release.

4. Check the result on <https://pypi.org/project/vexy-glob/>.

The upload step needs PyPI credentials in the repository: either a
`PYPI_API_TOKEN` secret, or a PyPI trusted publisher configured for the
`vexyart/vexy-glob` repository and the `release.yml` workflow.

### If something goes wrong

- **The script stops before `gitnextver`.** Nothing was committed or pushed.
  `Cargo.toml` may already hold the new version; keep it or restore it with
  `git checkout Cargo.toml`.
- **The tag check in the workflow fails.** The tag and `Cargo.toml` disagree.
  Nothing was uploaded. Delete the tag locally and on GitHub, fix
  `Cargo.toml`, and release again.
- **A wheel job fails.** Nothing was uploaded, because the upload job waits for
  all build jobs. Fix the problem and re-run the failed jobs, or release a new
  patch version.
