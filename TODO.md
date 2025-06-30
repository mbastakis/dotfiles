# TODO: VSCode Extensions Installation Script
CREATE data/scripts/install_vscode_extensions.sh
This script will install the VSCode extensions listed in: data/vscode_extensions/
data/vscode_extensions is a directory containing many extensions with a .vsix file.
The script should:
USE the vsce command to install each extension.
The script should be executable.
This script should be added in the config: config/config/dotfiles/config.yaml at the app tool.

#TODO: Add ai_docs and specs to the config
The ai_docs and specs directories are not included in the config.yaml file.
They exist in the config/ai_docs and config/specs directories.
They should be added to the config.yaml file in the stow tool.

#TODO: Fix dotfiles TUI keybindings
Currently, the keybindings in the TUI view for dotfiles are not working as expected.
We see in the footer of the TUI view that the keybindings: [r] refresh, [i] install, [u] update, [s] sync, ...
However in different tools the keybindings are not working as expected and are not consistent.
Sometimes the Enter key is used to install or sync, sometimes the 'i' key is used, and sometimes the 's' key is used.
PLAN we need to read the relevant files and understand all of the actions we can perform in the TUI view.
REFLECT on the keybindings and make them consistent across all tools.
WRITE refactor the keybindings in the TUI view to be consistent and intuitive and make them work as expected.

#TODO: Fix progress in tui view
Currently, when we run tools in the TUI view, we don't see any progress so we don't know if anything is running.
We need to fix this so that we can see the progress of the tools in the TUI
For example, in stow tool if I install or sync or update the tools, I don't see any progress in the TUI view.
We should see the progress of the tools in the TUI view, so we know something is running in the background.
