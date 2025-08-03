#!/bin/bash
# this_file: build.sh
# Build script for vexy_glob

set -e

echo "🔧 Syncing version..."
python sync_version.py

echo "📦 Building wheel..."
python -m maturin build --release -o dist/

echo "📦 Building source distribution..."
python -m maturin sdist -o dist/

echo "✅ Build complete!"
ls -la dist/