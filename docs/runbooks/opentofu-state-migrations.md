# OpenTofu State Migrations

Use this runbook for module extraction, resource-address changes, and source
directory moves. It preserves the six existing state boundaries and provides
a rollback path without committing state or plan files.

## Immutable Backend Contract

These values are fixed inputs to the homeserver refactor:

| Item | Value |
|---|---|
| AWS profile | `mbastakis` |
| S3 bucket | `mbastakis-homeserver-opentofu-state` |
| Region | `eu-central-1` |
| Locking | S3 native lockfile |
| Bootstrap key | `homeserver/bootstrap/terraform.tfstate` |
| DNS key | `homeserver/dns/terraform.tfstate` |
| AWS foundation key | `homeserver/aws-foundation/terraform.tfstate` |
| TrueNAS key | `homeserver/truenas/terraform.tfstate` |
| Authentik key | `homeserver/authentik/terraform.tfstate` |
| Tailscale policy key | `homeserver/tailscale/terraform.tfstate` |

Do not change a backend key while moving source files. Initialize a moved root
with its existing key and `-reconfigure`; do not use `-migrate-state` between
keys.

## Phase 2 Baseline

The live read-only baseline was captured on 2026-07-10. S3 versioning was
enabled and all five state objects had a current recoverable version. The
`tf:state:baseline` task prints the current version IDs needed for recovery but
does not download state contents.

| Stack | Prior versions before the baseline | Plan result |
|---|---:|---|
| Bootstrap | 0 | No changes |
| DNS | 8 | No changes |
| AWS foundation | 5 | No changes |
| TrueNAS | 7 | No changes |
| Authentik | 8 | No changes |

The bootstrap object's current version is the pre-migration recovery point. S3
versioning retains it as the prior version when a later state write occurs.

Provider lockfiles at the baseline:

| Stack | Providers | Lockfile SHA-256 |
|---|---|---|
| Bootstrap | `hashicorp/aws` 5.100.0 | `f732c556f5ff2395af5c8d5a15fabf04e6f71d7845e5575827e19dd140c76c5a` |
| DNS | `hashicorp/aws` 5.100.0 | `f732c556f5ff2395af5c8d5a15fabf04e6f71d7845e5575827e19dd140c76c5a` |
| AWS foundation | `hashicorp/aws` 5.100.0 | `f732c556f5ff2395af5c8d5a15fabf04e6f71d7845e5575827e19dd140c76c5a` |
| TrueNAS | `deevus/truenas` 0.16.0, `hashicorp/null` 3.3.0 | `cc23150259382aaa1da399c849970acec462547cf835846931c005e846af3532` |
| Authentik | `goauthentik/authentik` 2026.5.0 | `fd9bce38c95a1528777b9a7b91dd5214f60f424fa5f63be11eb018da49e33ce3` |

Live reconciler baseline:

| Domain | Result |
|---|---|
| TrueNAS apps | Backrest 1.1.10 and FileBrowser Quantum 1.1.20 match declarations. Syncthing 1.3.11 and Tailscale 1.4.11 are one patch newer than their 1.3.10 and 1.4.10 declaration pins. All four apps are running; no additional catalog apps were present. |
| TrueNAS snapshots | Three declared tasks exist and are up to date; no orphaned task was reported for the managed dataset. |
| Backrest | Repository and three daily plans are up to date; the retired combined plan is absent and no unmanaged plan was reported for the managed repository. |
| Tailscale | The desired policy and ACL tests pass the live validation API. The validation endpoint does not prove equality with the currently applied whole-policy document. |
| Syncthing | Both peers are reachable and contain the managed peer and folder IDs. Dry-run suppresses writes, but the current reconciler always reports its intended PUT operations and does not prove normalized equality. |

The catalog version differences are expected pre-existing drift. Phase 2 does
not change the pins or upgrade/downgrade either app.

## Phase 3 Module Migration Record

The Phase 3 module-extraction plans were reviewed on 2026-07-10. Each affected
stack reported explicit address moves only, with `0` to add, `0` to change, and
`0` to destroy:

| Stack | Module extraction | Resource moves |
|---|---|---:|
| Bootstrap | Hardened state bucket | 6 |
| AWS foundation | Hardened backup bucket and two IAM users | 12 |
| Authentik | Backrest, Sisyphus, and Traefik Dashboard forward-auth graphs | 15 |

The DNS and TrueNAS roots are unchanged. TrueNAS datasets remain explicit
because the current parent/child dependency graph is clearer than a protected
dataset module.

Each module test root has its own provider lockfile so `tf:test` uses the same
AWS 5.100.0 and Authentik 2026.5.0 provider versions as the affected stacks.

Separate approval was granted and the three migrations were applied one state
at a time. Each private temporary saved plan was checked from JSON for its
exact move count and rejected any action other than `no-op` before apply. Every
apply reported `0` added, `0` changed, and `0` destroyed, and every immediate
verification plan was clean. The temporary plans were removed.

Post-migration recovery points:

| Stack | Current version ID | Prior versions |
|---|---|---:|
| Bootstrap | `r.c8p8rro17CV9.Anqtc1vu28mXSytTC` | 1 |
| DNS | `qBEdC.tcI8ePKb66u6RptSd45yQiY1pu` | 8 |
| AWS foundation | `FqN5PrDpzdC2.vMXIc8asKgv0FhzXtt2` | 6 |
| TrueNAS | `zyHvOQQU9i6yv24setc.GGBam3MQbOJi` | 7 |
| Authentik | `fVUbJ_6QfXkadUrw1Xm6zJUSwEW2TVDy` | 9 |

The unchanged DNS and TrueNAS IDs confirm that Phase 3 wrote only the three
affected states. Their Phase 2 versions are now the direct rollback points for
the module-address migrations.

## Phase 4 Source Path Migration Record

The Phase 4 source-only migration completed on 2026-07-10:

| Stack/domain | Former path | Current path | State key |
|---|---|---|---|
| Bootstrap | `infra/terraform/bootstrap/` | `infra/aws/stacks/bootstrap/` | `homeserver/bootstrap/terraform.tfstate` |
| DNS | `infra/terraform/dns/` | `infra/aws/stacks/dns/` | `homeserver/dns/terraform.tfstate` |
| AWS foundation | `infra/terraform/aws-foundation/` | `infra/aws/stacks/foundation/` | `homeserver/aws-foundation/terraform.tfstate` |
| TrueNAS | `infra/terraform/truenas/` | `infra/truenas/tofu/` | `homeserver/truenas/terraform.tfstate` |
| Authentik | `infra/terraform/authentik/` | `infra/identity/authentik/tofu/` | `homeserver/authentik/terraform.tfstate` |
| Atlas Ansible | `infra/ansible/` | `infra/atlas/ansible/` | n/a |
| Tailscale policy | `infra/tailscale/` | `infra/network/tailscale/` | n/a |
| Syncthing desired state | `infra/syncthing/` | `infra/sync/syncthing/` | n/a |

Each OpenTofu root was initialized at its current path with `-reconfigure` and
its existing key. All five detailed-exit-code plans returned no changes. No
`-migrate-state`, resource-address migration, state write, or live apply was
required. The state version IDs and provider lockfile checksums remained equal
to the Phase 3 recovery points.

## Phase 7 Tailscale Import Record

The existing whole-tailnet policy was imported on 2026-07-10 into
`tailscale_acl.homeserver` under the new isolated
`homeserver/tailscale/terraform.tfstate` key. Import ID `acl` created state only
and did not replace the remote policy. The first plan proposed one in-place
representation update for HuJSON formatting and a source-path comment, with no
rule or test changes. After the approved apply, the immediate second plan was
clean.

The current state version is `NFKnamgZIuK.JXVLNs8eCwi3Y2TwCgqN`; prior versions
`BtHRDl9Zg2I.qfoFy9y79hB__Uqvk1qA` and
`rZu5xymvK.lb7ESW0V.NCeO20j3MEM_o` retain the first normalization and
post-import recovery points. The
provider lockfile pins `tailscale/tailscale` 0.29.2 and has SHA-256
`02620963d1154962d8de2df31cf2f98f08a26844887b7411363791fd97db55de`.
The API key was supplied from BWS as provider environment configuration and is
not a resource-state attribute. The non-secret policy body is stored in state.

## Ownership Boundaries

| Domain | Code owns | Code does not own or delete implicitly |
|---|---|---|
| OpenTofu | Resource addresses recorded in each independent state | Objects outside state; resources in another state key |
| TrueNAS apps | Four declared catalog app values, managed files, and path permissions | App runtime data, undeclared apps, automatic catalog upgrades |
| Snapshots | Declared schedules identified by naming schema on the Obsidian dataset | One-off snapshots and tasks on other datasets; orphaned tasks are warnings only |
| Backrest | `homeserver-s3`, three declared plans, and the explicitly retired legacy plan | Repository contents, GUID, auth, history, cache, logs, and undeclared plans |
| Tailscale | The whole ACL policy document when explicitly applied | Devices, auth keys, routes, DNS settings, and node lifecycle |
| Syncthing | Declared options, peer IDs, folder IDs, and `.stignore` on the two managed peers | Runtime API keys, generated device IDs, and additional devices or folders |

## Pre-Migration Checklist

1. Run `mise exec -- task infra:validate`.
2. Run `mise exec -- task tf:state:baseline` and retain the current state
   version IDs in the change record. Do not redirect state contents to the
   repository.
3. Confirm the lockfile checksums are unchanged or explain the provider update
   separately from the migration.
4. Run the affected stack plan and confirm the baseline is understood.
5. Add a `moved` block for every OpenTofu resource address change. Do not rely
   on resource-name similarity or manual import to infer identity.
6. Keep the backend bucket, region, and state key unchanged.
7. Run `tofu fmt`, `tofu validate`, and the affected live plan.
8. Stop if the plan contains an unexplained create, replace, or destroy action.
9. For a module extraction, require the plan to report address moves and no
   remote resource changes.
10. For a path move, initialize the new path with `-reconfigure` and the same
    backend key. Do not use `-migrate-state`.
11. Do not save a plan file in the repository. If a temporary plan is required,
    write it under a private OS temporary directory and remove it afterward.
12. Apply only after separate approval, then run a second plan and require it
    to be clean.
13. Keep successful `moved` blocks through the migration verification window,
    then remove them during an approved compatibility cleanup after clean plans.

## Rollback

### Before Apply

Revert the source/module change, remove the new `moved` blocks, reinitialize the
original root with its unchanged backend key, and rerun the plan. No state
rollback is needed because planning does not commit resource-address moves.

### After An Address-Only Apply

Revert the resource configuration and add inverse `moved` blocks from the new
addresses to the old addresses. The rollback plan must show address moves only,
with no create, replace, or destroy actions. Apply that plan only after separate
approval, then require a clean second plan.

Prefer inverse `moved` blocks over direct `tofu state mv` commands so the
rollback remains reviewable and repeatable.

### After A Source Path Move

Move the root back to its prior path and run its normal domain `*:init` task.
The task uses `-reconfigure` with the same state key. Run a plan and require no
path-induced changes.

### Restore A Prior S3 State Version

Use this only when state itself was written incorrectly and remote resources
did not change. Stop all concurrent OpenTofu operations, identify the prior
version with `tf:state:baseline`, initialize the correct stack/backend, and
download the selected version to a private temporary directory:

```bash
umask 077
stack="dns"
state_key="homeserver/dns/terraform.tfstate"
version_id="replace-with-recorded-version-id"
case "$stack" in
  bootstrap|dns) stack_dir="infra/aws/stacks/$stack" ;;
  aws-foundation|foundation) stack_dir="infra/aws/stacks/foundation" ;;
  truenas) stack_dir="infra/truenas/tofu" ;;
  authentik) stack_dir="infra/identity/authentik/tofu" ;;
  *) printf 'Unknown stack: %s\n' "$stack" >&2; exit 1 ;;
esac
recovery_dir="$(mktemp -d)"
trap 'rm -rf "$recovery_dir"' EXIT
aws-login exec mbastakis -- aws s3api get-object \
  --bucket mbastakis-homeserver-opentofu-state \
  --key "$state_key" \
  --version-id "$version_id" \
  "$recovery_dir/terraform.tfstate"
aws-login exec mbastakis -- tofu -chdir="$stack_dir" state push \
  "$recovery_dir/terraform.tfstate"
```

Do not use `-force` unless state lineage/serial recovery has been independently
reviewed. Never commit, attach, or paste state contents because state can contain
secret values.
