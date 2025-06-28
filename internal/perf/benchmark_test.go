package perf

import (
	"context"
	"fmt"
	"runtime"
	"sync"
	"testing"
	"time"
)

// BenchmarkStringBuilder tests the performance of our string builder
func BenchmarkStringBuilder(b *testing.B) {
	const testString = "Hello, World! "
	const iterations = 100

	b.Run("CustomStringBuilder", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			sb := NewStringBuilder()
			for j := 0; j < iterations; j++ {
				sb.WriteString(testString)
			}
			_ = sb.String()
			sb.Release()
		}
	})

	b.Run("StandardStringBuilder", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			var sb strings.Builder
			for j := 0; j < iterations; j++ {
				sb.WriteString(testString)
			}
			_ = sb.String()
		}
	})

	b.Run("StringConcatenation", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			result := ""
			for j := 0; j < iterations; j++ {
				result += testString
			}
			_ = result
		}
	})
}

// BenchmarkStringJoin tests string joining performance
func BenchmarkStringJoin(b *testing.B) {
	parts := []string{"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"}
	separator := ", "

	b.Run("CustomStringJoin", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_ = StringJoin(separator, parts...)
		}
	})

	b.Run("StandardJoin", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_ = strings.Join(parts, separator)
		}
	})
}

// BenchmarkStringReplace tests string replacement performance
func BenchmarkStringReplace(b *testing.B) {
	text := strings.Repeat("The quick brown fox jumps over the lazy dog. ", 100)
	
	b.Run("FewReplacements", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_ = StringReplace(text, "fox", "cat", -1)
		}
	})

	b.Run("ManyReplacements", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_ = StringReplace(text, "the", "a", -1)
		}
	})

	b.Run("StandardReplace", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_ = strings.Replace(text, "the", "a", -1)
		}
	})
}

// BenchmarkCache tests cache performance
func BenchmarkCache(b *testing.B) {
	cache := NewCache(1000, time.Hour)
	
	// Pre-populate cache
	for i := 0; i < 500; i++ {
		cache.Set(fmt.Sprintf("key%d", i), fmt.Sprintf("value%d", i))
	}

	b.Run("CacheGet", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			key := fmt.Sprintf("key%d", i%500)
			_, _ = cache.Get(key)
		}
	})

	b.Run("CacheSet", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			key := fmt.Sprintf("newkey%d", i)
			cache.Set(key, fmt.Sprintf("value%d", i))
		}
	})

	b.Run("CacheGetOrSet", func(b *testing.B) {
		counter := 0
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			key := fmt.Sprintf("getorset%d", i%100)
			_, _ = cache.GetOrSet(key, func() (interface{}, error) {
				counter++
				return fmt.Sprintf("computed%d", counter), nil
			})
		}
	})
}

// BenchmarkLRUCache tests LRU cache performance
func BenchmarkLRUCache(b *testing.B) {
	cache := NewLRUCache(1000)
	
	// Pre-populate cache
	for i := 0; i < 500; i++ {
		cache.Set(fmt.Sprintf("key%d", i), fmt.Sprintf("value%d", i))
	}

	b.Run("LRUGet", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			key := fmt.Sprintf("key%d", i%500)
			_, _ = cache.Get(key)
		}
	})

	b.Run("LRUSet", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			key := fmt.Sprintf("newkey%d", i)
			cache.Set(key, fmt.Sprintf("value%d", i))
		}
	})
}

// BenchmarkObjectPools tests object pool performance
func BenchmarkObjectPools(b *testing.B) {
	b.Run("StringBufferPool", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			buf := GetStringBuffer()
			buf.WriteString("Hello, World!")
			buf.WriteString(" This is a test.")
			_ = buf.String()
			PutStringBuffer(buf)
		}
	})

	b.Run("DirectAllocation", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			buf := &StringBuffer{buf: make([]byte, 0, 256)}
			buf.WriteString("Hello, World!")
			buf.WriteString(" This is a test.")
			_ = buf.String()
		}
	})

	b.Run("StringSlicePool", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			slice := StringSlicePool.Get()
			*slice = append(*slice, "one", "two", "three", "four", "five")
			StringSlicePool.Put(slice)
		}
	})
}

// BenchmarkConcurrentCache tests cache performance under concurrent load
func BenchmarkConcurrentCache(b *testing.B) {
	cache := NewCache(10000, time.Hour)
	
	// Pre-populate cache
	for i := 0; i < 1000; i++ {
		cache.Set(fmt.Sprintf("key%d", i), fmt.Sprintf("value%d", i))
	}

	b.Run("ConcurrentRead", func(b *testing.B) {
		b.RunParallel(func(pb *testing.PB) {
			i := 0
			for pb.Next() {
				key := fmt.Sprintf("key%d", i%1000)
				_, _ = cache.Get(key)
				i++
			}
		})
	})

	b.Run("ConcurrentWrite", func(b *testing.B) {
		b.RunParallel(func(pb *testing.PB) {
			i := 0
			for pb.Next() {
				key := fmt.Sprintf("writekey%d", i)
				cache.Set(key, fmt.Sprintf("value%d", i))
				i++
			}
		})
	})

	b.Run("ConcurrentMixed", func(b *testing.B) {
		b.RunParallel(func(pb *testing.PB) {
			i := 0
			for pb.Next() {
				if i%3 == 0 {
					// Write operation
					key := fmt.Sprintf("mixedkey%d", i)
					cache.Set(key, fmt.Sprintf("value%d", i))
				} else {
					// Read operation
					key := fmt.Sprintf("key%d", i%1000)
					_, _ = cache.Get(key)
				}
				i++
			}
		})
	})
}

// BenchmarkMonitor tests monitoring overhead
func BenchmarkMonitor(b *testing.B) {
	monitor := NewMonitor(time.Second, 100)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	monitor.Start(ctx)
	defer monitor.Stop()

	b.Run("RecordOperation", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			monitor.RecordOperation("test_op", time.Microsecond*10)
		}
	})

	b.Run("RecordCacheHit", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			monitor.RecordCacheHit("test_cache")
		}
	})

	b.Run("GetMetrics", func(b *testing.B) {
		// Record some operations first
		for i := 0; i < 100; i++ {
			monitor.RecordOperation("bench_op", time.Microsecond*5)
			monitor.RecordCacheHit("bench_cache")
		}

		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			_ = monitor.GetPerformanceMetrics()
		}
	})
}

// MemoryBenchmark provides memory allocation benchmarking utilities
type MemoryBenchmark struct {
	before runtime.MemStats
	after  runtime.MemStats
}

// StartMemoryBenchmark begins memory tracking
func StartMemoryBenchmark() *MemoryBenchmark {
	mb := &MemoryBenchmark{}
	runtime.GC()
	runtime.ReadMemStats(&mb.before)
	return mb
}

// End finishes memory tracking and returns allocation stats
func (mb *MemoryBenchmark) End() (allocations uint64, totalBytes uint64) {
	runtime.GC()
	runtime.ReadMemStats(&mb.after)
	return mb.after.Mallocs - mb.before.Mallocs, mb.after.TotalAlloc - mb.before.TotalAlloc
}

// BenchmarkMemoryAllocations tests memory allocation patterns
func BenchmarkMemoryAllocations(b *testing.B) {
	b.Run("StringBuilderAllocations", func(b *testing.B) {
		mb := StartMemoryBenchmark()
		b.ResetTimer()
		
		for i := 0; i < b.N; i++ {
			sb := NewStringBuilder()
			for j := 0; j < 10; j++ {
				sb.WriteString("test string ")
			}
			_ = sb.String()
			sb.Release()
		}
		
		b.StopTimer()
		allocs, bytes := mb.End()
		b.ReportMetric(float64(allocs)/float64(b.N), "allocs/op")
		b.ReportMetric(float64(bytes)/float64(b.N), "bytes/op")
	})

	b.Run("StandardBuilderAllocations", func(b *testing.B) {
		mb := StartMemoryBenchmark()
		b.ResetTimer()
		
		for i := 0; i < b.N; i++ {
			var sb strings.Builder
			for j := 0; j < 10; j++ {
				sb.WriteString("test string ")
			}
			_ = sb.String()
		}
		
		b.StopTimer()
		allocs, bytes := mb.End()
		b.ReportMetric(float64(allocs)/float64(b.N), "allocs/op")
		b.ReportMetric(float64(bytes)/float64(b.N), "bytes/op")
	})
}

// PerformanceTestSuite runs a comprehensive performance test suite
func PerformanceTestSuite(b *testing.B) {
	b.Run("StringOperations", func(b *testing.B) {
		BenchmarkStringBuilder(b)
		BenchmarkStringJoin(b)
		BenchmarkStringReplace(b)
	})

	b.Run("CacheOperations", func(b *testing.B) {
		BenchmarkCache(b)
		BenchmarkLRUCache(b)
		BenchmarkConcurrentCache(b)
	})

	b.Run("ObjectPools", func(b *testing.B) {
		BenchmarkObjectPools(b)
	})

	b.Run("Monitoring", func(b *testing.B) {
		BenchmarkMonitor(b)
	})

	b.Run("MemoryUsage", func(b *testing.B) {
		BenchmarkMemoryAllocations(b)
	})
}

// StressTest performs stress testing of performance components
func StressTest(t *testing.T) {
	const duration = 10 * time.Second
	const numGoroutines = 50

	ctx, cancel := context.WithTimeout(context.Background(), duration)
	defer cancel()

	monitor := NewMonitor(100*time.Millisecond, 1000)
	monitor.Start(ctx)
	defer monitor.Stop()

	cache := NewCache(10000, time.Minute)
	
	var wg sync.WaitGroup
	wg.Add(numGoroutines)

	// Start worker goroutines
	for i := 0; i < numGoroutines; i++ {
		go func(id int) {
			defer wg.Done()
			
			counter := 0
			for {
				select {
				case <-ctx.Done():
					return
				default:
					// Perform various operations
					key := fmt.Sprintf("stress_%d_%d", id, counter)
					
					// Cache operations
					cache.Set(key, fmt.Sprintf("value_%d", counter))
					_, _ = cache.Get(key)
					
					// String operations
					sb := NewStringBuilder()
					sb.WriteString(fmt.Sprintf("Worker %d operation %d", id, counter))
					_ = sb.String()
					sb.Release()
					
					// Monitor operations
					op := monitor.StartTimedOperation("stress_test")
					time.Sleep(time.Microsecond * 10) // Simulate work
					op.Finish()
					
					counter++
					
					if counter%1000 == 0 {
						runtime.GC() // Trigger GC occasionally
					}
				}
			}
		}(i)
	}

	wg.Wait()

	// Check final stats
	stats := cache.Stats()
	metrics := monitor.GetPerformanceMetrics()
	
	t.Logf("Stress test completed:")
	t.Logf("Cache size: %d items", stats.Size)
	t.Logf("Memory usage: %s", monitor.GetMemoryUsageString())
	t.Logf("Operations recorded: %d", len(metrics.OperationCounts))
}