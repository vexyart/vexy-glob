// this_file: src/pattern_cache.rs

use std::sync::{Arc, RwLock};
use std::collections::HashMap;
use anyhow::Result;
use globset::{GlobSet, GlobSetBuilder};
use once_cell::sync::Lazy;

/// Maximum number of patterns to cache
const CACHE_SIZE: usize = 1000;

/// Common file patterns to pre-compile at startup
const COMMON_PATTERNS: &[&str] = &[
    // Programming languages
    "*.py", "*.rs", "*.js", "*.ts", "*.jsx", "*.tsx",
    "*.c", "*.cpp", "*.h", "*.hpp", "*.java", "*.go",
    "*.rb", "*.php", "*.swift", "*.kt", "*.scala",
    
    // Data files
    "*.json", "*.yaml", "*.yml", "*.toml", "*.xml",
    "*.csv", "*.txt", "*.md", "*.rst",
    
    // Web assets
    "*.html", "*.css", "*.scss", "*.sass", "*.less",
    
    // Images
    "*.jpg", "*.jpeg", "*.png", "*.gif", "*.svg", "*.webp",
    
    // Common patterns
    "**/*.py", "**/*.rs", "**/*.js", "**/*.ts",
    "**/node_modules/**", "**/.git/**", "**/target/**",
    "**/__pycache__/**", "**/*.pyc", "**/.venv/**",
];

/// Cache entry containing compiled pattern
#[derive(Clone)]
pub struct CacheEntry {
    pub pattern: String,
    pub glob_set: Arc<GlobSet>,
    pub is_literal: bool,
    pub case_sensitive: bool,
}

/// LRU cache for compiled patterns
pub struct PatternCache {
    cache: Arc<RwLock<HashMap<CacheKey, CacheEntry>>>,
    access_order: Arc<RwLock<Vec<CacheKey>>>,
}

/// Key for cache lookup
#[derive(Hash, Eq, PartialEq, Clone)]
struct CacheKey {
    pattern: String,
    case_sensitive: bool,
}

impl PatternCache {
    /// Create a new pattern cache
    fn new() -> Self {
        let mut cache = HashMap::with_capacity(CACHE_SIZE);
        let mut access_order = Vec::with_capacity(CACHE_SIZE);
        
        // Pre-compile common patterns (case-insensitive by default)
        for &pattern in COMMON_PATTERNS {
            for case_sensitive in [true, false] {
                let key = CacheKey {
                    pattern: pattern.to_string(),
                    case_sensitive,
                };
                
                if let Ok(glob_set) = compile_pattern(pattern, case_sensitive) {
                    let entry = CacheEntry {
                        pattern: pattern.to_string(),
                        glob_set: Arc::new(glob_set),
                        is_literal: is_literal_pattern(pattern),
                        case_sensitive,
                    };
                    cache.insert(key.clone(), entry);
                    access_order.push(key);
                }
            }
        }
        
        Self {
            cache: Arc::new(RwLock::new(cache)),
            access_order: Arc::new(RwLock::new(access_order)),
        }
    }
    
    /// Get a compiled pattern from cache or compile and cache it
    pub fn get_or_compile(&self, pattern: &str, case_sensitive: bool) -> Result<CacheEntry> {
        let key = CacheKey {
            pattern: pattern.to_string(),
            case_sensitive,
        };
        
        // Try to get from cache (read lock)
        {
            let cache = self.cache.read().unwrap();
            if let Some(entry) = cache.get(&key) {
                // Update access order
                self.update_access_order(&key);
                return Ok(entry.clone());
            }
        }
        
        // Not in cache, compile it (write lock)
        let glob_set = compile_pattern(pattern, case_sensitive)?;
        let entry = CacheEntry {
            pattern: pattern.to_string(),
            glob_set: Arc::new(glob_set),
            is_literal: is_literal_pattern(pattern),
            case_sensitive,
        };
        
        // Insert into cache with LRU eviction
        {
            let mut cache = self.cache.write().unwrap();
            let mut access_order = self.access_order.write().unwrap();
            
            // Evict oldest if cache is full
            if cache.len() >= CACHE_SIZE {
                if let Some(oldest_key) = access_order.first() {
                    let oldest_key = oldest_key.clone();
                    cache.remove(&oldest_key);
                    access_order.retain(|k| k != &oldest_key);
                }
            }
            
            cache.insert(key.clone(), entry.clone());
            access_order.push(key);
        }
        
        Ok(entry)
    }
    
    /// Update access order for LRU tracking
    fn update_access_order(&self, key: &CacheKey) {
        let mut access_order = self.access_order.write().unwrap();
        access_order.retain(|k| k != key);
        access_order.push(key.clone());
    }
    
    /// Get cache statistics
    pub fn stats(&self) -> CacheStats {
        let cache = self.cache.read().unwrap();
        CacheStats {
            size: cache.len(),
            capacity: CACHE_SIZE,
            precompiled_patterns: COMMON_PATTERNS.len() * 2, // case sensitive + insensitive
        }
    }
}

/// Cache statistics
pub struct CacheStats {
    pub size: usize,
    pub capacity: usize,
    pub precompiled_patterns: usize,
}

/// Global pattern cache instance
pub static PATTERN_CACHE: Lazy<PatternCache> = Lazy::new(PatternCache::new);

/// Compile a glob pattern
fn compile_pattern(pattern: &str, case_sensitive: bool) -> Result<GlobSet> {
    // If pattern doesn't contain path separator, prepend **/ to match in any directory
    let adjusted_pattern = if !pattern.contains('/') && !pattern.contains('\\') {
        format!("**/{}", pattern)
    } else {
        pattern.to_string()
    };
    
    let glob = globset::GlobBuilder::new(&adjusted_pattern)
        .case_insensitive(!case_sensitive)
        .build()?;
    
    let mut builder = GlobSetBuilder::new();
    builder.add(glob);
    Ok(builder.build()?)
}

/// Check if a pattern is literal (no wildcards)
pub fn is_literal_pattern(pattern: &str) -> bool {
    !pattern.chars().any(|c| matches!(c, '*' | '?' | '[' | ']' | '{' | '}'))
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_pattern_cache_basic() {
        let cache = PatternCache::new();
        
        // Test getting a pre-compiled pattern
        let entry = cache.get_or_compile("*.py", false).unwrap();
        assert_eq!(entry.pattern, "*.py");
        assert!(!entry.is_literal);
        
        // Test getting a new pattern
        let entry = cache.get_or_compile("test/*.md", true).unwrap();
        assert_eq!(entry.pattern, "test/*.md");
        assert!(!entry.is_literal);
        
        // Test literal pattern detection
        let entry = cache.get_or_compile("README.md", false).unwrap();
        assert!(entry.is_literal);
    }
    
    #[test]
    fn test_cache_stats() {
        let stats = PATTERN_CACHE.stats();
        assert!(stats.size > 0); // Should have pre-compiled patterns
        assert_eq!(stats.capacity, CACHE_SIZE);
    }
}