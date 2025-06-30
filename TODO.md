# TODO: VSCode Extensions Installation Script
CREATE data/scripts/install_vscode_extensions.sh
This script will install the VSCode extensions listed in: data/vscode_extensions/
data/vscode_extensions is a directory containing many extensions with a .vsix file.
The script should:
USE the vsce command to install each extension.
The script should be executable.
This script should be added in the config: config/config/dotfiles/config.yaml at the app tool.
For now we only have one extension: data/vscode_extensions/tui_manager
this tui_manager/ is the out of a compiled VSCode extension.
We must use this script to add this extension to the VSCode installation.
