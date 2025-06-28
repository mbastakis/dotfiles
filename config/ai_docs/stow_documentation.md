# GNU Stow Documentation

## Overview

GNU Stow is a symlink farm manager which takes distinct sets of software and/or data located in separate directories on the filesystem, and makes them appear to be installed in a single directory tree. It's particularly useful for managing dotfiles by creating symlinks from a centralized repository to their expected locations.

## How Stow Works

### Basic Concept
Stow creates symbolic links from a "stow directory" (where your files are organized) to a "target directory" (where the files should appear to be installed). The key principle is that Stow mirrors the directory structure - if you have a file at `stow_dir/package/foo/bar.txt`, it will create a symlink at `target_dir/foo/bar.txt` pointing to the original file.

### Tree Folding
Rather than creating individual symlinks for each file, Stow will create a single symlink for an entire directory when possible. This is called "tree folding" - an entire subtree is "folded" into a single symlink. This reduces the number of symlinks and makes the system more efficient.

### Safety Features
Stow is designed to be completely safe:
- It will never overwrite files it doesn't "own"
- It performs conflict detection before making any changes
- It uses a two-phase algorithm: scan for conflicts first, then execute operations
- All operations can be simulated before execution

## Command Line Interface

### Basic Syntax
```bash
stow [OPTIONS] PACKAGE1 [PACKAGE2 ...]
```

### Common Options

#### Core Operations
- **No option (default)**: Install/stow packages
- **`-D, --delete`**: Delete/unstow packages
- **`-R, --restow`**: Restow packages (unstow then stow again)

#### Directory Control
- **`-d DIR, --dir=DIR`**: Set stow directory (default: current directory)
- **`-t DIR, --target=DIR`**: Set target directory (default: parent of stow directory)

#### Simulation and Testing
- **`-n, --no, --simulate`**: Don't actually make changes, just show what would be done
- **`-v, --verbose[=LEVEL]`**: Increase verbosity (can be repeated or set level 0-5)

#### Tree Management
- **`--no-folding`**: Disable tree folding (create individual symlinks instead of directory symlinks)
- **`--ignore=REGEX`**: Ignore files matching REGEX

#### Conflict Resolution
- **`--adopt`**: Move existing files into stow package instead of reporting conflicts
- **`--defer=REGEX`**: Don't stow files matching REGEX if already stowed elsewhere
- **`--override=REGEX`**: Force stowing files matching REGEX even if conflicts exist

#### Special Handling
- **`--dotfiles`**: Enable special handling for dotfiles (convert 'dot-' prefix to '.')

## Examples

### Basic Usage
```bash
# From within your dotfiles directory
cd ~/.dotfiles
stow vim        # Stow vim package to parent directory (~)
stow git zsh    # Stow multiple packages

# Specify directories explicitly
stow -d ~/.dotfiles -t ~ vim

# Simulate before actual operation
stow -n vim

# Remove/unstow packages
stow -D vim

# Restow (useful after adding new files)
stow -R vim
```

### Directory Structure Example
```
~/.dotfiles/              # Stow directory
├── vim/                  # Package directory
│   └── .vimrc           # Will link to ~/.vimrc
├── git/
│   ├── .gitconfig       # Will link to ~/.gitconfig
│   └── .gitignore_global
└── zsh/
    ├── .zshrc           # Will link to ~/.zshrc
    └── .oh-my-zsh/      # Entire directory will be linked
        └── themes/
```

Running `stow vim git zsh` creates:
```
~/
├── .vimrc -> .dotfiles/vim/.vimrc
├── .gitconfig -> .dotfiles/git/.gitconfig
├── .gitignore_global -> .dotfiles/git/.gitignore_global
├── .zshrc -> .dotfiles/zsh/.zshrc
└── .oh-my-zsh -> .dotfiles/zsh/.oh-my-zsh/
```

### Advanced Examples

#### Using --dotfiles for Hidden Files
```bash
# Package structure with dot- prefix
package/
├── dot-bashrc           # Will become ~/.bashrc
├── dot-vimrc           # Will become ~/.vimrc
└── dot-config/         # Will become ~/.config/
    └── nvim/
        └── init.vim

stow --dotfiles package
```

#### Handling Conflicts with --adopt
```bash
# If ~/.vimrc already exists and you want to move it into your package
stow --adopt vim

# This moves the existing ~/.vimrc to ~/.dotfiles/vim/.vimrc
# Then creates the symlink as normal
```

#### Complex Directory Structures
```bash
# For packages that mirror complex directory structures
package/
└── .config/
    ├── git/
    │   └── config
    └── nvim/
        └── init.lua

stow package  # Creates ~/.config/git/config and ~/.config/nvim/init.lua symlinks
```

## Conflict Detection and Resolution

### What Causes Conflicts
1. **File exists where symlink needed**: A regular file exists at the target location
2. **Directory exists where file symlink needed**: A directory exists where Stow wants to place a file symlink
3. **Symlink points elsewhere**: A symlink exists but points to a different location
4. **Mixed ownership**: Files owned by different packages in the same directory

### Conflict Messages
```bash
$ stow package
WARNING! stowing package would cause conflicts:
  * existing target is neither a link nor a directory: .vimrc
All operations aborted.
```

### Resolution Strategies

#### 1. Manual Resolution
Remove or move the conflicting files manually, then run stow again.

#### 2. Using --adopt
```bash
stow --adopt package
```
Moves existing files into the package directory, then creates symlinks.

#### 3. Using --override (Advanced)
```bash
stow --override='\.vimrc' package
```
Forces stowing even if conflicts exist for files matching the regex.

## Ignore Files

### .stow-local-ignore
Create this file in your stow directory or package directory to ignore files:

```bash
# .stow-local-ignore
\.git
\.gitignore
README\.md
\.DS_Store
.*\.backup\..*    # Ignore backup files
```

### Default Ignores
Stow automatically ignores:
- CVS directories
- .#* (temporary files)
- #*# (emacs backup files)
- *~ (backup files)

## Best Practices

### 1. Directory Organization
```bash
~/.dotfiles/
├── git/           # Package per tool/application
├── vim/
├── zsh/
├── tmux/
└── config/        # For ~/.config/* files
    └── .config/
        ├── nvim/
        ├── git/
        └── tmux/
```

### 2. Safe Operations
Always test with `--simulate` first:
```bash
stow -n package    # Check what would happen
stow package       # Actually do it
```

### 3. Package Management
```bash
# Enable packages selectively
stow vim git       # Only what you need

# Update after changes
stow -R package    # Restow to pick up new files

# Clean removal
stow -D package    # Remove all symlinks
```

### 4. Version Control Integration
```bash
# In your dotfiles repo
git add .
git commit -m "Add new vim configuration"
stow -R vim        # Restow to pick up changes
```

## Common Patterns for Dotfiles

### Pattern 1: Simple Package per Tool
```
dotfiles/
├── git/.gitconfig
├── vim/.vimrc
└── zsh/.zshrc
```

### Pattern 2: Config Directory Structure
```
dotfiles/
└── config/
    └── .config/
        ├── git/config
        ├── nvim/init.lua
        └── tmux/tmux.conf
```

### Pattern 3: Mixed Approach
```
dotfiles/
├── git/.gitconfig           # Home directory files
├── vim/.vimrc
└── config/                  # XDG config files
    └── .config/
        └── nvim/init.lua
```

## Troubleshooting

### Common Issues

#### 1. "Target is not owned by stow"
This means a file/directory exists that wasn't created by stow.
```bash
# Solution: Use --adopt or manually resolve
stow --adopt package
```

#### 2. "Too many levels of symbolic links"
Indicates circular symlinks or broken symlinks.
```bash
# Solution: Find and remove circular symlinks
find ~ -type l -exec test ! -e {} \; -print  # Find broken symlinks
```

#### 3. "Package not found"
The package directory doesn't exist.
```bash
# Solution: Check directory structure
ls -la stow_directory/
```

### Debugging Commands
```bash
# Verbose output to see what stow is doing
stow -v package

# Simulate to see planned operations
stow -n -v package

# Check current symlinks
find ~ -type l -ls | grep dotfiles
```

## Integration with Other Tools

### Git Hooks
```bash
#!/bin/bash
# .git/hooks/post-merge
# Automatically restow packages after git pull

stow -R vim git zsh config
```

### Shell Aliases
```bash
# Add to .bashrc or .zshrc
alias restow='cd ~/.dotfiles && stow -R *'
alias unstow='cd ~/.dotfiles && stow -D *'
```

## Advanced Features

### Package Dependencies
While Stow doesn't have built-in dependency management, you can create wrapper scripts:

```bash
#!/bin/bash
# install-dev-environment.sh

stow git           # Install git config first
stow vim           # Then vim (which might reference git config)
stow zsh           # Finally shell config
```

### Conditional Stowing
```bash
#!/bin/bash
# Stow packages based on system

if [[ "$OSTYPE" == "darwin"* ]]; then
    stow macos
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    stow linux
fi

stow common git vim  # Always install these
```

## Performance Considerations

### Tree Folding Benefits
- Fewer symlinks to manage
- Faster filesystem operations
- Cleaner output from `ls -la`

### When to Use --no-folding
- When you need individual file control
- When other tools expect individual symlinks
- For debugging symlink issues

## Summary

GNU Stow provides a robust, safe, and efficient way to manage dotfiles through symlinks. Its key strengths are:

1. **Safety**: Never overwrites files it doesn't own
2. **Efficiency**: Uses tree folding to minimize symlinks
3. **Flexibility**: Handles complex directory structures
4. **Simplicity**: Clean command-line interface
5. **Reliability**: Battle-tested conflict detection

By understanding these principles and following best practices, you can create a maintainable and portable dotfiles management system.