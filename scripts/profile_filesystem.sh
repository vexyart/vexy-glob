#!/bin/bash
# this_file: scripts/profile_filesystem.sh
# Filesystem-specific performance profiling for vexy_glob

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔍 Filesystem-Specific Performance Profiling"
echo "==========================================="

# Ensure we're in the project root
cd "$PROJECT_ROOT"

# Check current filesystem
CURRENT_FS=$(diskutil info / | grep "File System Personality" | awk '{print $4}')
echo "📁 Current filesystem: $CURRENT_FS"

# Create test directories with different characteristics
echo ""
echo "🏗️  Creating test environments..."

# Clean up any existing test directories
rm -rf target/fs_test_*

# Test 1: Shallow directory with many files (breadth-heavy)
echo "  1. Creating shallow directory (10,000 files in single directory)..."
mkdir -p target/fs_test_shallow
cd target/fs_test_shallow
for i in {1..10000}; do
    touch "file_${i}.txt"
done
cd "$PROJECT_ROOT"

# Test 2: Deep directory hierarchy (depth-heavy)
echo "  2. Creating deep directory (100 levels deep)..."
DEEP_DIR="target/fs_test_deep"
CURRENT_DIR="$DEEP_DIR"
for i in {1..100}; do
    CURRENT_DIR="$CURRENT_DIR/level_${i}"
done
mkdir -p "$CURRENT_DIR"
# Add a file at each level
CURRENT_DIR="$DEEP_DIR"
for i in {1..100}; do
    CURRENT_DIR="$CURRENT_DIR/level_${i}"
    touch "$CURRENT_DIR/file_${i}.txt"
done

# Test 3: Mixed realistic structure (like a typical project)
echo "  3. Creating mixed project structure..."
mkdir -p target/fs_test_mixed/{src/{components,lib,utils},tests,docs,node_modules/{package1,package2,package3}}
# Create files in each directory
find target/fs_test_mixed -type d -exec bash -c 'for i in {1..10}; do touch "$0/file_${i}.js"; done' {} \;

# Test 4: Case-sensitive vs case-insensitive (APFS specific)
if [[ "$CURRENT_FS" == "APFS" ]]; then
    echo "  4. Testing APFS case sensitivity..."
    mkdir -p target/fs_test_case
    cd target/fs_test_case
    touch lowercase.txt LOWERCASE.txt LowerCase.txt
    cd "$PROJECT_ROOT"
fi

# Build release version for profiling
echo ""
echo "🔨 Building release version with debug symbols..."
export CARGO_PROFILE_RELEASE_DEBUG=true
maturin build --release

echo ""
echo "🚀 Running filesystem-specific benchmarks..."

# Function to profile a specific test case
profile_test() {
    local test_name="$1"
    local test_dir="$2"
    local pattern="$3"
    
    echo ""
    echo "📊 Profiling: $test_name"
    echo "  Directory: $test_dir"
    echo "  Pattern: $pattern"
    echo "  ----------------------------------------"
    
    # Run with time measurement
    echo "  Timing measurement:"
    /usr/bin/time -l python -c "
import vexy_glob
import time
start = time.perf_counter()
results = list(vexy_glob.find('$pattern', root='$test_dir'))
end = time.perf_counter()
print(f'    Found {len(results)} files in {end-start:.3f} seconds')
print(f'    Rate: {len(results)/(end-start):.0f} files/second')
" 2>&1 | grep -E "(Found|Rate:|real|maximum resident)"
    
    # Create flamegraph for this specific test
    if command -v cargo-flamegraph &> /dev/null; then
        echo "  Generating flamegraph..."
        cargo flamegraph --bench hot_paths -- --bench "$test_name" -o "target/profiling/flamegraph_${test_name// /_}.svg" 2>/dev/null || true
    fi
}

# Profile each test case
profile_test "Shallow Directory Traversal" "target/fs_test_shallow" "*.txt"
profile_test "Deep Directory Traversal" "target/fs_test_deep" "**/*.txt"
profile_test "Mixed Project Structure" "target/fs_test_mixed" "**/*.js"

if [[ "$CURRENT_FS" == "APFS" ]]; then
    profile_test "APFS Case Sensitivity" "target/fs_test_case" "*case.txt"
fi

# Memory profiling
echo ""
echo "💾 Memory usage analysis..."
echo "  Running with memory profiler..."

python -c "
import vexy_glob
import tracemalloc
import gc

# Test memory usage for large directory
tracemalloc.start()
gc.collect()

snapshot1 = tracemalloc.take_snapshot()

# Iterate through files without collecting
results = 0
for f in vexy_glob.find('**/*.txt', root='target/fs_test_shallow'):
    results += 1

snapshot2 = tracemalloc.take_snapshot()

top_stats = snapshot2.compare_to(snapshot1, 'lineno')

print(f'  Processed {results} files')
print('  Top memory allocations:')
for stat in top_stats[:5]:
    print(f'    {stat}')

current, peak = tracemalloc.get_traced_memory()
print(f'  Current memory: {current / 1024 / 1024:.2f} MB')
print(f'  Peak memory: {peak / 1024 / 1024:.2f} MB')

tracemalloc.stop()
"

# System-specific profiling
echo ""
echo "🖥️  System-specific analysis..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  macOS-specific metrics:"
    # File system cache statistics
    echo "  File system cache:"
    vm_stat | grep -E "(File-backed pages|Pages purgeable)" | sed 's/^/    /'
    
    # Check for APFS optimizations
    if [[ "$CURRENT_FS" == "APFS" ]]; then
        echo "  APFS features in use:"
        diskutil apfs list | grep -E "(FileVault|Snapshot|Clone)" | head -5 | sed 's/^/    /'
    fi
fi

echo ""
echo "✅ Filesystem profiling complete!"
echo ""
echo "📈 Summary:"
echo "  - Test directories created in target/fs_test_*"
echo "  - Flamegraphs saved to target/profiling/ (if available)"
echo "  - Results show filesystem-specific performance characteristics"
echo ""
echo "🔍 Next steps:"
echo "  1. Compare results with different filesystem types"
echo "  2. Identify filesystem-specific bottlenecks"
echo "  3. Optimize for common filesystem patterns"