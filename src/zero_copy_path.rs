// this_file: src/zero_copy_path.rs
//! Zero-copy path handling optimizations for vexy_glob
//!
//! This module provides optimized path handling to reduce allocations
//! during file traversal and result collection.

use std::borrow::Cow;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use std::cell::RefCell;
use std::collections::HashMap;

/// String interner for path components to reduce repeated allocations
pub struct PathInterner {
    cache: RefCell<HashMap<String, Arc<str>>>,
}

impl PathInterner {
    pub fn new() -> Self {
        Self {
            cache: RefCell::new(HashMap::with_capacity(1024)),
        }
    }

    /// Intern a string, returning a shared reference
    pub fn intern(&self, s: &str) -> Arc<str> {
        let mut cache = self.cache.borrow_mut();
        if let Some(interned) = cache.get(s) {
            Arc::clone(interned)
        } else {
            let interned = Arc::from(s);
            cache.insert(s.to_string(), Arc::clone(&interned));
            interned
        }
    }

    /// Get cache statistics for optimization tuning
    pub fn stats(&self) -> (usize, usize) {
        let cache = self.cache.borrow();
        let size = cache.len();
        let bytes: usize = cache.iter()
            .map(|(k, v)| k.len() + v.len())
            .sum();
        (size, bytes)
    }
}

/// Optimized path representation that minimizes allocations
#[derive(Debug, Clone)]
pub enum OptimizedPath<'a> {
    /// Borrowed path (zero allocation)
    Borrowed(&'a Path),
    /// Owned path (only when necessary)
    Owned(PathBuf),
    /// Interned components for deeply nested paths
    Interned {
        components: Vec<Arc<str>>,
        is_absolute: bool,
    },
}

impl<'a> OptimizedPath<'a> {
    /// Create from a borrowed path
    pub fn from_path(path: &'a Path) -> Self {
        OptimizedPath::Borrowed(path)
    }

    /// Create an owned variant when borrowing isn't possible
    pub fn to_owned(&self) -> OptimizedPath<'static> {
        match self {
            OptimizedPath::Borrowed(p) => OptimizedPath::Owned(p.to_path_buf()),
            OptimizedPath::Owned(p) => OptimizedPath::Owned(p.clone()),
            OptimizedPath::Interned { components, is_absolute } => {
                OptimizedPath::Interned {
                    components: components.clone(),
                    is_absolute: *is_absolute,
                }
            }
        }
    }

    /// Get as a Path reference
    pub fn as_path(&self) -> Cow<'_, Path> {
        match self {
            OptimizedPath::Borrowed(p) => Cow::Borrowed(p),
            OptimizedPath::Owned(p) => Cow::Borrowed(p.as_path()),
            OptimizedPath::Interned { components, is_absolute } => {
                // Reconstruct path from interned components
                let mut path = PathBuf::new();
                if *is_absolute {
                    path.push("/");
                }
                for component in components {
                    path.push(component.as_ref());
                }
                Cow::Owned(path)
            }
        }
    }

    /// Convert to string with minimal allocation
    pub fn to_str_cow(&self) -> Cow<'_, str> {
        match self {
            OptimizedPath::Borrowed(p) => p.to_string_lossy(),
            OptimizedPath::Owned(p) => p.to_string_lossy(),
            OptimizedPath::Interned { components, is_absolute } => {
                // Build string from interned components
                let separator = std::path::MAIN_SEPARATOR;
                let mut result = String::new();
                if *is_absolute {
                    result.push(separator);
                }
                for (i, component) in components.iter().enumerate() {
                    if i > 0 {
                        result.push(separator);
                    }
                    result.push_str(component);
                }
                Cow::Owned(result)
            }
        }
    }

    /// Create interned version for deep paths
    pub fn intern_deep_path(path: &Path, interner: &PathInterner, depth_threshold: usize) -> Self {
        let components: Vec<_> = path.components().collect();
        
        if components.len() < depth_threshold {
            // Not deep enough to benefit from interning
            return OptimizedPath::Owned(path.to_path_buf());
        }

        let is_absolute = path.is_absolute();
        let mut interned_components = Vec::with_capacity(components.len());

        for component in components {
            if let Some(s) = component.as_os_str().to_str() {
                interned_components.push(interner.intern(s));
            }
        }

        OptimizedPath::Interned {
            components: interned_components,
            is_absolute,
        }
    }
}

/// Pool for reusing PathBuf allocations
pub struct PathBufPool {
    pool: RefCell<Vec<PathBuf>>,
    max_size: usize,
}

impl PathBufPool {
    pub fn new(max_size: usize) -> Self {
        Self {
            pool: RefCell::new(Vec::with_capacity(max_size)),
            max_size,
        }
    }

    /// Get a PathBuf from the pool or create a new one
    pub fn get(&self) -> PathBuf {
        self.pool.borrow_mut().pop().unwrap_or_else(PathBuf::new)
    }

    /// Return a PathBuf to the pool for reuse
    pub fn put(&self, mut path: PathBuf) {
        let mut pool = self.pool.borrow_mut();
        if pool.len() < self.max_size {
            path.clear();
            pool.push(path);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_path_interner() {
        let interner = PathInterner::new();
        
        let s1 = interner.intern("components");
        let s2 = interner.intern("components");
        
        // Should return the same Arc
        assert!(Arc::ptr_eq(&s1, &s2));
        
        let (size, _) = interner.stats();
        assert_eq!(size, 1);
    }

    #[test]
    fn test_optimized_path() {
        let path = Path::new("/home/user/documents/file.txt");
        let opt_path = OptimizedPath::from_path(path);
        
        match opt_path {
            OptimizedPath::Borrowed(p) => assert_eq!(p, path),
            _ => panic!("Expected borrowed path"),
        }
        
        let cow_str = opt_path.to_str_cow();
        assert_eq!(cow_str.as_ref(), "/home/user/documents/file.txt");
    }

    #[test]
    fn test_path_buf_pool() {
        let pool = PathBufPool::new(10);
        
        let path1 = pool.get();
        assert_eq!(path1, PathBuf::new());
        
        pool.put(path1);
        
        let path2 = pool.get();
        // Should reuse the same allocation
        assert_eq!(path2, PathBuf::new());
    }
}