# OpenCode Documentation

**Source:** https://opencode.ai/docs  
**Retrieved:** 2025-10-06

## Overview

OpenCode is an AI coding agent built for the terminal. It provides an interactive interface for working with codebases using LLM providers.

## Prerequisites

1. A modern terminal emulator:
   - WezTerm (cross-platform)
   - Alacritty (cross-platform)
   - Ghostty (Linux and macOS)
   - Kitty (Linux and macOS)

2. API keys for LLM providers you want to use

## Installation

### Quick Install (Recommended)
```bash
curl -fsSL https://opencode.ai/install | bash
```

### Package Managers

**Node.js:**
```bash
npm install -g opencode-ai
bun install -g opencode-ai
pnpm install -g opencode-ai
yarn global add opencode-ai
```

**macOS/Linux:**
```bash
brew install sst/tap/opencode
```

**Arch Linux:**
```bash
paru -S opencode-bin
```

**Windows:**
```bash
choco install opencode      # Chocolatey
winget install opencode     # WinGet
scoop install extras/opencode  # Scoop
npm install -g opencode-ai  # NPM
```

Binary releases available at: https://github.com/sst/opencode/releases

## Configuration

### Setting Up Providers

OpenCode supports multiple LLM providers. For new users, **OpenCode Zen** is recommended (curated, tested models).

**Setup steps:**
1. Run `opencode auth login`
2. Select provider (opencode recommended for Zen)
3. Visit https://opencode.ai/auth
4. Sign in, add billing details, copy API key
5. Paste API key when prompted

Alternative providers available - see: https://opencode.ai/docs/providers#directory

## Initialization

1. Navigate to your project:
```bash
cd /path/to/project
```

2. Run OpenCode:
```bash
opencode
```

3. Initialize for the project:
```
/init
```

This analyzes the project and creates an `AGENTS.md` file in the project root. **Commit this file to Git** - it helps OpenCode understand project structure and coding patterns.

## Usage Examples

### Ask Questions
```
How is authentication handled in @packages/functions/src/api/index.ts
```
- Use `@` key to fuzzy search for files in the project
- Useful for understanding unfamiliar code sections

### Add Features

**1. Create a Plan (Plan Mode)**
- Press **Tab** to switch to Plan mode (disables making changes, only suggests implementation)
- Indicator appears in lower right corner
- Example prompt:
```
When a user deletes a note, we'd like to flag it as deleted in the database.
Then create a screen that shows all the recently deleted notes.
From this screen, the user can undelete a note or permanently delete it.
```

**Tips:**
- Provide enough detail (talk to it like a junior developer)
- Give plenty of context and examples
- Drag and drop images into terminal to add them to prompts

**2. Iterate on the Plan**
```
We'd like to design this new screen using a design I've used before.
[Image #1] Take a look at this image and use it as a reference.
```

**3. Build the Feature**
- Press **Tab** again to switch back to Build mode
- Confirm:
```
Sounds good! Go ahead and make the changes.
```

### Make Direct Changes
For straightforward changes, skip planning and build directly:
```
We need to add authentication to the /settings route. Take a look at how this is
handled in the /notes route in @packages/functions/src/notes.ts and implement
the same logic in @packages/functions/src/settings.ts
```

### Undo/Redo Changes

**Undo:**
```
/undo
```
- Reverts changes and shows original message
- Can run multiple times to undo multiple changes
- Allows tweaking the prompt and retrying

**Redo:**
```
/redo
```
- Reapplies previously undone changes

## Sharing

Share conversations with your team:
```
/share
```
- Creates a link to the current conversation
- Copies link to clipboard
- **Conversations are NOT shared by default**
- Example: https://opencode.ai/s/4XP1fce5

## Customization

Available customizations:
- [Themes](https://opencode.ai/docs/themes)
- [Keybinds](https://opencode.ai/docs/keybinds)
- [Code Formatters](https://opencode.ai/docs/formatters)
- [Custom Commands](https://opencode.ai/docs/commands)
- [OpenCode Config](https://opencode.ai/docs/config)

## Key Commands

- `/init` - Initialize OpenCode for current project
- `/undo` - Revert changes
- `/redo` - Reapply changes
- `/share` - Share conversation
- `@` - Fuzzy search files
- **Tab** - Toggle between Plan/Build mode
- `/help` - Get help
- Report issues: https://github.com/sst/opencode/issues

## Additional Resources

- [TUI Usage](https://opencode.ai/docs/tui/)
- [CLI Usage](https://opencode.ai/docs/cli/)
- [IDE Integration](https://opencode.ai/docs/ide/)
- [GitHub Integration](https://opencode.ai/docs/github/)
- [GitLab Integration](https://opencode.ai/docs/gitlab/)
- [Rules Configuration](https://opencode.ai/docs/rules/)
- [Agents Configuration](https://opencode.ai/docs/agents/)
- [Models Configuration](https://opencode.ai/docs/models/)
- [Permissions](https://opencode.ai/docs/permissions/)
- [LSP Servers](https://opencode.ai/docs/lsp/)
- [MCP Servers](https://opencode.ai/docs/mcp-servers/)
- [Custom Tools](https://opencode.ai/docs/custom-tools/)
- [SDK](https://opencode.ai/docs/sdk/)
- [Server](https://opencode.ai/docs/server/)
- [Plugins](https://opencode.ai/docs/plugins/)

## Support

- GitHub: https://github.com/sst/opencode
- Discord: https://opencode.ai/discord
- Documentation: https://opencode.ai/docs

---

*Last documentation update: Oct 4, 2025*  
*Retrieved: Oct 6, 2025*  
*© Anomaly Innovations Inc.*
