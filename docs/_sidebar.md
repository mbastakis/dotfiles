- [Home](/)

- **Architecture**
  - [System Overview](architecture/overview.md)
  - [Chezmoi Lifecycle](architecture/chezmoi-lifecycle.md)
  - [Homeserver IaC](architecture/homeserver-iac.md)
  - [Homeserver Ownership](architecture/homeserver-ownership.md)

- **Decisions**
  - [0001: Rebuild atlas](adr/0001-rebuild-atlas-with-clean-ubuntu-and-ansible.md)
  - [0002: Manage TrueNAS](adr/0002-manage-truenas-with-opentofu-and-api-app-automation.md)
  - [0003: TaskChampion sync](adr/0003-taskwarrior-3x-with-taskchampion-sync-on-atlas.md)
  - [0004: TrueNAS API key via null_resource](adr/0004-truenas-api-key-via-null-resource.md)
  - [0005: Immich on atlas](adr/0005-run-immich-on-atlas-with-truenas-storage.md)
  - [0006: Domain-first homeserver IaC](adr/0006-domain-first-homeserver-iac.md)
  - [0007: OpenWrt risk-tiered convergence](adr/0007-manage-openwrt-router-as-typed-desired-state.md)

- **Components**
  - [Zsh](components/zsh.md)
  - [Config Overview](components/config-overview.md)
  - [Email](components/email.md)
  - [Neovim](components/nvim.md)
  - [OpenCode](components/opencode.md)
  - [Carapace](components/carapace.md)
  - [Karabiner](components/karabiner.md)

- **Runbooks**
  - [Add Household User](runbooks/add-household-user.md)
  - [Add Guest User](runbooks/add-guest-user.md)
  - [Add Obsidian Device](runbooks/add-obsidian-device.md)
  - [Restore from Restic](runbooks/restore-from-restic.md)
  - [Restore from ZFS Snapshot](runbooks/restore-from-zfs-snapshot.md)
  - [OpenTofu State Migrations](runbooks/opentofu-state-migrations.md)
  - [Homeserver Secret Rotation](runbooks/homeserver-secret-rotation.md)
  - [ntfy Notifications](runbooks/ntfy.md)
  - [Pi-hole DNS Filtering](runbooks/pihole.md)
  - [Sisyphus](runbooks/taskboard.md)
  - [Break-Glass Access](runbooks/break-glass-access.md)
  - [Apple Photos to Immich](runbooks/apple-photos-immich-migration.md)
  - [Audiobookshelf](runbooks/audiobookshelf.md)
  - [Legacy Speedport UPnP](runbooks/router-upnp-disable.md)
  - [OpenWrt Router Cutover](runbooks/openwrt-router-cutover.md)
  - [OpenWrt Router Recovery](runbooks/openwrt-router-recovery.md)

- **Workspaces**
  - [mrconfig](workspaces/mrconfig.md)

- **Reference**
  - [Shortcuts](shortcuts.md)

- **Meta**
  - [Maintenance](maintenance.md)
