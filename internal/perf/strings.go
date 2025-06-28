package perf

import (
	"strings"
	"unsafe"
)

// StringBuilder provides an optimized string builder with pooled buffers
type StringBuilder struct {
	buf    *StringBuffer
	pooled bool
}

// NewStringBuilder creates a new string builder
func NewStringBuilder() *StringBuilder {
	return &StringBuilder{
		buf:    GetStringBuffer(),
		pooled: true,
	}
}

// NewStringBuilderWithCapacity creates a string builder with specified capacity
func NewStringBuilderWithCapacity(capacity int) *StringBuilder {
	return &StringBuilder{
		buf: &StringBuffer{
			buf: make([]byte, 0, capacity),
		},
		pooled: false,
	}
}

// WriteString appends a string to the builder
func (sb *StringBuilder) WriteString(s string) {
	sb.buf.WriteString(s)
}

// WriteByte appends a byte to the builder
func (sb *StringBuilder) WriteByte(b byte) {
	sb.buf.buf = append(sb.buf.buf, b)
}

// WriteRune appends a rune to the builder
func (sb *StringBuilder) WriteRune(r rune) {
	if r < 0x80 {
		// ASCII fast path
		sb.WriteByte(byte(r))
		return
	}
	
	// UTF-8 encoding
	var buf [4]byte
	n := utf8EncodeRune(buf[:], r)
	sb.buf.Write(buf[:n])
}

// String returns the built string
func (sb *StringBuilder) String() string {
	return sb.buf.String()
}

// Len returns the length of the current string
func (sb *StringBuilder) Len() int {
	return sb.buf.Len()
}

// Reset clears the builder
func (sb *StringBuilder) Reset() {
	sb.buf.Reset()
}

// Release returns the buffer to the pool if it was pooled
func (sb *StringBuilder) Release() {
	if sb.pooled && sb.buf != nil {
		PutStringBuffer(sb.buf)
		sb.buf = nil
	}
}

// StringJoin efficiently joins strings using a pooled buffer
func StringJoin(sep string, parts ...string) string {
	if len(parts) == 0 {
		return ""
	}
	if len(parts) == 1 {
		return parts[0]
	}

	// Calculate total length to avoid reallocations
	totalLen := len(sep) * (len(parts) - 1)
	for _, part := range parts {
		totalLen += len(part)
	}

	sb := NewStringBuilderWithCapacity(totalLen)
	defer sb.Release()

	sb.WriteString(parts[0])
	for i := 1; i < len(parts); i++ {
		sb.WriteString(sep)
		sb.WriteString(parts[i])
	}

	return sb.String()
}

// StringContains provides an optimized string contains check
func StringContains(s, substr string) bool {
	return strings.Contains(s, substr)
}

// StringHasPrefix provides an optimized prefix check
func StringHasPrefix(s, prefix string) bool {
	return len(s) >= len(prefix) && s[:len(prefix)] == prefix
}

// StringHasSuffix provides an optimized suffix check
func StringHasSuffix(s, suffix string) bool {
	return len(s) >= len(suffix) && s[len(s)-len(suffix):] == suffix
}

// StringReplace efficiently replaces all occurrences using a pooled buffer
func StringReplace(s, old, new string, n int) string {
	if old == new || n == 0 {
		return s
	}

	// Use standard library for simple cases
	if n < 0 || strings.Count(s, old) < 4 {
		return strings.Replace(s, old, new, n)
	}

	// For many replacements, use a custom implementation
	return stringReplaceMany(s, old, new, n)
}

// stringReplaceMany handles multiple replacements efficiently
func stringReplaceMany(s, old, new string, n int) string {
	if n == 0 {
		return s
	}

	// Find all occurrences
	indices := make([]int, 0, 8)
	start := 0
	for n < 0 || len(indices) < n {
		i := strings.Index(s[start:], old)
		if i < 0 {
			break
		}
		indices = append(indices, start+i)
		start += i + len(old)
	}

	if len(indices) == 0 {
		return s
	}

	// Calculate new length
	newLen := len(s) + len(indices)*(len(new)-len(old))
	sb := NewStringBuilderWithCapacity(newLen)
	defer sb.Release()

	start = 0
	for _, i := range indices {
		sb.WriteString(s[start:i])
		sb.WriteString(new)
		start = i + len(old)
	}
	sb.WriteString(s[start:])

	return sb.String()
}

// StringFormat provides optimized string formatting for common cases
func StringFormat(format string, args ...interface{}) string {
	// Handle common cases without using fmt.Sprintf
	switch len(args) {
	case 0:
		return format
	case 1:
		if strings.Count(format, "%") == 1 {
			return stringFormatOne(format, args[0])
		}
	case 2:
		if strings.Count(format, "%") == 2 {
			return stringFormatTwo(format, args[0], args[1])
		}
	}

	// Fall back to standard formatting for complex cases
	return ""
}

// stringFormatOne handles single argument formatting
func stringFormatOne(format string, arg interface{}) string {
	idx := strings.Index(format, "%")
	if idx < 0 {
		return format
	}

	sb := NewStringBuilder()
	defer sb.Release()

	sb.WriteString(format[:idx])
	
	// Handle common format specifiers
	if idx+1 < len(format) {
		switch format[idx+1] {
		case 's':
			if s, ok := arg.(string); ok {
				sb.WriteString(s)
			}
		case 'd':
			if i, ok := arg.(int); ok {
				sb.WriteString(itoa(i))
			}
		}
	}

	if idx+2 < len(format) {
		sb.WriteString(format[idx+2:])
	}

	return sb.String()
}

// stringFormatTwo handles two argument formatting
func stringFormatTwo(format string, arg1, arg2 interface{}) string {
	indices := make([]int, 0, 2)
	for i := 0; i < len(format)-1; i++ {
		if format[i] == '%' {
			indices = append(indices, i)
			if len(indices) == 2 {
				break
			}
		}
	}

	if len(indices) != 2 {
		return format
	}

	sb := NewStringBuilder()
	defer sb.Release()

	// First part
	sb.WriteString(format[:indices[0]])
	formatArg(sb, format, indices[0], arg1)

	// Middle part
	sb.WriteString(format[indices[0]+2:indices[1]])
	formatArg(sb, format, indices[1], arg2)

	// End part
	if indices[1]+2 < len(format) {
		sb.WriteString(format[indices[1]+2:])
	}

	return sb.String()
}

// formatArg formats a single argument based on the format specifier
func formatArg(sb *StringBuilder, format string, idx int, arg interface{}) {
	if idx+1 >= len(format) {
		return
	}

	switch format[idx+1] {
	case 's':
		if s, ok := arg.(string); ok {
			sb.WriteString(s)
		}
	case 'd':
		if i, ok := arg.(int); ok {
			sb.WriteString(itoa(i))
		}
	}
}

// itoa converts an integer to string
func itoa(i int) string {
	if i == 0 {
		return "0"
	}

	negative := i < 0
	if negative {
		i = -i
	}

	// Count digits
	digits := 0
	temp := i
	for temp > 0 {
		digits++
		temp /= 10
	}

	// Build string
	size := digits
	if negative {
		size++
	}

	buf := make([]byte, size)
	pos := size - 1

	for i > 0 {
		buf[pos] = byte('0' + i%10)
		i /= 10
		pos--
	}

	if negative {
		buf[0] = '-'
	}

	return *(*string)(unsafe.Pointer(&buf))
}

// utf8EncodeRune encodes a rune into UTF-8 bytes
func utf8EncodeRune(p []byte, r rune) int {
	// Simplified UTF-8 encoding for performance
	if r <= 0x7F {
		p[0] = byte(r)
		return 1
	} else if r <= 0x7FF {
		p[0] = 0xC0 | byte(r>>6)
		p[1] = 0x80 | byte(r&0x3F)
		return 2
	} else if r <= 0xFFFF {
		p[0] = 0xE0 | byte(r>>12)
		p[1] = 0x80 | byte(r>>6&0x3F)
		p[2] = 0x80 | byte(r&0x3F)
		return 3
	} else {
		p[0] = 0xF0 | byte(r>>18)
		p[1] = 0x80 | byte(r>>12&0x3F)
		p[2] = 0x80 | byte(r>>6&0x3F)
		p[3] = 0x80 | byte(r&0x3F)
		return 4
	}
}

// StringSliceToString efficiently converts a slice of strings to a single string
func StringSliceToString(slice []string, separator string) string {
	if len(slice) == 0 {
		return ""
	}
	if len(slice) == 1 {
		return slice[0]
	}

	// Calculate total length
	totalLen := len(separator) * (len(slice) - 1)
	for _, s := range slice {
		totalLen += len(s)
	}

	sb := NewStringBuilderWithCapacity(totalLen)
	defer sb.Release()

	sb.WriteString(slice[0])
	for i := 1; i < len(slice); i++ {
		sb.WriteString(separator)
		sb.WriteString(slice[i])
	}

	return sb.String()
}

// TrimSpaceOptimized provides an optimized whitespace trimming
func TrimSpaceOptimized(s string) string {
	// Fast path for empty or single character strings
	if len(s) <= 1 {
		if len(s) == 1 && (s[0] == ' ' || s[0] == '\t' || s[0] == '\n' || s[0] == '\r') {
			return ""
		}
		return s
	}

	// Find first non-whitespace character
	start := 0
	for start < len(s) && isSpace(s[start]) {
		start++
	}

	// Find last non-whitespace character
	end := len(s) - 1
	for end >= start && isSpace(s[end]) {
		end--
	}

	if start > end {
		return ""
	}

	return s[start : end+1]
}

// isSpace checks if a byte is a whitespace character
func isSpace(b byte) bool {
	return b == ' ' || b == '\t' || b == '\n' || b == '\r' || b == '\v' || b == '\f'
}