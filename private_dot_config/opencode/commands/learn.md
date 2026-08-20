---
description: Extract non-obvious learnings from session to AGENTS.md files
---

# Extract Learnings

Analyze this session and extract non-obvious learnings to AGENTS.md files.

## Where to Place Learnings

AGENTS.md files can exist at any directory level. When an agent reads a file, any AGENTS.md in parent directories is automatically loaded. Place learnings as close to the relevant code as possible:

- Project-wide → root `AGENTS.md`
- Package/module-specific → `packages/foo/AGENTS.md`
- Feature-specific → `src/auth/AGENTS.md`

## What Counts as a Learning

**Include** (non-obvious discoveries only):
- Hidden relationships between files or modules
- Execution paths that differ from code appearance
- Non-obvious configuration, env vars, or flags
- Debugging breakthroughs when errors were misleading
- API/tool quirks and workarounds
- Build/test commands not in README
- Architectural decisions and constraints
- Files that must change together

**Exclude**:
- Obvious facts from documentation
- Standard language/framework behavior
- Things already in an AGENTS.md
- Verbose explanations
- Session-specific details

## Process

1. Review session for:
   - Discoveries that took multiple attempts
   - Unexpected connections between components
   - "Aha" moments that weren't obvious from docs

2. For each learning, determine scope (which directory?)

3. Read existing AGENTS.md files at relevant levels

4. Create or update AGENTS.md at appropriate level
   - Keep entries to 1-3 lines per insight
   - Use consistent formatting with existing entries

5. Summarize changes:
   - Which AGENTS.md files were created/updated
   - How many learnings per file

## Example Good vs Bad Entries

**Good** (non-obvious, actionable):
```
## Neovim LSP
- `after/lsp/*.lua` files auto-loaded by nvim-lspconfig - don't require explicit imports
- Mason installs to ~/.local/share/nvim/mason/bin - add to PATH for CLI usage
```

**Bad** (obvious or verbose):
```
## Neovim
- Neovim is a text editor (obvious)
- The configuration is written in Lua (standard knowledge)
- I spent 30 minutes debugging this issue... (session-specific)
```
