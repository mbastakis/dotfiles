# Homeserver IaC

The homeserver automation is source-only infrastructure code under `infra/`. It does not deploy through chezmoi.

## Roles

| Host | Role | Management path |
|---|---|---|
| `atlas` | Ubuntu application/server host, Tailscale entry node, Traefik/AuthentiK host | Ansible under `infra/ansible/` |
| `truenas` | TrueNAS SCALE storage appliance with minimal apps | OpenTofu under `infra/terraform/truenas/` plus catalog app API wrapper |
| Authentik | Homeserver identity and FileBrowser Quantum OIDC config | OpenTofu under `infra/terraform/authentik/` after the atlas Authentik service is reachable |

## TrueNAS Scope

`truenas` targets TrueNAS SCALE 25.04.2 or newer. It is storage-first and may run only minimal storage-adjacent apps: Tailscale, Syncthing, FileBrowser Quantum, and Backrest/restic backup services.

OpenTofu may manage lower-blast-radius configuration:

- child datasets under the existing `pool_4tb` pool
- permissions and service identities where provider support is clean
- snapshot and backup jobs
- host-path app prerequisites

OpenTofu does not manage pool creation, disk layout, boot pool, network interfaces, update train selection, or app runtime data.

The temporary atlas migration datasets under `pool_4tb/backups` were removed after their FileBrowser payload was verified in `homeserver/data/files/household`. The TrueNAS stack now owns only the target homeserver datasets and no longer imports legacy backup-staging paths.

TrueNAS SSH key installation is a one-time bootstrap step, not part of the persistent OpenTofu state. Run `mise exec -- task truenas:bootstrap-ssh-key` to create a dataset-backed home at `/mnt/pool_4tb/mbastakis`, add the managed `id_ed25519.pub` key to the `mbastakis` TrueNAS user through the TrueNAS CLI shell, set that account's login shell to `/usr/bin/bash`, and enable passwordless sudo for provider automation; after that, the `truenas` SSH alias and `192.168.1.74` host entry both pin `~/.ssh/id_ed25519`.

## App Model

Stable TrueNAS catalog apps are preferred when they fit. App declarations live under `infra/truenas/apps/`, pin explicit catalog versions, and contain non-secret values only.

The current provider can manage custom Compose apps but does not yet expose full catalog app install fields. Until that changes, catalog app declarations are applied through a small TrueNAS API or `midclt` wrapper.

## Backup Model

TrueNAS backups use restic to S3 from the NAS itself. The initial off-NAS backup scope is Obsidian and personal files; app config datasets are not part of the first backup scope because they should be recreated from code.

The active restic repository must remain immediately readable. Use S3 Intelligent-Tiering without archive tiers or Glacier Instant Retrieval, not asynchronous Glacier or Deep Archive lifecycle rules.

## OpenTofu State

The OpenTofu state backend is owned by the `infra/terraform/bootstrap/` stack. Its one-time helper runs the first apply with local state, creates or adopts the fixed S3 bucket, then migrates bootstrap state into that bucket. The backend identity is fixed in the repository: S3 bucket `mbastakis-homeserver-opentofu-state`, region `eu-central-1`, and S3 native lockfiles. Individual stacks use separate state keys in the same backend:

| Stack | Path | State key |
|---|---|---|
| Bootstrap | `infra/terraform/bootstrap/` | `homeserver/bootstrap/terraform.tfstate` |
| DNS | `infra/terraform/dns/` | `homeserver/dns/terraform.tfstate` |
| AWS foundation | `infra/terraform/aws-foundation/` | `homeserver/aws-foundation/terraform.tfstate` |
| TrueNAS | `infra/terraform/truenas/` | `homeserver/truenas/terraform.tfstate` |
| Authentik | `infra/terraform/authentik/` | `homeserver/authentik/terraform.tfstate` |

The DNS stack manages the Route53 public hosted zone and the private homeserver service records (`auth` and `files`) pointing at atlas over Tailscale. The legacy Cloudflare Tunnel / external-dns records were intentionally not migrated; `mbastakis.com` starts fresh in AWS DNS. Registrar nameserver delegation at Enartia/Papaki remains a manual cutover step documented in `infra/terraform/dns/README.md`.

The AWS foundation stack manages the restic backup bucket, restic IAM, and Traefik Route53 ACME IAM. It reads the Route53 zone for IAM scoping but does not own DNS records. It does not manage the state bucket; that belongs to the bootstrap stack.

`infra/tailscale/policy.hujson` captures the current tailnet policy snapshot used for homeserver tag ownership. `infra/tailscale/manage-policy` validates/applies it with a caller-supplied `TAILSCALE_API_KEY`; the API token is an operator credential and is not stored in the repository.

`Taskfile.yml` verifies the fixed S3 bucket before remote stack initialization, planning, or applying. Plan/apply tasks re-run `tofu init -reconfigure` with the fixed backend config and `use_lockfile=true` first, so a local `-backend=false` validation init or accidental alternate backend cannot be reused silently.

## Tooling

Repo-local tooling is pinned in `mise.toml` and exposed through `Taskfile.yml`:

```bash
mise install
task tf:bootstrap-state
task tf:bootstrap:plan
task tf:dns:plan
task tf:fmt
task tf:fmt:check
task tf:tflint
task tf:docs
task truenas:bootstrap-ssh-key
task tf:dns:init
task tf:aws-foundation:init
task tf:truenas:init
task tf:authentik:init
task tailscale:policy:validate
```

AWS-backed OpenTofu commands run through `aws-login exec mbastakis --` so credentials are resolved outside the repository. The profile is hardcoded in repository workflows; targeting a different AWS account requires an intentional code change.

TrueNAS OpenTofu plan/apply tasks read the SSH private key from `~/.ssh/id_ed25519` at runtime and export `TF_VAR_truenas_ssh_private_key` for the provider. Override with `TRUENAS_SSH_PRIVATE_KEY_PATH` if a different key is required; key material is not stored in the repository.

Atlas Tailscale enrollment uses `infra/secrets/homeserver-secrets exec atlas-tailscale` so the preauth key is injected only for the child Ansible process. The role stores the key briefly in `/run` with root-only permissions and removes it after `tailscale up`.

The atlas homeserver playbook uses Traefik's file provider for both private browser entrypoints (`auth` and `files`) instead of Docker labels/socket discovery. Authentik listens on the Compose network at port `9000`; FileBrowser Quantum is reached over the LAN at the TrueNAS app port.

The Authentik stack owns the FileBrowser Quantum OIDC provider. It explicitly enables the `authorization_code` grant required by FileBrowser's `/api/auth/oidc/login` and `/api/auth/oidc/callback` flow; an empty grant list causes Authentik to redirect back with `invalid_request` and FileBrowser to report `invalid_grant`.

TrueNAS apps currently rely on explicit public DNS resolvers (`1.1.1.1`, `8.8.8.8`) so containers resolve the Route53 delegation even if the LAN router caches the former Cloudflare nameservers during cutover.

## References

- ADR: `docs/adr/0002-manage-truenas-with-opentofu-and-api-app-automation.md:1`
- OpenTofu stacks: `infra/terraform/README.md:1`
- TrueNAS app declarations: `infra/truenas/apps/README.md:1`
- Repo tool pins: `mise.toml:1`
- Task targets: `Taskfile.yml:1`
