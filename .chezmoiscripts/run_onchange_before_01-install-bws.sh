#!/bin/bash
# Install the Bitwarden Secrets Manager CLI before templates need it.
# Desired version: 2.1.0

set -euo pipefail

BWS_VERSION="2.1.0"

if command -v bws &>/dev/null && [[ "$(bws --version 2>/dev/null)" == "bws ${BWS_VERSION}" ]]; then
    echo "BWS CLI ${BWS_VERSION} is already installed."
    exit 0
fi

echo "Installing Bitwarden Secrets Manager CLI ${BWS_VERSION}..."
if ! curl -fsSL https://bws.bitwarden.com/install.sh | BWS_VERSION="$BWS_VERSION" bash; then
    echo "Error: failed to install BWS ${BWS_VERSION}." >&2
    echo "Retry in an interactive terminal with: BWS_VERSION=${BWS_VERSION} curl -fsSL https://bws.bitwarden.com/install.sh | bash" >&2
    exit 1
fi

if ! command -v bws &>/dev/null; then
    echo "Error: BWS installation completed but 'bws' is not on PATH." >&2
    echo "Add '$HOME/.local/bin' to PATH or install BWS manually, then retry chezmoi." >&2
    exit 1
fi

if [[ "$(bws --version 2>/dev/null)" != "bws ${BWS_VERSION}" ]]; then
    echo "Error: expected BWS ${BWS_VERSION}, got '$(bws --version 2>/dev/null || echo unknown)'." >&2
    exit 1
fi

echo "BWS CLI ${BWS_VERSION} installed successfully."
