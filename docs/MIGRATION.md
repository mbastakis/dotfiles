# Migration Guide

This guide helps you migrate from the legacy dotfiles system to the new TUI-based manager.

## Overview

The new dotfiles TUI manager provides a modern, interactive interface for managing your dotfiles with enhanced features:

- **Interactive TUI**: User-friendly terminal interface
- **Advanced Theming**: Customizable color schemes and styles
- **Performance Optimization**: Efficient operations with caching and monitoring
- **Comprehensive Testing**: Full test coverage for reliability
- **Tool Integration**: Support for multiple package managers and tools

## Migration Checklist

### Phase 1: Backup and Preparation

1. **Backup Current Configuration**
   ```bash
   # Backup your current dotfiles directory
   cp -r ~/.dotfiles ~/.dotfiles.backup
   
   # Backup any existing configuration files
   cp ~/.config/dotfiles/config.yaml ~/.config/dotfiles/config.yaml.backup
   ```

2. **Install Dependencies**
   ```bash
   # Ensure Go is installed (version 1.19+)
   go version
   
   # Install required tools
   # ... (tool-specific installation instructions)
   ```

3. **Download New Version**
   ```bash
   # Clone or download the new dotfiles manager
   git clone <repository-url> ~/dotfiles-new
   cd ~/dotfiles-new
   ```

### Phase 2: Configuration Migration

#### Legacy Configuration Format

If you have an existing configuration, it likely looks like this:

```yaml
# Legacy format (~/.dotfiles/config.yaml)
packages:
  - name: vim
    enabled: true
  - name: zsh
    enabled: true

settings:
  auto_confirm: false
  backup_enabled: true
```

#### New Configuration Format

The new format provides more structure and options:

```yaml
# New format (~/.config/dotfiles/config.yaml)
global:
  dotfiles_path: "/Users/username/.dotfiles"
  log_level: "info"
  dry_run: false
  auto_confirm: false
  backup_enabled: true
  backup_suffix: ".backup"

tui:
  color_scheme: "default"
  animations: true
  confirm_destructive: true
  show_progress: true

stow:
  packages:
    - name: "vim"
      target: "/Users/username"
      enabled: true
      priority: 1
    - name: "zsh"
      target: "/Users/username"
      enabled: true
      priority: 2

tools:
  homebrew:
    enabled: true
    auto_update: false
  npm:
    enabled: true
    global_packages: true
```

#### Migration Script

Use the provided migration script to convert your configuration:

```bash
# Run the configuration migration
./scripts/migrate-config.sh ~/.dotfiles/config.yaml ~/.config/dotfiles/config.yaml
```

### Phase 3: Theme Migration

#### Legacy Theme System

The legacy system had basic color support:

```bash
# Legacy theme switching
export DOTFILES_THEME=dark
```

#### New Theme System

The new system provides comprehensive theme management:

```yaml
# Custom theme definition
themes:
  my-custom-theme:
    primary: "#007acc"
    secondary: "#4ec9b0"
    success: "#4ec9b0"
    warning: "#ffcc02"
    error: "#f14c4c"
    background: "#1e1e1e"
    foreground: "#d4d4d4"
```

**Migration Steps:**

1. **Export Current Colors** (if applicable)
   ```bash
   # Extract current theme settings
   ./scripts/export-theme.sh > my-theme.yaml
   ```

2. **Import to New System**
   ```bash
   # Import theme to new system
   ./scripts/import-theme.sh my-theme.yaml
   ```

3. **Set Default Theme**
   ```bash
   # Set your preferred theme
   dotfiles theme set my-custom-theme
   ```

### Phase 4: Package Migration

#### Stow Package Migration

If you're using GNU Stow, your packages should mostly work as-is:

1. **Verify Package Structure**
   ```
   ~/.dotfiles/
   ├── vim/
   │   └── .vimrc
   ├── zsh/
   │   ├── .zshrc
   │   └── .zsh/
   └── git/
       └── .gitconfig
   ```

2. **Update Package Configuration**
   ```yaml
   stow:
     packages:
       - name: "vim"
         target: "/Users/username"
         enabled: true
         priority: 1
         # Optional: specific files to include/exclude
         include:
           - ".vimrc"
           - ".vim/"
         exclude:
           - ".vim/temp/"
   ```

3. **Test Package Installation**
   ```bash
   # Test in dry-run mode first
   dotfiles --dry-run sync
   
   # Apply changes
   dotfiles sync
   ```

#### Tool-Specific Migrations

**Homebrew Migration:**
```bash
# Export current packages
brew bundle dump --file=Brewfile.backup

# Import to new system
dotfiles tools homebrew import Brewfile.backup
```

**NPM Migration:**
```bash
# Export global packages
npm list -g --depth=0 > npm-packages.txt

# Import to new system
dotfiles tools npm import npm-packages.txt
```

### Phase 5: Testing and Validation

#### Pre-Migration Testing

1. **Run Tests**
   ```bash
   # Run the test suite
   go test ./...
   
   # Run integration tests
   go test -tags=integration ./test/integration/
   ```

2. **Dry Run Migration**
   ```bash
   # Test migration without making changes
   dotfiles migrate --dry-run --from ~/.dotfiles.backup
   ```

#### Post-Migration Validation

1. **Verify Configuration**
   ```bash
   # Check configuration is loaded correctly
   dotfiles config validate
   
   # Show current configuration
   dotfiles config show
   ```

2. **Test Core Functions**
   ```bash
   # Test package management
   dotfiles packages list
   dotfiles packages status
   
   # Test tool integration
   dotfiles tools status
   
   # Test theme system
   dotfiles themes list
   dotfiles themes current
   ```

3. **Verify File Links**
   ```bash
   # Check that symlinks are correct
   ls -la ~/ | grep -E '\->'
   
   # Verify file contents
   diff ~/.vimrc ~/.dotfiles/vim/.vimrc
   ```

### Phase 6: Advanced Features

#### Performance Monitoring

Enable performance monitoring for large configurations:

```yaml
performance:
  monitoring_enabled: true
  cache_enabled: true
  profiling_enabled: false  # Enable only for debugging
```

#### Custom Tool Integration

Add custom tools to the system:

```go
// Example: Custom tool implementation
type MyTool struct {
    name string
}

func (t *MyTool) Name() string { return t.name }
func (t *MyTool) IsEnabled() bool { return true }
// ... implement other Tool interface methods
```

## Common Migration Issues

### Issue 1: Symlink Conflicts

**Problem**: Existing symlinks conflict with new package management.

**Solution**:
```bash
# Remove conflicting symlinks
dotfiles clean --dry-run  # Preview changes
dotfiles clean            # Remove conflicts

# Re-create with new system
dotfiles sync
```

### Issue 2: Permission Issues

**Problem**: Permission denied when creating symlinks.

**Solution**:
```bash
# Fix ownership
sudo chown -R $USER:$USER ~/.dotfiles

# Check target directory permissions
ls -la ~/
```

### Issue 3: Missing Dependencies

**Problem**: Tools or dependencies not found.

**Solution**:
```bash
# Install missing tools
dotfiles tools install-missing

# Or install specific tool
dotfiles tools homebrew install
```

### Issue 4: Configuration Validation Errors

**Problem**: New configuration format validation fails.

**Solution**:
```bash
# Validate configuration and show errors
dotfiles config validate --verbose

# Use migration helper
dotfiles migrate fix-config ~/.config/dotfiles/config.yaml
```

## Rollback Procedure

If you need to rollback to the legacy system:

1. **Stop New System**
   ```bash
   # Remove new symlinks
   dotfiles clean --all
   ```

2. **Restore Backup**
   ```bash
   # Restore original configuration
   cp ~/.dotfiles.backup/* ~/.dotfiles/
   cp ~/.config/dotfiles/config.yaml.backup ~/.config/dotfiles/config.yaml
   ```

3. **Re-apply Legacy System**
   ```bash
   # Use your legacy installation script
   ~/.dotfiles/install.sh
   ```

## Incremental Migration

For large configurations, consider incremental migration:

### Week 1: Core Packages
- Migrate essential packages (vim, zsh, git)
- Test basic functionality
- Verify symlinks work correctly

### Week 2: Development Tools
- Migrate development environment packages
- Configure tool integrations
- Test workflow compatibility

### Week 3: Advanced Features
- Set up custom themes
- Enable performance monitoring
- Configure automatic updates

### Week 4: Full Migration
- Migrate remaining packages
- Remove legacy system
- Document any customizations

## Support and Troubleshooting

### Getting Help

1. **Check Documentation**
   - [User Guide](./USER_GUIDE.md)
   - [Configuration Reference](./CONFIGURATION.md)
   - [Performance Guide](./PERFORMANCE.md)

2. **Debug Mode**
   ```bash
   # Run with debug logging
   dotfiles --log-level debug <command>
   
   # Enable verbose output
   dotfiles --verbose <command>
   ```

3. **Generate Support Bundle**
   ```bash
   # Create diagnostic information
   dotfiles support bundle > support-info.txt
   ```

### Reporting Issues

When reporting migration issues, include:
- Original configuration files
- Error messages and logs
- System information (OS, Go version, etc.)
- Steps to reproduce the issue

### Community Resources

- GitHub Issues: Report bugs and feature requests
- Wiki: Community-contributed guides and tips
- Discussions: Ask questions and share experiences

## Post-Migration Optimization

### Performance Tuning

After migration, optimize performance:

```bash
# Enable caching for large configurations
dotfiles config set performance.cache_enabled true

# Adjust cache sizes
dotfiles config set performance.cache_size 2000

# Enable monitoring
dotfiles config set performance.monitoring_enabled true
```

### Automation

Set up automation for maintenance:

```bash
# Add to crontab for daily updates
0 9 * * * /usr/local/bin/dotfiles sync --quiet

# Weekly tool updates
0 9 * * 1 /usr/local/bin/dotfiles tools update --all
```

### Custom Workflows

Create custom commands for your workflow:

```yaml
# Add to config.yaml
custom_commands:
  dev-setup:
    description: "Set up development environment"
    commands:
      - "dotfiles packages enable dev-*"
      - "dotfiles tools npm install"
      - "dotfiles sync"
```

This migration guide ensures a smooth transition to the new dotfiles TUI manager while preserving your existing configuration and customizations.