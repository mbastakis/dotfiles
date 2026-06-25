# Homeserver OpenTofu

Source-only OpenTofu stacks for homeserver infrastructure. This directory is ignored by chezmoi and is run from the workstation through `task` targets.

## Stacks

| Path | Purpose | State key |
|---|---|---|
| `bootstrap/` | OpenTofu-managed S3 state backend bucket; first run starts local, then migrates to S3 | `homeserver/bootstrap/terraform.tfstate` |
| `aws-foundation/` | AWS backup bucket and IAM foundation for restic backups | `homeserver/aws-foundation/terraform.tfstate` |
| `truenas/` | TrueNAS SCALE datasets, low-risk NAS configuration, backup jobs, and app prerequisites | `homeserver/truenas/terraform.tfstate` |

## Rules

- Use `tofu`, not the Terraform CLI.
- Run AWS-backed commands through `aws-login exec mbastakis --`.
- Keep each stack in its own S3 state key.
- Do not commit `.tfstate`, plan files, `.terraform/`, or generated secrets.
- Do not let the TrueNAS stack create, destroy, or repartition pools.

## State Backend

The S3 state backend is owned by the `bootstrap/` OpenTofu stack. Its one-time helper, `bootstrap/create-state-backend.sh`, runs the first apply with local state, adopts the legacy script-created bucket when present, then migrates bootstrap state to S3.

All steady-state stacks initialize with backend config passed by the `Taskfile.yml` targets. `Taskfile.yml` verifies that the fixed S3 bucket exists before remote `init`, `plan`, or `apply`. Plan/apply tasks re-run `tofu init -reconfigure` with the fixed backend config before executing.

Fixed backend values used by `Taskfile.yml`:

| Item | Value |
|---|---|
| S3 bucket | `mbastakis-homeserver-opentofu-state` |
| Region | `eu-central-1` |
| Locking | S3 native lockfile |

## Verification

```bash
task tf:backend:check
task tf:bootstrap:plan
task tf:fmt
task tf:fmt:check
task tf:tflint
task tf:docs
```
