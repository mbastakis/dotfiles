#!/usr/bin/env bash
# Build all TUI apps in the apps/ workspace
# Usage: build_apps.sh [--force]
#   --force: Remove node_modules and bun.lock before installing

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Find dotfiles directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_DIR="$(dirname "$SCRIPT_DIR")"
APPS_DIR="$DOTFILES_DIR/apps"
BIN_DIR="$DOTFILES_DIR/dot-bin"

# Parse arguments
FORCE=false
for arg in "$@"; do
  case $arg in
    --force|-f)
      FORCE=true
      ;;
  esac
done

# Check prerequisites
if ! command -v bun &>/dev/null; then
  log_error "bun is required but not installed"
  exit 1
fi

if [[ ! -d "$APPS_DIR" ]]; then
  log_error "Apps directory not found: $APPS_DIR"
  exit 1
fi

if [[ ! -f "$APPS_DIR/package.json" ]]; then
  log_error "Workspace package.json not found at $APPS_DIR/package.json"
  exit 1
fi

# Force clean if requested
if [[ "$FORCE" == "true" ]]; then
  log_info "Force rebuild: removing node_modules and lock files..."
  rm -rf "$APPS_DIR/node_modules"
  rm -f "$APPS_DIR/bun.lock"
  for app_dir in "$APPS_DIR"/*/; do
    if [[ -f "${app_dir}package.json" ]]; then
      rm -rf "${app_dir}node_modules"
      rm -f "${app_dir}bun.lock"
    fi
  done
fi

# Install workspace dependencies
log_info "Installing workspace dependencies..."
cd "$APPS_DIR"
if [[ -f "bun.lock" ]]; then
  bun install --frozen-lockfile 2>/dev/null || bun install
else
  bun install
fi

# Generate wrapper scripts for each app
log_info "Generating wrapper scripts in $BIN_DIR..."
mkdir -p "$BIN_DIR"

for app_dir in "$APPS_DIR"/*/; do
  # Skip shared package and non-app directories
  app_name="$(basename "$app_dir")"
  [[ "$app_name" == "shared" ]] && continue
  [[ ! -f "${app_dir}package.json" ]] && continue
  
  # Check if it has a start script (indicates it's a runnable app)
  if ! grep -q '"start"' "${app_dir}package.json" 2>/dev/null; then
    continue
  fi
  
  # Determine wrapper name (use existing name or derive from app name)
  case "$app_name" in
    service-manager)
      wrapper_name="svc"
      ;;
    *)
      wrapper_name="$app_name"
      ;;
  esac
  
  wrapper_path="$BIN_DIR/$wrapper_name"
  
  # Generate wrapper script
  cat > "$wrapper_path" << EOF
#!/usr/bin/env bash
# Auto-generated wrapper for $app_name TUI app
# Regenerate with: bin/build_apps.sh

set -euo pipefail

# Find dotfiles directory
DOTFILES_DIR=""
for dir in ~/dev/dotfiles ~/dotfiles ~/.dotfiles; do
  if [[ -d "\$dir/apps/$app_name" ]]; then
    DOTFILES_DIR="\$dir"
    break
  fi
done

if [[ -z "\$DOTFILES_DIR" ]]; then
  echo "Error: Could not find dotfiles directory with apps/$app_name" >&2
  exit 1
fi

APPS_DIR="\$DOTFILES_DIR/apps"
APP_DIR="\$APPS_DIR/$app_name"

# Ensure workspace dependencies are installed
if [[ ! -d "\$APPS_DIR/node_modules" ]]; then
  echo "Installing workspace dependencies..." >&2
  (cd "\$APPS_DIR" && bun install)
fi

# Run from app directory for proper module resolution
cd "\$APP_DIR"
exec bun run src/index.tsx "\$@"
EOF
  
  chmod +x "$wrapper_path"
  log_info "Generated wrapper: $wrapper_name -> apps/$app_name"
done

log_info "Build complete!"
