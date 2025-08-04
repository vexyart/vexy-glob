// this_file: src/simd_string.rs

//! High-performance string operations for pattern matching.
//!
//! This module provides optimized string comparison functions. 
//! Future work will include SIMD optimizations for even better performance.

/// High-performance string comparison operations
pub struct FastStringOps;

impl FastStringOps {
    /// Fast case-insensitive string equality check
    pub fn eq_ignore_case(a: &str, b: &str) -> bool {
        a.eq_ignore_ascii_case(b)
    }
    
    /// Fast case-insensitive ends_with check
    pub fn ends_with_ignore_case(haystack: &str, needle: &str) -> bool {
        if needle.len() > haystack.len() {
            return false;
        }
        haystack[haystack.len() - needle.len()..].eq_ignore_ascii_case(needle)
    }
    
    /// Fast case-sensitive ends_with check
    pub fn ends_with(haystack: &str, needle: &str) -> bool {
        haystack.ends_with(needle)
    }
    
    /// Fast case-sensitive equality
    pub fn eq(a: &str, b: &str) -> bool {
        a == b
    }
}

/// Performance-optimized pattern matching utilities
pub struct FastPatternMatch;

impl FastPatternMatch {
    /// Optimized filename matching
    pub fn filename_equals(filename: &str, pattern: &str, case_sensitive: bool) -> bool {
        if case_sensitive {
            FastStringOps::eq(filename, pattern)
        } else {
            FastStringOps::eq_ignore_case(filename, pattern)
        }
    }
    
    /// Optimized path suffix matching
    pub fn path_ends_with(path_str: &str, pattern: &str, case_sensitive: bool) -> bool {
        if case_sensitive {
            FastStringOps::ends_with(path_str, pattern)
        } else {
            FastStringOps::ends_with_ignore_case(path_str, pattern)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_eq_ignore_case() {
        assert!(FastStringOps::eq_ignore_case("Hello", "HELLO"));
        assert!(FastStringOps::eq_ignore_case("test", "TEST"));
        assert!(!FastStringOps::eq_ignore_case("hello", "world"));
        assert!(FastStringOps::eq_ignore_case("", ""));
        
        // Test longer strings
        let long_a = "this_is_a_very_long_filename_that_should_trigger_optimization.py";
        let long_b = "THIS_IS_A_VERY_LONG_FILENAME_THAT_SHOULD_TRIGGER_OPTIMIZATION.PY";
        assert!(FastStringOps::eq_ignore_case(long_a, long_b));
    }
    
    #[test]
    fn test_ends_with_ignore_case() {
        assert!(FastStringOps::ends_with_ignore_case("test.PY", ".py"));
        assert!(FastStringOps::ends_with_ignore_case("main.RUST", ".rust"));
        assert!(!FastStringOps::ends_with_ignore_case("test.py", ".js"));
        
        // Test longer patterns
        let path = "src/very_long_filename_for_testing_acceleration.RS";
        let pattern = "testing_acceleration.rs";
        assert!(FastStringOps::ends_with_ignore_case(path, pattern));
    }
    
    #[test]
    fn test_fast_pattern_match() {
        // Case sensitive matching
        assert!(FastPatternMatch::filename_equals("test.py", "test.py", true));
        assert!(!FastPatternMatch::filename_equals("test.py", "TEST.PY", true));
        
        // Case insensitive matching
        assert!(FastPatternMatch::filename_equals("test.py", "TEST.PY", false));
        assert!(FastPatternMatch::filename_equals("Main.Rs", "main.rs", false));
        
        // Path suffix matching
        assert!(FastPatternMatch::path_ends_with("/src/main.rs", "main.rs", true));
        assert!(FastPatternMatch::path_ends_with("/SRC/MAIN.RS", "main.rs", false));
    }
}