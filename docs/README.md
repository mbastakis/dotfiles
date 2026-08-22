# Dotfiles

Docs for the chezmoi-managed dotfiles in this repo. The config files are the source of truth; these pages only hold what the code can't show — cross-tool wiring, rationale, and runbooks.

## Pages

- [Nocturne Rose](showcase.md) — the shared workstation palette
- [Shortcuts](shortcuts.md) — every custom keybinding, layer by layer
- [Architecture](architecture.md) — how `chezmoi apply` builds a machine
- [Email](email.md) — NeoMutt Gmail stack runbook

Homeserver infrastructure lives in the sibling [`kavouki`](https://github.com/mbastakis/kavouki) repo; workstation-owned decisions are recorded here.

## Conventions

- Cite source files by path, never by line number — line numbers rot.
- Diagrams are Mermaid; they render on GitHub and in this site.
- Custom configuration only. Plugin defaults are out of scope unless overridden.
- Update a page when its *insight* changes, not when an inventory (package, plugin, alias) changes.
