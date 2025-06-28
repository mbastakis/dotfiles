# Performance Guide

This guide covers the performance optimization features and best practices for the dotfiles TUI manager.

## Overview

The dotfiles TUI manager includes comprehensive performance optimization features:

- **Object Pooling**: Reduces allocations for frequently used objects
- **Memory Monitoring**: Real-time memory usage tracking and profiling
- **String Optimization**: Efficient string operations with reduced allocations
- **Caching System**: Multi-level caching for expensive operations
- **Benchmarking**: Performance testing and profiling tools

## Performance Features

### Object Pooling

The `internal/perf/pool.go` module provides object pools for common allocations:

```go
// String buffer pooling
sb := perf.GetStringBuffer()
sb.WriteString("Hello, World!")
result := sb.String()
perf.PutStringBuffer(sb) // Return to pool

// Slice pooling
strings := perf.StringSlicePool.Get()
*strings = append(*strings, "item1", "item2")
perf.StringSlicePool.Put(strings)
```

**Available Pools:**
- `StringBuffer`: For building strings efficiently
- `StatusResult`: For caching tool status results
- `ViewCache`: For caching rendered views
- `StringSlicePool`: For string slice operations
- `IntSlicePool`: For integer slice operations

### Memory Monitoring

Monitor memory usage and performance metrics in real-time:

```go
// Start global monitoring
ctx := context.Background()
perf.StartGlobalMonitor(ctx)
defer perf.StopGlobalMonitor()

// Record operations
op := perf.StartGlobalTimedOperation("theme_load")
// ... perform operation ...
op.Finish()

// Get current stats
monitor := perf.GetGlobalMonitor()
fmt.Println(monitor.GetMemoryUsageString())
```

**Monitoring Features:**
- Memory allocation tracking
- Garbage collection statistics
- Operation timing and counts
- Cache hit/miss ratios
- Goroutine count monitoring

### String Optimization

Use optimized string operations to reduce allocations:

```go
// Efficient string building
sb := perf.NewStringBuilder()
defer sb.Release()
sb.WriteString("Hello")
sb.WriteString(" World")
result := sb.String()

// Optimized string joining
result := perf.StringJoin(", ", "one", "two", "three")

// Efficient string replacement
result := perf.StringReplace(text, "old", "new", -1)
```

### Caching System

Multi-level caching for expensive operations:

```go
// Basic cache usage
cache := perf.NewCache(1000, 5*time.Minute)
cache.Set("key", "value")
if value, exists := cache.Get("key"); exists {
    // Use cached value
}

// Cache with computation
value, err := cache.GetOrSet("expensive_key", func() (interface{}, error) {
    // Expensive computation here
    return computeExpensiveValue(), nil
})

// Global caches are available
perf.StatusCache.Set("tool_status", status)
perf.ViewCache.Set("main_view", renderedView)
```

**Available Global Caches:**
- `DefaultCache`: General purpose (1000 items, 5min TTL)
- `StatusCache`: Tool status results (100 items, 30sec TTL)
- `ViewCache`: Rendered views (50 items, 1min TTL)
- `ConfigCache`: Configuration data (20 items, 10min TTL)
- `ThemeCache`: Theme data (10 items, 15min TTL)

### Profiling

Automatic and manual profiling capabilities:

```go
// Manual profiling
profiler := perf.NewProfiler("./profiles")
profiler.Start()
// ... run application ...
profiler.Stop()

// Automatic profiling with conditions
autoProfiler := perf.NewAutoProfiler("./profiles", 10*time.Second)
autoProfiler.AddCondition(perf.HighMemoryCondition(100 * 1024 * 1024))
autoProfiler.AddCondition(perf.SlowOperationCondition("theme_load", 100*time.Millisecond))
autoProfiler.Start(ctx)
```

## Performance Best Practices

### 1. Use Object Pools

Always use object pools for frequently allocated objects:

```go
// Good: Use pooled buffer
sb := perf.GetStringBuffer()
defer perf.PutStringBuffer(sb)

// Bad: Direct allocation
sb := &bytes.Buffer{}
```

### 2. Cache Expensive Operations

Cache results of expensive computations:

```go
// Good: Cache theme rendering
themeKey := fmt.Sprintf("theme_%s_%dx%d", name, width, height)
if cached, exists := perf.ViewCache.Get(themeKey); exists {
    return cached.(string)
}
result := renderTheme(name, width, height)
perf.ViewCache.Set(themeKey, result)
return result
```

### 3. Monitor Performance

Use timing and monitoring for critical paths:

```go
func loadConfiguration() error {
    op := perf.StartGlobalTimedOperation("config_load")
    defer op.Finish()
    
    // ... load configuration ...
    return nil
}
```

### 4. Optimize String Operations

Use efficient string operations:

```go
// Good: Use StringBuilder for multiple concatenations
sb := perf.NewStringBuilder()
defer sb.Release()
for _, item := range items {
    sb.WriteString(item)
    sb.WriteString("\n")
}

// Bad: String concatenation in loop
var result string
for _, item := range items {
    result += item + "\n"
}
```

### 5. Batch Operations

Batch operations to reduce overhead:

```go
// Good: Batch cache operations
keys := []string{"key1", "key2", "key3"}
values := make([]interface{}, len(keys))
for i, key := range keys {
    if value, exists := cache.Get(key); exists {
        values[i] = value
    }
}

// Process all values at once
processBatch(values)
```

## Benchmarking

Run performance benchmarks to measure improvements:

```bash
# Run all benchmarks
go test -bench=. ./internal/perf/

# Run specific benchmark
go test -bench=BenchmarkStringBuilder ./internal/perf/

# Run with memory allocation stats
go test -bench=. -benchmem ./internal/perf/

# Run stress test
go test -run=TestStress ./internal/perf/
```

**Benchmark Categories:**
- String operations (building, joining, replacing)
- Cache operations (get, set, concurrent access)
- Object pool performance
- Memory allocation patterns
- Concurrent access patterns

## Memory Optimization

### Garbage Collection Tuning

Monitor GC behavior and tune if necessary:

```go
// Check GC stats
stats := perf.GetGlobalMonitor().GetCurrentMemoryStats()
fmt.Printf("GC cycles: %d, Pause time: %d ns\n", 
    stats.NumGC, stats.PauseTotalNs)

// Force GC if needed (rarely necessary)
perf.GetGlobalMonitor().ForceGC()
```

### Memory Leak Detection

Use profiling to detect memory leaks:

```bash
# Generate memory profile
go tool pprof http://localhost:6060/debug/pprof/heap

# Analyze profile
(pprof) top
(pprof) list functionName
(pprof) web
```

## Performance Metrics

Key metrics to monitor:

### Memory Metrics
- **Alloc**: Currently allocated bytes
- **TotalAlloc**: Total bytes allocated over time
- **Sys**: Bytes obtained from system
- **NumGC**: Number of GC cycles
- **HeapInuse**: Bytes in in-use heap spans

### Operation Metrics
- **Operation Count**: Number of times each operation was performed
- **Average Latency**: Average time per operation
- **Cache Hit Ratio**: Percentage of cache hits vs. misses

### System Metrics
- **Goroutine Count**: Number of active goroutines
- **CPU Usage**: Percentage of CPU time used
- **Memory Growth Rate**: Rate of memory allocation

## Troubleshooting Performance Issues

### High Memory Usage

1. Check for memory leaks using profiling
2. Verify caches have appropriate size limits
3. Ensure objects are returned to pools
4. Monitor GC frequency and pause times

### Slow Operations

1. Add timing measurements to identify bottlenecks
2. Check cache hit ratios for expensive operations
3. Profile CPU usage to find hot spots
4. Consider parallelizing independent operations

### High CPU Usage

1. Profile CPU usage to identify expensive functions
2. Check for inefficient algorithms or loops
3. Verify string operations are optimized
4. Look for excessive garbage collection

## Configuration

Configure performance features through environment variables:

```bash
# Enable performance monitoring
export DOTFILES_PERF_MONITORING=true

# Set cache sizes
export DOTFILES_CACHE_SIZE=2000
export DOTFILES_VIEW_CACHE_SIZE=100

# Enable profiling
export DOTFILES_PROFILE_ENABLED=true
export DOTFILES_PROFILE_DIR=./profiles

# Set monitoring interval
export DOTFILES_MONITOR_INTERVAL=5s
```

## Integration with TUI

The performance system integrates seamlessly with the TUI:

```go
// Theme manager with caching
func (tm *ThemeManager) GetStyles() *Styles {
    cacheKey := fmt.Sprintf("styles_%s", tm.currentTheme)
    if cached, exists := perf.ThemeCache.Get(cacheKey); exists {
        return cached.(*Styles)
    }
    
    styles := tm.generateStyles()
    perf.ThemeCache.Set(cacheKey, styles)
    return styles
}

// View rendering with performance monitoring
func (m *Model) View() string {
    op := perf.StartGlobalTimedOperation("view_render")
    defer op.Finish()
    
    // Use pooled string builder
    sb := perf.GetStringBuilder()
    defer perf.PutStringBuffer(sb.buf)
    
    // Render view components
    sb.WriteString(m.renderHeader())
    sb.WriteString(m.renderContent())
    sb.WriteString(m.renderFooter())
    
    return sb.String()
}
```

This performance system ensures the dotfiles TUI manager runs efficiently even with large configurations and frequent operations.