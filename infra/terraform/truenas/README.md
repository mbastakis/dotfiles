# TrueNAS

OpenTofu stack for supported TrueNAS SCALE configuration. This stack targets TrueNAS SCALE 25.04.2 or newer and uses the shared S3 backend owned by the bootstrap stack.

## Owns

- Child datasets under the existing `pool_4tb` pool
- Dataset permissions and host-path plumbing where provider support is clean
- Snapshot tasks and backup/sync jobs where supported
- Service users/groups needed by managed services
- Restic client job prerequisites for backing selected datasets up to S3

## Does Not Own

- Pool creation, destruction, or disk layout
- Boot pool or update train selection
- Network interface setup
- App runtime data
- Manual one-time bootstrap actions
- TrueNAS catalog app lifecycle when provider support is insufficient

Catalog apps are declared under `infra/truenas/apps/` and applied through the API wrapper until native provider support is good enough.

## Current Inventory

Read-only TrueNAS CLI inventory on `TrueNAS-25.04.2.6` found one healthy pool, `pool_4tb`, and these existing backup datasets:

- `pool_4tb/backups`
- `pool_4tb/backups/atlas`
- `pool_4tb/backups/atlas/2026-06-23`

These datasets are represented as `truenas_dataset` resources with `prevent_destroy = true` and OpenTofu `import` blocks. The first real plan with provider credentials should import them into state, not create or delete them.

The dated `2026-06-23` dataset contains backup data and is protected from Terraform destroy. Do not remove its resource or import block unless intentionally changing the ownership model for that preserved backup artifact.

## Authentication

The provider is configured for SSH authentication and requires private-key access before it can manage TrueNAS resources. Bootstrap that once outside OpenTofu with:

```bash
mise exec -- task truenas:bootstrap-ssh-key
```

The bootstrap helper creates a dataset-backed home at `/mnt/pool_4tb/mbastakis`, adds the managed `private_dot_ssh/id_ed25519.pub` key to the TrueNAS `mbastakis` user through the TrueNAS CLI shell, sets the login shell to `/usr/bin/bash`, enables passwordless sudo for the same admin user, then tests `~/.ssh/id_ed25519` and `sudo -n true`.

`Taskfile.yml` reads the private key from `~/.ssh/id_ed25519` at runtime and exports `TF_VAR_truenas_ssh_private_key` only for `tofu plan`/`tofu apply`. Override the key path with `TRUENAS_SSH_PRIVATE_KEY_PATH` if needed. Do not commit `.tfvars` files or key material.

The recorded SSH host key fingerprint for the provider is the NAS ECDSA host key:

```text
SHA256:PaERL229czZ7ImwLw6mCaZzlIKKmwdTuqTopEyEVjEU
```

## State Key

```text
homeserver/truenas/terraform.tfstate
```

## Commands

```bash
task truenas:bootstrap-ssh-key
task tf:truenas:init
task tf:truenas:plan
task tf:truenas:apply
```

Do not run `apply` until `plan` shows imports/adoption only and no deletes/replacements.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| terraform | >= 1.8.0 |
| truenas | ~> 0.16.0 |

## Providers

| Name | Version |
| ---- | ------- |
| truenas | 0.16.0 |

## Resources

| Name | Type |
| ---- | ---- |
| [truenas_dataset.backups](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.backups_atlas](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.backups_atlas_2026_06_23](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_pool.pool_4tb](https://registry.terraform.io/providers/deevus/truenas/latest/docs/data-sources/pool) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| truenas\_host | TrueNAS host or IP address. | `string` | `"192.168.1.74"` | no |
| truenas\_ssh\_host\_key\_fingerprint | TrueNAS SSH host key fingerprint. The provider currently negotiates the ECDSA host key. | `string` | `"SHA256:PaERL229czZ7ImwLw6mCaZzlIKKmwdTuqTopEyEVjEU"` | no |
| truenas\_ssh\_port | TrueNAS SSH port. | `number` | `22` | no |
| truenas\_ssh\_private\_key | Private key content for the TrueNAS SSH user. Supply via environment/secret manager; never commit it. | `string` | n/a | yes |
| truenas\_ssh\_user | TrueNAS SSH user used by OpenTofu. Must authenticate with a private key. | `string` | `"mbastakis"` | no |
<!-- END_TF_DOCS -->
