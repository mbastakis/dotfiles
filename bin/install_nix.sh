#!/usr/bin/env bash

set -euo pipefail

if command -v nix >/dev/null 2>&1; then
    echo "Nix is already installed."
else
    echo "Installing Nix package manager..."
    curl -L https://nixos.org/nix/install | sh
    echo "Nix installation complete."
fi

# Install Nix Flakes
if [ -f "$HOME/.config/nix-darwin/flake.nix" ]; then
  echo "Nix Flakes are already set up."
  cd "$HOME/.config/nix-darwin" || exit 1
  sudo nix run nix-darwin --extra-experimental-features 'nix-command flakes' -- switch --flake .#simple
  cd - || exit 1
else
  echo "Nix Flakes are not set up."
fi
