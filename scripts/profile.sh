#!/bin/bash
# this_file: scripts/profile.sh
# Performance profiling script for vexy_glob hot path analysis

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🔥 Starting performance profiling analysis..."

# Ensure we're in the project root
cd "$PROJECT_ROOT"

# Clean up any existing trace files
rm -f cargo-flamegraph.trace*

# Create profiling output directory
mkdir -p target/profiling

# Set up debug symbols for profiling
export CARGO_PROFILE_BENCH_DEBUG=true

echo "🔧 Configuration:"
echo "  - Debug symbols enabled for profiling"
echo "  - Trace files cleaned"

# Function to run flamegraph on specific benchmark
profile_benchmark() {
    local bench_name="$1"
    local output_name="$2"
    
    echo "📊 Profiling: $bench_name -> $output_name"
    
    # Run flamegraph with perf sampling
    cargo flamegraph \
        --bench "$bench_name" \
        --output "target/profiling/${output_name}.svg" \
        --freq 997 \
        --min-width 0.01 \
        -- --bench
}

# Profile the main hot_paths benchmark
echo "🚀 Profiling hot_paths benchmark..."
profile_benchmark "hot_paths" "hot_paths_full"

# Profile individual benchmark groups by creating focused runs
echo "🎯 Creating focused profiling runs..."

# Create temporary benchmark files for focused profiling
cat > "benches/profile_traversal.rs" << 'EOF'
// Temporary focused benchmark for profiling directory traversal
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use std::fs::{File, create_dir_all};
use std::io::Write;
use tempfile::TempDir;
use ignore::WalkBuilder;

fn create_test_environment() -> TempDir {
    let tmp_dir = TempDir::new().expect("Failed to create temp directory");
    let base_path = tmp_dir.path();
    
    // Create a realistic directory structure for profiling
    for project_i in 0..20 {
        let project_dir = base_path.join(format!("project_{}", project_i));
        create_dir_all(&project_dir).unwrap();
        
        let src_dir = project_dir.join("src");
        create_dir_all(&src_dir).unwrap();
        for i in 0..100 {
            let mut file = File::create(src_dir.join(format!("module_{}.py", i))).unwrap();
            writeln!(file, "def function_{}(): pass", i).unwrap();
        }
    }
    
    tmp_dir
}

fn bench_focused_traversal(c: &mut Criterion) {
    let tmp_dir = create_test_environment();
    let root_path = tmp_dir.path();
    
    c.bench_function("focused_traversal", |b| {
        b.iter(|| {
            let walker = WalkBuilder::new(root_path).build();
            let mut count = 0;
            for entry in walker {
                if let Ok(_entry) = entry {
                    count += 1;
                }
            }
            black_box(count)
        })
    });
}

criterion_group!(focused_benches, bench_focused_traversal);
criterion_main!(focused_benches);
EOF

echo "🔍 Profiling focused directory traversal..."
profile_benchmark "profile_traversal" "traversal_focused"

# Profile pattern matching focused
cat > "benches/profile_patterns.rs" << 'EOF'
// Temporary focused benchmark for profiling pattern matching
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use globset::GlobSetBuilder;
use std::path::PathBuf;

fn bench_focused_patterns(c: &mut Criterion) {
    // Create sample paths for testing
    let sample_paths: Vec<PathBuf> = (0..1000)
        .map(|i| PathBuf::from(format!("project_{}/src/module_{}.py", i % 10, i)))
        .collect();
    
    c.bench_function("focused_glob_matching", |b| {
        let mut builder = GlobSetBuilder::new();
        builder.add(globset::Glob::new("*.py").unwrap());
        let glob_set = builder.build().unwrap();
        
        b.iter(|| {
            let mut matches = 0;
            for path in &sample_paths {
                if glob_set.is_match(path) {
                    matches += 1;
                }
            }
            black_box(matches)
        })
    });
}

criterion_group!(focused_benches, bench_focused_patterns);
criterion_main!(focused_benches);
EOF

echo "🎯 Profiling focused pattern matching..."
profile_benchmark "profile_patterns" "patterns_focused"

# Clean up temporary benchmark files
rm -f benches/profile_traversal.rs benches/profile_patterns.rs

echo "📈 Performance profiling complete!"
echo "📁 Results saved to target/profiling/"
echo "🌐 Open SVG files in browser to view flamegraphs:"
ls -la target/profiling/*.svg

echo ""
echo "🔥 Flamegraph Analysis Summary:"
echo "- hot_paths_full.svg: Complete benchmark suite profile"
echo "- traversal_focused.svg: Directory traversal hot paths"
echo "- patterns_focused.svg: Pattern matching hot paths"
echo ""
echo "💡 Next steps:"
echo "1. Open flamegraphs in browser for analysis"
echo "2. Identify CPU-intensive functions (wide bars)"
echo "3. Look for optimization opportunities in hot paths"
echo "4. Focus on functions with high self-time percentages"