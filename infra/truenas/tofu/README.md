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

Read-only TrueNAS CLI inventory on `TrueNAS-25.04.2.6` found one healthy pool, `pool_4tb`. The legacy atlas migration datasets under `pool_4tb/backups` were removed after their FileBrowser payload was verified in the household FileBrowser dataset.

This stack now owns the target `pool_4tb/homeserver/...` dataset tree only, including the photo datasets, the durable `homeserver/data/books` library, and Audiobookshelf's separate config, metadata, and backup datasets. Writable app paths and books use `apps:apps` ownership; the Immich dataset also contains the OpenTofu-owned `.immich-storage` mount sentinel. Completed migration-staging state scaffolding has been removed. Do not reintroduce migration-staging datasets unless there is a new one-time migration with an explicit cleanup plan.

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
task truenas:tofu:init
task truenas:tofu:plan
task truenas:tofu:apply
```

Run `plan` before `apply`; the expected steady state is no changes unless new homeserver datasets are intentionally added.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| terraform | >= 1.8.0 |
| null | ~> 3.2 |
| truenas | ~> 0.16.0 |

## Providers

| Name | Version |
| ---- | ------- |
| null | 3.3.0 |
| truenas | 0.16.0 |

## Resources

| Name | Type |
| ---- | ---- |
| [null_resource.homepage_truenas_api_key](https://registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource) | resource |
| [truenas_dataset.apps_audiobookshelf](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_audiobookshelf_backups](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_audiobookshelf_config](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_audiobookshelf_metadata](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_backrest](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_backrest_cache](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_backrest_config](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_backrest_data](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_filebrowser_quantum](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_filebrowser_quantum_config](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_syncthing](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_syncthing_config](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_tailscale](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.apps_tailscale_state](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.data_books](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.data_files](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.data_files_household](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.data_files_users](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.data_files_users_chara](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.data_files_users_michail](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.data_obsidian](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.data_obsidian_michail](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.data_photos](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.data_photos_apple_originals](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.data_photos_immich](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.data_taskchampion_backup](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.homeserver](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.homeserver_apps](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_dataset.homeserver_data](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/dataset) | resource |
| [truenas_file.immich_storage_sentinel](https://registry.terraform.io/providers/deevus/truenas/latest/docs/resources/file) | resource |
| [truenas_pool.pool_4tb](https://registry.terraform.io/providers/deevus/truenas/latest/docs/data-sources/pool) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| homepage\_truenas\_api\_key\_name | Name assigned to the TrueNAS API key used by the Homepage dashboard widget. | `string` | `"homepage-dashboard"` | no |
| homepage\_truenas\_api\_key\_secret\_key | BWS key where the Homepage TrueNAS API key value is stored. | `string` | `"homeserver/truenas/api-keys/homepage"` | no |
| homepage\_truenas\_api\_key\_username | TrueNAS username that owns the API key used by the Homepage dashboard widget. | `string` | `"mbastakis"` | no |
| homeserver\_bws\_project\_id | Bitwarden Secrets Manager project ID used for homeserver automation secrets. | `string` | `"b6b2ed62-40f0-446b-b39f-b475001583b9"` | no |
| truenas\_connection\_host | Runtime TrueNAS SSH endpoint. Task plan/apply selects LAN first and Tailscale otherwise. | `string` | `"192.168.1.74"` | no |
| truenas\_host | Stable TrueNAS LAN identity used by managed resource metadata. | `string` | `"192.168.1.74"` | no |
| truenas\_ssh\_host\_key\_fingerprint | TrueNAS SSH host key fingerprint. The provider currently negotiates the ECDSA host key. | `string` | `"SHA256:PaERL229czZ7ImwLw6mCaZzlIKKmwdTuqTopEyEVjEU"` | no |
| truenas\_ssh\_port | TrueNAS SSH port. | `number` | `22` | no |
| truenas\_ssh\_private\_key | Private key content for the TrueNAS SSH user. Supply via environment/secret manager; never commit it. | `string` | n/a | yes |
| truenas\_ssh\_user | TrueNAS SSH user used by OpenTofu. Must authenticate with a private key. | `string` | `"mbastakis"` | no |
<!-- END_TF_DOCS -->
