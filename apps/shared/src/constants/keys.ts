// Standard navigation keys used across all TUI apps

export const NAV_KEYS = {
  // Vertical navigation
  DOWN: ["j", "ArrowDown"],
  UP: ["k", "ArrowUp"],
  FIRST: ["g"],
  LAST: ["G"],

  // Horizontal/depth navigation
  SELECT: ["l", "Enter"],
  BACK: ["h", "Escape"],

  // Common actions
  QUIT: ["q"],
  HELP: ["?"],
  REFRESH: ["r", "R"],
} as const

/**
 * Check if a key matches a navigation action
 */
export function isNavKey(key: string, action: keyof typeof NAV_KEYS): boolean {
  return NAV_KEYS[action].includes(key as never)
}

/**
 * Get all keys for a navigation action (for display purposes)
 */
export function getNavKeyDisplay(action: keyof typeof NAV_KEYS): string {
  const keys = NAV_KEYS[action]
  return keys.length === 1 ? keys[0] : keys.join("/")
}
