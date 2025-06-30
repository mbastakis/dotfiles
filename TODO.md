# TODO: VSCode Extensions Installation Script
CREATE data/scripts/install_vscode_extensions.sh
This script will install the VSCode extensions listed in: data/vscode_extensions/
data/vscode_extensions is a directory containing many extensions with a .vsix file.
The script should:
USE the vsce command to install each extension.
The script should be executable.
This script should be added in the config: config/config/dotfiles/config.yaml at the app tool.

# TODO: Fix Homebrew status
In the TUI app, the Homebrew status is not being displayed correctly.
This needs to be fixed so that the Homebrew status is shown correctly in the TUI app

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

# TODO: Fix taps in Homebrew
Currently the taps in Homebrew are not being handled correctly.
Check Homebrew apps, in there I have some taps like: "nikitabobko/tap/aerospace"
Let's create another Brewfile.tap file that will handle the taps.
This file should be added in the config: config/config/dotfiles/config.yaml
The taps should be installed using the Homebrew command.
We should gather all the taps from the Homebrew apps, core, dev and add them to the Brewfile.tap file.
We should add good status control to the taps, so that we can see if they are installed or not using brew cli command.
Status of the taps should be displayed in the TUI app and cli app.
Underastand how current tool handles Homebrew tool and keep the same structure and conventions.

# TODO: fix status for mas in Homebrew
Currently the status for mas in Homebrew is not being displayed correctly.
Since this is not a Homebrew app, we need to handle it separately.
Check the apps that are installed in my machine and check the mas list and compare. 
Use mas as much as possible to get the status of the apps.
