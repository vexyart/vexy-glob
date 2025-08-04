// this_file: benches/comprehensive_benchmarks.rs
//! Comprehensive benchmarks using realistic datasets for performance validation
//! 
//! This benchmark suite uses the enhanced dataset generators to test vexy_glob
//! performance across different scales, file types, and directory structures
//! that mirror real-world usage patterns.

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId, Throughput};
use std::time::Duration;

mod datasets;
use datasets::*;

// Import vexy_glob components for direct Rust-level benchmarking
use globset::{Glob, GlobSetBuilder};
use ignore::WalkBuilder;
use grep_searcher::Searcher;
use grep_regex::RegexMatcherBuilder;

/// Benchmark directory traversal across different dataset scales
fn bench_scalable_traversal(c: &mut Criterion) {
    let test_env = create_comprehensive_test_environment();
    let base_path = test_env.path();
    
    let mut group = c.benchmark_group("scalable_traversal");
    group.measurement_time(Duration::from_secs(10));
    
    // Test different dataset scales
    for config in [DatasetConfig::small(), DatasetConfig::medium()] {
        let dataset_path = base_path.join(format!("dataset_{}", config.name));
        
        group.throughput(Throughput::Elements(config.total_files as u64));
        group.bench_with_input(
            BenchmarkId::new("basic_walk", config.name),
            &dataset_path,
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
        
        group.bench_with_input(
            BenchmarkId::new("parallel_walk", config.name),
            &dataset_path,
            |b, path| {
                b.iter(|| {
                    let walker = WalkBuilder::new(path)
                        .threads(4)
                        .build_parallel();
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
        
        group.bench_with_input(
            BenchmarkId::new("gitignore_aware", config.name),
            &dataset_path,
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
    }
    
    group.finish();
}

/// Benchmark pattern matching with realistic file patterns
fn bench_realistic_patterns(c: &mut Criterion) {
    let test_env = create_comprehensive_test_environment();
    let base_path = test_env.path();
    
    // Collect realistic file paths from different project types
    let mut all_paths = Vec::new();
    let walker = WalkBuilder::new(base_path).build();
    for entry in walker.take(5000) {
        if let Ok(entry) = entry {
            if entry.file_type().map_or(false, |ft| ft.is_file()) {
                all_paths.push(entry.path().to_path_buf());
            }
        }
    }
    
    let mut group = c.benchmark_group("realistic_patterns");
    group.throughput(Throughput::Elements(all_paths.len() as u64));
    
    // Test common development patterns
    let test_patterns = vec![
        ("python_files", "**/*.py"),
        ("rust_files", "**/*.rs"),
        ("js_ts_files", "**/*.{js,ts,jsx,tsx}"),
        ("config_files", "**/*.{json,yaml,toml,ini}"),
        ("source_files", "**/*.{py,rs,js,ts,c,cpp,h,java,go}"),
        ("test_files", "**/test_*.{py,rs,js}"),
        ("build_artifacts", "**/target/**/*"),
        ("documentation", "**/*.{md,rst,txt}"),
    ];
    
    for (pattern_name, pattern_str) in test_patterns {
        let glob = Glob::new(pattern_str).unwrap();
        let mut builder = GlobSetBuilder::new();
        builder.add(glob);
        let glob_set = builder.build().unwrap();
        
        group.bench_with_input(
            BenchmarkId::new("glob_match", pattern_name),
            &all_paths,
            |b, paths| {
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
    }
    
    group.finish();
}

/// Benchmark content search across different file types and sizes
fn bench_content_search_realistic(c: &mut Criterion) {
    let test_env = create_comprehensive_test_environment();
    let base_path = test_env.path();
    
    // Collect files by type for targeted content search
    let mut files_by_type = std::collections::HashMap::new();
    let walker = WalkBuilder::new(base_path).build();
    
    for entry in walker {
        if let Ok(entry) = entry {
            if let Some(ext) = entry.path().extension() {
                if let Some(ext_str) = ext.to_str() {
                    let file_list = files_by_type.entry(ext_str.to_string()).or_insert_with(Vec::new);
                    if file_list.len() < 1000 {  // Limit per file type for benchmark performance
                        file_list.push(entry.path().to_path_buf());
                    }
                }
            }
        }
    }
    
    let mut group = c.benchmark_group("content_search_realistic");
    group.measurement_time(Duration::from_secs(15));
    
    // Test different search patterns on different file types
    let search_patterns = vec![
        ("simple_word", "target_pattern"),
        ("todo_comments", r"(TODO|FIXME|BUG|HACK)"),
        ("function_definitions", r"(function|def|fn)\s+\w+"),
        ("import_statements", r"(import|#include|use)\s+"),
        ("class_structs", r"(class|struct|interface)\s+\w+"),
    ];
    
    for file_type in ["py", "rs", "js", "cpp", "txt"] {
        if let Some(files) = files_by_type.get(file_type) {
            if files.is_empty() { continue; }
            
            group.throughput(Throughput::Elements(files.len() as u64));
            
            for (pattern_name, pattern_regex) in &search_patterns {
                let matcher = RegexMatcherBuilder::new()
                    .case_insensitive(true)
                    .build(pattern_regex)
                    .unwrap();
                
                group.bench_with_input(
                    BenchmarkId::new(format!("{}_{}", file_type, pattern_name), files.len()),
                    files,
                    |b, file_paths| {
                        b.iter(|| {
                            let mut total_matches = 0;
                            let mut searcher = Searcher::new();
                            
                            for file_path in file_paths {
                                if let Ok(file) = std::fs::File::open(file_path) {
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
                                    total_matches += sink.count;
                                }
                            }
                            black_box(total_matches)
                        })
                    },
                );
            }
        }
    }
    
    group.finish();
}

/// Benchmark special filesystem scenarios (performance edge cases)
fn bench_filesystem_edge_cases(c: &mut Criterion) {
    let test_env = create_comprehensive_test_environment();
    let base_path = test_env.path();
    let special_cases_path = base_path.join("special_cases");
    
    let mut group = c.benchmark_group("filesystem_edge_cases");
    group.measurement_time(Duration::from_secs(8));
    
    // Deep directory nesting
    group.bench_function("deep_nesting", |b| {
        let deep_path = special_cases_path.join("deep_nesting");
        b.iter(|| {
            let walker = WalkBuilder::new(&deep_path).build();
            let mut count = 0;
            for entry in walker {
                if let Ok(_entry) = entry {
                    count += 1;
                }
            }
            black_box(count)
        })
    });
    
    // Many files in flat directory
    group.bench_function("flat_many_files", |b| {
        let flat_path = special_cases_path.join("flat_many_files");
        b.iter(|| {
            let walker = WalkBuilder::new(&flat_path).build();
            let mut count = 0;
            for entry in walker {
                if let Ok(_entry) = entry {
                    count += 1;
                }
            }
            black_box(count)
        })
    });
    
    // Mixed file sizes with pattern matching
    group.bench_function("mixed_file_sizes_glob", |b| {
        let sizes_path = special_cases_path.join("file_sizes");
        let glob = Glob::new("*.txt").unwrap();
        let mut builder = GlobSetBuilder::new();
        builder.add(glob);
        let glob_set = builder.build().unwrap();
        
        b.iter(|| {
            let walker = WalkBuilder::new(&sizes_path).build();
            let mut matches = 0;
            for entry in walker {
                if let Ok(entry) = entry {
                    if glob_set.is_match(entry.path()) {
                        matches += 1;
                    }
                }
            }
            black_box(matches)
        })
    });
    
    // Content search across different file sizes
    group.bench_function("mixed_file_sizes_content", |b| {
        let sizes_path = special_cases_path.join("file_sizes");
        let matcher = RegexMatcherBuilder::new()
            .case_insensitive(true)
            .build("target_pattern")
            .unwrap();
        
        b.iter(|| {
            let walker = WalkBuilder::new(&sizes_path).build();
            let mut total_matches = 0;
            let mut searcher = Searcher::new();
            
            for entry in walker {
                if let Ok(entry) = entry {
                    if entry.file_type().map_or(false, |ft| ft.is_file()) {
                        if let Ok(file) = std::fs::File::open(entry.path()) {
                            struct CountSink { count: usize }
                            
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
                            total_matches += sink.count;
                        }
                    }
                }
            }
            black_box(total_matches)
        })
    });
    
    group.finish();
}

/// Benchmark realistic project workflow scenarios
fn bench_project_workflows(c: &mut Criterion) {
    let test_env = create_comprehensive_test_environment();
    let base_path = test_env.path();
    
    let mut group = c.benchmark_group("project_workflows");
    group.measurement_time(Duration::from_secs(12));
    
    // Scenario: Find all Python files in web app project
    group.bench_function("find_python_files", |b| {
        let project_path = base_path.join("project_python_web_app");
        let glob = Glob::new("**/*.py").unwrap();
        let mut builder = GlobSetBuilder::new();
        builder.add(glob);
        let glob_set = builder.build().unwrap();
        
        b.iter(|| {
            let walker = WalkBuilder::new(&project_path).build();
            let mut matches = 0;
            for entry in walker {
                if let Ok(entry) = entry {
                    if glob_set.is_match(entry.path()) {
                        matches += 1;
                    }
                }
            }
            black_box(matches)
        })
    });
    
    // Scenario: Find all source files across multiple projects
    group.bench_function("find_all_source_files", |b| {
        let glob = Glob::new("**/*.{py,rs,js,ts,cpp,c,h}").unwrap();
        let mut builder = GlobSetBuilder::new();
        builder.add(glob);
        let glob_set = builder.build().unwrap();
        
        b.iter(|| {
            let walker = WalkBuilder::new(base_path).build();
            let mut matches = 0;
            for entry in walker {
                if let Ok(entry) = entry {
                    if glob_set.is_match(entry.path()) {
                        matches += 1;
                    }
                }
            }
            black_box(matches)
        })
    });
    
    // Scenario: Search for TODO comments across all projects
    group.bench_function("search_todo_comments", |b| {
        let matcher = RegexMatcherBuilder::new()
            .case_insensitive(true)
            .build(r"(TODO|FIXME|BUG|HACK)")
            .unwrap();
        
        b.iter(|| {
            let walker = WalkBuilder::new(base_path)
                .git_ignore(true)
                .build();
            let mut total_matches = 0;
            let mut searcher = Searcher::new();
            
            for entry in walker {
                if let Ok(entry) = entry {
                    if entry.file_type().map_or(false, |ft| ft.is_file()) {
                        // Only search text files
                        if let Some(ext) = entry.path().extension() {
                            if let Some(ext_str) = ext.to_str() {
                                if matches!(ext_str, "py" | "rs" | "js" | "ts" | "cpp" | "c" | "h" | "txt" | "md") {
                                    if let Ok(file) = std::fs::File::open(entry.path()) {
                                        struct CountSink { count: usize }
                                        
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
                                        total_matches += sink.count;
                                    }
                                }
                            }
                        }
                    }
                }
            }
            black_box(total_matches)
        })
    });
    
    group.finish();
}

criterion_group!(
    comprehensive_benches,
    bench_scalable_traversal,
    bench_realistic_patterns,
    bench_content_search_realistic,
    bench_filesystem_edge_cases,
    bench_project_workflows
);
criterion_main!(comprehensive_benches);