# Homeserver IaC

The homeserver automation is source-only infrastructure code under `infra/`. It does not deploy through chezmoi.

## Roles

| Host | Role | Management path |
|---|---|---|
| `atlas` | Ubuntu application/server host | Ansible under `infra/ansible/` |
| `truenas` | TrueNAS SCALE storage appliance with minimal apps | OpenTofu under `infra/terraform/truenas/` plus catalog app API wrapper |

## TrueNAS Scope

`truenas` targets TrueNAS SCALE 25.04.2 or newer. It is storage-first and may run only minimal storage-adjacent apps: Syncthing, File Browser, and backup-related services.

OpenTofu may manage lower-blast-radius configuration:

- child datasets under the existing `pool_4tb` pool
- permissions and service identities where provider support is clean
- snapshot and backup jobs
- host-path app prerequisites

OpenTofu does not manage pool creation, disk layout, boot pool, network interfaces, update train selection, or app runtime data.

The first adopted TrueNAS resources are existing backup datasets under `pool_4tb/backups`. They are imported into state with `prevent_destroy = true` so adoption does not recreate or delete backup data.

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
| AWS foundation | `infra/terraform/aws-foundation/` | `homeserver/aws-foundation/terraform.tfstate` |
| TrueNAS | `infra/terraform/truenas/` | `homeserver/truenas/terraform.tfstate` |

The AWS foundation stack manages the restic backup bucket and IAM. It does not manage the state bucket; that belongs to the bootstrap stack.

`Taskfile.yml` verifies the fixed S3 bucket before remote stack initialization, planning, or applying. Plan/apply tasks re-run `tofu init -reconfigure` with the fixed backend config and `use_lockfile=true` first, so a local `-backend=false` validation init or accidental alternate backend cannot be reused silently.

## Tooling

Repo-local tooling is pinned in `mise.toml` and exposed through `Taskfile.yml`:

```bash
mise install
task tf:bootstrap-state
task tf:bootstrap:plan
task tf:fmt
task tf:fmt:check
task tf:tflint
task tf:docs
task truenas:bootstrap-ssh-key
task tf:aws-foundation:init
task tf:truenas:init
```

AWS-backed OpenTofu commands run through `aws-login exec mbastakis --` so credentials are resolved outside the repository. The profile is hardcoded in repository workflows; targeting a different AWS account requires an intentional code change.

TrueNAS OpenTofu plan/apply tasks read the SSH private key from `~/.ssh/id_ed25519` at runtime and export `TF_VAR_truenas_ssh_private_key` for the provider. Override with `TRUENAS_SSH_PRIVATE_KEY_PATH` if a different key is required; key material is not stored in the repository.

## References

- ADR: `docs/adr/0002-manage-truenas-with-opentofu-and-api-app-automation.md:1`
- OpenTofu stacks: `infra/terraform/README.md:1`
- TrueNAS app declarations: `infra/truenas/apps/README.md:1`
- Repo tool pins: `mise.toml:1`
- Task targets: `Taskfile.yml:1`
