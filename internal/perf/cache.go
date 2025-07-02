package perf

import (
	"context"
	"sync"
	"time"

	"github.com/mbastakis/dotfiles/internal/config"
)

// CacheItem represents a cached item with expiration
type CacheItem struct {
	Value       interface{}
	ExpiresAt   time.Time
	AccessCount int64
	CreatedAt   time.Time
}

// IsExpired checks if the cache item has expired
func (ci *CacheItem) IsExpired() bool {
	return time.Now().After(ci.ExpiresAt)
}

// Cache provides a thread-safe cache with TTL and size limits
type Cache struct {
	mu         sync.RWMutex
	items      map[string]*CacheItem
	maxSize    int
	defaultTTL time.Duration
	onEvict    func(key string, value interface{})
}

// NewCache creates a new cache with specified parameters
func NewCache(maxSize int, defaultTTL time.Duration) *Cache {
	return &Cache{
		items:      make(map[string]*CacheItem),
		maxSize:    maxSize,
		defaultTTL: defaultTTL,
	}
}

// SetEvictionCallback sets a callback function called when items are evicted
func (c *Cache) SetEvictionCallback(callback func(key string, value interface{})) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.onEvict = callback
}

// Set stores a value in the cache with default TTL
func (c *Cache) Set(key string, value interface{}) {
	c.SetWithTTL(key, value, c.defaultTTL)
}

// SetWithTTL stores a value in the cache with custom TTL
func (c *Cache) SetWithTTL(key string, value interface{}, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := time.Now()
	item := &CacheItem{
		Value:       value,
		ExpiresAt:   now.Add(ttl),
		AccessCount: 0,
		CreatedAt:   now,
	}

	// Check if we need to evict items
	if len(c.items) >= c.maxSize {
		c.evictLRU()
	}

	c.items[key] = item
}

// Get retrieves a value from the cache
func (c *Cache) Get(key string) (interface{}, bool) {
	c.mu.RLock()
	item, exists := c.items[key]
	c.mu.RUnlock()

	if !exists {
		return nil, false
	}

	if item.IsExpired() {
		c.Delete(key)
		return nil, false
	}

	// Update access count atomically
	c.mu.Lock()
	item.AccessCount++
	c.mu.Unlock()

	return item.Value, true
}

// GetOrSet gets a value from cache or sets it using the provided function
func (c *Cache) GetOrSet(key string, fn func() (interface{}, error)) (interface{}, error) {
	// Try to get from cache first
	if value, exists := c.Get(key); exists {
		return value, nil
	}

	// Not in cache, compute the value
	value, err := fn()
	if err != nil {
		return nil, err
	}

	// Store in cache
	c.Set(key, value)
	return value, nil
}

// GetOrSetWithTTL gets a value from cache or sets it with custom TTL
func (c *Cache) GetOrSetWithTTL(key string, ttl time.Duration, fn func() (interface{}, error)) (interface{}, error) {
	if value, exists := c.Get(key); exists {
		return value, nil
	}

	value, err := fn()
	if err != nil {
		return nil, err
	}

	c.SetWithTTL(key, value, ttl)
	return value, nil
}

// Delete removes a key from the cache
func (c *Cache) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if item, exists := c.items[key]; exists {
		delete(c.items, key)
		if c.onEvict != nil {
			c.onEvict(key, item.Value)
		}
	}
}

// Clear removes all items from the cache
func (c *Cache) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.onEvict != nil {
		for key, item := range c.items {
			c.onEvict(key, item.Value)
		}
	}

	c.items = make(map[string]*CacheItem)
}

// Size returns the current number of items in the cache
func (c *Cache) Size() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return len(c.items)
}

// Keys returns all keys in the cache
func (c *Cache) Keys() []string {
	c.mu.RLock()
	defer c.mu.RUnlock()

	keys := make([]string, 0, len(c.items))
	for key := range c.items {
		keys = append(keys, key)
	}
	return keys
}

// evictLRU evicts the least recently used item
func (c *Cache) evictLRU() {
	var lruKey string
	var lruItem *CacheItem
	var lruAccess int64 = -1

	for key, item := range c.items {
		if item.IsExpired() {
			// Prioritize expired items for eviction
			lruKey = key
			lruItem = item
			break
		}

		if lruAccess == -1 || item.AccessCount < lruAccess {
			lruKey = key
			lruItem = item
			lruAccess = item.AccessCount
		}
	}

	if lruKey != "" {
		delete(c.items, lruKey)
		if c.onEvict != nil {
			c.onEvict(lruKey, lruItem.Value)
		}
	}
}

// CleanupExpired removes all expired items from the cache
func (c *Cache) CleanupExpired() int {
	c.mu.Lock()
	defer c.mu.Unlock()

	removed := 0
	for key, item := range c.items {
		if item.IsExpired() {
			delete(c.items, key)
			if c.onEvict != nil {
				c.onEvict(key, item.Value)
			}
			removed++
		}
	}
	return removed
}

// StartCleanupTimer starts a background goroutine to periodically clean expired items
func (c *Cache) StartCleanupTimer(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	go func() {
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				c.CleanupExpired()
			}
		}
	}()
}

// Stats returns cache statistics
func (c *Cache) Stats() CacheStats {
	c.mu.RLock()
	defer c.mu.RUnlock()

	expired := 0
	totalAccess := int64(0)

	for _, item := range c.items {
		if item.IsExpired() {
			expired++
		}
		totalAccess += item.AccessCount
	}

	return CacheStats{
		Size:        len(c.items),
		Expired:     expired,
		TotalAccess: totalAccess,
	}
}

// CacheStats represents cache statistics
type CacheStats struct {
	Size        int
	Expired     int
	TotalAccess int64
}

// AsyncCache provides asynchronous caching with background refresh
type AsyncCache struct {
	cache      *Cache
	mu         sync.RWMutex
	loading    map[string]chan struct{}
	refreshing map[string]bool
}

// NewAsyncCache creates a new async cache
func NewAsyncCache(maxSize int, defaultTTL time.Duration) *AsyncCache {
	return &AsyncCache{
		cache:      NewCache(maxSize, defaultTTL),
		loading:    make(map[string]chan struct{}),
		refreshing: make(map[string]bool),
	}
}

// GetOrLoad gets a value from cache or loads it asynchronously
func (ac *AsyncCache) GetOrLoad(key string, loader func() (interface{}, error)) (interface{}, error) {
	// Try cache first
	if value, exists := ac.cache.Get(key); exists {
		return value, nil
	}

	// Check if already loading
	ac.mu.Lock()
	if ch, loading := ac.loading[key]; loading {
		ac.mu.Unlock()
		// Wait for the loading to complete
		<-ch
		// Try cache again
		if value, exists := ac.cache.Get(key); exists {
			return value, nil
		}
		// If still not in cache, there was an error during loading
		return loader()
	}

	// Start loading
	ch := make(chan struct{})
	ac.loading[key] = ch
	ac.mu.Unlock()

	// Load the value
	value, err := loader()

	// Cleanup loading state
	ac.mu.Lock()
	delete(ac.loading, key)
	close(ch)
	ac.mu.Unlock()

	if err != nil {
		return nil, err
	}

	// Store in cache
	ac.cache.Set(key, value)
	return value, nil
}

// RefreshInBackground refreshes a cache entry in the background
func (ac *AsyncCache) RefreshInBackground(key string, loader func() (interface{}, error)) {
	ac.mu.Lock()
	if ac.refreshing[key] {
		ac.mu.Unlock()
		return
	}
	ac.refreshing[key] = true
	ac.mu.Unlock()

	go func() {
		defer func() {
			ac.mu.Lock()
			delete(ac.refreshing, key)
			ac.mu.Unlock()
		}()

		value, err := loader()
		if err == nil {
			ac.cache.Set(key, value)
		}
	}()
}

// LRUCache provides a pure LRU cache implementation
type LRUCache struct {
	mu       sync.RWMutex
	capacity int
	items    map[string]*lruNode
	head     *lruNode
	tail     *lruNode
}

type lruNode struct {
	key   string
	value interface{}
	prev  *lruNode
	next  *lruNode
}

// NewLRUCache creates a new LRU cache
func NewLRUCache(capacity int) *LRUCache {
	cache := &LRUCache{
		capacity: capacity,
		items:    make(map[string]*lruNode),
	}

	// Initialize dummy head and tail nodes
	cache.head = &lruNode{}
	cache.tail = &lruNode{}
	cache.head.next = cache.tail
	cache.tail.prev = cache.head

	return cache
}

// Get retrieves a value from the LRU cache
func (lc *LRUCache) Get(key string) (interface{}, bool) {
	lc.mu.Lock()
	defer lc.mu.Unlock()

	if node, exists := lc.items[key]; exists {
		lc.moveToHead(node)
		return node.value, true
	}
	return nil, false
}

// Set stores a value in the LRU cache
func (lc *LRUCache) Set(key string, value interface{}) {
	lc.mu.Lock()
	defer lc.mu.Unlock()

	if node, exists := lc.items[key]; exists {
		node.value = value
		lc.moveToHead(node)
		return
	}

	newNode := &lruNode{key: key, value: value}
	lc.items[key] = newNode
	lc.addToHead(newNode)

	if len(lc.items) > lc.capacity {
		tail := lc.removeTail()
		delete(lc.items, tail.key)
	}
}

// moveToHead moves a node to the head of the list
func (lc *LRUCache) moveToHead(node *lruNode) {
	lc.removeNode(node)
	lc.addToHead(node)
}

// addToHead adds a node to the head of the list
func (lc *LRUCache) addToHead(node *lruNode) {
	node.prev = lc.head
	node.next = lc.head.next
	lc.head.next.prev = node
	lc.head.next = node
}

// removeNode removes a node from the list
func (lc *LRUCache) removeNode(node *lruNode) {
	node.prev.next = node.next
	node.next.prev = node.prev
}

// removeTail removes the tail node and returns it
func (lc *LRUCache) removeTail() *lruNode {
	lastNode := lc.tail.prev
	lc.removeNode(lastNode)
	return lastNode
}

// Global caches for common use cases (initialized from config)
var (
	DefaultCache *Cache
	StatusCache  *Cache
	ViewCache    *Cache
	ConfigCache  *Cache
	ThemeCache   *Cache
)

// InitGlobalCaches initializes global caches from configuration
func InitGlobalCaches(ctx context.Context, cfg *config.Config) error {
	// Parse cache settings and create caches
	defaultTTL, err := time.ParseDuration(cfg.Performance.Cache.Default.TTL)
	if err != nil {
		return err
	}
	DefaultCache = NewCache(cfg.Performance.Cache.Default.Size, defaultTTL)
	
	statusTTL, err := time.ParseDuration(cfg.Performance.Cache.Status.TTL)
	if err != nil {
		return err
	}
	StatusCache = NewCache(cfg.Performance.Cache.Status.Size, statusTTL)
	
	viewTTL, err := time.ParseDuration(cfg.Performance.Cache.View.TTL)
	if err != nil {
		return err
	}
	ViewCache = NewCache(cfg.Performance.Cache.View.Size, viewTTL)
	
	configTTL, err := time.ParseDuration(cfg.Performance.Cache.Config.TTL)
	if err != nil {
		return err
	}
	ConfigCache = NewCache(cfg.Performance.Cache.Config.Size, configTTL)
	
	themeTTL, err := time.ParseDuration(cfg.Performance.Cache.Theme.TTL)
	if err != nil {
		return err
	}
	ThemeCache = NewCache(cfg.Performance.Cache.Theme.Size, themeTTL)
	
	// Start cleanup timers with configurable intervals
	defaultCleanup, err := time.ParseDuration(cfg.Performance.Cache.Default.CleanupInterval)
	if err != nil {
		return err
	}
	DefaultCache.StartCleanupTimer(ctx, defaultCleanup)
	
	statusCleanup, err := time.ParseDuration(cfg.Performance.Cache.Status.CleanupInterval)
	if err != nil {
		return err
	}
	StatusCache.StartCleanupTimer(ctx, statusCleanup)
	
	viewCleanup, err := time.ParseDuration(cfg.Performance.Cache.View.CleanupInterval)
	if err != nil {
		return err
	}
	ViewCache.StartCleanupTimer(ctx, viewCleanup)
	
	configCleanup, err := time.ParseDuration(cfg.Performance.Cache.Config.CleanupInterval)
	if err != nil {
		return err
	}
	ConfigCache.StartCleanupTimer(ctx, configCleanup)
	
	themeCleanup, err := time.ParseDuration(cfg.Performance.Cache.Theme.CleanupInterval)
	if err != nil {
		return err
	}
	ThemeCache.StartCleanupTimer(ctx, themeCleanup)
	
	return nil
}
