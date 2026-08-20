# Dotfiles Documentation

Topic-based documentation for the chezmoi-managed dotfiles in this repository.

> **Source of truth:** Config files in the repo are authoritative. These docs never enumerate what the code already lists (packages, plugins, aliases, options) — they hold only what's hard to reconstruct from the code: cross-tool aggregations, design rationale, and runbooks.

## Topics

- [Shortcuts](shortcuts.md) — every custom keybinding across all layers (Karabiner → Ghostty → tmux → zsh → NeoMutt → Neovim), plus the input-flow model
- [Architecture](architecture.md) — chezmoi apply lifecycle, fresh-machine bootstrap, encryption/secrets chain, profiles, operational gotchas
- [Email](email.md) — NeoMutt Gmail stack runbook: setup, troubleshooting, tuning rationale
- [Tool Notes](tool-notes.md) — non-obvious per-tool design notes (zsh startup order, Neovim LSP layering, `tw` vs go-task collision, mrconfig dynamic discovery)

External homeserver infrastructure, its architecture decisions, and its runbooks live in the sibling [`kavouki`](https://github.com/mbastakis/kavouki) repository. Workstation-owned decisions are recorded here.

## Conventions

- **Citations** reference source files by path only (e.g. `private_dot_config/zsh/keybindings.zsh`), never by line number — line numbers rot on every edit.
- **Diagrams** are Mermaid fenced code blocks; they render on GitHub and in the Docsify site.
- **Scope:** custom configuration only. Plugin-default keymaps are excluded unless a custom override is defined.
- **Maintenance:** update a doc only when its *insight* changes — a new shortcut, a changed contract, a new gotcha. Inventory changes (new package, plugin, alias) never require a doc edit.
