#!/bin/bash
# Strict mode for safer scripting
set -euo pipefail
IFS=$'\n\t'

# Check for Homebrew to be present, install if it's missing
if test ! "$(which brew)"; then
   echo "🍺 Installing Homebrew"
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"  
   brew update
 else
   echo "Homebrew is already installed."
fi