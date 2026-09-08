# Dotfiles

Docs for the chezmoi-managed dotfiles in this repo. The config files are the source of truth; these pages only hold what the code can't show — cross-tool wiring, rationale, and runbooks.

## Pages

- [Nocturne Rose](showcase.md) — the shared workstation palette
- [Shortcuts](shortcuts.md) — every custom keybinding, layer by layer
- [Architecture](architecture.md) — how `chezmoi apply` builds a machine
- [Email](email.md) — NeoMutt Gmail stack runbook

Homeserver infrastructure lives in the sibling [`kavouki`](https://github.com/mbastakis/kavouki) repo; workstation-owned decisions are recorded here.

## Theme maintenance

Nocturne Rose owns application theme mappings and ready-made native files in its
`dist/` directory. Copy changed outputs to the destinations listed in that
repository's `CONSUMERS.md`, review them here, then apply only the affected managed
targets with chezmoi. Dedicated theme files are native app files. Mixed configs
include native snippets from the ignored, source-only `theme-fragments/` directory;
chezmoi retains host and secret rendering. tmux loads its palette before TPM and
its final styles after TPM.

`docs/theme.css` and `docs/showcase.md` are committed native outputs too. Docs
serving and deployment use them directly.

## Conventions

- Cite source files by path, never by line number — line numbers rot.
- Diagrams are Mermaid; they render on GitHub and in this site.
- Custom configuration only. Plugin defaults are out of scope unless overridden.
- Update a page when its *insight* changes, not when an inventory (package, plugin, alias) changes.
