package perf

import (
	"context"
	"fmt"
	"runtime"
	"sync"
	"time"
)

// MemoryStats represents memory usage statistics
type MemoryStats struct {
	// Memory allocations
	Alloc        uint64 // bytes allocated and not yet freed
	TotalAlloc   uint64 // bytes allocated (even if freed)
	Sys          uint64 // bytes obtained from system
	NumGC        uint32 // number of garbage collections
	PauseTotalNs uint64 // total GC pause time

	// Heap statistics
	HeapAlloc   uint64 // bytes allocated and not yet freed (same as Alloc above)
	HeapSys     uint64 // bytes obtained from system
	HeapInuse   uint64 // bytes in in-use spans
	HeapReleased uint64 // bytes released to OS

	// Goroutine count
	NumGoroutine int

	// Timestamp
	Timestamp time.Time
}

// PerformanceMetrics holds various performance metrics
type PerformanceMetrics struct {
	Memory           MemoryStats
	OperationCounts  map[string]int64
	OperationLatency map[string]time.Duration
	CacheHitRatio    map[string]float64
}

// Monitor provides memory and performance monitoring capabilities
type Monitor struct {
	mu               sync.RWMutex
	enabled          bool
	interval         time.Duration
	memoryHistory    []MemoryStats
	maxHistorySize   int
	operationCounts  map[string]int64
	operationLatency map[string]time.Duration
	cacheStats       map[string]*MonitorCacheStats
	stopCh           chan struct{}
	doneCh           chan struct{}
}

// MonitorCacheStats tracks cache hit/miss statistics
type MonitorCacheStats struct {
	Hits   int64
	Misses int64
}

// HitRatio returns the cache hit ratio
func (cs *MonitorCacheStats) HitRatio() float64 {
	total := cs.Hits + cs.Misses
	if total == 0 {
		return 0
	}
	return float64(cs.Hits) / float64(total)
}

// NewMonitor creates a new performance monitor
func NewMonitor(interval time.Duration, maxHistorySize int) *Monitor {
	return &Monitor{
		enabled:          false,
		interval:         interval,
		memoryHistory:    make([]MemoryStats, 0, maxHistorySize),
		maxHistorySize:   maxHistorySize,
		operationCounts:  make(map[string]int64),
		operationLatency: make(map[string]time.Duration),
		cacheStats:       make(map[string]*MonitorCacheStats),
		stopCh:           make(chan struct{}),
		doneCh:           make(chan struct{}),
	}
}

// Start begins monitoring
func (m *Monitor) Start(ctx context.Context) {
	m.mu.Lock()
	if m.enabled {
		m.mu.Unlock()
		return
	}
	m.enabled = true
	m.mu.Unlock()

	go m.monitorLoop(ctx)
}

// Stop stops monitoring
func (m *Monitor) Stop() {
	m.mu.Lock()
	if !m.enabled {
		m.mu.Unlock()
		return
	}
	m.enabled = false
	m.mu.Unlock()

	close(m.stopCh)
	<-m.doneCh
}

// monitorLoop runs the monitoring loop
func (m *Monitor) monitorLoop(ctx context.Context) {
	defer close(m.doneCh)

	ticker := time.NewTicker(m.interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-m.stopCh:
			return
		case <-ticker.C:
			m.collectMemoryStats()
		}
	}
}

// collectMemoryStats collects current memory statistics
func (m *Monitor) collectMemoryStats() {
	var ms runtime.MemStats
	runtime.ReadMemStats(&ms)

	stats := MemoryStats{
		Alloc:        ms.Alloc,
		TotalAlloc:   ms.TotalAlloc,
		Sys:          ms.Sys,
		NumGC:        ms.NumGC,
		PauseTotalNs: ms.PauseTotalNs,
		HeapAlloc:    ms.HeapAlloc,
		HeapSys:      ms.HeapSys,
		HeapInuse:    ms.HeapInuse,
		HeapReleased: ms.HeapReleased,
		NumGoroutine: runtime.NumGoroutine(),
		Timestamp:    time.Now(),
	}

	m.mu.Lock()
	m.memoryHistory = append(m.memoryHistory, stats)
	if len(m.memoryHistory) > m.maxHistorySize {
		// Remove oldest entry
		copy(m.memoryHistory, m.memoryHistory[1:])
		m.memoryHistory = m.memoryHistory[:m.maxHistorySize]
	}
	m.mu.Unlock()
}

// GetCurrentMemoryStats returns the most recent memory statistics
func (m *Monitor) GetCurrentMemoryStats() MemoryStats {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if len(m.memoryHistory) == 0 {
		// Collect fresh stats if none available
		m.mu.RUnlock()
		m.collectMemoryStats()
		m.mu.RLock()
	}

	if len(m.memoryHistory) > 0 {
		return m.memoryHistory[len(m.memoryHistory)-1]
	}

	return MemoryStats{}
}

// GetMemoryHistory returns the memory statistics history
func (m *Monitor) GetMemoryHistory() []MemoryStats {
	m.mu.RLock()
	defer m.mu.RUnlock()

	// Return a copy to avoid race conditions
	history := make([]MemoryStats, len(m.memoryHistory))
	copy(history, m.memoryHistory)
	return history
}

// RecordOperation records an operation execution
func (m *Monitor) RecordOperation(operation string, duration time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.operationCounts[operation]++
	
	// Update average latency
	if existing, exists := m.operationLatency[operation]; exists {
		// Simple moving average
		count := m.operationCounts[operation]
		m.operationLatency[operation] = (existing*time.Duration(count-1) + duration) / time.Duration(count)
	} else {
		m.operationLatency[operation] = duration
	}
}

// RecordCacheHit records a cache hit
func (m *Monitor) RecordCacheHit(cacheName string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if stats, exists := m.cacheStats[cacheName]; exists {
		stats.Hits++
	} else {
		m.cacheStats[cacheName] = &MonitorCacheStats{Hits: 1, Misses: 0}
	}
}

// RecordCacheMiss records a cache miss
func (m *Monitor) RecordCacheMiss(cacheName string) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if stats, exists := m.cacheStats[cacheName]; exists {
		stats.Misses++
	} else {
		m.cacheStats[cacheName] = &MonitorCacheStats{Hits: 0, Misses: 1}
	}
}

// GetPerformanceMetrics returns current performance metrics
func (m *Monitor) GetPerformanceMetrics() PerformanceMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()

	// Copy operation counts and latency
	opCounts := make(map[string]int64)
	for k, v := range m.operationCounts {
		opCounts[k] = v
	}

	opLatency := make(map[string]time.Duration)
	for k, v := range m.operationLatency {
		opLatency[k] = v
	}

	// Copy cache hit ratios
	cacheRatios := make(map[string]float64)
	for name, stats := range m.cacheStats {
		cacheRatios[name] = stats.HitRatio()
	}

	return PerformanceMetrics{
		Memory:           m.GetCurrentMemoryStats(),
		OperationCounts:  opCounts,
		OperationLatency: opLatency,
		CacheHitRatio:    cacheRatios,
	}
}

// ForceGC forces garbage collection and waits for it to complete
func (m *Monitor) ForceGC() {
	runtime.GC()
}

// GetMemoryUsageString returns a human-readable memory usage string
func (m *Monitor) GetMemoryUsageString() string {
	stats := m.GetCurrentMemoryStats()
	return fmt.Sprintf("Alloc: %s, Sys: %s, NumGC: %d, Goroutines: %d",
		formatBytes(stats.Alloc),
		formatBytes(stats.Sys),
		stats.NumGC,
		stats.NumGoroutine,
	)
}

// formatBytes formats bytes into human-readable format
func formatBytes(bytes uint64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := uint64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(bytes)/float64(div), "KMGTPE"[exp])
}

// Global monitor instance
var globalMonitor = NewMonitor(5*time.Second, 100)

// StartGlobalMonitor starts the global performance monitor
func StartGlobalMonitor(ctx context.Context) {
	globalMonitor.Start(ctx)
}

// StopGlobalMonitor stops the global performance monitor
func StopGlobalMonitor() {
	globalMonitor.Stop()
}

// GetGlobalMonitor returns the global monitor instance
func GetGlobalMonitor() *Monitor {
	return globalMonitor
}

// TimedOperation is a helper for timing operations
type TimedOperation struct {
	name    string
	start   time.Time
	monitor *Monitor
}

// StartTimedOperation starts timing an operation
func (m *Monitor) StartTimedOperation(name string) *TimedOperation {
	return &TimedOperation{
		name:    name,
		start:   time.Now(),
		monitor: m,
	}
}

// Finish finishes timing the operation and records it
func (to *TimedOperation) Finish() {
	duration := time.Since(to.start)
	to.monitor.RecordOperation(to.name, duration)
}

// StartGlobalTimedOperation starts timing an operation using the global monitor
func StartGlobalTimedOperation(name string) *TimedOperation {
	return globalMonitor.StartTimedOperation(name)
}