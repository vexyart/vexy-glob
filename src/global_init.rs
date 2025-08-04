// this_file: src/global_init.rs
//
// Global initialization module to reduce cold start performance variance
// Pre-initializes thread pools, buffers, and other expensive one-time setup costs

use once_cell::sync::Lazy;
use std::sync::Arc;
use crossbeam_channel::{bounded, Receiver, Sender};
use anyhow::Result;

/// Pre-initialized thread pool configuration
static THREAD_POOL_INIT: Lazy<()> = Lazy::new(|| {
    // Force Rayon thread pool initialization by running a dummy parallel operation
    use rayon::prelude::*;
    
    // Create a small workload to initialize the thread pool
    let dummy_data: Vec<i32> = (0..100).collect();
    let _sum: i32 = dummy_data.par_iter().sum();
    
    // This ensures the Rayon global thread pool is fully initialized
    // and ready for use in subsequent operations
});

/// Pre-allocated channel pool for reducing allocation overhead
#[derive(Clone)]
pub struct ChannelPool {
    small_channels: Arc<Vec<(Sender<crate::FindResult>, Receiver<crate::FindResult>)>>,
    medium_channels: Arc<Vec<(Sender<crate::FindResult>, Receiver<crate::FindResult>)>>,
    large_channels: Arc<Vec<(Sender<crate::FindResult>, Receiver<crate::FindResult>)>>,
}

impl ChannelPool {
    fn new() -> Self {
        let mut small_channels = Vec::new();
        let mut medium_channels = Vec::new();
        let mut large_channels = Vec::new();
        
        // Pre-allocate channels of different sizes
        // Small: for content search (500 capacity)
        for _ in 0..4 {
            let (tx, rx) = bounded(500);
            small_channels.push((tx, rx));
        }
        
        // Medium: for standard file finding (5000 capacity)
        for _ in 0..4 {
            let (tx, rx) = bounded(5000);
            medium_channels.push((tx, rx));
        }
        
        // Large: for sorting operations (10000 capacity)
        for _ in 0..2 {
            let (tx, rx) = bounded(10000);
            large_channels.push((tx, rx));
        }
        
        Self {
            small_channels: Arc::new(small_channels),
            medium_channels: Arc::new(medium_channels),
            large_channels: Arc::new(large_channels),
        }
    }
    
    /// Get a pre-allocated channel based on workload type
    pub fn get_channel(&self, capacity: usize) -> (Sender<crate::FindResult>, Receiver<crate::FindResult>) {
        // For now, always create a new channel with the requested capacity
        // TODO: Implement actual pooling logic with channel reuse
        bounded(capacity)
    }
    
    /// Get statistics about the channel pool
    pub fn stats(&self) -> ChannelPoolStats {
        ChannelPoolStats {
            small_channels: self.small_channels.len(),
            medium_channels: self.medium_channels.len(),
            large_channels: self.large_channels.len(),
        }
    }
}

/// Channel pool statistics
pub struct ChannelPoolStats {
    pub small_channels: usize,
    pub medium_channels: usize,
    pub large_channels: usize,
}

/// Global channel pool instance
static CHANNEL_POOL: Lazy<ChannelPool> = Lazy::new(ChannelPool::new);

/// Global initialization function that forces all lazy statics to initialize
/// This should be called during module import to pay all one-time costs upfront
pub fn ensure_global_init() -> Result<()> {
    // Force thread pool initialization
    Lazy::force(&THREAD_POOL_INIT);
    
    // Force pattern cache initialization
    let _pattern_stats = crate::pattern_cache::PATTERN_CACHE.stats();
    
    // Force channel pool initialization
    let _channel_stats = CHANNEL_POOL.stats();
    
    // Additional warmup: compile a test pattern to ensure all code paths are JIT-compiled
    let _test_pattern = crate::pattern_cache::PATTERN_CACHE.get_or_compile("**/*.test", false)?;
    
    Ok(())
}

/// Get the global channel pool
pub fn get_channel_pool() -> &'static ChannelPool {
    &CHANNEL_POOL
}

/// Performance metrics for global initialization
#[derive(Debug)]
pub struct InitMetrics {
    pub thread_pool_ready: bool,
    pub pattern_cache_size: usize,
    pub channel_pool_size: usize,
}

/// Get current initialization metrics
pub fn get_init_metrics() -> InitMetrics {
    let pattern_stats = crate::pattern_cache::PATTERN_CACHE.stats();
    let channel_stats = CHANNEL_POOL.stats();
    
    InitMetrics {
        thread_pool_ready: Lazy::get(&THREAD_POOL_INIT).is_some(),
        pattern_cache_size: pattern_stats.size,
        channel_pool_size: channel_stats.small_channels + channel_stats.medium_channels + channel_stats.large_channels,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_global_init() {
        let result = ensure_global_init();
        assert!(result.is_ok());
        
        let metrics = get_init_metrics();
        assert!(metrics.thread_pool_ready);
        assert!(metrics.pattern_cache_size > 0);
        assert!(metrics.channel_pool_size > 0);
    }
    
    #[test]
    fn test_channel_pool() {
        let pool = get_channel_pool();
        let (tx, rx) = pool.get_channel(1000);
        
        // Test that channel works
        tx.send(crate::FindResult::Path("test".to_string())).unwrap();
        let result = rx.recv().unwrap();
        
        match result {
            crate::FindResult::Path(path) => assert_eq!(path, "test"),
            _ => panic!("Expected Path result"),
        }
    }
}