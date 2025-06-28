package perf

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"runtime/pprof"
	"sync"
	"time"
)

// Profiler provides application profiling capabilities
type Profiler struct {
	mu           sync.Mutex
	enabled      bool
	profileDir   string
	cpuProfile   *os.File
	memProfile   *os.File
	blockProfile *os.File
	mutex        *os.File
	startTime    time.Time
}

// NewProfiler creates a new profiler instance
func NewProfiler(profileDir string) *Profiler {
	return &Profiler{
		profileDir: profileDir,
	}
}

// Start begins profiling
func (p *Profiler) Start() error {
	p.mu.Lock()
	defer p.mu.Unlock()

	if p.enabled {
		return fmt.Errorf("profiler already started")
	}

	// Create profile directory if it doesn't exist
	if err := os.MkdirAll(p.profileDir, 0755); err != nil {
		return fmt.Errorf("failed to create profile directory: %w", err)
	}

	p.startTime = time.Now()
	timestamp := p.startTime.Format("20060102_150405")

	// Start CPU profiling
	cpuFile := filepath.Join(p.profileDir, fmt.Sprintf("cpu_%s.prof", timestamp))
	var err error
	p.cpuProfile, err = os.Create(cpuFile)
	if err != nil {
		return fmt.Errorf("failed to create CPU profile: %w", err)
	}

	if err := pprof.StartCPUProfile(p.cpuProfile); err != nil {
		p.cpuProfile.Close()
		return fmt.Errorf("failed to start CPU profile: %w", err)
	}

	// Enable block and mutex profiling
	runtime.SetBlockProfileRate(1)
	runtime.SetMutexProfileFraction(1)

	p.enabled = true
	return nil
}

// Stop ends profiling and writes profile files
func (p *Profiler) Stop() error {
	p.mu.Lock()
	defer p.mu.Unlock()

	if !p.enabled {
		return fmt.Errorf("profiler not started")
	}

	timestamp := p.startTime.Format("20060102_150405")

	// Stop CPU profiling
	pprof.StopCPUProfile()
	if p.cpuProfile != nil {
		p.cpuProfile.Close()
		p.cpuProfile = nil
	}

	// Write memory profile
	memFile := filepath.Join(p.profileDir, fmt.Sprintf("mem_%s.prof", timestamp))
	p.memProfile, _ = os.Create(memFile)
	if p.memProfile != nil {
		runtime.GC() // Force GC before memory profile
		pprof.WriteHeapProfile(p.memProfile)
		p.memProfile.Close()
		p.memProfile = nil
	}

	// Write block profile
	blockFile := filepath.Join(p.profileDir, fmt.Sprintf("block_%s.prof", timestamp))
	p.blockProfile, _ = os.Create(blockFile)
	if p.blockProfile != nil {
		pprof.Lookup("block").WriteTo(p.blockProfile, 0)
		p.blockProfile.Close()
		p.blockProfile = nil
	}

	// Write mutex profile
	mutexFile := filepath.Join(p.profileDir, fmt.Sprintf("mutex_%s.prof", timestamp))
	p.mutex, _ = os.Create(mutexFile)
	if p.mutex != nil {
		pprof.Lookup("mutex").WriteTo(p.mutex, 0)
		p.mutex.Close()
		p.mutex = nil
	}

	// Write goroutine profile
	goroutineFile := filepath.Join(p.profileDir, fmt.Sprintf("goroutine_%s.prof", timestamp))
	if file, err := os.Create(goroutineFile); err == nil {
		pprof.Lookup("goroutine").WriteTo(file, 0)
		file.Close()
	}

	p.enabled = false
	return nil
}

// IsEnabled returns whether profiling is currently enabled
func (p *Profiler) IsEnabled() bool {
	p.mu.Lock()
	defer p.mu.Unlock()
	return p.enabled
}

// WriteMemoryProfile writes a memory profile snapshot
func (p *Profiler) WriteMemoryProfile(filename string) error {
	p.mu.Lock()
	defer p.mu.Unlock()

	file, err := os.Create(filename)
	if err != nil {
		return fmt.Errorf("failed to create memory profile: %w", err)
	}
	defer file.Close()

	runtime.GC() // Force GC before memory profile
	return pprof.WriteHeapProfile(file)
}

// ProfiledFunction wraps a function with profiling
func (p *Profiler) ProfiledFunction(name string, fn func()) {
	if !p.enabled {
		fn()
		return
	}

	// Add a label for this function
	pprof.Do(context.Background(), pprof.Labels("function", name), func(ctx context.Context) {
		fn()
	})
}

// AutoProfiler provides automatic profiling capabilities
type AutoProfiler struct {
	profiler    *Profiler
	monitor     *Monitor
	interval    time.Duration
	conditions  []ProfileCondition
	mu          sync.RWMutex
	lastProfile time.Time
	cooldown    time.Duration
}

// ProfileCondition defines when automatic profiling should trigger
type ProfileCondition struct {
	Name      string
	CheckFunc func(metrics PerformanceMetrics) bool
	Duration  time.Duration
}

// NewAutoProfiler creates a new automatic profiler
func NewAutoProfiler(profileDir string, interval time.Duration) *AutoProfiler {
	return &AutoProfiler{
		profiler: NewProfiler(profileDir),
		monitor:  NewMonitor(interval, 100),
		interval: interval,
		cooldown: 5 * time.Minute, // Default cooldown between profiles
	}
}

// AddCondition adds a profiling condition
func (ap *AutoProfiler) AddCondition(condition ProfileCondition) {
	ap.mu.Lock()
	defer ap.mu.Unlock()
	ap.conditions = append(ap.conditions, condition)
}

// SetCooldown sets the cooldown period between automatic profiles
func (ap *AutoProfiler) SetCooldown(cooldown time.Duration) {
	ap.mu.Lock()
	defer ap.mu.Unlock()
	ap.cooldown = cooldown
}

// Start begins automatic profiling
func (ap *AutoProfiler) Start(ctx context.Context) {
	ap.monitor.Start(ctx)
	
	go ap.monitorLoop(ctx)
}

// Stop ends automatic profiling
func (ap *AutoProfiler) Stop() {
	ap.monitor.Stop()
	if ap.profiler.IsEnabled() {
		ap.profiler.Stop()
	}
}

// monitorLoop runs the automatic profiling monitoring loop
func (ap *AutoProfiler) monitorLoop(ctx context.Context) {
	ticker := time.NewTicker(ap.interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			ap.checkConditions()
		}
	}
}

// checkConditions checks if any profiling conditions are met
func (ap *AutoProfiler) checkConditions() {
	ap.mu.RLock()
	conditions := make([]ProfileCondition, len(ap.conditions))
	copy(conditions, ap.conditions)
	cooldown := ap.cooldown
	lastProfile := ap.lastProfile
	ap.mu.RUnlock()

	// Check cooldown
	if time.Since(lastProfile) < cooldown {
		return
	}

	metrics := ap.monitor.GetPerformanceMetrics()

	for _, condition := range conditions {
		if condition.CheckFunc(metrics) {
			ap.triggerProfile(condition)
			break // Only trigger one profile at a time
		}
	}
}

// triggerProfile starts profiling for a specified duration
func (ap *AutoProfiler) triggerProfile(condition ProfileCondition) {
	ap.mu.Lock()
	ap.lastProfile = time.Now()
	ap.mu.Unlock()

	// Start profiling
	if err := ap.profiler.Start(); err != nil {
		return // Failed to start profiling
	}

	// Profile for the specified duration
	time.AfterFunc(condition.Duration, func() {
		ap.profiler.Stop()
	})
}

// Common profiling conditions

// HighMemoryCondition triggers profiling when memory usage is high
func HighMemoryCondition(threshold uint64) ProfileCondition {
	return ProfileCondition{
		Name: "high_memory",
		CheckFunc: func(metrics PerformanceMetrics) bool {
			return metrics.Memory.Alloc > threshold
		},
		Duration: 30 * time.Second,
	}
}

// HighGoroutineCondition triggers profiling when goroutine count is high
func HighGoroutineCondition(threshold int) ProfileCondition {
	return ProfileCondition{
		Name: "high_goroutines",
		CheckFunc: func(metrics PerformanceMetrics) bool {
			return metrics.Memory.NumGoroutine > threshold
		},
		Duration: 30 * time.Second,
	}
}

// SlowOperationCondition triggers profiling when operations are slow
func SlowOperationCondition(operation string, threshold time.Duration) ProfileCondition {
	return ProfileCondition{
		Name: fmt.Sprintf("slow_%s", operation),
		CheckFunc: func(metrics PerformanceMetrics) bool {
			if latency, exists := metrics.OperationLatency[operation]; exists {
				return latency > threshold
			}
			return false
		},
		Duration: 60 * time.Second,
	}
}

// LowCacheHitRatioCondition triggers profiling when cache hit ratio is low
func LowCacheHitRatioCondition(cacheName string, threshold float64) ProfileCondition {
	return ProfileCondition{
		Name: fmt.Sprintf("low_cache_hit_%s", cacheName),
		CheckFunc: func(metrics PerformanceMetrics) bool {
			if ratio, exists := metrics.CacheHitRatio[cacheName]; exists {
				return ratio < threshold
			}
			return false
		},
		Duration: 45 * time.Second,
	}
}

// Global profiler instances
var (
	GlobalProfiler     = NewProfiler("./profiles")
	GlobalAutoProfiler = NewAutoProfiler("./profiles", 10*time.Second)
)

// InitGlobalProfiler initializes the global profiler with common conditions
func InitGlobalProfiler() {
	// Add common profiling conditions
	GlobalAutoProfiler.AddCondition(HighMemoryCondition(100 * 1024 * 1024)) // 100MB
	GlobalAutoProfiler.AddCondition(HighGoroutineCondition(1000))
	GlobalAutoProfiler.AddCondition(SlowOperationCondition("theme_load", 100*time.Millisecond))
	GlobalAutoProfiler.AddCondition(LowCacheHitRatioCondition("theme_cache", 0.8))
}

// StartGlobalProfiling starts global profiling
func StartGlobalProfiling(ctx context.Context) {
	GlobalAutoProfiler.Start(ctx)
}

// StopGlobalProfiling stops global profiling
func StopGlobalProfiling() {
	GlobalAutoProfiler.Stop()
}