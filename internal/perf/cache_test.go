package perf

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/mbastakis/dotfiles/internal/config"
)

func TestNewCache(t *testing.T) {
	cache := NewCache(10, time.Minute)
	
	if cache == nil {
		t.Fatal("Expected NewCache to return non-nil cache")
	}
	
	if cache.maxSize != 10 {
		t.Errorf("Expected maxSize to be 10, got %d", cache.maxSize)
	}
	
	if cache.defaultTTL != time.Minute {
		t.Errorf("Expected defaultTTL to be 1 minute, got %v", cache.defaultTTL)
	}
}

func TestCache_SetAndGet(t *testing.T) {
	cache := NewCache(10, time.Minute)
	
	// Test basic set and get
	key := "test-key"
	value := "test-value"
	
	cache.Set(key, value)
	
	retrieved, exists := cache.Get(key)
	if !exists {
		t.Error("Expected key to exist in cache")
	}
	
	if retrieved != value {
		t.Errorf("Expected retrieved value to be '%s', got '%v'", value, retrieved)
	}
}

func TestCache_SetWithTTL(t *testing.T) {
	cache := NewCache(10, time.Minute)
	
	key := "test-key"
	value := "test-value"
	ttl := 100 * time.Millisecond
	
	cache.SetWithTTL(key, value, ttl)
	
	// Should exist immediately
	_, exists := cache.Get(key)
	if !exists {
		t.Error("Expected key to exist immediately after setting")
	}
	
	// Wait for expiration
	time.Sleep(150 * time.Millisecond)
	
	_, exists = cache.Get(key)
	if exists {
		t.Error("Expected key to be expired after TTL")
	}
}

func TestCache_Delete(t *testing.T) {
	cache := NewCache(10, time.Minute)
	
	key := "test-key"
	value := "test-value"
	
	cache.Set(key, value)
	
	// Verify it exists
	_, exists := cache.Get(key)
	if !exists {
		t.Error("Expected key to exist before deletion")
	}
	
	// Delete it
	cache.Delete(key)
	
	// Verify it's gone
	_, exists = cache.Get(key)
	if exists {
		t.Error("Expected key to not exist after deletion")
	}
}

func TestCache_Clear(t *testing.T) {
	cache := NewCache(10, time.Minute)
	
	// Add multiple items
	cache.Set("key1", "value1")
	cache.Set("key2", "value2")
	cache.Set("key3", "value3")
	
	// Verify they exist
	if cache.Size() != 3 {
		t.Errorf("Expected cache size to be 3, got %d", cache.Size())
	}
	
	// Clear cache
	cache.Clear()
	
	// Verify it's empty
	if cache.Size() != 0 {
		t.Errorf("Expected cache size to be 0 after clear, got %d", cache.Size())
	}
}

func TestCache_MaxSize(t *testing.T) {
	maxSize := 3
	cache := NewCache(maxSize, time.Minute)
	
	// Add more items than max size
	for i := 0; i < maxSize+2; i++ {
		cache.Set(fmt.Sprintf("key%d", i), fmt.Sprintf("value%d", i))
	}
	
	// Should not exceed max size
	if cache.Size() > maxSize {
		t.Errorf("Expected cache size to not exceed %d, got %d", maxSize, cache.Size())
	}
}

func TestCache_Stats(t *testing.T) {
	cache := NewCache(10, time.Minute)
	
	// Add some items
	cache.Set("key1", "value1")
	cache.Set("key2", "value2")
	
	// Access items to increase access count
	cache.Get("key1")
	cache.Get("key1")
	
	stats := cache.Stats()
	if stats.Size != 2 {
		t.Errorf("Expected cache size to be 2, got %d", stats.Size)
	}
	if stats.TotalAccess == 0 {
		t.Error("Expected total access to be greater than 0")
	}
}

func TestCache_Cleanup(t *testing.T) {
	cache := NewCache(10, time.Minute)
	
	// Add items with short TTL
	cache.SetWithTTL("key1", "value1", 50*time.Millisecond)
	cache.SetWithTTL("key2", "value2", 200*time.Millisecond)
	
	// Wait for first to expire
	time.Sleep(100 * time.Millisecond)
	
	// Run cleanup
	removed := cache.CleanupExpired()
	
	if removed == 0 {
		t.Error("Expected at least one item to be removed during cleanup")
	}
	
	// First should be gone when accessed, second should remain
	_, exists1 := cache.Get("key1")
	_, exists2 := cache.Get("key2")
	
	if exists1 {
		t.Error("Expected expired key1 to be cleaned up")
	}
	if !exists2 {
		t.Error("Expected key2 to still exist after cleanup")
	}
}

func TestInitGlobalCaches(t *testing.T) {
	cfg := &config.Config{
		Performance: config.PerformanceConfig{
			Cache: config.CacheConfig{
				Default: config.CacheSetting{
					Size:            1000,
					TTL:             "5m",
					CleanupInterval: "1m",
				},
				Status: config.CacheSetting{
					Size:            100,
					TTL:             "30s",
					CleanupInterval: "15s",
				},
				View: config.CacheSetting{
					Size:            50,
					TTL:             "1m",
					CleanupInterval: "30s",
				},
				Config: config.CacheSetting{
					Size:            20,
					TTL:             "10m",
					CleanupInterval: "2m",
				},
				Theme: config.CacheSetting{
					Size:            10,
					TTL:             "15m",
					CleanupInterval: "5m",
				},
			},
		},
	}
	
	ctx := context.Background()
	err := InitGlobalCaches(ctx, cfg)
	if err != nil {
		t.Fatalf("Expected InitGlobalCaches to succeed, got error: %v", err)
	}
	
	// Test that all global caches are initialized
	if DefaultCache == nil {
		t.Error("Expected DefaultCache to be initialized")
	}
	if StatusCache == nil {
		t.Error("Expected StatusCache to be initialized")
	}
	if ViewCache == nil {
		t.Error("Expected ViewCache to be initialized")
	}
	if ConfigCache == nil {
		t.Error("Expected ConfigCache to be initialized")
	}
	if ThemeCache == nil {
		t.Error("Expected ThemeCache to be initialized")
	}
}

func TestInitGlobalCaches_InvalidConfig(t *testing.T) {
	cfg := &config.Config{
		Performance: config.PerformanceConfig{
			Cache: config.CacheConfig{
				Default: config.CacheSetting{
					Size:            1000,
					TTL:             "invalid-duration",
					CleanupInterval: "1m",
				},
			},
		},
	}
	
	ctx := context.Background()
	err := InitGlobalCaches(ctx, cfg)
	if err == nil {
		t.Error("Expected InitGlobalCaches to fail with invalid TTL")
	}
}

func TestCache_GetOrSet(t *testing.T) {
	cache := NewCache(10, time.Minute)
	
	key := "computed-key"
	expectedValue := "computed-value"
	callCount := 0
	
	computeFunc := func() (interface{}, error) {
		callCount++
		return expectedValue, nil
	}
	
	// First call should compute and cache
	value1, err := cache.GetOrSet(key, computeFunc)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}
	if value1 != expectedValue {
		t.Errorf("Expected value to be '%s', got '%v'", expectedValue, value1)
	}
	if callCount != 1 {
		t.Errorf("Expected compute function to be called once, called %d times", callCount)
	}
	
	// Second call should use cache
	value2, err := cache.GetOrSet(key, computeFunc)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}
	if value2 != expectedValue {
		t.Errorf("Expected cached value to be '%s', got '%v'", expectedValue, value2)
	}
	if callCount != 1 {
		t.Errorf("Expected compute function to be called only once, called %d times", callCount)
	}
}

func TestCache_Keys(t *testing.T) {
	cache := NewCache(10, time.Minute)
	
	// Add some keys
	cache.Set("key1", "value1")
	cache.Set("key2", "value2")
	cache.Set("key3", "value3")
	
	keys := cache.Keys()
	if len(keys) != 3 {
		t.Errorf("Expected 3 keys, got %d", len(keys))
	}
	
	// Check that all expected keys are present
	keyMap := make(map[string]bool)
	for _, key := range keys {
		keyMap[key] = true
	}
	
	expectedKeys := []string{"key1", "key2", "key3"}
	for _, expectedKey := range expectedKeys {
		if !keyMap[expectedKey] {
			t.Errorf("Expected key '%s' to be present", expectedKey)
		}
	}
}