#!/usr/bin/env bash
# Build all apps in the apps/ workspace (Bun/OpenTUI + Go)
# Usage: build_apps.sh [--force]
#   --force: Clean rebuild (remove node_modules, rebuild all binaries)

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

mkdir -p "$BIN_DIR"

# ============================================================================
# Bun/OpenTUI Apps
# ============================================================================
build_bun_apps() {
  # Check if there are any bun apps
  if [[ ! -f "$APPS_DIR/package.json" ]]; then
    log_info "No Bun workspace found, skipping..."
    return 0
  fi

  if ! command -v bun &>/dev/null; then
    log_warning "bun not installed, skipping Bun apps"
    return 0
  fi

  # Force clean if requested
  if [[ "$FORCE" == "true" ]]; then
    log_info "Force rebuild: removing node_modules and lock files..."
    rm -rf "$APPS_DIR/node_modules"
    for app_dir in "$APPS_DIR"/*/; do
      if [[ -f "${app_dir}package.json" ]]; then
        rm -rf "${app_dir}node_modules"
      fi
    done
  fi

  # Install workspace dependencies
  log_info "Installing Bun workspace dependencies..."
  cd "$APPS_DIR"
  if [[ -f "bun.lock" ]]; then
    bun install --frozen-lockfile 2>/dev/null || bun install
  else
    bun install
  fi

  # Generate wrapper scripts for each app
  log_info "Generating Bun app wrappers..."

  for app_dir in "$APPS_DIR"/*/; do
    app_name="$(basename "$app_dir")"
    
    # Skip non-bun directories
    [[ "$app_name" == "shared" ]] && continue
    [[ ! -f "${app_dir}package.json" ]] && continue
    
    # Skip if it's a Go app (has go.mod)
    [[ -f "${app_dir}go.mod" ]] && continue
    
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
}

# ============================================================================
# Go Apps
# ============================================================================
build_go_apps() {
  if ! command -v go &>/dev/null; then
    log_warning "go not installed, skipping Go apps"
    return 0
  fi

  local found_go_apps=false
  
  for app_dir in "$APPS_DIR"/*/; do
    app_name="$(basename "$app_dir")"
    
    # Check if it's a Go app
    [[ ! -f "${app_dir}go.mod" ]] && continue
    
    found_go_apps=true
    
    # Determine binary name
    # Apps with shell wrappers get _ prefix (internal/hidden)
    # These apps have shell functions that wrap the binary
    case "$app_name" in
      aws-login)
        # aws-login has a shell wrapper in aws.zsh
        binary_name="_${app_name}"
        ;;
      *)
        binary_name="$app_name"
        ;;
    esac
    
    binary_path="$BIN_DIR/$binary_name"
    
    # Check if rebuild needed (skip if binary newer than all source files)
    if [[ "$FORCE" != "true" ]] && [[ -f "$binary_path" ]]; then
      newest_source=$(find "$app_dir" -name '*.go' -newer "$binary_path" 2>/dev/null | head -1)
      if [[ -z "$newest_source" ]]; then
        log_info "Go app $app_name is up to date"
        continue
      fi
    fi
    
    log_info "Building Go app: $app_name"
    
    if (cd "$app_dir" && go build -o "$binary_path" .); then
      log_info "Built: $app_name -> $BIN_DIR/$binary_name"
    else
      log_warning "Failed to build $app_name"
    fi
  done
  
  if [[ "$found_go_apps" == "false" ]]; then
    log_info "No Go apps found"
  fi
}

# ============================================================================
# Main
# ============================================================================
if [[ ! -d "$APPS_DIR" ]]; then
  log_error "Apps directory not found: $APPS_DIR"
  exit 1
fi

build_bun_apps
build_go_apps

log_info "Build complete!"
