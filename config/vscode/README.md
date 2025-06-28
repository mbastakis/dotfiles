# VS Code Configuration

This directory contains VS Code configuration files managed as part of the dotfiles repository.

## Files

- **`settings.json`** - User settings for VS Code
- **`keybindings.json`** - Custom key bindings
- **`extensions.txt`** - List of installed extensions

## Setup

### Automatic Setup (Recommended)

Run the bootstrap script which will handle VS Code configuration:

```bash
./bootstrap.sh
```

### Manual Setup

1. **Set up symlinks** (creates links from VS Code config to dotfiles):
   ```bash
   ./bin/setup_vscode setup
   ```

2. **Sync existing config** (copies current VS Code config to dotfiles, then creates symlinks):
   ```bash
   ./bin/setup_vscode sync
   ```

3. **Install extensions** from the list:
   ```bash
   ./bin/setup_vscode extensions install
   ```

4. **Update extensions list** with currently installed extensions:
   ```bash
   ./bin/setup_vscode extensions update
   ```

## How It Works

The setup script creates symbolic links from VS Code's configuration directory to your dotfiles:

**macOS:**
- `~/Library/Application Support/Code/User/settings.json` → `~/dev/dotfiles/vscode/settings.json`
- `~/Library/Application Support/Code/User/keybindings.json` → `~/dev/dotfiles/vscode/keybindings.json`

**Linux:**
- `~/.config/Code/User/settings.json` → `~/dev/dotfiles/vscode/settings.json`
- `~/.config/Code/User/keybindings.json` → `~/dev/dotfiles/vscode/keybindings.json`

## Workflow

1. **Making Changes**: When you modify settings through VS Code's UI or directly edit the files, changes are automatically reflected in your dotfiles repository since they're symlinked.

2. **Committing Changes**: After making changes, commit them to your dotfiles repository:
   ```bash
   cd ~/dev/dotfiles
   git add vscode/
   git commit -m "Update VS Code configuration"
   git push
   ```

3. **Installing on New Machine**: Run the bootstrap script or manually run `./bin/setup_vscode setup` to create the symlinks.

4. **Keeping Extensions in Sync**: Regularly update your extensions list:
   ```bash
   ./bin/setup_vscode extensions update
   ```

## Extension Management

The `extensions.txt` file contains a list of all installed extensions. This allows you to:

- Keep track of which extensions you use
- Quickly install all extensions on a new machine
- Share your extension list with others

### Adding New Extensions

When you install new extensions through VS Code, update the list:

```bash
./bin/setup_vscode extensions update
```

Or manually:

```bash
code --list-extensions > vscode/extensions.txt
```

### Installing Extensions

To install all extensions from the list on a new machine:

```bash
./bin/setup_vscode extensions install
```

Or manually:

```bash
cat vscode/extensions.txt | xargs -L 1 code --install-extension
```

## Troubleshooting

### VS Code CLI Not Found

If you get errors about the `code` command not being found:

1. Open VS Code
2. Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
3. Run "Shell Command: Install 'code' command in PATH"

### Backup Files

The setup script automatically creates backups of existing configuration files before creating symlinks. Look for files with `.backup.YYYYMMDD_HHMMSS` suffix in the VS Code user directory.

### Permission Issues

If you encounter permission issues, ensure your user has write access to the VS Code configuration directory and your dotfiles directory.

## Best Practices

1. **Regular Updates**: Update your extensions list regularly to keep it in sync
2. **Commit Often**: Commit changes to your dotfiles repository frequently
3. **Test on Clean Install**: Occasionally test your setup on a clean machine or VM
4. **Document Custom Settings**: Add comments to your settings.json to explain custom configurations

## Related Files

- [`bin/setup_vscode`](../bin/setup_vscode) - Main setup script
- [`bin/update_dotfiles`](../bin/update_dotfiles) - Updates various dotfiles including VS Code extensions
- [`bootstrap.sh`](../bootstrap.sh) - Main installation script that includes VS Code setup
