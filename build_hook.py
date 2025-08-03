#!/usr/bin/env python3
# this_file: build_hook.py
"""Custom build hook for hatch to integrate with maturin."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Build hook to compile Rust extension with maturin."""

    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        """Initialize the build hook and run maturin build."""
        if self.target_name not in ["wheel", "sdist"]:
            return

        # Get the root directory
        root = Path(self.root)
        
        # Sync version to Cargo.toml
        sync_script = root / "sync_version.py"
        if sync_script.exists():
            subprocess.run([sys.executable, str(sync_script)], cwd=root)
        
        # Run maturin build
        env = os.environ.copy()
        
        # For wheel builds, use maturin build
        if self.target_name == "wheel":
            # For editable builds, use maturin develop
            if "editable" in getattr(self, "versions", []):
                cmd = [
                    sys.executable, "-m", "maturin", "develop",
                    "--release",
                ]
            else:
                cmd = [
                    sys.executable, "-m", "maturin", "build",
                    "--release",
                    "--out", str(self.directory),
                    "--interpreter", sys.executable,
                ]
            
            # Add platform-specific options
            if sys.platform == "darwin":
                # Build universal2 wheels on macOS if requested
                if os.environ.get("CIBW_ARCHS_MACOS") == "universal2":
                    cmd.extend(["--target", "universal2-apple-darwin"])
            
            try:
                subprocess.run(cmd, check=True, cwd=root, env=env)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"maturin build failed: {e}")
        
        # For sdist, ensure Cargo.toml is included
        elif self.target_name == "sdist":
            # Add Rust source files to the distribution
            rust_files = [
                "Cargo.toml",
                "Cargo.lock",
                "src/**/*.rs",
                "build.rs" if (root / "build.rs").exists() else None,
            ]
            
            for pattern in filter(None, rust_files):
                if "*" in pattern:
                    # Handle glob patterns
                    base_dir = root / Path(pattern).parts[0]
                    if base_dir.exists():
                        for file in base_dir.rglob(Path(pattern).name):
                            rel_path = file.relative_to(root)
                            build_data["force_include"][str(rel_path)] = str(rel_path)
                else:
                    # Handle specific files
                    file_path = root / pattern
                    if file_path.exists():
                        build_data["force_include"][pattern] = pattern


