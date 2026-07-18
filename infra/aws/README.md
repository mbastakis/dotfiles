# Homeserver AWS Infrastructure

Source-only AWS OpenTofu stacks and modules. This directory is ignored by
chezmoi and is operated from the workstation through `aws:*` tasks.

## Stacks

| Path | Purpose | State key |
|---|---|---|
| `stacks/bootstrap/` | OpenTofu-managed S3 state backend bucket; first run starts local, then migrates to S3 | `homeserver/bootstrap/terraform.tfstate` |
| `stacks/dns/` | Route53 public hosted zone and homeserver private service records for `mbastakis.com` | `homeserver/dns/terraform.tfstate` |
| `stacks/foundation/` | AWS backup bucket and IAM foundation for restic backups and Traefik ACME | `homeserver/aws-foundation/terraform.tfstate` |

## Modules

Reusable resource graphs live under `modules/` without owning separate state:

| Path | Policy boundary |
|---|---|
| `modules/hardened-s3-bucket/` | Private S3 access, ownership, TLS-only policy, encryption, optional versioning and lifecycle rules, and destroy protection |
| `modules/iam-user/` | Protected IAM user, stack-owned inline policy, access key, tags, and sensitive credentials |

Root stacks retain backend ownership, policy JSON, stable resource identities,
and public outputs. The one-time module-extraction `moved` blocks were removed
after the migrated addresses and clean plans were verified.

## Rules

- Use `tofu`, not the Terraform CLI.
- Run AWS-backed commands through `aws-login exec mbastakis --`.
- Keep each stack in its own S3 state key.
- Do not commit `.tfstate`, plan files, `.terraform/`, or generated secrets.
- Follow `docs/runbooks/opentofu-state-migrations.md` for every resource-address
  or source-path migration.

## State Backend

The S3 state backend is owned by the `stacks/bootstrap/` OpenTofu stack. Its
one-time helper, `stacks/bootstrap/create-state-backend.sh`, runs the first
apply with local state, adopts the legacy script-created bucket when present,
then migrates bootstrap state to S3.

All steady-state stacks initialize with backend config passed by the `Taskfile.yml` targets. `Taskfile.yml` verifies that the fixed S3 bucket exists before remote `init`, `plan`, or `apply`. Plan/apply tasks re-run `tofu init -reconfigure` with the fixed backend config before executing.

Fixed backend values used by `Taskfile.yml`:

| Item | Value |
|---|---|
| S3 bucket | `mbastakis-homeserver-opentofu-state` |
| Region | `eu-central-1` |
| Locking | S3 native lockfile |

Run `task tf:state:baseline` before migrations. It verifies the immutable
backend identity, confirms S3 versioning and all six current state objects,
and prints state version IDs plus provider lockfile checksums without
downloading state contents.

## Verification

```bash
task aws:backend:check
task tf:state:baseline
task aws:bootstrap:plan
task aws:dns:plan
task aws:foundation:plan
task tf:fmt
task tf:fmt:check
task tf:tflint
task tf:docs
task tf:test
```

The other OpenTofu roots are owned by `infra/truenas/tofu/`,
`infra/identity/authentik/tofu/`, and `infra/network/tailscale/tofu/`.
Deployment uses domain commands; `tf:*` contains only cross-stack quality and
state tooling.
