# Navi - Interactive Cheatsheet Tool

**Repository:** https://github.com/denisidoro/navi  
**License:** Apache-2.0  
**Stars:** 16.3k  
**Language:** Rust (81%), Shell (16.3%)

## Overview

**navi** is an interactive cheatsheet tool for the command-line that allows you to browse through cheatsheets and execute commands with dynamically displayed argument suggestions. It uses **fzf** or **skim** under the hood and can be used as a command or shell widget (à la Ctrl-R).

## Key Features

- **Interactive Command Execution**: Browse cheatsheets and execute commands interactively
- **Dynamic Argument Suggestions**: Values for command arguments are dynamically displayed in a list
- **Multiple Usage Modes**: CLI command, shell widget, Tmux widget, aliases, or shell scripting tool
- **Extensible**: Write your own cheatsheets or import from repositories
- **Integration**: Works with tldr, cheat.sh, and TiddlyWiki

## Benefits

- Spare you from knowing CLIs by heart
- Eliminate copy-pasting output from intermediate commands
- Reduce typing
- Teach you new one-liners

## Installation

### Recommended (Homebrew)
```bash
brew install navi
```

### Other Package Managers
Available on multiple package managers (see Repology badge on repo).

## Usage Modes

### 1. Terminal Command
```bash
navi
```
**Pros:** Access to all subcommands and flags

### 2. Shell Widget
Install as a shell widget for better shell history integration and command editing.

**Pros:** 
- Shell history is correctly populated with actual commands
- Edit commands before executing

### 3. Tmux Widget
Use cheatsheets in any command-line app, even in SSH sessions.

### 4. Aliases
Create aliases for frequently used commands.

### 5. Shell Scripting Tool
Use navi in shell scripts for automation.

## Cheatsheet Repositories

### Default Location
`~/.local/share/navi/cheats/`

### Capabilities
- **Browse Featured Cheatsheets**: Discover community-maintained cheatsheets
- **Import from Git**: Add cheatsheets from git repositories
- **Write Custom Cheatsheets**: Create your own (and share them)
- **Import from Other Tools**: Use cheatsheets from tldr and cheat.sh
- **Auto-Update**: Keep repositories synchronized
- **TiddlyWiki Integration**: Auto-export from TiddlyWiki notes using a plugin

## Cheatsheet Syntax

Cheatsheets are `.cheat` files with the following structure:

```cheat
% git, code

# Change branch
git checkout <branch>

$ branch: git branch | awk '{print $NF}'
```

### Syntax Components
- `%` - Tags/categories
- `#` - Command description
- Command with `<placeholders>`
- `$` - Dynamic variable definitions with shell commands

## Customization Options

- **Custom Config File**: Set up your own configuration
- **Custom Paths**: Define paths for config files and cheatsheets
- **Color Themes**: Change color schemes
- **Column Resizing**: Adjust column widths
- **Search Behavior**: Override fzf options for custom search

## Configuration Paths

You can customize:
- Config file location
- Cheatsheet directories
- Colors and themes
- Column sizes
- fzf behavior

## Help

```bash
navi --help
```

For detailed documentation, check:
- `/docs` folder in the repository
- Official website

## Integration Examples

### Shell History
Configure as a shell widget to properly populate shell history with executed commands instead of just `navi`.

### Tmux
Use as a Tmux widget to access cheatsheets system-wide.

### Shell Scripting
Incorporate into scripts for dynamic command building.

## Community

- **Contributors:** 94
- **Used by:** 226 repositories
- **Forks:** 533
- **Latest Release:** v2.24.0 (January 29, 2025)

## Topics/Tags
shell, bash, rust, cli, snippets, terminal, command-line, snippet, cheatsheets

## Notes for AI/LLM Context

### Use Cases
1. **Developer Productivity**: Quick access to command syntax without memorizing
2. **Learning Tool**: Discover new commands and patterns
3. **Automation**: Scriptable interface for command building
4. **Team Knowledge Sharing**: Share cheatsheets across teams via git repositories

### Architecture
- Written in Rust for performance
- Uses fzf/skim for fuzzy finding interface
- Modular cheatsheet system with git integration
- Shell integration via widgets (bash/zsh/fish)

### Key Differentiators vs Other Tools
- **vs tldr**: Interactive execution with dynamic variables, not just reference
- **vs cheat.sh**: Local-first with custom cheatsheets, faster, offline support
- **vs plain aliases**: Dynamic argument suggestions, searchable, organized by tags

### Integration Points
- Shell (bash/zsh/fish/PowerShell)
- Tmux
- Git (for cheatsheet repositories)
- External tools (tldr, cheat.sh, TiddlyWiki)

---

**Last Updated:** October 7, 2025  
**Source:** GitHub repository scraped via webfetch
