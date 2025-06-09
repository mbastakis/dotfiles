# Obsidian Configuration

This directory contains your Obsidian configuration that will be symlinked to your Obsidian vaults.

## Setup

To link your Obsidian configuration to a vault, run:

```bash
./bin/setup_obsidian
```

Or if you're setting up during the initial bootstrap:

```bash
./bootstrap.sh
```

## How it works

1. Your Obsidian configuration is stored in `dotfiles/obsidian/.obsidian/`
2. The setup script creates a symlink from your vault's `.obsidian` directory to this configuration
3. Any changes you make in Obsidian's settings will be reflected in your dotfiles
4. You can commit and push these changes to keep your Obsidian settings in sync across machines

## Manual Setup

If you need to manually link a vault:

```bash
# Replace /path/to/your/vault with your actual vault path
ln -sf /Users/A200407315/dev/dotfiles/obsidian/.obsidian /path/to/your/vault/.obsidian
```

## Multiple Vaults

You can link the same configuration to multiple vaults. Each vault will share the same settings, which is useful for maintaining consistency across different Obsidian vaults.

## Backup

The setup script automatically backs up any existing `.obsidian` configuration before creating the symlink. Backups are timestamped and stored in the same directory as your vault.
