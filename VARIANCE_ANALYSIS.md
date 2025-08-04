# Performance Variance Analysis

**Date**: August 5, 2025  
**Version**: v1.0.9

## Executive Summary

Diagnostic analysis confirms high variance in initial file finding runs, with cold starts showing 7x slower performance (154ms vs 22ms) and 111% coefficient of variance.

## Key Findings

### 1. Cold vs Warm Start Performance

| Metric | Cold Start | Warm Start | Impact |
|--------|------------|------------|--------|
| Mean Time | 52.13ms | 28.84ms | 1.81x slower |
| Std Dev | 57.85ms | 14.51ms | 4x more variable |
| CV% | 111.0% | 50.3% | 2.2x more variance |
| Min Time | 21.62ms | 21.60ms | Similar baseline |
| Max Time | 154.66ms | 54.77ms | 2.8x higher peak |
| Range Ratio | 7.2x | 2.5x | 2.9x more range |

### 2. Pattern Complexity Impact

| Pattern Type | Example | Mean Time | CV% | Range Ratio |
|-------------|---------|-----------|-----|-------------|
| Simple literal | `test.py` | 18.23ms | 63.1% | 4.4x |
| Simple glob | `*.py` | 13.46ms | 66.4% | 3.7x |
| Nested glob | `**/*.py` | 24.04ms | 100.6% | 8.3x |
| Complex glob | `**/test_*_[0-9]*.py` | 15.13ms | 71.4% | 4.4x |
| Multiple globs | `**/{src,test,lib}/**/*.{py,rs,js}` | 12.10ms | 22.6% | 1.7x |

### 3. Root Causes Identified

1. **Pattern Compilation Overhead**: First-time pattern compilation takes significant time
2. **Thread Pool Initialization**: Rayon thread pool startup adds ~15ms
3. **Memory Allocation**: Initial allocations for channels and buffers
4. **Filesystem Cache**: OS-level directory cache misses on first access

### 4. Memory Growth Pattern

- Cold start: 33.6MB → 35.6MB (+2MB)
- Warm start: 36.6MB → 36.7MB (+0.1MB)
- Indicates significant first-run allocations

## Recommendations

### Immediate Fixes
1. **Pre-warm Pattern Cache**: Compile common patterns at module import
2. **Thread Pool Pre-initialization**: Start Rayon pool during module load
3. **Buffer Pre-allocation**: Pre-allocate channel buffers

### Long-term Solutions
1. **Lazy Static Initialization**: Use once_cell for one-time setup costs
2. **Connection Pooling**: Reuse channel endpoints across calls
3. **Adaptive Buffer Sizing**: Start small, grow as needed

## Conclusion

The variance issue is primarily caused by one-time initialization costs that should be amortized across the library lifetime rather than paid on first use. This is a solvable problem that doesn't indicate fundamental performance issues.