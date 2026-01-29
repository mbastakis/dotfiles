// @dotfiles/shared - Shared code for OpenTUI apps

// Theme
export { colors, type Colors, type ColorName } from "./theme"

// Utilities
export { truncateText, truncatePath, truncateLine } from "./utils"

// Hooks
export { useFileWatcher } from "./hooks"

// Components
export {
  Panel,
  KeyHint,
  KeyHintBar,
  PropertyRow,
  StatusIndicator,
  EmptyState,
} from "./components"

// Constants
export { NAV_KEYS, isNavKey, getNavKeyDisplay } from "./constants"
