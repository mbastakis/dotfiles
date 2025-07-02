package perf

import (
	"sync"
)

// StringBuffer provides a pooled bytes.Buffer for string operations
type StringBuffer struct {
	buf []byte
}

// Write appends bytes to the buffer
func (sb *StringBuffer) Write(p []byte) (int, error) {
	sb.buf = append(sb.buf, p...)
	return len(p), nil
}

// WriteString appends a string to the buffer
func (sb *StringBuffer) WriteString(s string) (int, error) {
	sb.buf = append(sb.buf, s...)
	return len(s), nil
}

// String returns the buffer contents as a string
func (sb *StringBuffer) String() string {
	return string(sb.buf)
}

// Reset clears the buffer for reuse
func (sb *StringBuffer) Reset() {
	sb.buf = sb.buf[:0]
}

// Len returns the length of the buffer
func (sb *StringBuffer) Len() int {
	return len(sb.buf)
}

// Pool for string buffers to reduce allocations
var stringBufferPool = sync.Pool{
	New: func() interface{} {
		return &StringBuffer{
			buf: make([]byte, 0, 256), // Pre-allocate 256 bytes
		}
	},
}

// GetStringBuffer gets a buffer from the pool
func GetStringBuffer() *StringBuffer {
	return stringBufferPool.Get().(*StringBuffer)
}

// PutStringBuffer returns a buffer to the pool
func PutStringBuffer(buf *StringBuffer) {
	buf.Reset()
	stringBufferPool.Put(buf)
}

// StatusResult represents a cached tool status result
type StatusResult struct {
	ToolName string
	Data     interface{}
	CachedAt int64
}

// Reset clears the status result for reuse
func (sr *StatusResult) Reset() {
	sr.ToolName = ""
	sr.Data = nil
	sr.CachedAt = 0
}

// Pool for status results
var statusResultPool = sync.Pool{
	New: func() interface{} {
		return &StatusResult{}
	},
}

// GetStatusResult gets a status result from the pool
func GetStatusResult() *StatusResult {
	return statusResultPool.Get().(*StatusResult)
}

// PutStatusResult returns a status result to the pool
func PutStatusResult(result *StatusResult) {
	result.Reset()
	statusResultPool.Put(result)
}

// CachedView represents a cached view string with metadata
type CachedView struct {
	Content   string
	Width     int
	Height    int
	ThemeName string
	CachedAt  int64
}

// Reset clears the view cache for reuse
func (vc *CachedView) Reset() {
	vc.Content = ""
	vc.Width = 0
	vc.Height = 0
	vc.ThemeName = ""
	vc.CachedAt = 0
}

// Pool for view cache objects
var viewCachePool = sync.Pool{
	New: func() interface{} {
		return &CachedView{}
	},
}

// GetViewCache gets a view cache from the pool
func GetViewCache() *CachedView {
	return viewCachePool.Get().(*CachedView)
}

// PutViewCache returns a view cache to the pool
func PutViewCache(cache *CachedView) {
	cache.Reset()
	viewCachePool.Put(cache)
}

// SlicePool provides pooled slices of various types
type SlicePool[T any] struct {
	pool sync.Pool
}

// NewSlicePool creates a new slice pool for type T
func NewSlicePool[T any](initialCapacity int) *SlicePool[T] {
	return &SlicePool[T]{
		pool: sync.Pool{
			New: func() interface{} {
				slice := make([]T, 0, initialCapacity)
				return &slice
			},
		},
	}
}

// Get gets a slice from the pool
func (sp *SlicePool[T]) Get() *[]T {
	return sp.pool.Get().(*[]T)
}

// Put returns a slice to the pool
func (sp *SlicePool[T]) Put(slice *[]T) {
	*slice = (*slice)[:0] // Reset length but keep capacity
	sp.pool.Put(slice)
}

// Common slice pools
var (
	StringSlicePool = NewSlicePool[string](16)
	IntSlicePool    = NewSlicePool[int](16)
)
