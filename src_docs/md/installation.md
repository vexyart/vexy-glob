# Installation

`vexy-glob` needs Python 3.8 or newer. The compiled part is a single extension
module, `vexy_glob._vexy_glob`, built against the stable Python ABI (`abi3`), so
one wheel per platform covers every supported Python version.

## Install from PyPI

1. Install the package with `uv`:

    ```bash
    uv pip install vexy-glob
    ```

    Or with `pip`:

    ```bash
    python -m pip install vexy-glob
    ```

2. Check that the extension loads:

    ```bash
    python -c "import vexy_glob; print(vexy_glob.__version__)"
    ```

    The command prints the installed version.

3. Check that the `vg` command is on your `PATH`:

    ```bash
    vg find "*.py" --depth 1
    ```

    The command lists Python files in the current directory.

The package depends on `fire` and `rich`, which the CLI uses. `pip` and `uv`
install them automatically.

## Wheels and source builds

The release workflow builds wheels for these platforms:

| Platform | Architectures |
| --- | --- |
| Linux (manylinux) | `x86_64`, `aarch64` |
| macOS | `x86_64`, `arm64` |
| Windows | `x64` |

If PyPI has no wheel for your platform, `pip` downloads the source
distribution and compiles it. That needs a Rust toolchain:

1. Install Rust from <https://rustup.rs/>.
2. Run the install command again. `pip` calls `maturin`, which runs
   `cargo build --release` and packages the result. The first build downloads
   and compiles the Rust dependencies, which takes a few minutes.

## Install from a Git checkout

Prerequisites: Python 3.8 or newer, a Rust toolchain and `uv`.

1. Clone the repository:

    ```bash
    git clone https://github.com/vexyart/vexy-glob.git
    cd vexy-glob
    ```

2. Create a virtual environment:

    ```bash
    uv venv --python 3.12
    source .venv/bin/activate
    ```

3. Build the extension and install it into the environment in editable mode:

    ```bash
    uv pip install maturin
    maturin develop --release
    ```

    `maturin develop` compiles `src/*.rs`, places the extension next to
    `vexy_glob/__init__.py` and installs the package. Leave out `--release` for
    a faster, unoptimised debug build.

4. Run the tests to confirm the build:

    ```bash
    uv pip install pytest
    python -m pytest tests/ -q
    ```

## Build a wheel yourself

`./build.sh package` builds the source distribution and one wheel for the
current machine into `dist/`, then runs `twine check` on both:

```bash
./build.sh package
ls dist/
```

```text
vexy_glob-1.0.9-cp38-abi3-macosx_11_0_arm64.whl
vexy_glob-1.0.9.tar.gz
```

The version in the file names comes from the `version` field in `Cargo.toml`.

## Uninstall

```bash
uv pip uninstall vexy-glob
```
