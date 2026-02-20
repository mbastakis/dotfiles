# Dotfiles Documentation

Component-based documentation for the chezmoi-managed dotfiles in this repository.

> **Source of truth:** Config files in the repo are authoritative. These docs consolidate and explain behavior; when in doubt, check the referenced source files. Citations use `path:line` format relative to repo root.

## Architecture

- [System Overview](architecture/overview.md) -- source-to-target mapping, component boundaries, deployment scope
- [Chezmoi Lifecycle](architecture/chezmoi-lifecycle.md) -- apply order, encryption, templates, and secrets flow

## Components

- [Zsh](components/zsh.md) -- shell startup, load order, modules, and tool integrations
- [Config Overview](components/config-overview.md) -- summary of all `~/.config/` areas managed by chezmoi
- [Neovim](components/nvim.md) -- bootstrap flow, plugin organization, LSP layering, and custom keymaps
- [OpenCode](components/opencode.md) -- config model, MCP setup, agents, and custom commands
- [Carapace](components/carapace.md) -- completion registry, spec types, bridge model, and sync workflow
- [Karabiner](components/karabiner.md) -- generated build pipeline, home row mods, and rule organization

## Workspaces

- [mrconfig](workspaces/mrconfig.md) -- multi-repo workspace layout with static and dynamic discovery

## Reference

- [Shortcuts](shortcuts.md) -- unified index of custom keymaps across all layers (shell, terminal, editor, keyboard)

## Maintenance

- [Maintenance Guide](maintenance.md) -- when and how to update these docs

## Conventions

### Citations

Source references use `path:line` format relative to the repo root:

```
dot_zsh/keybindings.zsh:14    -- line 14 of the zsh keybindings file
AGENTS.md:42                  -- line 42 of the root AGENTS file
```

### Diagrams

Mermaid fenced code blocks are used for architecture and flow diagrams. They render natively on GitHub and in any Mermaid-compatible viewer.

### Scope

These docs cover **custom configuration only**. Plugin-default keymaps (e.g., blink.cmp defaults, origami fold defaults) are excluded unless a custom override is defined. See [Shortcuts](shortcuts.md) for details on what is and isn't included.
