#!/usr/bin/env python
# this_file: examples/vexy_globbench.py

import time
import fire
import glob
import pathlib
import os
import sys

# Add project root to path to allow importing vexy_glob
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

try:
    import vexy_glob
except ImportError:
    print("Error: 'vexy_glob' library not found.", file=sys.stderr)
    print(
        "Please ensure it is installed, e.g., by running 'maturin develop' in the project root.",
        file=sys.stderr,
    )
    sys.exit(1)


class VexyGlobBench:
    """
    A Fire CLI tool to benchmark file searching methods.
    """

    def _run_benchmark(self, name, func, print_paths=False):
        print(f"--- Benchmarking {name} ---")
        start_time = time.perf_counter()
        results = list(func())
        end_time = time.perf_counter()
        print(f"Found {len(results)} files in {end_time - start_time:.6f} seconds.")
        if print_paths:
            for path in results:
                print(path)
        print("-" * (len(name) + 22))
        return results

    def run(self, dir: str = ".", ext: str = "md", print_paths: bool = False):
        """
        Recursively finds all files with a given extension in a directory and benchmarks the time.

        :param dir: The directory to search in (default: current directory).
        :param ext: The file extension to search for (default: 'md').
        :param print_paths: Whether to print the found paths (default: False).
        """
        abs_dir = os.path.abspath(dir)
        print(f"Searching for *.{ext} files in '{abs_dir}'\n")

        # --- vexy_glob ---
        def vexy_glob_search():
            return vexy_glob.find(f"**/*.{ext}", root=dir)

        self._run_benchmark("vexy_glob", vexy_glob_search, print_paths)

        # --- glob ---
        def glob_search():
            return glob.glob(os.path.join(abs_dir, f"**/*.{ext}"), recursive=True)

        self._run_benchmark("glob", glob_search, print_paths)

        # --- pathlib ---
        def pathlib_search():
            p = pathlib.Path(dir)
            return p.rglob(f"*.{ext}")

        self._run_benchmark("pathlib", pathlib_search, print_paths)


if __name__ == "__main__":
    bench = VexyGlobBench()
    fire.Fire(bench.run)
