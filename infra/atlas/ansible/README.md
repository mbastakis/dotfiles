# Ansible Infrastructure

Source-only Ansible automation for personal servers. This directory is ignored by chezmoi and is run from the workstation, not deployed to managed hosts.

## atlas

`atlas` is expected to be a fresh Ubuntu Server 26.04 LTS host before Ansible runs. The base playbook manages access, wired DHCP, laptop always-on power behavior, Docker Engine/CLI support, and terminal comfort. The Tailscale playbook enrolls atlas as `tag:homeserver-entry`. The homeserver playbook deploys the private Traefik/AuthentiK/TaskChampion/Sisyphus/Homepage/Pi-hole Docker Compose stack, and the separate Immich playbook deploys the mount-gated photo stack.

Ubuntu Server 26.04 may use `sudo-rs` as `/usr/bin/sudo`; `atlas` uses `/usr/bin/sudo.ws` for Ansible privilege escalation because Ansible 2.21 cannot reliably match `sudo-rs` prompts.

## Immich precondition

ADR-0005 accepts atlas for a reduced-performance Immich deployment. Immich will use CPU-only machine learning and software transcoding because the installed GeForce GT 650M cannot meet Immich v3.0.2's CUDA or NVENC requirements. Postgres, Valkey, generated media, and machine-learning cache will stay on atlas under the local `/home` HDD; Postgres and Valkey must never use NFS. The host's 6.7 GiB RAM plus 4 GiB swap is accepted at Immich's minimum, below its 8 GB recommendation. The router reserves `192.168.1.19` for atlas's wired MAC, and a lease renewal verified the address. `nfs-common` provides the client for the host-restricted TrueNAS media mount. Host vars record these explicit tradeoffs and deliberately do not declare an NVIDIA driver package.

## Preferred Task Interface

Run Atlas operations from the repository root through go-task:

```bash
mise exec -- task atlas:validate
mise exec -- task atlas:bootstrap
mise exec -- task atlas:base:plan
mise exec -- task atlas:base:apply
mise exec -- task atlas:tailscale:plan
mise exec -- task atlas:tailscale:apply
mise exec -- task atlas:homeserver:plan
mise exec -- task atlas:homeserver:apply
mise exec -- task atlas:pihole:plan
mise exec -- task atlas:pihole:apply
mise exec -- task atlas:taskboard:test
mise exec -- task atlas:taskboard:smoke:live
mise exec -- task atlas:immich:plan
mise exec -- task atlas:immich:apply
```

Arguments after `--` pass through to `ansible-playbook`, including limits,
tags, verbosity, and password prompts. For example:

```bash
mise exec -- task atlas:base:plan -- --limit atlas --tags ssh -v
```

Plan tasks use Ansible check mode and diff output. Check mode is advisory when
a module cannot fully model a remote mutation without applying it. Review the
output before running the corresponding apply task.

The direct `ansible-playbook` commands below are retained for troubleshooting.

If the fresh install only has password SSH, run `mise exec -- task atlas:bootstrap` once first. It installs the workstation public key for `mbastakis` without privilege escalation. The equivalent direct command is:

```bash
cd infra/atlas/ansible
ansible-playbook playbooks/atlas-bootstrap.yml --ask-pass
```

After bootstrap, run `mise exec -- task atlas:base:apply`. The equivalent direct command with an initial become-password prompt is:

```bash
cd infra/atlas/ansible
ansible-playbook playbooks/atlas-base.yml --ask-become-pass
```

The base playbook installs passwordless sudo for `mbastakis`, so subsequent runs should not need `--ask-become-pass`:

```bash
cd infra/atlas/ansible
ansible-playbook playbooks/atlas-base.yml
```

If key-based SSH is already working, bootstrap is not required. If password SSH is still needed for the base play, run it with:

```bash
cd infra/atlas/ansible
ansible-playbook playbooks/atlas-base.yml --ask-pass --ask-become-pass
```

After key access is working, subsequent runs should not need `--ask-pass`. After passwordless sudo is applied, subsequent runs should not need `--ask-become-pass` either.

The inventory targets the `atlas` OpenSSH alias. `~/bin/homeserver-route` verifies Atlas's pinned SSH host key on `192.168.1.19` and prefers that LAN path when present; otherwise the alias connects to `100.101.208.110` through Tailscale. This applies to every `atlas:*` plan and deployment task. Use `atlas-lan` or `atlas-tailscale` to select a route explicitly, or set `HOMESERVER_ROUTE_FORCE=lan|tailscale` while troubleshooting.

## Tailscale enrollment

Create a one-off, non-ephemeral Tailscale preauth key allowed to advertise `tag:homeserver-entry`, store it in BWS as `homeserver/tailscale/atlas/auth-key`, then commit only the BWS secret ID in `infra/secrets/homeserver.bws.yaml`.

Prefer `mise exec -- task atlas:tailscale:apply`. The equivalent direct command through the secret helper is:

```bash
cd infra/atlas/ansible
../secrets/homeserver-secrets exec atlas-tailscale -- \
  ansible-playbook playbooks/atlas-tailscale.yml
```

The role installs Tailscale from the official apt repository, enrolls atlas as hostname `atlas`, disables accepted DNS/routes, advertises no subnet routes, does not advertise an exit node, disables Tailscale SSH, and prints the atlas Tailscale IPv4 for `TF_VAR_atlas_tailscale_ipv4`. If Tailscale has not published a package repo for the detected Ubuntu codename yet, override `atlas_tailscale_apt_suite` in host vars.

## Homeserver stack

After AWS foundation outputs for the Traefik Route53 ACME IAM key and the truenas stack's Homepage API key have been stored in BWS, prefer `mise exec -- task atlas:homeserver:apply`. The equivalent direct command is:

```bash
../secrets/homeserver-secrets exec atlas-homeserver -- \
  ansible-playbook playbooks/atlas-homeserver.yml
```

The playbook writes restricted env files under `/opt/homeserver/env`, renders Docker Compose for Traefik, Authentik, Postgres, Redis, TaskChampion sync, Sisyphus, and Homepage, and uses Traefik file-provider routes for `auth.mbastakis.com`, `code.mbastakis.com`, `files.mbastakis.com`, `tasks.mbastakis.com`, `taskboard.mbastakis.com`, `home.mbastakis.com`, `traefik.mbastakis.com`, and `backrest.mbastakis.com`. The FileBrowser and Backrest routes point to the TrueNAS app ports. The OpenCode route preserves `code.mbastakis.com` while connecting to the Mac's authenticated Tailscale Serve endpoint with its `*.ts.net` TLS server name. The Traefik dashboard, Sisyphus, and Backrest routes use Authentik forward-auth; OpenCode instead uses its own oauth2-proxy and native OIDC provider. The matching Authentik providers/applications are managed by `infra/identity/authentik/tofu`. Sisyphus is a local-build container with Taskwarrior 3.x and its own synced replica under `/opt/homeserver/taskboard/data`; the deployment identifiers remain `taskboard`. Its Python service is split into focused HTTP, Taskwarrior runtime, board projection, validation, and mutation modules. The Homepage container has no Docker socket, uses Ansible-owned YAML config, and reads widget secrets from `HOMEPAGE_VAR_*` values. Its header includes a Google web search that expands to the available desktop space and fills the mobile header width, while custom CSS keeps each service section visually separated. Homepage includes OpenCode in the Applications group. Widget/monitor URLs for TrueNAS-hosted apps use the NAS LAN address from inside Docker, while browser links can still point at tailnet/private routes. The role also manages the daily TaskChampion backup timer that copies the sync SQLite file to TrueNAS. A focused local Ansible module updates the TrueNAS middleware user record with atlas's generated backup key, native delegated file management owns the backup directory, and `community.docker.docker_compose_v2` converges the stack without parsing CLI output.

`atlas:taskboard:test` runs an isolated real-Taskwarrior HTTP mutation lifecycle followed by the locked mocked Playwright regression suite. `atlas:homeserver:apply` runs `atlas:taskboard:smoke:live` after convergence; the smoke resolves the current container endpoint, opens an SSH tunnel, permits only GET requests, and verifies the deployed board without mutating tasks.

The TaskChampion backup connection trusts only TrueNAS Ed25519 public host keys declared in `atlas_homeserver_truenas_backup_ssh_host_keys`. The role renders those approved keys into atlas's managed `known_hosts` file; it does not enroll trust with `ssh-keyscan` or retrieve private host keys. Obtain the current public host key through the TrueNAS console or another independently authenticated channel before setting the inventory value. The list supports planned rotation: declare both independently verified old and new public keys, apply, rotate the server key, then remove the old key and apply again.

Each TaskChampion backup takes a local lock, gracefully stops only the `taskchampion-sync` Compose service, and uses host Python's SQLite backup API to produce a standalone database. The script requires `PRAGMA quick_check` to return `ok` and restarts the service before contacting TrueNAS. Its `EXIT` cleanup retries the restart after every post-stop failure. TrueNAS receives a hidden temporary file that is atomically renamed only after transfer succeeds; retention pruning runs only after that publication.

The role also owns an isolated ntfy Compose project at `/opt/homeserver/ntfy`, exposed as `push.mbastakis.com`. Use `atlas:ntfy:plan` and `atlas:ntfy:apply` to converge it without touching unrelated homeserver services. The container runs as UID/GID 1000 with all capabilities dropped, stores its auth database and 12-hour message cache under `/opt/homeserver/ntfy/data`, and uses declarative credentials from the `atlas-homeserver` BWS target. Traefik does not add Authentik forward-auth because the iOS notification extension must authenticate directly while the app is suspended. Native ntfy ACLs deny anonymous access, grant `michail` read-only access, and grant the isolated `opencode` identity write-only access to its topic.

## Immich stack

Run `mise exec -- task atlas:immich:apply` only after the TrueNAS Immich dataset, sentinel, NFS export, the atlas homeserver stack, `photos.mbastakis.com` DNS record, and Authentik Immich OIDC application exist. The `atlas-immich` BWS target injects the dedicated Postgres password and OIDC client secret.

The role owns `/opt/homeserver/immich`, the NFS mount and automount units, `immich.service`, the Traefik route, and local runtime paths below `/home/mbastakis/.local/share/immich`. It verifies the exact NFS source and `.immich-storage` content before deployment and on every service start. Container-level restart is disabled; attached Compose exits if any child exits and systemd restarts the coherent stack only after repeating the storage gate. Unmounting the media filesystem stops the service through `BindsTo`.

Immich uses CPU-only v3.0.2 server and machine-learning images, the pinned Immich Postgres/VectorChord image, and pinned Valkey. Postgres, Valkey, thumbnails, encoded video, and ML caches are local. Only durable `/data` is NFS-backed. The server joins the external `homeserver` network for Traefik; its explicit `immich-valkey` hostname prevents collision with Authentik's Redis service on that network. `vm.overcommit_memory=1` supports Valkey background saves.

Ansible renders `/opt/homeserver/immich/immich.json` as a UID-1000-readable `0600` file and mounts it read-only as `IMMICH_CONFIG_FILE`. This makes code authoritative and the corresponding administration controls read-only. The file enables the date-based storage template and daily 02:00 database dumps with 14 retained copies, limits CPU-heavy queues to one worker, enforces software transcoding with two threads, and configures native Authentik OIDC for web and mobile clients. The existing `mbastakis@gmail.com` administrator links to the managed Authentik `michail` subject by matching email; the Authentik role claim grants `admin` only to that subject and `user` to every other newly registered identity. The bootstrap `akadmin` identity is not permitted to authorize the Immich application. Local password login remains enabled for break-glass access. Device permissions, selected mobile albums, user storage labels, and other per-user state remain runtime-owned.

Verify the deployment with:

```bash
ssh atlas sudo systemctl status immich.service
ssh atlas sudo docker compose --project-directory /opt/homeserver/immich ps
curl https://photos.mbastakis.com/api/server/ping
```

## Files

| Path | Purpose |
|---|---|
| `ansible.cfg` | Repo-local Ansible defaults |
| `requirements.yml` | Locked `community.docker` collection used for Compose convergence |
| `library/truenas_user_ssh_key.py` | Check-mode-aware TrueNAS middleware user-key module |
| `inventories/home/hosts.yml` | Home inventory, including `atlas` |
| `inventories/home/host_vars/atlas.yml` | atlas user, SSH key, and package variables |
| `playbooks/atlas-bootstrap.yml` | One-time first-run SSH key bootstrap |
| `playbooks/atlas-base.yml` | Initial atlas base configuration |
| `playbooks/atlas-tailscale.yml` | Tailscale enrollment for atlas as `tag:homeserver-entry` |
| `playbooks/atlas-homeserver.yml` | Traefik/AuthentiK homeserver application stack |
| `playbooks/atlas-immich.yml` | Dedicated fail-closed Immich deployment |
| `roles/base_access/` | Admin user, SSH keys, sudo group, SSH hardening |
| `roles/network_dhcp/` | Explicit wired DHCP netplan config |
| `roles/laptop_power/` | Lid-close ignore policy and masked sleep targets |
| `roles/docker_cli/` | Docker apt repository, Docker Engine/CLI, Compose plugin |
| `roles/terminal_comfort/` | Shared Neovim/tmux/Yazi/Lazygit config deployment, Neovim parser/Mason bootstrap, Zsh server subset, Starship, keybindings, CLI tools |
| `roles/atlas_tailscale/` | Tailscale apt repository, service, and homeserver-entry enrollment/settings |
| `roles/atlas_homeserver/` | Docker Compose deployment for Traefik, Authentik, Postgres, Redis, TaskChampion sync, Sisyphus, ntfy, Homepage, private routing, and sync backup timer |
| `roles/atlas_immich/` | Persistent NFS gate, local runtime storage, pinned Immich Compose project, systemd lifecycle, and private route |

## Verification

```bash
cd infra/atlas/ansible
ansible-playbook playbooks/atlas-base.yml --syntax-check
ansible-playbook playbooks/atlas-tailscale.yml --syntax-check
ansible-playbook playbooks/atlas-homeserver.yml --syntax-check
ansible-playbook playbooks/atlas-immich.yml --syntax-check
```

If `ansible-playbook` is missing on the workstation, install Ansible before running the syntax check or applying the playbook.
