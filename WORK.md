---
this_file: WORK.md
---

# WORK.md - Current Work Progress

The site uses fly-january 0.2.1 with `chrome: none`. The release workflow builds wheels and an sdist from version tags and uses PyPI Trusted Publishing.

## Latest verification

- `./build.sh docs` built 13 pages in strict mode without warnings. Static checks matched the Fly assets to the installed theme.
- `./build.sh package` built an sdist and macOS arm64 wheel. Both passed Twine checks. A clean Python 3.13 environment installed the wheel and passed an import and CLI smoke check.
- Rust passed all 10 tests. Pytest passed 152 of 156. The same four CLI failures reproduced in the previous run.

Native platform checks and release verification remain in `PLAN.md`. The next macOS run needs to exercise the APFS checks bypassed in the saved run.
