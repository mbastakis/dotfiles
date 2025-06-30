# TODO: VSCode Extensions Installation Script
CREATE data/scripts/install_vscode_extensions.sh
This script will install the VSCode extensions listed in: data/vscode_extensions/
data/vscode_extensions is a directory containing many extensions with a .vsix file.
The script should:
USE the vsce command to install each extension.
The script should be executable.
This script should be added in the config: config/config/dotfiles/config.yaml at the app tool.

# TODO: Refactor go code to use my name
Currently the go code uses yourusername as the author name and package name.
We need to change this to use my name and package name.
My name is: mbastakis
SEARCH 
All instances of "yourusername" in the Go code.
REPLACE 
All instances of "yourusername" with "mbastakis".
UPDATE 
The package name to match my name if necessary.
TEST 
The code to ensure it works with the new name.
