#!/usr/bin/env python3
# this_file: sync_version.py
"""Synchronize version from git tags to Cargo.toml."""

import re
import subprocess
import sys
from pathlib import Path


def get_git_version() -> str:
    """Get version from git tags using hatch-vcs logic."""
    try:
        # Try to get version from git describe
        result = subprocess.run(
            ["git", "describe", "--tags", "--long", "--match", "v*"],
            capture_output=True,
            text=True,
            check=True
        )
        version_str = result.stdout.strip()
        
        # Parse git describe output: v0.1.0-5-g1234567
        match = re.match(r"^v?(\d+\.\d+\.\d+)(?:-(\d+)-g([a-f0-9]+))?", version_str)
        if match:
            base_version = match.group(1)
            distance = match.group(2)
            
            if distance and int(distance) > 0:
                # Development version
                parts = base_version.split(".")
                parts[-1] = str(int(parts[-1]) + 1)
                return ".".join(parts) + f".dev{distance}"
            else:
                # Tagged version
                return base_version
    except subprocess.CalledProcessError:
        pass
    
    # Fallback to default version
    return "0.1.0"


def update_cargo_toml(version: str) -> None:
    """Update version in Cargo.toml."""
    cargo_path = Path("Cargo.toml")
    if not cargo_path.exists():
        print("Error: Cargo.toml not found", file=sys.stderr)
        sys.exit(1)
    
    content = cargo_path.read_text()
    
    # Remove .dev suffix for Cargo (it doesn't support dev versions)
    cargo_version = re.sub(r"\.dev\d+$", "", version)
    
    # Update version line
    new_content = re.sub(
        r'^version = "[^"]*"',
        f'version = "{cargo_version}"',
        content,
        count=1,
        flags=re.MULTILINE
    )
    
    if new_content != content:
        cargo_path.write_text(new_content)
        print(f"Updated Cargo.toml version to {cargo_version}")
    else:
        print(f"Cargo.toml already at version {cargo_version}")


def main():
    """Main entry point."""
    version = get_git_version()
    print(f"Git version: {version}")
    update_cargo_toml(version)


if __name__ == "__main__":
    main()