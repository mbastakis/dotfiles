# atlas Clean Install Runbook

## Current Status

The backup checkpoint passed on 2026-06-23.

Backup artifacts:

- Actual UI export: `~/Backups/atlas/2026-06-23/2026-06-23-My-Finances-99b520e.zip`
- Actual safety copy: `~/Backups/atlas/2026-06-23/actual-safety-copy.tar.gz`
- Backup manifest: `~/Backups/atlas/2026-06-23/MANIFEST.md`
- File Browser data: TrueNAS `pool_4tb/backups/atlas/2026-06-23/filebrowser`

Temporary NFS ingest plumbing was removed after verification.

## atlas Hardware Snapshot

Collected before reinstall:

| Item | Value |
|---|---|
| Current OS | Ubuntu 22.04.4 LTS |
| Firmware | UEFI |
| Original wired interface | `enp4s0` |
| Current IP | `192.168.1.16/24` via DHCP |
| Default gateway | `192.168.1.1` |
| Root disk | `/dev/sda`, 111.8G SATA SSD, serial `00000000000000003850`, WWN `0x5000000000000000` |
| Data disk | `/dev/sdb`, 698.6G HGST HTS541075A9, serial `130830JD12001AGDD4BK`, WWN `0x5000cca69ac5a207` |

## Disk Decision Gate

Do not start the installer until the wipe target is explicit.

Confirmed target:

- Wipe `/dev/sda` for the fresh Ubuntu Server install.
- Wipe `/dev/sdb` as well and leave it blank for later storage automation.

Mount and format `/dev/sdb` only through a later Ansible/app-storage change.

## Install Path

Use physical USB install media for the OS installation. SSH-first bootstrap and autoinstall scripts are intentionally not used after the failed attempt on 2026-06-23.

1. Boot atlas from Ubuntu Server 26.04 LTS install media.
2. Select a clean install targeting the SSD (`/dev/sda`, 111.8G SATA SSD) for the OS.
3. Create admin user `mbastakis`.
4. Enable OpenSSH server.
5. Keep the host on wired DHCP; the fresh install came up at `192.168.1.19`.
6. Leave the HDD (`/dev/sdb`, 698.6G HGST) blank if possible; the fresh install mounted it as `/home`.
7. After first boot, run `infra/ansible/playbooks/atlas-base.yml` from the workstation.

## Required Base Settings

The base playbook manages these post-install settings:

- SSH key access for `mbastakis` using the workstation public key.
- Password and keyboard-interactive SSH disabled after the key is installed.
- Passwordless sudo for `mbastakis` after the first privileged Ansible run; the atlas account password is not stored in the repository.
- Wired DHCP through netplan on `enp3s0`.
- Laptop lid close and idle sleep ignored so atlas stays running.
- Sleep, suspend, hibernate, hybrid-sleep, and suspend-then-hibernate targets masked.
- Docker Engine/CLI and Compose plugin installed, with `mbastakis` in the `docker` group.
- Ansible privilege escalation uses `/usr/bin/sudo.ws` because Ubuntu Server 26.04 may default `/usr/bin/sudo` to `sudo-rs`, whose prompt format is incompatible with Ansible 2.21.
- Terminal comfort for `mbastakis`: Zsh login shell, server-safe Zsh config, Starship prompt, shared tmux config in SSH/server mode, shared Yazi and Lazygit configs, full Neovim Lua config with plugin/parser/Mason bootstrap and OSC52 remote clipboard support, and supporting CLI tools including Go, Rust/Cargo, and Nix for Mason-managed language tools.

## First Ansible Pass

After the fresh install is reachable:

If key-based SSH was not installed by the OS installer, bootstrap the host once:

```bash
cd infra/ansible
ansible-playbook playbooks/atlas-bootstrap.yml --ask-pass
```

The bootstrap play installs the workstation public key for `mbastakis` without privilege escalation.

Then run the base playbook:

```bash
cd infra/ansible
ansible-playbook playbooks/atlas-base.yml --ask-become-pass
```

After this succeeds, reruns do not need the become password prompt:

```bash
cd infra/ansible
ansible-playbook playbooks/atlas-base.yml
```

If password SSH is still required for the base play:

```bash
cd infra/ansible
ansible-playbook playbooks/atlas-base.yml --ask-pass --ask-become-pass
```
