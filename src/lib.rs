// this_file: src/lib.rs

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::PyDict;
use ignore::{WalkBuilder, WalkState, DirEntry};
use globset::{GlobSet, GlobSetBuilder};
use crossbeam_channel::Receiver;
use std::path::Path;
use std::sync::Arc;
use std::fs::File;
use std::time::SystemTime;
use anyhow::Result;
use grep_searcher::{Searcher, Sink, SinkMatch};
use grep_regex::{RegexMatcher, RegexMatcherBuilder};

mod zero_copy_path;
mod pattern_cache;
mod simd_string;
mod global_init;

/// Main module definition for vexy_glob
#[pymodule]
fn _vexy_glob(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Perform global initialization to reduce cold start variance
    global_init::ensure_global_init()
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(
            format!("Failed to initialize vexy_glob: {}", e)
        ))?;
    
    m.add_function(wrap_pyfunction!(find, m)?)?;
    m.add_function(wrap_pyfunction!(search, m)?)?;
    m.add_class::<VexyGlobIterator>()?;
    Ok(())
}

/// Search result for content matching
#[derive(Debug, Clone)]
pub struct SearchResultRust {
    pub path: String,  // Changed from PathBuf to String for zero-copy optimization
    pub line_number: u64,
    pub line_text: String,
    pub matches: Vec<String>,
}

/// Result type for path finding and content search
#[derive(Debug, Clone)]
enum FindResult {
    Path(String),  // Changed from PathBuf to String for zero-copy optimization
    Search(SearchResultRust),
    Error(String),
}

/// Buffer configuration for channel capacity optimization
struct BufferConfig {
    /// Channel capacity for results
    channel_capacity: usize,
}

impl BufferConfig {
    /// Get optimal channel capacity based on workload characteristics
    fn for_workload(is_content_search: bool, has_sorting: bool, thread_count: usize) -> Self {
        if is_content_search {
            // Content search produces results more slowly, smaller channel is sufficient
            BufferConfig {
                channel_capacity: 500,
            }
        } else if has_sorting {
            // Sorting requires collecting all results, larger channel capacity helps
            BufferConfig {
                channel_capacity: 10_000,
            }
        } else {
            // Standard file finding - scale with thread count for better parallelism
            // More threads = potentially more concurrent file discoveries
            BufferConfig {
                channel_capacity: 1000 * thread_count.max(1).min(8), // Cap at 8000 for memory
            }
        }
    }
}

/// Python iterator class for streaming results
#[pyclass]
struct VexyGlobIterator {
    receiver: Option<Receiver<FindResult>>,
    as_path_objects: bool,
}

#[pymethods]
impl VexyGlobIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }
    
    fn __next__(mut slf: PyRefMut<'_, Self>) -> Option<PyObject> {
        if let Some(receiver) = &slf.receiver {
            match receiver.recv() {
                Ok(FindResult::Path(path_str)) => {
                    Python::with_gil(|py| {
                        if slf.as_path_objects {
                            // Return as pathlib.Path
                            let pathlib = py.import("pathlib").ok()?;
                            let path_class = pathlib.getattr("Path").ok()?;
                            Some(path_class.call1((path_str,)).ok()?.into())
                        } else {
                            // Return as string (already a string, no conversion needed)
                            Some(path_str.into_pyobject(py).ok()?.into())
                        }
                    })
                }
                Ok(FindResult::Search(search_result)) => {
                    Python::with_gil(|py| {
                        // Create a dictionary representing SearchResult
                        let result_dict = PyDict::new(py);
                        
                        let path_obj: PyObject = if slf.as_path_objects {
                            let pathlib = py.import("pathlib").ok()?;
                            let path_class = pathlib.getattr("Path").ok()?;
                            path_class.call1((&search_result.path,)).ok()?.into()
                        } else {
                            search_result.path.clone().into_pyobject(py).ok()?.into()
                        };
                        
                        result_dict.set_item("path", path_obj).ok()?;
                        result_dict.set_item("line_number", search_result.line_number).ok()?;
                        result_dict.set_item("line_text", search_result.line_text).ok()?;
                        result_dict.set_item("matches", search_result.matches).ok()?;
                        
                        Some(result_dict.into())
                    })
                }
                Ok(FindResult::Error(err)) => {
                    // Log error but continue iteration
                    eprintln!("Error during traversal: {}", err);
                    Self::__next__(slf)
                }
                Err(_) => {
                    // Channel closed, iteration complete
                    slf.receiver = None;
                    None
                }
            }
        } else {
            None
        }
    }
}

/// Custom Sink implementation for collecting search results
struct SearchSink {
    path: String,  // Changed to String for zero-copy optimization
    results: Vec<SearchResultRust>,
}

impl SearchSink {
    fn new(path: String) -> Self {
        Self {
            path,
            results: Vec::new(),
        }
    }
    
    fn into_results(self) -> Vec<SearchResultRust> {
        self.results
    }
}

impl Sink for SearchSink {
    type Error = std::io::Error;
    
    fn matched(&mut self, _searcher: &Searcher, mat: &SinkMatch<'_>) -> Result<bool, Self::Error> {
        let line_number = mat.line_number().unwrap_or(0);
        
        // Extract the line text from the buffer
        let mut line_bytes = Vec::new();
        for line in mat.lines() {
            line_bytes.extend_from_slice(line);
        }
        let line_text = String::from_utf8_lossy(&line_bytes).to_string();
        
        // Extract matches from the line
        let mut matches = Vec::new();
        // For now, just use the entire line as a match
        // TODO: Extract actual regex matches
        matches.push(line_text.trim().to_string());
        
        self.results.push(SearchResultRust {
            path: self.path.clone(),
            line_number,
            line_text,
            matches,
        });
        
        Ok(true) // Continue searching
    }
}

/// Find files and directories matching the given criteria
#[pyfunction]
#[pyo3(signature = (
    paths,
    glob = None,
    regex = None,
    file_type = None,
    extension = None,
    exclude = None,
    max_depth = None,
    min_size = None,
    max_size = None,
    mtime_after = None,
    mtime_before = None,
    atime_after = None,
    atime_before = None,
    ctime_after = None,
    ctime_before = None,
    hidden = false,
    no_ignore = false,
    no_global_ignore = false,
    custom_ignore_files = None,
    follow_symlinks = false,
    same_file_system = false,
    case_sensitive_glob = true,
    as_path_objects = false,
    yield_results = true,
    sort = None,
    threads = 0
))]
fn find(
    py: Python<'_>,
    paths: Vec<String>,
    glob: Option<String>,
    regex: Option<String>,
    file_type: Option<String>,
    extension: Option<Vec<String>>,
    exclude: Option<Vec<String>>,
    max_depth: Option<usize>,
    min_size: Option<u64>,
    max_size: Option<u64>,
    mtime_after: Option<f64>,  // Unix timestamp as float
    mtime_before: Option<f64>, // Unix timestamp as float
    atime_after: Option<f64>,  // Unix timestamp as float
    atime_before: Option<f64>, // Unix timestamp as float
    ctime_after: Option<f64>,  // Unix timestamp as float
    ctime_before: Option<f64>, // Unix timestamp as float
    hidden: bool,
    no_ignore: bool,
    no_global_ignore: bool,
    custom_ignore_files: Option<Vec<String>>,
    follow_symlinks: bool,
    same_file_system: bool,
    case_sensitive_glob: bool,
    as_path_objects: bool,
    yield_results: bool,
    sort: Option<String>,
    threads: usize,
) -> PyResult<PyObject> {
    // Build glob pattern matcher with literal optimization
    let pattern_matcher = if let Some(pattern) = glob {
        Some(PatternMatcher::new(&pattern, case_sensitive_glob)
            .map_err(|e| PyValueError::new_err(format!("Invalid glob pattern: {}", e)))?)
    } else {
        None
    };
    
    // Build exclude pattern matcher
    let exclude_set = if let Some(ref patterns) = exclude {
        if !patterns.is_empty() {
            Some(build_glob_set(patterns, case_sensitive_glob)
                .map_err(|e| PyValueError::new_err(format!("Invalid exclude pattern: {}", e)))?)
        } else {
            None
        }
    } else {
        None
    };
    
    // Build regex matcher if provided
    let regex_matcher = if let Some(pattern) = regex {
        Some(regex::Regex::new(&pattern)
            .map_err(|e| PyValueError::new_err(format!("Invalid regex pattern: {}", e)))?)
    } else {
        None
    };
    
    // Parse file type filter
    let file_type_filter = file_type.as_ref().and_then(|t| match t.as_str() {
        "f" => Some(FileType::File),
        "d" => Some(FileType::Dir),
        "l" => Some(FileType::Symlink),
        _ => None,
    });
    
    // Force collection when sorting is requested
    let actual_yield_results = yield_results && sort.is_none();
    
    // Get optimal buffer configuration
    let buffer_config = BufferConfig::for_workload(false, sort.is_some(), threads);
    
    // Create channel for results with optimal capacity using global pool
    let (tx, rx) = global_init::get_channel_pool().get_channel(buffer_config.channel_capacity);
    
    // Build the walker
    let mut builder = WalkBuilder::new(&paths[0]);
    
    // Add additional paths
    for path in &paths[1..] {
        builder.add(path);
    }
    
    // Configure walker options
    builder
        .hidden(!hidden)
        .ignore(!no_ignore)  // respect .ignore files
        .git_ignore(!no_ignore)  // respect .gitignore files
        .git_global(!no_global_ignore)  // respect global gitignore
        .git_exclude(!no_ignore)  // respect .git/info/exclude
        .follow_links(follow_symlinks)  // follow symbolic links
        .same_file_system(same_file_system)  // don't cross filesystem boundaries
        .max_depth(max_depth)
        .threads(if threads == 0 { num_cpus::get() } else { threads });
    
    // Add custom ignore files
    if let Some(ref ignore_files) = custom_ignore_files {
        for ignore_file in ignore_files {
            if std::path::Path::new(ignore_file).exists() {
                builder.add_ignore(ignore_file);
            }
        }
    }
    
    // Automatically add .fdignore files if they exist and no_ignore is false
    if !no_ignore {
        for path in &paths {
            let fdignore_path = std::path::Path::new(path).join(".fdignore");
            if fdignore_path.exists() {
                builder.add_ignore(&fdignore_path);
            }
        }
    }
    
    // Clone necessary data for the thread
    let pattern_matcher = Arc::new(pattern_matcher);
    let exclude_set = Arc::new(exclude_set);
    let regex_matcher = Arc::new(regex_matcher);
    let extension = Arc::new(extension);
    let min_size = Arc::new(min_size);
    let max_size = Arc::new(max_size);
    let mtime_after = Arc::new(mtime_after);
    let mtime_before = Arc::new(mtime_before);
    let atime_after = Arc::new(atime_after);
    let atime_before = Arc::new(atime_before);
    let ctime_after = Arc::new(ctime_after);
    let ctime_before = Arc::new(ctime_before);
    
    // Spawn walker thread
    let walker_thread = std::thread::spawn(move || {
        let walker = builder.build_parallel();
        walker.run(|| {
            let tx = tx.clone();
            let pattern_matcher = Arc::clone(&pattern_matcher);
            let exclude_set = Arc::clone(&exclude_set);
            let regex_matcher = Arc::clone(&regex_matcher);
            let extension = Arc::clone(&extension);
            let min_size = Arc::clone(&min_size);
            let max_size = Arc::clone(&max_size);
            let mtime_after = Arc::clone(&mtime_after);
            let mtime_before = Arc::clone(&mtime_before);
            let atime_after = Arc::clone(&atime_after);
            let atime_before = Arc::clone(&atime_before);
            let ctime_after = Arc::clone(&ctime_after);
            let ctime_before = Arc::clone(&ctime_before);
            
            Box::new(move |result| {
                match result {
                    Ok(entry) => {
                        if should_include_entry(
                            &entry,
                            &pattern_matcher,
                            &exclude_set,
                            &regex_matcher,
                            file_type_filter,
                            &extension,
                            *min_size,
                            *max_size,
                            *mtime_after,
                            *mtime_before,
                            *atime_after,
                            *atime_before,
                            *ctime_after,
                            *ctime_before,
                        ) {
                            // Zero-copy optimization: convert path to string once
                            let path_string = entry.path().to_string_lossy().into_owned();
                            let _ = tx.send(FindResult::Path(path_string));
                        }
                    }
                    Err(err) => {
                        let _ = tx.send(FindResult::Error(err.to_string()));
                    }
                }
                WalkState::Continue
            })
        });
    });
    
    if actual_yield_results {
        // Return iterator for streaming
        Ok(Py::new(py, VexyGlobIterator {
            receiver: Some(rx),
            as_path_objects,
        })?.into())
    } else {
        // Collect all results into a list
        py.allow_threads(|| {
            walker_thread.join().unwrap();
        });
        
        let mut results = Vec::new();
        while let Ok(result) = rx.recv() {
            if let FindResult::Path(path) = result {
                results.push(path);
            }
        }
        
        // Sort results if requested
        if let Some(ref sort_by) = sort {
            match sort_by.as_str() {
                "name" => results.sort_by(|a, b| {
                    let a_name = std::path::Path::new(a).file_name().and_then(|n| n.to_str()).unwrap_or("");
                    let b_name = std::path::Path::new(b).file_name().and_then(|n| n.to_str()).unwrap_or("");
                    a_name.cmp(b_name)
                }),
                "path" => results.sort(),
                "size" => {
                    results.sort_by_key(|p| {
                        std::fs::metadata(p).ok().map(|m| m.len()).unwrap_or(0)
                    });
                }
                "mtime" => {
                    results.sort_by_key(|p| {
                        std::fs::metadata(p).ok()
                            .and_then(|m| m.modified().ok())
                            .unwrap_or(SystemTime::UNIX_EPOCH)
                    });
                }
                _ => return Err(PyValueError::new_err(format!("Invalid sort option: {}. Use 'name', 'path', 'size', or 'mtime'", sort_by))),
            }
        }
        
        // Convert to Python list
        Python::with_gil(|py| {
            let py_list = pyo3::types::PyList::empty(py);
            for path in results {
                if as_path_objects {
                    let pathlib = py.import("pathlib")?;
                    let path_class = pathlib.getattr("Path")?;
                    let path_obj = path_class.call1((path,))?;
                    py_list.append(path_obj)?;
                } else {
                    py_list.append(path)?;
                }
            }
            Ok(py_list.into())
        })
    }
}

/// Search for content within files using grep functionality
#[pyfunction]
#[pyo3(signature = (
    content_regex,
    paths,
    glob = None,
    regex = None,
    file_type = None,
    extension = None,
    exclude = None,
    max_depth = None,
    min_size = None,
    max_size = None,
    mtime_after = None,
    mtime_before = None,
    atime_after = None,
    atime_before = None,
    ctime_after = None,
    ctime_before = None,
    hidden = false,
    no_ignore = false,
    no_global_ignore = false,
    custom_ignore_files = None,
    follow_symlinks = false,
    same_file_system = false,
    case_sensitive_glob = true,
    _case_sensitive_content = true,
    as_path_objects = false,
    yield_results = true,
    _multiline = false,
    threads = 0
))]
fn search(
    py: Python<'_>,
    content_regex: String,
    paths: Vec<String>,
    glob: Option<String>,
    regex: Option<String>,
    file_type: Option<String>,
    extension: Option<Vec<String>>,
    exclude: Option<Vec<String>>,
    max_depth: Option<usize>,
    min_size: Option<u64>,
    max_size: Option<u64>,
    mtime_after: Option<f64>,
    mtime_before: Option<f64>,
    atime_after: Option<f64>,
    atime_before: Option<f64>,
    ctime_after: Option<f64>,
    ctime_before: Option<f64>,
    hidden: bool,
    no_ignore: bool,
    no_global_ignore: bool,
    custom_ignore_files: Option<Vec<String>>,
    follow_symlinks: bool,
    same_file_system: bool,
    case_sensitive_glob: bool,
    _case_sensitive_content: bool,
    as_path_objects: bool,
    yield_results: bool,
    _multiline: bool,
    threads: usize,
) -> PyResult<PyObject> {
    // Build content pattern matcher with case sensitivity
    let content_matcher = RegexMatcherBuilder::new()
        .case_insensitive(!_case_sensitive_content)
        .build(&content_regex)
        .map_err(|e| PyValueError::new_err(format!("Invalid content regex: {}", e)))?;
    
    // Build glob pattern matcher with literal optimization
    let pattern_matcher = if let Some(pattern) = glob {
        Some(PatternMatcher::new(&pattern, case_sensitive_glob)
            .map_err(|e| PyValueError::new_err(format!("Invalid glob pattern: {}", e)))?)
    } else {
        None
    };
    
    // Build exclude pattern matcher
    let exclude_set = if let Some(ref patterns) = exclude {
        if !patterns.is_empty() {
            Some(build_glob_set(patterns, case_sensitive_glob)
                .map_err(|e| PyValueError::new_err(format!("Invalid exclude pattern: {}", e)))?)
        } else {
            None
        }
    } else {
        None
    };
    
    // Build regex matcher if provided
    let regex_matcher = if let Some(pattern) = regex {
        Some(regex::Regex::new(&pattern)
            .map_err(|e| PyValueError::new_err(format!("Invalid regex pattern: {}", e)))?)
    } else {
        None
    };
    
    // Parse file type filter
    let file_type_filter = file_type.as_ref().and_then(|t| match t.as_str() {
        "f" => Some(FileType::File),
        "d" => Some(FileType::Dir),
        "l" => Some(FileType::Symlink),
        _ => None,
    });
    
    // Get optimal buffer configuration for content search
    let buffer_config = BufferConfig::for_workload(true, false, threads);
    
    // Create channel for results with optimal capacity using global pool
    let (tx, rx) = global_init::get_channel_pool().get_channel(buffer_config.channel_capacity);
    
    // Build the walker
    let mut builder = WalkBuilder::new(&paths[0]);
    
    // Add additional paths
    for path in &paths[1..] {
        builder.add(path);
    }
    
    // Configure walker options
    builder
        .hidden(!hidden)
        .ignore(!no_ignore)  // respect .ignore files
        .git_ignore(!no_ignore)  // respect .gitignore files
        .git_global(!no_global_ignore)  // respect global gitignore
        .git_exclude(!no_ignore)  // respect .git/info/exclude
        .follow_links(follow_symlinks)  // follow symbolic links
        .same_file_system(same_file_system)  // don't cross filesystem boundaries
        .max_depth(max_depth)
        .threads(if threads == 0 { num_cpus::get() } else { threads });
    
    // Add custom ignore files
    if let Some(ref ignore_files) = custom_ignore_files {
        for ignore_file in ignore_files {
            if std::path::Path::new(ignore_file).exists() {
                builder.add_ignore(ignore_file);
            }
        }
    }
    
    // Automatically add .fdignore files if they exist and no_ignore is false
    if !no_ignore {
        for path in &paths {
            let fdignore_path = std::path::Path::new(path).join(".fdignore");
            if fdignore_path.exists() {
                builder.add_ignore(&fdignore_path);
            }
        }
    }
    
    // Clone necessary data for the thread
    let pattern_matcher = Arc::new(pattern_matcher);
    let exclude_set = Arc::new(exclude_set);
    let regex_matcher = Arc::new(regex_matcher);
    let extension = Arc::new(extension);
    let min_size = Arc::new(min_size);
    let max_size = Arc::new(max_size);
    let mtime_after = Arc::new(mtime_after);
    let mtime_before = Arc::new(mtime_before);
    let atime_after = Arc::new(atime_after);
    let atime_before = Arc::new(atime_before);
    let ctime_after = Arc::new(ctime_after);
    let ctime_before = Arc::new(ctime_before);
    let content_matcher = Arc::new(content_matcher);
    
    // Spawn walker thread
    let walker_thread = std::thread::spawn(move || {
        let walker = builder.build_parallel();
        walker.run(|| {
            let tx = tx.clone();
            let pattern_matcher = Arc::clone(&pattern_matcher);
            let exclude_set = Arc::clone(&exclude_set);
            let regex_matcher = Arc::clone(&regex_matcher);
            let extension = Arc::clone(&extension);
            let min_size = Arc::clone(&min_size);
            let max_size = Arc::clone(&max_size);
            let mtime_after = Arc::clone(&mtime_after);
            let mtime_before = Arc::clone(&mtime_before);
            let atime_after = Arc::clone(&atime_after);
            let atime_before = Arc::clone(&atime_before);
            let ctime_after = Arc::clone(&ctime_after);
            let ctime_before = Arc::clone(&ctime_before);
            let content_matcher = Arc::clone(&content_matcher);
            
            Box::new(move |result| {
                match result {
                    Ok(entry) => {
                        // First check if path matches our filters
                        if should_include_entry(
                            &entry,
                            &pattern_matcher,
                            &exclude_set,
                            &regex_matcher,
                            file_type_filter,
                            &extension,
                            *min_size,
                            *max_size,
                            *mtime_after,
                            *mtime_before,
                            *atime_after,
                            *atime_before,
                            *ctime_after,
                            *ctime_before,
                        ) {
                            // Only search content in files, not directories
                            if entry.file_type().map_or(false, |ft| ft.is_file()) {
                                if let Err(e) = search_file_content(&tx, &entry, &content_matcher) {
                                    let _ = tx.send(FindResult::Error(format!("Content search error: {}", e)));
                                }
                            }
                        }
                    }
                    Err(err) => {
                        let _ = tx.send(FindResult::Error(err.to_string()));
                    }
                }
                WalkState::Continue
            })
        });
    });
    
    if yield_results {
        // Return iterator for streaming
        Ok(Py::new(py, VexyGlobIterator {
            receiver: Some(rx),
            as_path_objects,
        })?.into())
    } else {
        // Collect all results into a list
        py.allow_threads(|| {
            walker_thread.join().unwrap();
        });
        
        let mut results = Vec::new();
        while let Ok(result) = rx.recv() {
            if let FindResult::Search(search_result) = result {
                results.push(search_result);
            }
        }
        
        // Convert to Python list
        Python::with_gil(|py| {
            let py_list = pyo3::types::PyList::empty(py);
            for search_result in results {
                let result_dict = PyDict::new(py);
                
                let path_obj: PyObject = if as_path_objects {
                    let pathlib = py.import("pathlib")?;
                    let path_class = pathlib.getattr("Path")?;
                    path_class.call1((&search_result.path,))?.into()
                } else {
                    search_result.path.clone().into_pyobject(py)?.into()
                };
                
                result_dict.set_item("path", path_obj)?;
                result_dict.set_item("line_number", search_result.line_number)?;
                result_dict.set_item("line_text", search_result.line_text)?;
                result_dict.set_item("matches", search_result.matches)?;
                
                py_list.append(result_dict)?;
            }
            Ok(py_list.into())
        })
    }
}

// Helper types and functions

#[derive(Debug, Clone, Copy)]
enum FileType {
    File,
    Dir,
    Symlink,
}

/// Pattern matcher that optimizes for literal patterns
#[derive(Debug)]
enum PatternMatcher {
    /// Literal pattern - direct string comparison
    Literal { pattern: String, case_sensitive: bool },
    /// Glob pattern - uses GlobSet
    Glob(GlobSet),
}

impl PatternMatcher {
    /// Create a new pattern matcher using cached compilation, optimizing for literal patterns
    fn new(pattern: &str, case_sensitive: bool) -> Result<Self> {
        if pattern_cache::is_literal_pattern(pattern) {
            Ok(PatternMatcher::Literal { 
                pattern: pattern.to_string(), 
                case_sensitive 
            })
        } else {
            // Use cached pattern compilation for performance
            let cached_entry = pattern_cache::PATTERN_CACHE.get_or_compile(pattern, case_sensitive)?;
            Ok(PatternMatcher::Glob((*cached_entry.glob_set).clone()))
        }
    }
    
    /// Check if a path matches the pattern
    fn is_match(&self, path: &Path) -> bool {
        match self {
            PatternMatcher::Literal { pattern, case_sensitive } => {
                // For literal patterns, we need to check if the pattern contains a path separator
                // If it does, match against the full path; otherwise match against the filename
                if pattern.contains('/') || pattern.contains('\\') {
                    let path_str = path.to_string_lossy();
                    if *case_sensitive {
                        path_str.ends_with(pattern)
                    } else {
                        path_str.to_lowercase().ends_with(&pattern.to_lowercase())
                    }
                } else {
                    // Match against filename only
                    if let Some(filename) = path.file_name() {
                        let filename_str = filename.to_string_lossy();
                        if *case_sensitive {
                            filename_str.as_ref() == pattern
                        } else {
                            filename_str.to_lowercase() == pattern.to_lowercase()
                        }
                    } else {
                        false
                    }
                }
            }
            PatternMatcher::Glob(glob_set) => glob_set.is_match(path),
        }
    }
}


/// Build a GlobSet from patterns using cached compilation
fn build_glob_set(patterns: &[String], case_sensitive: bool) -> Result<GlobSet> {
    let mut builder = GlobSetBuilder::new();
    
    for pattern in patterns {
        // Get cached pattern compilation (warming the cache)
        let _cached_entry = pattern_cache::PATTERN_CACHE.get_or_compile(pattern, case_sensitive)?;
        
        // Extract the first glob from the cached GlobSet and add it to our builder
        // Since each cached entry contains a single pattern, we can rebuild it here
        let adjusted_pattern = if !pattern.contains('/') && !pattern.contains('\\') {
            format!("**/{}", pattern)
        } else {
            pattern.clone()
        };
        
        let glob = globset::GlobBuilder::new(&adjusted_pattern)
            .case_insensitive(!case_sensitive)
            .build()?;
        builder.add(glob);
    }
    
    Ok(builder.build()?)
}

/// Check if a directory entry should be included based on filters
fn should_include_entry(
    entry: &DirEntry,
    pattern_matcher: &Option<PatternMatcher>,
    exclude_set: &Option<GlobSet>,
    regex_matcher: &Option<regex::Regex>,
    file_type_filter: Option<FileType>,
    extensions: &Option<Vec<String>>,
    min_size: Option<u64>,
    max_size: Option<u64>,
    mtime_after: Option<f64>,
    mtime_before: Option<f64>,
    atime_after: Option<f64>,
    atime_before: Option<f64>,
    ctime_after: Option<f64>,
    ctime_before: Option<f64>,
) -> bool {
    let path = entry.path();
    
    // Check glob pattern
    if let Some(ref matcher) = pattern_matcher {
        if !matcher.is_match(path) {
            return false;
        }
    }
    
    // Check exclude patterns
    if let Some(ref excludes) = exclude_set {
        if excludes.is_match(path) {
            return false;
        }
    }
    
    // Check regex pattern
    if let Some(ref regex) = regex_matcher {
        if let Some(path_str) = path.to_str() {
            if !regex.is_match(path_str) {
                return false;
            }
        }
    }
    
    // Check file type
    if let Some(filter) = file_type_filter {
        let file_type = entry.file_type();
        let matches = match filter {
            FileType::File => file_type.map_or(false, |ft| ft.is_file()),
            FileType::Dir => file_type.map_or(false, |ft| ft.is_dir()),
            FileType::Symlink => file_type.map_or(false, |ft| ft.is_symlink()),
        };
        if !matches {
            return false;
        }
    }
    
    // Check extensions
    if let Some(ref exts) = extensions {
        if !exts.is_empty() {
            if let Some(ext) = path.extension() {
                if let Some(ext_str) = ext.to_str() {
                    if !exts.iter().any(|e| e == ext_str) {
                        return false;
                    }
                }
            } else {
                // No extension, don't include
                return false;
            }
        }
    }
    
    // Check file size
    if min_size.is_some() || max_size.is_some() {
        // Only check size for files
        if let Some(file_type) = entry.file_type() {
            if file_type.is_file() {
                if let Ok(metadata) = entry.metadata() {
                    let size = metadata.len();
                    
                    if let Some(min) = min_size {
                        if size < min {
                            return false;
                        }
                    }
                    
                    if let Some(max) = max_size {
                        if size > max {
                            return false;
                        }
                    }
                }
            }
        }
    }
    
    // Check modification time
    if mtime_after.is_some() || mtime_before.is_some() {
        if let Ok(metadata) = entry.metadata() {
            if let Ok(modified) = metadata.modified() {
                if let Ok(duration) = modified.duration_since(SystemTime::UNIX_EPOCH) {
                    let mtime = duration.as_secs_f64();
                    
                    if let Some(after) = mtime_after {
                        if mtime < after {
                            return false;
                        }
                    }
                    
                    if let Some(before) = mtime_before {
                        if mtime > before {
                            return false;
                        }
                    }
                }
            }
        }
    }
    
    // Check access time
    if atime_after.is_some() || atime_before.is_some() {
        if let Ok(metadata) = entry.metadata() {
            if let Ok(accessed) = metadata.accessed() {
                if let Ok(duration) = accessed.duration_since(SystemTime::UNIX_EPOCH) {
                    let atime = duration.as_secs_f64();
                    
                    if let Some(after) = atime_after {
                        if atime < after {
                            return false;
                        }
                    }
                    
                    if let Some(before) = atime_before {
                        if atime > before {
                            return false;
                        }
                    }
                }
            }
        }
    }
    
    // Check creation time
    if ctime_after.is_some() || ctime_before.is_some() {
        if let Ok(metadata) = entry.metadata() {
            if let Ok(created) = metadata.created() {
                if let Ok(duration) = created.duration_since(SystemTime::UNIX_EPOCH) {
                    let ctime = duration.as_secs_f64();
                    
                    if let Some(after) = ctime_after {
                        if ctime < after {
                            return false;
                        }
                    }
                    
                    if let Some(before) = ctime_before {
                        if ctime > before {
                            return false;
                        }
                    }
                }
            }
        }
    }
    
    true
}

/// Search file content using grep functionality
fn search_file_content(
    tx: &crossbeam_channel::Sender<FindResult>,
    entry: &DirEntry,
    content_matcher: &RegexMatcher,
) -> Result<()> {
    let path = entry.path();
    
    // Open the file
    let file = match File::open(path) {
        Ok(f) => f,
        Err(e) => {
            let _ = tx.send(FindResult::Error(format!("Failed to open {}: {}", path.display(), e)));
            return Ok(());
        }
    };
    
    // Create searcher (buffer size optimization deferred - API doesn't support it directly)
    let mut searcher = Searcher::new();
    
    // Create sink for collecting results (zero-copy: convert path to string once)
    let mut sink = SearchSink::new(path.to_string_lossy().into_owned());
    
    // Search the file content
    match searcher.search_file(content_matcher, &file, &mut sink) {
        Ok(_) => {
            // Send all collected results
            for result in sink.into_results() {
                let _ = tx.send(FindResult::Search(result));
            }
        }
        Err(e) => {
            let _ = tx.send(FindResult::Error(format!("Search error in {}: {}", path.display(), e)));
        }
    }
    
    Ok(())
}