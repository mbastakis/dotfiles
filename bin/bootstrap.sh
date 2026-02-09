#!/usr/bin/env bash
set -euo pipefail

# bootstrap.sh — First-time setup for a new machine.
#
# Usage:
#   curl -fsLS https://raw.githubusercontent.com/<user>/dotfiles/main/bin/bootstrap.sh | bash
#   — or —
#   bash <(curl -fsLS ...) [--profile personal|work]
#
# What it does:
#   1. Installs Homebrew (if missing)
#   2. Installs chezmoi + age via Homebrew
#   3. Prompts for your age secret key (the single unlock secret)
#   4. Runs chezmoi init --apply (single pass — everything resolves)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }

CHEZMOI_CONFIG_DIR="$HOME/.config/chezmoi"
AGE_KEY_FILE="$CHEZMOI_CONFIG_DIR/key.txt"
GITHUB_USER="mbastakis"

# Parse arguments
PROFILE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    *) log_error "Unknown argument: $1"; exit 1 ;;
  esac
done

# 1. Install Homebrew
if ! command -v brew &>/dev/null; then
  log_info "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
else
  log_info "Homebrew already installed."
fi

# 2. Install chezmoi + age
for tool in chezmoi age; do
  if ! command -v "$tool" &>/dev/null; then
    log_info "Installing $tool..."
    brew install "$tool"
  else
    log_info "$tool already installed."
  fi
done

# 3. Set up age identity (the single unlock secret)
if [[ -f "$AGE_KEY_FILE" ]]; then
  log_info "Age key already exists at $AGE_KEY_FILE"
else
  mkdir -p "$CHEZMOI_CONFIG_DIR"
  echo ""
  log_warn "Age secret key required to decrypt secrets."
  log_warn "Retrieve it from Bitwarden or your memory."
  echo ""
  printf "Paste your age secret key (AGE-SECRET-KEY-...): "
  IFS= read -r -s age_key
  printf "\n"

  if [[ ! "$age_key" =~ ^AGE-SECRET-KEY- ]]; then
    log_error "Invalid age key format. Must start with AGE-SECRET-KEY-"
    exit 1
  fi

  cat > "$AGE_KEY_FILE" << EOF
# chezmoi age identity
$age_key
EOF
  chmod 600 "$AGE_KEY_FILE"
  log_info "Age key saved to $AGE_KEY_FILE"
fi

# 4. chezmoi init + apply (single pass)
#    age key decrypts SSH keys directly
#    chezmoi-bws wrapper decrypts BWS token from bin/bws_token.age using same age key
#    bitwardenSecrets template calls resolve immediately
log_info "Running chezmoi init --apply..."

init_args=(--apply)
if [[ -n "$PROFILE" ]]; then
  init_args+=(--promptString "profile=$PROFILE")
fi

chezmoi init "$GITHUB_USER" "${init_args[@]}"

# 5. Done
echo ""
log_info "Bootstrap complete!"
echo ""
echo "  What was set up:"
echo "    - SSH keys decrypted and deployed"
echo "    - BWS secrets resolved into shell config"
echo "    - All dotfiles applied"
echo ""
echo "  Next steps:"
echo "    1. Open a new terminal to load the updated shell config"
echo "    2. Run: brew bundle --file=\$HOME/.local/share/chezmoi/Brewfile"
echo "       (installs MAS apps that require interactive login)"
echo ""
