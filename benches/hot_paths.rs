// this_file: benches/hot_paths.rs
//! Hot path benchmarks for vexy_glob performance optimization
//! 
//! This benchmark suite identifies performance bottlenecks in critical
//! code paths for file finding, pattern matching, and content search.

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use std::fs::{File, create_dir_all};
use std::io::Write;
use std::path::PathBuf;
use tempfile::TempDir;
use globset::GlobSetBuilder;
use ignore::WalkBuilder;
use regex::Regex;

/// Create a realistic test environment for benchmarking
fn create_test_environment() -> TempDir {
    let tmp_dir = TempDir::new().expect("Failed to create temp directory");
    let base_path = tmp_dir.path();
    
    // Create a structure that mimics real-world projects
    // Total: ~2000 files across various directories
    for project_i in 0..10 {
        let project_dir = base_path.join(format!("project_{}", project_i));
        create_dir_all(&project_dir).unwrap();
        
        // Source code directory
        let src_dir = project_dir.join("src");
        create_dir_all(&src_dir).unwrap();
        for i in 0..50 {
            let mut file = File::create(src_dir.join(format!("module_{}.py", i))).unwrap();
            writeln!(file, "def function_{}():", i).unwrap();
            writeln!(file, "    '''Function {} documentation'''", i).unwrap();
            writeln!(file, "    target_pattern_content = {}", i).unwrap();
            writeln!(file, "    return 'result_{}'", i).unwrap();
        }
        
        // Test directory
        let test_dir = project_dir.join("tests");
        create_dir_all(&test_dir).unwrap();
        for i in 0..30 {
            let mut file = File::create(test_dir.join(format!("test_{}.py", i))).unwrap();
            writeln!(file, "import pytest").unwrap();
            writeln!(file, "def test_function_{}():", i).unwrap();
            writeln!(file, "    assert True  # target_pattern_content").unwrap();
        }
        
        // Documentation
        let docs_dir = project_dir.join("docs");
        create_dir_all(&docs_dir).unwrap();
        for i in 0..20 {
            let mut file = File::create(docs_dir.join(format!("doc_{}.md", i))).unwrap();
            writeln!(file, "# Documentation {}", i).unwrap();
            writeln!(file, "This contains target_pattern_content for testing.").unwrap();
        }
        
        // Binary/build artifacts (should be filtered out)
        let build_dir = project_dir.join("build");
        create_dir_all(&build_dir).unwrap();
        for i in 0..15 {
            let mut file = File::create(build_dir.join(format!("artifact_{}.o", i))).unwrap();
            file.write_all(&[0u8; 1024]).unwrap(); // Binary content
        }
        
        // Configuration and hidden files
        let mut gitignore = File::create(project_dir.join(".gitignore")).unwrap();
        writeln!(gitignore, "build/").unwrap();
        writeln!(gitignore, "*.o").unwrap();
        writeln!(gitignore, "__pycache__/").unwrap();
    }
    
    tmp_dir
}

/// Benchmark directory traversal with ignore crate
fn bench_directory_traversal(c: &mut Criterion) {
    let tmp_dir = create_test_environment();
    let root_path = tmp_dir.path();
    
    let mut group = c.benchmark_group("directory_traversal");
    
    // Benchmark basic traversal
    group.bench_with_input(
        BenchmarkId::new("basic_walk", "2k_files"),
        root_path,
        |b, path| {
            b.iter(|| {
                let walker = WalkBuilder::new(path).build();
                let mut count = 0;
                for entry in walker {
                    if let Ok(_entry) = entry {
                        count += 1;
                    }
                }
                black_box(count)
            })
        },
    );
    
    // Benchmark parallel traversal
    group.bench_with_input(
        BenchmarkId::new("parallel_walk", "2k_files"),
        root_path,
        |b, path| {
            b.iter(|| {
                let walker = WalkBuilder::new(path).threads(4).build_parallel();
                let count = std::sync::atomic::AtomicUsize::new(0);
                walker.run(|| {
                    let count = &count;
                    Box::new(move |_result| {
                        count.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                        ignore::WalkState::Continue
                    })
                });
                black_box(count.load(std::sync::atomic::Ordering::Relaxed))
            })
        },
    );
    
    // Benchmark with gitignore processing
    group.bench_with_input(
        BenchmarkId::new("gitignore_walk", "2k_files"),
        root_path,
        |b, path| {
            b.iter(|| {
                let walker = WalkBuilder::new(path)
                    .git_ignore(true)
                    .hidden(false)
                    .build();
                let mut count = 0;
                for entry in walker {
                    if let Ok(_entry) = entry {
                        count += 1;
                    }
                }
                black_box(count)
            })
        },
    );
    
    group.finish();
}

/// Benchmark pattern matching performance
fn bench_pattern_matching(c: &mut Criterion) {
    let tmp_dir = create_test_environment();
    let root_path = tmp_dir.path();
    
    // Collect sample paths for testing
    let mut sample_paths = Vec::new();
    let walker = WalkBuilder::new(root_path).build();
    for entry in walker.take(1000) {
        if let Ok(entry) = entry {
            sample_paths.push(entry.path().to_path_buf());
        }
    }
    
    let mut group = c.benchmark_group("pattern_matching");
    
    // Test literal pattern matching
    group.bench_with_input(
        BenchmarkId::new("literal_match", "1k_paths"),
        &sample_paths,
        |b, paths| {
            b.iter(|| {
                let target = "module_25.py";
                let mut matches = 0;
                for path in paths {
                    if let Some(filename) = path.file_name() {
                        if filename == target {
                            matches += 1;
                        }
                    }
                }
                black_box(matches)
            })
        },
    );
    
    // Test glob pattern matching
    group.bench_with_input(
        BenchmarkId::new("glob_match", "1k_paths"),
        &sample_paths,
        |b, paths| {
            let mut builder = GlobSetBuilder::new();
            builder.add(globset::Glob::new("*.py").unwrap());
            let glob_set = builder.build().unwrap();
            
            b.iter(|| {
                let mut matches = 0;
                for path in paths {
                    if glob_set.is_match(path) {
                        matches += 1;
                    }
                }
                black_box(matches)
            })
        },
    );
    
    // Test regex pattern matching
    group.bench_with_input(
        BenchmarkId::new("regex_match", "1k_paths"),
        &sample_paths,
        |b, paths| {
            let regex = Regex::new(r"test_\d+\.py$").unwrap();
            
            b.iter(|| {
                let mut matches = 0;
                for path in paths {
                    if let Some(path_str) = path.to_str() {
                        if regex.is_match(path_str) {
                            matches += 1;
                        }
                    }
                }
                black_box(matches)
            })
        },
    );
    
    // Test complex glob patterns
    group.bench_with_input(
        BenchmarkId::new("complex_glob", "1k_paths"),
        &sample_paths,
        |b, paths| {
            let mut builder = GlobSetBuilder::new();
            builder.add(globset::Glob::new("**/src/*.py").unwrap());
            builder.add(globset::Glob::new("**/tests/test_*.py").unwrap());
            builder.add(globset::Glob::new("**/docs/*.md").unwrap());
            let glob_set = builder.build().unwrap();
            
            b.iter(|| {
                let mut matches = 0;
                for path in paths {
                    if glob_set.is_match(path) {
                        matches += 1;
                    }
                }
                black_box(matches)
            })
        },
    );
    
    group.finish();
}

/// Benchmark file metadata operations
fn bench_file_metadata(c: &mut Criterion) {
    let tmp_dir = create_test_environment();
    let root_path = tmp_dir.path();
    
    // Collect sample entries for testing
    let mut sample_entries = Vec::new();
    let walker = WalkBuilder::new(root_path).build();
    for entry in walker.take(500) {
        if let Ok(entry) = entry {
            sample_entries.push(entry);
        }
    }
    
    let mut group = c.benchmark_group("file_metadata");
    
    // Benchmark file type checking
    group.bench_with_input(
        BenchmarkId::new("file_type_check", "500_files"),
        &sample_entries,
        |b, entries| {
            b.iter(|| {
                let mut file_count = 0;
                for entry in entries {
                    if let Some(file_type) = entry.file_type() {
                        if file_type.is_file() {
                            file_count += 1;
                        }
                    }
                }
                black_box(file_count)
            })
        },
    );
    
    // Benchmark path-to-string conversion
    group.bench_with_input(
        BenchmarkId::new("path_to_string", "500_files"),
        &sample_entries,
        |b, entries| {
            b.iter(|| {
                let mut converted = 0;
                for entry in entries {
                    if let Some(_path_str) = entry.path().to_str() {
                        converted += 1;
                    }
                }
                black_box(converted)
            })
        },
    );
    
    group.finish();
}

/// Benchmark content searching operations
fn bench_content_search(c: &mut Criterion) {
    let tmp_dir = create_test_environment();
    let root_path = tmp_dir.path();
    
    // Collect Python files for content search
    let mut python_files = Vec::new();
    let walker = WalkBuilder::new(root_path).build();
    for entry in walker {
        if let Ok(entry) = entry {
            if let Some(ext) = entry.path().extension() {
                if ext == "py" {
                    python_files.push(entry.path().to_path_buf());
                }
            }
        }
    }
    
    let mut group = c.benchmark_group("content_search");
    
    // Benchmark grep-searcher with regex
    group.bench_with_input(
        BenchmarkId::new("grep_search", format!("{}_py_files", python_files.len())),
        &python_files,
        |b, files| {
            use grep_searcher::Searcher;
            use grep_regex::RegexMatcherBuilder;
            
            let matcher = RegexMatcherBuilder::new()
                .case_insensitive(true)
                .build("target_pattern_content")
                .unwrap();
            
            b.iter(|| {
                let mut matches = 0;
                let mut searcher = Searcher::new();
                
                for file_path in files {
                    if let Ok(file) = std::fs::File::open(file_path) {
                        // Simple sink that counts matches
                        struct CountSink {
                            count: usize,
                        }
                        
                        impl grep_searcher::Sink for CountSink {
                            type Error = std::io::Error;

                            fn matched(
                                &mut self,
                                _searcher: &grep_searcher::Searcher,
                                _mat: &grep_searcher::SinkMatch<'_>,
                            ) -> Result<bool, Self::Error> {
                                self.count += 1;
                                Ok(true)
                            }
                        }
                        
                        let mut sink = CountSink { count: 0 };
                        let _ = searcher.search_file(&matcher, &file, &mut sink);
                        matches += sink.count;
                    }
                }
                black_box(matches)
            })
        },
    );
    
    group.finish();
}

criterion_group!(
    benches,
    bench_directory_traversal,
    bench_pattern_matching,
    bench_file_metadata,
    bench_content_search
);
criterion_main!(benches);