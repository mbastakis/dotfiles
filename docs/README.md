# Dotfiles Documentation

Component-based documentation for the chezmoi-managed dotfiles in this repository.

> **Source of truth:** Config files in the repo are authoritative. These docs consolidate and explain behavior; when in doubt, check the referenced source files. Citations use `path:line` format relative to repo root.

## Architecture

- [System Overview](architecture/overview.md) -- source-to-target mapping, component boundaries, deployment scope
- [Chezmoi Lifecycle](architecture/chezmoi-lifecycle.md) -- apply order, encryption, templates, and secrets flow
- [Homeserver IaC](architecture/homeserver-iac.md) -- OpenTofu, TrueNAS, catalog apps, and backup architecture
- [Homeserver Ownership](architecture/homeserver-ownership.md) -- desired-state and runtime-state ownership matrix

## Decisions

- [0001: Rebuild atlas with clean Ubuntu and Ansible](adr/0001-rebuild-atlas-with-clean-ubuntu-and-ansible.md)
- [0002: Manage TrueNAS with OpenTofu and API app automation](adr/0002-manage-truenas-with-opentofu-and-api-app-automation.md)
- [0003: Taskwarrior 3.x with TaskChampion sync on atlas](adr/0003-taskwarrior-3x-with-taskchampion-sync-on-atlas.md)
- [0004: TrueNAS API key via null_resource](adr/0004-truenas-api-key-via-null-resource.md)
- [0005: Immich on atlas with TrueNAS storage](adr/0005-run-immich-on-atlas-with-truenas-storage.md)
- [0006: Domain-first homeserver IaC operated through Task](adr/0006-domain-first-homeserver-iac.md)

## Components

- [Zsh](components/zsh.md) -- shell startup, load order, modules, and tool integrations
- [Config Overview](components/config-overview.md) -- summary of all `~/.config/` areas managed by chezmoi
- [Email](components/email.md) -- NeoMutt Gmail stack, daily workflow, automation, and troubleshooting
- [Neovim](components/nvim.md) -- bootstrap flow, plugin organization, LSP layering, and custom keymaps
- [OpenCode](components/opencode.md) -- config model, MCP setup, agents, and custom commands
- [Carapace](components/carapace.md) -- completion registry, spec types, bridge model, and sync workflow
- [Karabiner](components/karabiner.md) -- generated build pipeline, home row mods, and rule organization

## Runbooks

- [Add Household User](runbooks/add-household-user.md) -- Tailscale + Authentik + FileBrowser onboarding
- [Add Guest User](runbooks/add-guest-user.md) -- limited FileBrowser-only access
- [Add Obsidian Device](runbooks/add-obsidian-device.md) -- Syncthing peer enrollment
- [Restore from Restic](runbooks/restore-from-restic.md) -- off-NAS S3 disaster recovery
- [Restore from ZFS Snapshot](runbooks/restore-from-zfs-snapshot.md) -- local quick rollback
- [OpenTofu State Migrations](runbooks/opentofu-state-migrations.md) -- state baselines, moved blocks, and rollback
- [Homeserver Secret Rotation](runbooks/homeserver-secret-rotation.md) -- BWS inventory and credential rotation procedures
- [Sisyphus](runbooks/taskboard.md) -- Taskwarrior Kanban board operations
- [Break-Glass Access](runbooks/break-glass-access.md) -- Authentik/OIDC outage recovery
- [Apple Photos to Immich Migration](runbooks/apple-photos-immich-migration.md) -- archive, pilot, metadata, validation, and resume gates
- [Audiobookshelf](runbooks/audiobookshelf.md) -- deployment, mobile setup, storage, backups, and restore
- [Router UPnP Disable](runbooks/router-upnp-disable.md) -- router hardening

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
private_dot_config/zsh/keybindings.zsh:14    -- line 14 of the zsh keybindings file
AGENTS.md:42                  -- line 42 of the root AGENTS file
```

### Diagrams

Mermaid fenced code blocks are used for architecture and flow diagrams. They render natively on GitHub and in any Mermaid-compatible viewer.

### Scope

These docs cover **custom configuration only**. Plugin-default keymaps (e.g., blink.cmp defaults, origami fold defaults) are excluded unless a custom override is defined. See [Shortcuts](shortcuts.md) for details on what is and isn't included.
