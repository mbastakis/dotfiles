# TODO: VSCode Extensions Installation Script
CREATE data/scripts/install_vscode_extensions.sh
This script will install the VSCode extensions listed in: data/vscode_extensions/
data/vscode_extensions is a directory containing many extensions with a .vsix file.
The script should:
USE the vsce command to install each extension.
The script should be executable.
This script should be added in the config: config/config/dotfiles/config.yaml at the app tool.

#TODO: Fix progress in tui view
Currently, when we run tools in the TUI view, we don't see any progress so we don't know if anything is running.
We need to fix this so that we can see the progress of the tools in the TUI
For example, in stow tool if I install or sync or update the tools, I don't see any progress in the TUI view.
We should see the progress of the tools in the TUI view, so we know something is running in the background.

#TODO: Fix the stow tool status
Currently, the stow tool status is not working properly in the TUI view.
We need to fix this so that we can see the status of the each package of the stow tool in the TUI view.
For example I see that the files for package 'config' exist in `~/.config/` but the status is not showing that.
We should see the status of each package in the TUI view, so we know the status
