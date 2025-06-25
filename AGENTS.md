# AGENTS.md - Coding Agent Guidelines

## Build/Test/Lint Commands
- No package.json or traditional build system - this is a dotfiles repository
- Main entry point: `./bin/dotfiles COMMAND` (unified interface)
- Bootstrap: `./bootstrap.sh [OPTIONS]` (full system setup)
- Test individual components: `./bin/dotfiles COMPONENT --dry-run`
- Lint shell scripts: Use `shellcheck` if available

## Unified Command Interface
All operations use the main `./bin/dotfiles` script:
- `./bin/dotfiles bootstrap --all` - Full system setup
- `./bin/dotfiles update` - Update all components
- `./bin/dotfiles stow -a` - Link all configurations
- `./bin/dotfiles brew install -c dev` - Install dev tools
- `./bin/dotfiles vscode sync` - Sync VS Code settings
- `./bin/dotfiles status` - Show system status

## Code Style Guidelines

### Shell Scripts (Bash/ZSH)
- Use `#!/usr/bin/env bash` shebang for `/bin` scripts
- Set strict mode: `set -euo pipefail` and `IFS=$'\n\t'`
- Always source `scripts/utils.sh` and call `init_utils`
- Use CLI argument parsing with `parse_args()` from utils
- Support `--verbose`, `--dry-run`, `-y/--yes`, `--help` flags
- Use logging functions: `log_info()`, `log_warning()`, `log_error()`, `log_section()`

### File Organization
- `/bin/` - User-facing automation scripts with full CLI support
- `/scripts/` - Internal setup/installation scripts
- All scripts must use `utils.sh` for consistency
- Configuration files in `config/.config/` (GNU Stow structure)

### Error Handling & Utils Integration
- Always call `init_utils` after sourcing utils.sh
- Use `die()` for fatal errors, `ask_yes_no()` for prompts
- Use `command_exists()`, `backup_file()`, `ensure_dir()` utilities
- Support dry-run mode with `DRY_RUN` variable
- Use `FORCE_YES` for non-interactive automation

### CLI Standards
- All `/bin` scripts support: `-v/--verbose`, `-y/--yes`, `--dry-run`, `-h/--help`
- Use consistent help format with examples and option descriptions
- Support component-specific flags (e.g., `--core`, `--apps`, `--dev`)
- Enable automation with non-interactive modes