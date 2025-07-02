#TODO: Themes don't change the UI
- Investigate the issue and identify the root cause
- Implement a fix for the theme switching functionality
- Test the fix to ensure it works as expected
- Update any relevant documentation
- Use snaphappy and target the Ghostty terminal that is running the doti tool to capture screenshots of the UI before and after the fix

#TODO: debug install_vscode_extensions.sh
When running the script manually: `./data/scripts/install_vscode_extensions.sh`
- The script runs successfully and installs the extensions as expected.
Logs:
```
 ./data/scripts/install_vscode_extensions.sh
[INFO] Starting VSCode Extensions Installation
[INFO] Extensions data directory: /Users/A200407315/dev/dotfiles/data/vscode_extensions
[INFO] VSCode found: /opt/homebrew/bin/code
[INFO] Processing extension directory: tui_manager
[INFO] Packaging extension: tui_manager
 INFO  Files included in the VSIX:
tui_manager.vsix
├─ [Content_Types].xml
├─ extension.vsixmanifest
└─ extension/
   ├─ LICENSE.md [1.04 KB]
   ├─ extension.js [3.14 KB]
   ├─ extension.js.map [2.31 KB]
   └─ package.json [1.31 KB]

 DONE  Packaged: tui_manager.vsix (6 files, 4.51 KB)
[INFO] Successfully packaged tui_manager.vsix
[INFO] VSIX file created: /Users/A200407315/dev/dotfiles/data/vscode_extensions/tui_manager/tui_manager.vsix
[INFO] Installing extension: tui_manager
Installing extensions...
Extension 'tui_manager.vsix' was successfully installed.
[INFO] Successfully installed tui_manager
[INFO] Cleaned up /Users/A200407315/dev/dotfiles/data/vscode_extensions/tui_manager/tui_manager.vsix
[INFO] Installation complete!
[INFO] Successfully installed: 1 extensions
[INFO] All extensions processed
```

When running with our dotfiles tool: `./bin/dotfiles apps sync --verbose`
- The script installs the extension but fails with exit code 1 and doesn't fully finish execution.
Logs:
```
Synchronizing apps...
❌
Error: failed to run some apps: vscode_extensions: script data/scripts/install_vscode_extensions.sh failed (step 1): execution failed: exit status 1
Output: [INFO] Starting VSCode Extensions Installation
[INFO] Extensions data directory: /Users/A200407315/dev/dotfiles/data/vscode_extensions
[INFO] VSCode found: /opt/homebrew/bin/code
[INFO] Processing extension directory: tui_manager
[INFO] Packaging extension: tui_manager
 INFO  Files included in the VSIX:
tui_manager.vsix
├─ [Content_Types].xml
├─ extension.vsixmanifest
└─ extension/
   ├─ LICENSE.md [1.04 KB]
   ├─ extension.js [3.14 KB]
   ├─ extension.js.map [2.31 KB]
   └─ package.json [1.31 KB]

 DONE  Packaged: tui_manager.vsix (6 files, 4.51 KB)
[INFO] Successfully packaged tui_manager.vsix
[INFO] VSIX file created: /Users/A200407315/dev/dotfiles/data/vscode_extensions/tui_manager/tui_manager.vsix
[INFO] Installing extension: tui_manager
Installing extensions...
Extension 'tui_manager.vsix' was successfully installed.
[INFO] Successfully installed tui_manager
```

As we can see there are missing logs:
```
[INFO] Cleaned up /Users/A200407315/dev/dotfiles/data/vscode_extensions/tui_manager/tui_manager.vsix
[INFO] Installation complete!
[INFO] Successfully installed: 1 extensions
[INFO] All extensions processed
```

UNDERSTAND the issue
PLAN a fix
REFACTOR the script to ensure it works correctly with our dotfiles tool
TEST the fix by running the script with our dotfiles tool again
EXPECTATION we want this script to work correctly and to be able to be run in any state and it should work. We will be running everything automatically so we need our code to work in any state.

#TODO: config.go while we have config/dotfiles/config.yaml is confusing
