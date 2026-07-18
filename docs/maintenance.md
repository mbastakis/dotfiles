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
| Repo-local `mise.toml`, `Taskfile.yml`, Renovate, GitHub Actions, pre-commit, TFLint, terraform-docs, or homeserver IaC tooling modified | [config-overview.md](components/config-overview.md), [homeserver-iac.md](architecture/homeserver-iac.md) |
| Custom keymap added/changed in any layer | [shortcuts.md](shortcuts.md) |
| Homeserver operational procedure added/changed | Relevant doc in [runbooks/](runbooks/) |
| OpenWrt contract, firmware lock/packages, reconciler stage, Task surface, or ownership changed | [homeserver-iac.md](architecture/homeserver-iac.md), [homeserver-ownership.md](architecture/homeserver-ownership.md), [ADR-0007](adr/0007-manage-openwrt-router-as-typed-desired-state.md), and both OpenWrt runbooks |
| OpenWrt physical cutover accepted or rolled back | [overview.md](architecture/overview.md), [OpenWrt cutover](runbooks/openwrt-router-cutover.md), `CONTEXT.md`, README/sidebar, and Speedport runbook retirement decision |

## OpenWrt Release Review

For each proposed OpenWrt release, review WR3000E v1/R53 support and open issues,
stock-layout profile continuity, release/Image Builder checksums, builder digest,
package intent, resolved manifest, helper/public-key overlay, and forbidden-image
checks. Build and verify locally, run offline validation, then use a wired
maintenance window with an encrypted config backup, remote hash verification,
`sysupgrade -T`, and config-preserving sysupgrade without force. Reconcile and
run status after boot. Major releases require a separate clean-migration review;
do not use unattended upgrades or `owut` as another owner.

Do not mark physical phases complete from documentation or fixture tests. Record
operator evidence for board identity, MTD backups, rollback test, staged
acceptance, TFTP/UART readiness, and the seven-day observation window first.

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
