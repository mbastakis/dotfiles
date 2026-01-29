// Text truncation utilities

/**
 * Truncate text from the end, adding ellipsis if too long
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - 3) + "..."
}

/**
 * Truncate a path from the start, keeping the most relevant end portion
 */
export function truncatePath(path: string, maxLength: number): string {
  if (path.length <= maxLength) return path
  return "..." + path.slice(-(maxLength - 3))
}

/**
 * Truncate a single line, useful for log lines or command output
 */
export function truncateLine(line: string, maxLength: number): string {
  // Remove newlines and truncate
  const cleaned = line.replace(/[\r\n]+/g, " ").trim()
  return truncateText(cleaned, maxLength)
}
