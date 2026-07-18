# Homeserver IaC

The homeserver automation is source-only infrastructure code under `infra/`. It does not deploy through chezmoi.

## Roles

| Host | Role | Management path |
|---|---|---|
| `atlas` | Ubuntu application/server host, Tailscale entry node, Traefik/AuthentiK host, Homepage dashboard | Ansible under `infra/atlas/ansible/` |
| `truenas` | TrueNAS SCALE storage appliance with minimal apps, including Audiobookshelf | OpenTofu under `infra/truenas/tofu/` plus catalog app API wrapper |
| Authentik | Homeserver identity plus FileBrowser Quantum, Immich, and Audiobookshelf OIDC config | OpenTofu under `infra/identity/authentik/tofu/` after the atlas Authentik service is reachable |

## TrueNAS Scope

`truenas` targets TrueNAS SCALE 25.04.2 or newer. It is storage-first and may run only minimal storage-adjacent apps: Tailscale, Syncthing, FileBrowser Quantum, Backrest/restic backup services, and Audiobookshelf. Audiobookshelf is placed on TrueNAS so its SQLite database and media avoid network storage.

OpenTofu may manage lower-blast-radius configuration:

- child datasets under the existing `pool_4tb` pool
- permissions and service identities where provider support is clean
- snapshot and backup jobs
- host-path app prerequisites

OpenTofu does not manage pool creation, disk layout, boot pool, network interfaces, update train selection, or app runtime data.

The temporary atlas migration datasets under `pool_4tb/backups` were removed after their FileBrowser payload was verified in `homeserver/data/files/household`. The TrueNAS stack now owns only the target homeserver datasets and no longer imports legacy backup-staging paths.

TrueNAS SSH key installation is a one-time bootstrap step, not part of the persistent OpenTofu state. Run `mise exec -- task truenas:bootstrap-ssh-key` to create a dataset-backed home at `/mnt/pool_4tb/mbastakis`, add the managed `id_ed25519.pub` key to the `mbastakis` TrueNAS user through the TrueNAS CLI shell, set that account's login shell to `/usr/bin/bash`, and enable passwordless sudo for provider automation; after that, the `truenas` SSH alias and `192.168.1.74` host entry both pin `~/.ssh/id_ed25519`.

TrueNAS API keys for automation consumers (e.g. the Homepage dashboard widget) are created through a `null_resource` with a `local-exec` provisioner that invokes the typed `homeserver-iac api-key` publisher over the same SSH bootstrap path. The `deevus/truenas` provider does not expose an `api_key` resource, so the `null_resource` bridges the gap code-managed. The publisher checks both TrueNAS and BWS, handles the generated value only in memory, compensates for a failed BWS write by removing only the key it just created, and never persists the value in OpenTofu state. The resource remains `prevent_destroy` (see ADR-0004).

## App Model

Stable TrueNAS catalog apps are preferred when they fit. App declarations live under `infra/truenas/apps/`, pin explicit catalog versions, and contain non-secret values only.

The current provider can manage custom Compose apps but does not yet expose full catalog app install fields. Until that changes, catalog app declarations are applied through a small TrueNAS API or `midclt` wrapper.

## Typed Desired State

The Python package under `infra/src/homeserver_iac/` defines separate Pydantic
contracts and reconcilers for TrueNAS catalog apps, Audiobookshelf API configuration, periodic snapshots, bounded
NFS and SMB exports, disk maintenance, Backrest policy, Syncthing, and BWS secret metadata. Every document declares an
explicit schema version and bounded `ownership.scope`; Syncthing is schema v2
because it also declares the TrueNAS host path used for ignore files. Resource IDs such
as app names, snapshot task IDs, Backrest repository/plan IDs, Syncthing folder
IDs, NFS and SMB share IDs, and secret aliases are stable comparison keys.

Secret-bearing fields use typed `secret_ref` objects that contain only a
logical alias. Secret values are not representable in the model, schema
validation never resolves BWS, and the common plan serializer carries changed
field names rather than before/after values. Secret metadata records ownership,
lifecycle, BWS identity, and target environment bindings without storing secret
material.

Generated JSON Schemas live in `infra/schemas/` and each YAML document has a
`yaml-language-server` schema hint. Public Python operations are Task-only:

```bash
mise exec -- task infra:python:sync       # explicit dependency installation
mise exec -- task infra:desired:validate  # no live APIs or secret resolution
mise exec -- task infra:python:validate   # format, lint, types, tests, schemas
mise exec -- task infra:schemas:generate  # intentional schema regeneration
```

Validation uses exit code `0` for valid/no drift, `2` for drift, `3` for schema
or input validation failure, and `4` for operational failure. The common
operation order is create, update, explicit delete, stale, warning, then
unchanged. Stale resources are reported but never implicitly deleted; deletion
requires an explicit declaration and remains a separate apply/prune action.

Phase 6 moved BWS injection, snapshots, Backrest, Syncthing, catalog apps, and
TrueNAS API-key publication into the typed runtime. Stable script paths are thin
Python shims; the superseded shell implementations and rollback task aliases
were removed after the Phase 8 compatibility window.

### OpenWrt Network Domain (Production Accepted)

The `infra/network/openwrt/router.yaml` contract is the single human-edited
policy source for the Cudy WR3000E v1/R53. It pins the stock-layout management
image and owns stable system, VLAN 835 PPPoE, trusted/guest network, DHCP/DNS,
firewall, radio, Dropbear/uHTTPd, IPv6-PD, SQM, and flow-offload fields. Leases,
WAN addresses, delegated prefixes, counters, logs, host/TLS keys, calibration
data, and device-specific boot state remain runtime-owned.

DNS keeps global rebinding protection enabled while exempting only the twelve
Route53 private-service FQDNs that intentionally resolve to atlas's Tailscale
address. Atlas and TrueNAS reservations publish static forward/reverse local DNS
records so names do not depend on current DHCP lease timing. LAN and guest
clients continue to query OpenWrt. Its dnsmasq resolver sends queries to Pi-hole
on atlas first and uses Cloudflare only when Pi-hole is unavailable, so an atlas
outage disables filtering but does not disable internet DNS.

The firmware overlay contains only the public SSH key and a non-secret
stdin-to-libubus helper. BWS values are injected after boot and never enter the
image, argv, or plan output. Pinned `community.openwrt` modules own routine
system, trusted DHCP/DNS/reservations, main Wi-Fi, SQM, and flow-offload fields.
They operate without Python on the router, use stable managed section names,
prune only bounded prefixes, and suppress secret task output.

Base LAN/management, WAN, complete guest networking, and IPv6 remain
reachability-critical. A narrow control-side extension applies those as separate
protected transactions with strict SSH, encrypted bundles, rpcd timed rollback,
health gates, and same-session confirmation. Routine convergence creates no
transaction bundle. rpcd protection is lost across reboot, power loss, or
rpcd/ubus restart, so Speedport, TFTP, and UART recovery remain separate.

The Ansible-first ownership transfer was accepted on production with a
zero-change apply and second zero-change plan. No protected transaction was
created because router state did not change. Historical encrypted transaction
evidence remains preserved but routine-stage bundles are no longer revertible
through the protected controller.

Public operations are `network:openwrt:validate`, `network:openwrt:firmware:build`,
`network:openwrt:firmware:verify`, `network:openwrt:bootstrap`,
`network:openwrt:plan`, `network:openwrt:apply`, `network:openwrt:status`,
`network:openwrt:backup`, `network:openwrt:recover`, and
`network:openwrt:upgrade`, and `network:openwrt:clean-rebuild`. Task is the only
public interface. Ansible playbooks, collection modules, and Python entrypoints
are implementation details. Firmware build writes only under
`.local/openwrt/`; known hosts, encrypted backups, and protected transaction
bundles also remain there. Live operations are never dependencies of
`infra:validate`.

The firmware builder runs the official Linux amd64 Image Builder in a
digest-pinned container through arm64 Colima. Its case-sensitive ephemeral
filesystem is writable; the pinned archive and generated public-only overlay are
read-only inputs, and only finished output is mounted back under `.local/`.
Verification is network-disabled and independently checks embedded sysupgrade
metadata/layout, the resolved package sidecar, and the actual squashfs key/helper
content and permissions.

Production cutover and staged acceptance completed on 2026-07-17. The Cudy is
the active router; the configured Speedport remains powered off and unchanged as
the physical rollback path during the observation window. The settings-free
clean-rebuild drill completed that day with a fresh protected transaction
generation, zero-change apply and plan, verified encrypted backup, working
trusted and guest Wi-Fi, and restored dependent-host connectivity. The
observation window started on 2026-07-17 and can close no earlier than
2026-07-24; only rollback-router retirement remains open. See the
[cutover](../runbooks/openwrt-router-cutover.md) and
[recovery](../runbooks/openwrt-router-recovery.md) runbooks.

The Immich storage phase adds typed share reconcilers because the current TrueNAS provider has no NFS or SMB share and service resources. Their ownership boundary is limited to declared exports. The Immich NFS export is read/write only from atlas's reserved `192.168.1.19` address, maps all access to `apps:apps`, and rejects wildcard client declarations. The temporary Apple migration SMB share is non-browsable, rejects guest access, authenticates only `mbastakis`, and maps writes to `apps:apps`; it is removed after migration acceptance. OpenTofu separately owns the dataset permissions and `.immich-storage` sentinel. The atlas `atlas_immich` Ansible role owns the NFS mount/automount, verifies the live source and sentinel, and runs the dedicated Compose project through a mount-bound systemd service. Docker restart policies cannot independently start Immich without that host-level gate. The role also mounts a read-only, secret-bearing `IMMICH_CONFIG_FILE`, making global application settings and the OIDC client policy code-owned while user records, OIDC account links, and mobile-device choices remain runtime-owned.

The typed reconcilers read live state, normalize only code-owned fields, preserve
runtime-owned and unmanaged objects, and emit the common secret-safe operation
plan. Snapshot deletion requires `--prune`; Backrest deletes only IDs listed in
`retirePlans`; Syncthing and catalog apps preserve undeclared devices, folder
bindings, apps, and runtime fields. FileBrowser's self-written YAML defaults and
Tailscale's hardened state-directory mode are explicit runtime ownership
boundaries.

## Backup Model

TrueNAS backups use restic to S3 from the NAS itself. The off-NAS backup scope is Obsidian, personal files, the atlas-copied TaskChampion sync SQLite backup, durable Immich media, the Apple originals archive, weekly Audiobookshelf application archives, and monthly book media. General app config datasets and regenerable caches remain excluded.

The backup model follows 3-2-1 principles: live TrueNAS datasets are the primary copy, local ZFS snapshots are the fast rollback copy, and encrypted restic snapshots in S3 are the offsite copy. Syncthing replicas are useful extra device copies, but synchronization is not treated as the backup authority.

Backrest uses one restic repository, `homeserver-s3`, and separate plans per data domain. Files, Obsidian, Immich media plus native database dumps, Apple originals, and TaskChampion run daily; Audiobookshelf application archives run weekly and book media runs monthly. The Immich plan follows the 02:00 native database dump, and the stable Apple archive skips unchanged runs. This keeps deduplication in one repo while making failures, restores, and retention clearer per dataset.

Backrest repository and plan policy is code-owned in `infra/truenas/backrest/backrest-plans.yaml` and reconciled through the Backrest API with `infra/truenas/backrest/manage-backrest`. Do not edit Backrest `config.json` directly because it also contains runtime-owned fields such as repository GUID, auth state, multihost identity, and config `modno`.

Atlas serializes its TaskChampion exports locally. During each export it stops only
the `taskchampion-sync` Compose service, creates a standalone SQLite database
through Python's backup API, and accepts it only when `PRAGMA quick_check`
returns `ok`. An `EXIT` trap restores the service on every failure path, and the
normal path restores service before any network transfer. TrueNAS publication is
transactional at the file level: rsync writes a hidden temporary name, SSH
atomically renames it to the timestamped final name, and retention pruning starts
only after that rename succeeds. SSH remains pinned to the independently verified
managed `known_hosts` entries.

The Backrest repository passes restic `--limit-upload=6000`, capping S3 writes
at about 49.2 Mb/s so backup traffic uses no more than half of the 100 Mb/s WAN
upload service. This does not throttle restores, Syncthing, application traffic,
or the small Atlas-to-TrueNAS TaskChampion copy. Backrest serializes its normal
backup queue, so the limit is aggregate for these managed plans; concurrent
external restic processes and Backrest's unrestricted Run Command path are
outside that guarantee.

The SMART daemon, pool scrub, and SMART schedules are code-owned under
`infra/truenas/maintenance/`. The reconciler requires `smartd` to be enabled at
boot and running, while TrueNAS remains responsible for supervising and
alerting on the daemon. The scrub keeps TrueNAS's 35-day threshold and moves its
weekly eligibility check after the overnight backup window. SMART short tests
run weekly and extended tests monthly on separate days from the scrub. The
reconciler refuses to apply maintenance changes unless the pool is `ONLINE`;
after a disk incident, replace and resilver first, then run the post-replacement
scrub before applying the recurring policy.

The active restic repository must remain immediately readable. The AWS foundation stack transitions active repository objects to S3 Glacier Instant Retrieval; do not use asynchronous Glacier Flexible Retrieval or Deep Archive lifecycle rules for the active repository.

## OpenTofu State

The OpenTofu state backend is owned by the `infra/aws/stacks/bootstrap/` stack. Its one-time helper runs the first apply with local state, creates or adopts the fixed S3 bucket, then migrates bootstrap state into that bucket. The backend identity is fixed in the repository: S3 bucket `mbastakis-homeserver-opentofu-state`, region `eu-central-1`, and S3 native lockfiles. Individual stacks use separate state keys in the same backend:

| Stack | Path | State key |
|---|---|---|
| Bootstrap | `infra/aws/stacks/bootstrap/` | `homeserver/bootstrap/terraform.tfstate` |
| DNS | `infra/aws/stacks/dns/` | `homeserver/dns/terraform.tfstate` |
| AWS foundation | `infra/aws/stacks/foundation/` | `homeserver/aws-foundation/terraform.tfstate` |
| TrueNAS | `infra/truenas/tofu/` | `homeserver/truenas/terraform.tfstate` |
| Authentik | `infra/identity/authentik/tofu/` | `homeserver/authentik/terraform.tfstate` |
| Tailscale policy | `infra/network/tailscale/tofu/` | `homeserver/tailscale/terraform.tfstate` |

The DNS stack manages the Route53 public hosted zone and the private homeserver service records (`auth`, `code`, `files`, `tasks`, `taskboard`, `home`, `traefik`, `backrest`, `photos`, `audiobooks`, `push`, and `pihole`) pointing at atlas over Tailscale. The legacy Cloudflare Tunnel / external-dns records were intentionally not migrated; `mbastakis.com` starts fresh in AWS DNS. Registrar nameserver delegation at Enartia/Papaki remains a manual cutover step documented in `infra/aws/stacks/dns/README.md`.

The AWS foundation stack manages the restic backup bucket, restic IAM, and Traefik Route53 ACME IAM. It reads the Route53 zone for IAM scoping but does not own DNS records. It does not manage the state bucket; that belongs to the bootstrap stack.

Repeated provider resource graphs are implemented by local modules under
`infra/aws/modules/` and `infra/identity/authentik/modules/`. The hardened S3 module encodes private access,
ownership, TLS-only policy, encryption, optional versioning and lifecycle
rules, and destroy protection. The IAM-user module receives stack-owned policy
JSON so least-privilege decisions remain visible in the AWS foundation root.
The Authentik forward-auth module receives stable application identity, URLs,
description, allowed groups, shared flow IDs, and the embedded outpost ID. Root
stacks still own all state keys, provider configuration, policy decisions, and
public outputs; explicit `moved` blocks preserve every extracted resource
identity.

TrueNAS datasets remain explicit root resources. Their parent/child
dependencies and individual `prevent_destroy` boundaries are clearer in the
current graph than behind a dataset module, so Phase 3 intentionally performs
no TrueNAS dataset address migration.

`infra/network/tailscale/policy.hujson` implements the default-deny ACL model from the target architecture (§6): three groups (`homeserver-admins`, `homeserver-household`, `obsidian-sync`), specific accept rules for tagged nodes, a narrow Atlas-to-OpenCode-Mac port-`443` path, a general `autogroup:member` rule for non-tagged tailnet connectivity, and a `tests` section asserting both the intended paths and denied infra surfaces. Tailscale Funnel is intentionally not enabled. The imported `tailscale_acl.homeserver` resource owns the whole policy through the official provider. Provider authentication is injected from BWS at runtime, so neither the API key nor the Atlas and TrueNAS enrollment auth keys enter OpenTofu state. The non-secret whole policy is stored in state as a normal resource attribute.

The provider is pinned to `tailscale/tailscale` 0.29.2. That release validates
HuJSON locally but does not call Tailscale's remote policy-validation endpoint
during plan; the upstream implementation exists only on unreleased main.
`infra/network/tailscale/manage-policy` therefore remains as validation-only
glue and is run before every provider plan and apply.

Phase 7 also re-evaluated the remaining custom reconcilers against current
upstream implementations:

| Domain | Decision | Concrete gap |
|---|---|---|
| Syncthing | Retain the typed Python reconciler | `benleppke.syncthing` 0.9.0 cannot additively preserve unmanaged folder-device bindings, replaces the complete ignore list, and compares order-sensitive `.stignore` rules as a set. |
| TrueNAS | Retain the current provider plus typed reconcilers | The appliance is on 25.04.2.6 while the broad `PjSalty/truenas` 2.x support target is 25.10+. Its app version field forces replacement, and generated API keys enter state. No official iXsystems provider covers the required surface. |
| Backrest | Retain the typed Python reconciler | Backrest documents only backup triggering and operation queries as stable; repository and plan configuration endpoints remain outside its stable public API. |

Atlas no longer embeds nested shell programs for TrueNAS backup setup or parses
Docker Compose CLI output for idempotence. The homeserver role uses a focused,
check-mode-aware `truenas_user_ssh_key` module for the middleware-owned user key,
`ansible.builtin.file` for the delegated backup directory, and
`community.docker.docker_compose_v2` for Compose convergence.

`Taskfile.yml` verifies the fixed S3 bucket before remote stack initialization, planning, or applying. Plan/apply tasks re-run `tofu init -reconfigure` with the fixed backend config and `use_lockfile=true` first, so a local `-backend=false` validation init or accidental alternate backend cannot be reused silently.

Before any module, address, or source-path migration, run
`mise exec -- task tf:state:baseline`. It rejects a changed bucket or region,
requires S3 versioning and all six fixed state keys, and reports recoverable
version IDs plus lockfile checksums without downloading state contents. Every
resource address change requires an explicit `moved` block; source-path moves
reuse the existing key with `-reconfigure`, never a key-to-key state migration.
The checklist and rollback commands live in
`docs/runbooks/opentofu-state-migrations.md`.

## Task Ownership And Validation

`Taskfile.yml` is the only public repository-root deployment interface. It retains only
repository orchestration and includes domain implementations from
`infra/Taskfile.yml`, `infra/aws/Taskfile.yml`, `infra/atlas/Taskfile.yml`,
`infra/truenas/Taskfile.yml`, `infra/identity/Taskfile.yml`,
`infra/network/Taskfile.yml`, and `infra/sync/Taskfile.yml`. Cross-stack
OpenTofu quality and state commands remain in `infra/tofu.Taskfile.yml`; old
`tf:<stack>:*`, `tailscale:*`, and `syncthing:*` deployment aliases are removed.
The root continues to provide the fixed OpenTofu backend bucket and region to
included tasks.

`mise exec -- task infra:validate` is the offline gate. It verifies the public
task surface and OpenTofu formatting, checks all Atlas playbook syntax,
validates the Backrest declaration, runs the locked Python
format/lint/type/test/schema gate, runs Bash syntax and ShellCheck, and applies
the relaxed yamllint policy. It does not run
`tf:validate`, which may initialize providers on a fresh workstation, or
`network:policy:validate`, which calls the live Tailscale API. It also avoids
all AWS, BWS, SSH, live-plan, and apply paths. Live reconciler plans are separate
domain tasks and are never dependencies of `infra:validate`.

Atlas operations use `atlas:*` tasks. Plan tasks run Ansible check mode with
diff output, which is advisory when a module cannot fully model a remote
mutation without applying it. Apply tasks remain explicit and are never called
as dependencies of validation. The inventory targets the `atlas` OpenSSH alias,
which uses `~/bin/homeserver-route` to accept the LAN address only when its
ED25519 host key matches the pinned Atlas fingerprint and otherwise connects to
the Atlas Tailscale address.

`mise exec -- task infra:status` is the live, read-only aggregate. It runs the
`aws:status`, `truenas:status`, `identity:status`, `network:status`,
`sync:status`, and `atlas:status` domain checks in order. It never applies
changes and is intentionally excluded from offline validation.

## Tooling

Repo-local tooling is pinned in `mise.toml` and exposed through `Taskfile.yml`:

```bash
mise install
task infra:validate
task infra:status
task infra:python:sync
task infra:desired:validate
task infra:python:validate
task infra:schemas:generate
task atlas:validate
task atlas:base:plan
task aws:bootstrap-state
task tf:state:baseline
task aws:bootstrap:plan
task aws:dns:plan
task aws:foundation:plan
task atlas:audiobookshelf:plan
task tf:fmt
task tf:fmt:check
task tf:test
task tf:tflint
task tf:docs
task truenas:bootstrap-ssh-key
task truenas:backrest:validate
task truenas:backrest:plan
task truenas:maintenance:plan
task truenas:audiobookshelf:plan
task truenas:snapshots:plan
task truenas:snapshots:photos:plan
task truenas:snapshots:audiobookshelf:plan
task truenas:snapshots:books:plan
task truenas:nfs:plan
task truenas:apps:plan
task truenas:api-key:plan
task sync:plan:all
task truenas:tofu:plan
task identity:authentik:plan
task network:policy:validate
task network:policy:plan
```

AWS-backed OpenTofu commands run through `aws-login exec mbastakis --` so credentials are resolved outside the repository. The profile is hardcoded in repository workflows; targeting a different AWS account requires an intentional code change.

TrueNAS OpenTofu plan/apply tasks read the SSH private key from `~/.ssh/id_ed25519` at runtime and export `TF_VAR_truenas_ssh_private_key` for the provider. Override with `TRUENAS_SSH_PRIVATE_KEY_PATH` if a different key is required; key material is not stored in the repository. The tasks also export the address selected by `~/bin/homeserver-route`: a LAN endpoint is accepted only when its ED25519 host key matches the pinned TrueNAS fingerprint, with Tailscale as the fallback. The provider independently pins TrueNAS's ECDSA host key. Typed SSH reconcilers use the routed `truenas` OpenSSH alias, and Syncthing receives a route-specific API URL. Because the ACL denies raw Backrest port `30329` to clients and TrueNAS OpenSSH disables forwarding, remote Backrest reconciliation creates a temporary tunnel through Atlas to the TrueNAS LAN endpoint rather than weakening either control. `HOMESERVER_ROUTE_FORCE=lan|tailscale` and the explicit `*-lan`/`*-tailscale` SSH aliases are troubleshooting overrides.

Typed TrueNAS SSH clients reject unknown host keys even when using an ephemeral client identity. Atlas's TaskChampion backup separately renders only independently verified Ed25519 public host keys from `atlas_homeserver_truenas_backup_ssh_host_keys`; multiple approved keys allow an explicit old/new overlap during rotation. Neither path automatically enrolls trust or reads a TrueNAS private host key.

NFS shares are identified by exact path, SMB shares by case-folded name, and periodic snapshot tasks by dataset plus naming schema. Plan and apply both raise an operational error before any mutation when more than one live resource matches a declared or explicitly retired managed identity. Operators must resolve the duplicate directly before reconciliation can continue.

Atlas Tailscale enrollment uses `infra/secrets/homeserver-secrets exec atlas-tailscale` so the preauth key is injected only for the child Ansible process. The role stores the key briefly in `/run` with root-only permissions and removes it after `tailscale up`.

The atlas homeserver playbook uses Traefik's file provider for private entrypoints (`auth`, `code`, `files`, `tasks`, `taskboard`, `home`, `traefik`, `backrest`, `audiobooks`, `push`, and `pihole`) instead of Docker labels/socket discovery. Authentik listens on the Compose network at port `9000`; FileBrowser Quantum, Backrest, and Audiobookshelf are reached over the LAN at their TrueNAS app ports; TaskChampion sync listens only on the Compose network and is routed at `tasks.mbastakis.com`; Sisyphus builds locally from source as the `taskboard` service, listens on the Compose network at port `8080`, is routed at `taskboard.mbastakis.com`, and is protected by the shared Authentik forward-auth middleware; the Homepage dashboard listens on port `3000` and is routed at `home.mbastakis.com`; the Traefik dashboard is routed privately at `traefik.mbastakis.com` through `api@internal` and protected by the same middleware; Backrest is routed at `backrest.mbastakis.com` and protected by the same middleware. Pi-hole publishes DNS only on atlas's reserved LAN address, forwards upstream to Cloudflare without using OpenWrt, and exposes its passwordless container UI only through an Authentik-protected Traefik route. ntfy runs unprivileged on the Compose network, stores its native auth and temporary message cache in SQLite under `/opt/homeserver/ntfy`, and is routed at `push.mbastakis.com` without interactive forward-auth so iOS background polling can authenticate directly. Its declarative deny-by-default ACL grants `michail` read-only access to all topics and grants the isolated `opencode` identity write-only access to its topic. The OpenCode router terminates `code.mbastakis.com` TLS, preserves that host, and uses the Mac's `*.ts.net` name for verified TLS SNI to the Tailscale Serve backend. Audiobookshelf is routed without forward-auth so its native web and mobile authentication callbacks remain usable; OpenCode uses oauth2-proxy rather than the shared forward-auth middleware. The role also installs a daily systemd timer that copies the TaskChampion SQLite file to a TrueNAS dataset for Backrest.

The Authentik OpenTofu stack owns the default brand in addition to the Traefik Dashboard, Sisyphus, and Backrest proxy providers/applications. The brand uses the Hyperion title, image, and background already served by Homepage, defaults Authentik to dark mode, and loads `catppuccin-mocha.css`. The theme changes semantic Authentik and PatternFly variables plus explicitly exported component parts rather than private DOM selectors, reducing upgrade breakage while covering login flows and the user library. The imported default brand is protected from accidental destruction and retains Authentik's default invalidation and user-settings flows while using the managed homeserver authentication flow.

The proxy providers are attached to the embedded Authentik proxy outpost, and access is limited to the `homeserver-files-admins` group. Traefik routes `/outpost.goauthentik.io/` on each protected host back to Authentik without the forward-auth middleware so callback/session endpoints do not loop through the protected application router. Sisyphus keeps `/healthz` unprotected for Homepage monitoring.

The Homepage dashboard container runs unprivileged without the Docker socket; all services are configured manually in `services.yaml` with native widgets for TrueNAS, Tailscale, Backrest, and Traefik, a custom API widget backed by Glances for Atlas host metrics, plus selected `siteMonitor` checks. The dashboard puts FileBrowser Quantum, Immich, Audiobookshelf, Sisyphus, and the Michail-only OpenCode link in Applications, then separates data protection, platform, and network operations; link-only external destinations live in `bookmarks.yaml` rather than being represented as services. Status-only backends do not link to machine endpoints, and the dashboard does not include a self-referential Homepage card. After rendered dashboard config changes, the role calls Homepage's revalidation endpoint because service data hot-reloads but layout settings are part of the statically generated page state. The header includes Homepage's native Google web search widget; custom CSS lets it use available desktop space, gives it the full header width on mobile, emphasizes the application row, and adds responsive gaps between service sections. Hyperion and Sisyphus image assets are stored with the Ansible role and deployed through the existing `/app/public/images` mount; Hyperion is used for the header logo and favicon, while Sisyphus is used for the taskboard card. Browser-facing links can use tailnet/private hostnames, but widget and monitor URLs for TrueNAS-hosted apps use the NAS LAN address because atlas Docker containers do not reliably route to the host's Tailscale interface. Glances runs as a private Compose service on the `homeserver` network and exposes host CPU, memory, and GPU metrics only to Homepage; the GPU block depends on the host GPU being visible to the Glances container. The Homepage container sets `NODE_TLS_REJECT_UNAUTHORIZED=0` so the internal TrueNAS widget can read the NAS API through its self-signed certificate; keep that scoped to this private dashboard container. The Traefik API is exposed on port `8080` inside the Compose network only (`--api.dashboard=true --api.insecure=true`, no host port published) so the Traefik widget can read route/middleware data without exposing the dashboard UI to the tailnet. Homepage widget secrets are injected through a dedicated `atlas-homepage` BWS target with `HOMEPAGE_VAR_*` environment variables.

The Pi-hole card uses Homepage's native Pi-hole v6 widget over the internal Compose endpoint so Authentik does not intercept its API requests. It reports total queries, blocked queries, blocked percentage, and gravity domains; the browser-facing link remains protected by Authentik.

The OpenWrt card links to the Cudy WR3000E LuCI interface and checks its HTTPS endpoint. Router metrics require a dedicated least-privilege `rpcd` account rather than the root management credential.

The household-facing polish keeps operations visible without letting them dominate the launch surface: application cards use larger launch targets, operational cards use darker surfaces, and section headings retain contrast over the wallpaper. Homepage Quick Launch searches service names and descriptions and exposes a mobile trigger, while the technical version footer stays hidden. Tailscale widgets intentionally show only address and last-seen data with theme-aware icons to avoid wrapped version strings, and Authentik uses its internal liveness endpoint for the same availability signal as other applications.

The Authentik stack owns the FileBrowser Quantum, Immich, Audiobookshelf, and OpenCode native OIDC providers. OpenCode registers the strict `https://code.mbastakis.com/oauth2/callback` URI, includes the shared group claim, and permits only the dedicated `opencode-users` group; only `michail` is assigned to that group. oauth2-proxy repeats the group check before forwarding browser traffic to the Mac's loopback-only OpenCode server. It requests the managed `offline_access` scope assigned to the OpenCode provider so Authentik's 10-minute access token can be renewed with the provider's seven-day refresh token when a suspended browser resumes. Immich registers strict web login, manual-linking, and mobile callback URIs plus its backchannel logout endpoint. Audiobookshelf registers strict `/audiobookshelf` web/mobile callbacks because version 2.35.1 validates browser callbacks against its compiled router base path. Other application policies permit members of the household/admin groups; the bootstrap `akadmin` identity is not a member and cannot authorize these applications. A dedicated `immich` scope emits `immich_role=admin` only for the managed `michail` identity, and a dedicated `audiobookshelf` scope emits the `admin` role only for that identity; every other accepted identity receives `user`. OpenTofu assigns `mbastakis@gmail.com` to `michail`, generates and persists dedicated 4096-bit RSA keys and long-lived self-signed certificates for Immich, Audiobookshelf, and OpenCode in the encrypted, versioned S3 state, then recreates the Authentik certificate resources during a server rebuild. Authentik uses them to sign tokens with RS256; oauth2-proxy requires the OpenCode provider's published JWKS key and cannot use Authentik's symmetric HS256 default. Signing-key rotation is explicit because replacing a key without an overlapping JWKS window can invalidate active tokens. The existing Immich administrator links by matching email, while Audiobookshelf's BWS-backed `michail` root links by matching username on its first OIDC login. Local password login remains enabled for break-glass access and Audiobookshelf API reconciliation. All native providers explicitly enable the `authorization_code` grant; an empty grant list causes clients to fail with `invalid_request` or `invalid_grant`.

Traefik's private `websecure` entrypoint uses a finite three-hour request-body read timeout and ten-minute idle timeout. Traefik otherwise defaults to a 60-second whole-request read deadline, which interrupts large Immich video uploads; response writes retain Traefik's unlimited default, and no buffering middleware is used.

The Authentik stack also owns the force-password-reset-on-first-login flow. Users are created with `attributes.reset_password = true`; the authentication flow conditionally inserts a prompt stage (new password entry) and a user-write stage (persist new password + clear the marker) between the identification stage (order 10) and the user-login stage (order 20). Two expression policies gate the stages: `reset_password_check` returns `True` only when the marker is set, and `reset_password_update` clears the marker in-place. The `authentik_user` lifecycle uses `ignore_changes = [password, attributes]` so OpenTofu does not fight the runtime mutation when Authentik flips `reset_password` from `true` to `false`. New users get the marker automatically on creation; existing users created before the flow was applied need a one-time manual marker set through the Authentik admin UI.

TrueNAS apps use explicit public DNS resolvers (`1.1.1.1`, `8.8.8.8`) so containers resolve the Route53 delegation independently of router-local DNS cache and rebinding policy.

## References

- ADR: `docs/adr/0002-manage-truenas-with-opentofu-and-api-app-automation.md:1`
- ADR: `docs/adr/0004-truenas-api-key-via-null-resource.md:1`
- ADR: `docs/adr/0006-domain-first-homeserver-iac.md:1`
- Ownership matrix: `docs/architecture/homeserver-ownership.md:1`
- Secret rotation: `docs/runbooks/homeserver-secret-rotation.md:1`
- State migration runbook: `docs/runbooks/opentofu-state-migrations.md:1`
- AWS OpenTofu stacks: `infra/aws/README.md:1`
- TrueNAS app declarations: `infra/truenas/apps/README.md:1`
- Repo tool pins: `mise.toml:1`
- Task targets: `Taskfile.yml:1`
