# Ansible Infrastructure

Source-only Ansible automation for personal servers. This directory is ignored by chezmoi and is run from the workstation, not deployed to managed hosts.

## atlas

`atlas` is expected to be a fresh Ubuntu Server 26.04 LTS host before Ansible runs. The initial playbook manages base access, wired DHCP, laptop always-on power behavior, Docker Engine/CLI support, and terminal comfort only; application stacks are intentionally out of scope.

Ubuntu Server 26.04 may use `sudo-rs` as `/usr/bin/sudo`; `atlas` uses `/usr/bin/sudo.ws` for Ansible privilege escalation because Ansible 2.21 cannot reliably match `sudo-rs` prompts.

If the fresh install only has password SSH, run the bootstrap play once first. It installs the workstation public key for `mbastakis` without privilege escalation:

```bash
cd infra/ansible
ansible-playbook playbooks/atlas-bootstrap.yml --ask-pass
```

After bootstrap, run the base playbook:

```bash
cd infra/ansible
ansible-playbook playbooks/atlas-base.yml --ask-become-pass
```

The base playbook installs passwordless sudo for `mbastakis`, so subsequent runs should not need `--ask-become-pass`:

```bash
cd infra/ansible
ansible-playbook playbooks/atlas-base.yml
```

If key-based SSH is already working, bootstrap is not required. If password SSH is still needed for the base play, run it with:

```bash
cd infra/ansible
ansible-playbook playbooks/atlas-base.yml --ask-pass --ask-become-pass
```

After key access is working, subsequent runs should not need `--ask-pass`. After passwordless sudo is applied, subsequent runs should not need `--ask-become-pass` either.

## Files

| Path | Purpose |
|---|---|
| `ansible.cfg` | Repo-local Ansible defaults |
| `inventories/home/hosts.yml` | Home inventory, including `atlas` |
| `inventories/home/host_vars/atlas.yml` | atlas user, SSH key, and package variables |
| `playbooks/atlas-bootstrap.yml` | One-time first-run SSH key bootstrap |
| `playbooks/atlas-base.yml` | Initial atlas base configuration |
| `roles/base_access/` | Admin user, SSH keys, sudo group, SSH hardening |
| `roles/network_dhcp/` | Explicit wired DHCP netplan config |
| `roles/laptop_power/` | Lid-close ignore policy and masked sleep targets |
| `roles/docker_cli/` | Docker apt repository, Docker Engine/CLI, Compose plugin |
| `roles/terminal_comfort/` | Shared Neovim/tmux/Yazi/Lazygit config deployment, Neovim parser/Mason bootstrap, Zsh server subset, Starship, keybindings, CLI tools |

## Verification

```bash
cd infra/ansible
ansible-playbook playbooks/atlas-base.yml --syntax-check
```

If `ansible-playbook` is missing on the workstation, install Ansible before running the syntax check or applying the playbook.
