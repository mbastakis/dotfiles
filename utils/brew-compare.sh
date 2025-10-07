#!/usr/bin/env bash

set -euo pipefail

FLAKE_PATH="${1:-$HOME/dev/dotfiles/dot-config/nix-darwin/flake.nix}"

if [[ ! -f "$FLAKE_PATH" ]]; then
  echo "Error: flake.nix not found at $FLAKE_PATH"
  exit 1
fi

log_info() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
log_success() { echo -e "\033[1;32m[✓]\033[0m $*"; }
log_warning() { echo -e "\033[1;33m[!]\033[0m $*"; }
log_error() { echo -e "\033[1;31m[✗]\033[0m $*"; }

extract_brews() {
  awk '/homebrew\.brews = \[/,/\];/' "$FLAKE_PATH" | \
    grep -o '"[^"]*"' | \
    tr -d '"' | \
    sed 's|.*/||' | \
    sort -u
}

extract_casks() {
  awk '/homebrew\.casks = \[/,/\];/' "$FLAKE_PATH" | \
    grep -o '"[^"]*"' | \
    tr -d '"' | \
    sort -u
}

get_installed_brews() {
  brew list --formula -1 | sort -u
}

get_installed_casks() {
  brew list --cask -1 | sort -u
}

log_info "Extracting brew packages from $FLAKE_PATH..."
flake_brews=()
while IFS= read -r line; do
  [[ -n "$line" ]] && flake_brews+=("$line")
done < <(extract_brews)

flake_casks=()
while IFS= read -r line; do
  [[ -n "$line" ]] && flake_casks+=("$line")
done < <(extract_casks)

log_info "Getting installed brew packages..."
installed_brews=()
while IFS= read -r line; do
  [[ -n "$line" ]] && installed_brews+=("$line")
done < <(get_installed_brews)

installed_casks=()
while IFS= read -r line; do
  [[ -n "$line" ]] && installed_casks+=("$line")
done < <(get_installed_casks)

echo ""
log_info "=== BREW FORMULAS COMPARISON ==="
echo ""

missing_brews=()
for brew in "${flake_brews[@]}"; do
  if ! printf '%s\n' "${installed_brews[@]}" | grep -qx "$brew"; then
    missing_brews+=("$brew")
  fi
done

extra_brews=()
for brew in "${installed_brews[@]}"; do
  if ! printf '%s\n' "${flake_brews[@]}" | grep -qx "$brew"; then
    extra_brews+=("$brew")
  fi
done

if [[ ${#missing_brews[@]} -gt 0 ]]; then
  log_warning "Missing from system (in flake.nix but not installed):"
  printf '  %s\n' "${missing_brews[@]}"
  echo ""
else
  log_success "All flake brews are installed"
  echo ""
fi

if [[ ${#extra_brews[@]} -gt 0 ]]; then
  log_warning "Extra on system (installed but not in flake.nix):"
  printf '  %s\n' "${extra_brews[@]}"
  echo ""
else
  log_success "No extra brews on system"
  echo ""
fi

echo ""
log_info "=== BREW CASKS COMPARISON ==="
echo ""

missing_casks=()
for cask in "${flake_casks[@]}"; do
  if ! printf '%s\n' "${installed_casks[@]}" | grep -qx "$cask"; then
    missing_casks+=("$cask")
  fi
done

extra_casks=()
for cask in "${installed_casks[@]}"; do
  if ! printf '%s\n' "${flake_casks[@]}" | grep -qx "$cask"; then
    extra_casks+=("$cask")
  fi
done

if [[ ${#missing_casks[@]} -gt 0 ]]; then
  log_warning "Missing from system (in flake.nix but not installed):"
  printf '  %s\n' "${missing_casks[@]}"
  echo ""
else
  log_success "All flake casks are installed"
  echo ""
fi

if [[ ${#extra_casks[@]} -gt 0 ]]; then
  log_warning "Extra on system (installed but not in flake.nix):"
  printf '  %s\n' "${extra_casks[@]}"
  echo ""
else
  log_success "No extra casks on system"
  echo ""
fi

echo ""
log_info "=== SUMMARY ==="
echo "Flake brews: ${#flake_brews[@]}"
echo "Installed brews: ${#installed_brews[@]}"
echo "Missing brews: ${#missing_brews[@]}"
echo "Extra brews: ${#extra_brews[@]}"
echo ""
echo "Flake casks: ${#flake_casks[@]}"
echo "Installed casks: ${#installed_casks[@]}"
echo "Missing casks: ${#missing_casks[@]}"
echo "Extra casks: ${#extra_casks[@]}"
