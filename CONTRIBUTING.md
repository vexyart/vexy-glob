# Contributing to vexy_glob

Thank you for your interest in contributing to vexy_glob! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

1. **Python 3.8+**: Install via your package manager or from python.org
2. **Rust**: Install from https://rustup.rs/
3. **uv**: Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Setting Up the Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/vexy_glob.git
cd vexy_glob

# Create virtual environment and install dependencies
uv venv --python 3.12
uv sync

# Build the Rust extension in development mode
maturin develop

# Run tests to verify setup
python -m pytest tests/ -v
```

## Development Workflow

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_basic.py -v

# Run with coverage
python -m pytest tests/ --cov=vexy_glob --cov-report=html

# Run Rust tests
cargo test

# Run benchmarks
python -m pytest tests/test_benchmarks.py -v --benchmark-only
```

### Code Quality

Before submitting a PR, ensure your code passes all quality checks:

```bash
# Python formatting and linting
fd -e py -x uvx autoflake -i {}
fd -e py -x uvx pyupgrade --py312-plus {}
fd -e py -x uvx ruff check --output-format=github --fix --unsafe-fixes {}
fd -e py -x uvx ruff format --respect-gitignore --target-version py312 {}

# Rust formatting and linting
cargo fmt
cargo clippy -- -D warnings
```

### Building Wheels

```bash
# Build wheel for current platform
maturin build --release

# Build universal wheel (requires multiple Python versions)
maturin build --release --universal2
```

## Making Changes

### Code Style

- **Python**: Follow PEP 8, use type hints, write clear docstrings
- **Rust**: Follow standard Rust conventions, use `cargo fmt`
- **Comments**: Explain WHY, not just WHAT
- **File paths**: Include `# this_file: path/to/file` comment in all source files

### Commit Messages

Follow conventional commit format:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions/changes
- `chore:` Maintenance tasks
- `perf:` Performance improvements

Example: `feat: add content search functionality with regex support`

### Pull Request Process

1. Fork the repository and create a feature branch
2. Make your changes following the guidelines above
3. Add tests for new functionality
4. Update documentation as needed
5. Ensure all tests pass locally
6. Submit a PR with a clear description

### Testing Guidelines

- Write tests for all new functionality
- Include edge cases and error conditions
- Use descriptive test names
- Keep tests focused and independent
- Add benchmarks for performance-critical code

## Architecture Overview

### Rust Side (`src/`)
- `lib.rs`: Main PyO3 module and Python bindings
- Core functionality using `ignore` and `globset` crates
- Content search using `grep-searcher` and `grep-regex`
- Producer-consumer pattern with crossbeam channels

### Python Side (`vexy_glob/`)
- `__init__.py`: Public API and convenience functions
- Exception hierarchy for error handling
- Type hints and comprehensive docstrings

## Performance Considerations

When contributing performance improvements:
1. Always benchmark before and after changes
2. Use the existing benchmark suite as a baseline
3. Consider memory usage, not just speed
4. Document performance characteristics

## Getting Help

- Open an issue for bugs or feature requests
- Start a discussion for design decisions
- Check existing issues before creating new ones

## License

By contributing to vexy_glob, you agree that your contributions will be licensed under the MIT License.