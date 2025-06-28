# Git Configuration

This directory contains Git configuration files that are automatically symlinked to your home directory using GNU Stow.

## Files

- `.gitconfig` - Main Git configuration with conditional includes
- `.gitconfig-work` - Work-specific Git configuration (used for repos in `~/dev/work/`)
- `.gitconfig-personal` - Personal Git configuration (used for repos in `~/dev/personal/`)

## How it works

The main `.gitconfig` file uses Git's `includeIf` directive to conditionally load different configurations based on the repository location:

- Repositories in `~/dev/work/` will use the work email and settings
- Repositories in `~/dev/personal/` will use the personal email and settings
- All other repositories will use the default settings from the main `.gitconfig`

## Setup

These files are automatically symlinked when you run `./bootstrap.sh` or can be manually linked using:

```bash
stow --adopt -v --no-folding -t "$HOME" git
```

## Testing

To verify the configuration is working correctly:

```bash
# Test work configuration
cd ~/dev/work/some-repo
git config user.email  # Should show work email

# Test personal configuration  
cd ~/dev/personal/some-repo
git config user.email  # Should show personal email

# Test default configuration
cd ~/some-other-location
git config user.email  # Should show default email
```
