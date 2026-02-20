# Maintenance Guide

How to keep these docs aligned with configuration changes.

## Update Triggers

Update the corresponding doc when any of the following change:

| Change | Doc to update |
|---|---|
| New/modified chezmoi lifecycle script | [chezmoi-lifecycle.md](architecture/chezmoi-lifecycle.md) |
| New source-to-target mapping or `.chezmoiignore` entry | [overview.md](architecture/overview.md) |
| Zsh module added/removed/reordered | [zsh.md](components/zsh.md) |
| New `~/.config/` component managed by chezmoi | [config-overview.md](components/config-overview.md) |
| Neovim plugin added/removed, LSP server changed | [nvim.md](components/nvim.md) |
| OpenCode agent/command/MCP change | [opencode.md](components/opencode.md) |
| Carapace spec added or bridge type changed | [carapace.md](components/carapace.md) |
| Karabiner rule file added or HRM config changed | [karabiner.md](components/karabiner.md) |
| Workspace `dot_mrconfig` modified | [mrconfig.md](workspaces/mrconfig.md) |
| Custom keymap added/changed in any layer | [shortcuts.md](shortcuts.md) |

## Review Order for Quick Updates

When making a targeted config change, update docs in this order:

1. **Component doc** -- update the specific component doc first.
2. **Shortcuts** -- if a keymap was added/changed/removed, update `shortcuts.md`.
3. **Cross-links** -- verify that any new sections are linked from `docs/README.md`.
4. **Architecture** -- only if deployment boundaries or lifecycle behavior changed.

## Checklist for New Components

When adding a new managed component to chezmoi:

- [ ] Add entry to [config-overview.md](components/config-overview.md).
- [ ] Create dedicated doc in `docs/components/` if the component is non-trivial.
- [ ] Add custom keymaps (if any) to [shortcuts.md](shortcuts.md).
- [ ] Link new doc from [docs/README.md](README.md).
- [ ] Update [overview.md](architecture/overview.md) if new source-to-target paths are involved.

## Scope Reminder

- Document **custom configuration only**. Do not document third-party default keymaps.
- Reference source files with `path:line` citations so readers can verify claims.
- Keep one topic per file to reduce merge conflicts.
- Prefer concise tables over prose for quick scanning.

## References

- Docs tree root: `docs/README.md`
- Implementation plan: `docs/implementation-plan.md`
