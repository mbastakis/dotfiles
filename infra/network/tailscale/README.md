# Homeserver Tailscale Policy

Source-controlled tailnet policy used by the homeserver rollout.

## Files

| Path | Purpose |
|---|---|
| `policy.hujson` | Tailnet policy snapshot with homeserver tag ownership |
| `manage-policy` | Small API wrapper for remote validation without printing the API token |
| `tofu/` | Official-provider root for the imported whole-tailnet policy |

## Current scope

The policy implements the default-deny ACL model from `specs/homeserver-target-architecture.md` §6.

### Tag ownership

Both tags are owned by `autogroup:admin` so admin-created auth keys can enroll tagged homeserver nodes:

- `tag:homeserver-entry` — atlas
- `tag:homeserver-storage` — truenas

### Groups

| Group | Members | Purpose |
|---|---|---|
| `group:homeserver-admins` | Michail | Infra-surface access to atlas and truenas |
| `group:homeserver-household` | Michail + Chara | Web-app-only access through atlas, including Files and Immich |
| `group:obsidian-sync` | Michail | Syncthing sync port on truenas |

### Access classes

| Rule | Src | Dst | Ports |
|---|---|---|---|
| General tailnet | `autogroup:member` | `autogroup:member:*` | `*` (excludes tagged nodes) |
| Admin — atlas | `group:homeserver-admins` | `tag:homeserver-entry` | `22,443` |
| Admin — truenas | `group:homeserver-admins` | `tag:homeserver-storage` | `22,443,8384,30334` |
| Web ingress | `tag:homeserver-entry` | `tag:homeserver-storage` | `30329,30334` (Traefik → Backrest/FileBrowser) |
| OpenCode ingress | `tag:homeserver-entry` | `opencode-host` | `443` (Traefik → Tailscale Serve) |
| Household web | `group:homeserver-household` | `tag:homeserver-entry` | `443` |
| Obsidian sync | `group:obsidian-sync` | `tag:homeserver-storage` | `22000` |

Non-admin household users are denied access to all infra surfaces by default (no accept rule covers `tag:homeserver-storage` for them). The `tests` section asserts this invariant.

`tasks.mbastakis.com` and `push.mbastakis.com` share Traefik HTTPS on atlas with the other private web applications. Tailscale ACLs are IP/port based, so the current policy makes them tailnet-private but not hostname-isolated from household users who can reach atlas `:443`; TaskChampion's client-ID allowlist/client-side encryption and ntfy's native deny-by-default ACLs remain the service-specific controls. Strict Michail-only network isolation would require a separate ingress IP/port/tag or a Traefik source-IP allowlist for known Michail devices.

### Port map

| Port | Service | Node |
|---|---|---|
| `22` | SSH | atlas, truenas |
| `443` | Traefik HTTPS / TrueNAS admin UI / OpenCode Tailscale Serve | atlas / truenas / OpenCode Mac |
| `8384` | Syncthing admin UI | truenas |
| `22000` | Syncthing sync protocol | truenas |
| `30329` | Backrest backend for Authentik-protected Traefik route | truenas |
| `30334` | FileBrowser Quantum | truenas |

### Tailscale Funnel

Tailscale Funnel (`nodeAttrs` with `funnel`) is intentionally **not** enabled. Phase 1 has no public internet exposure; all homeserver services are private over Tailscale.

### OpenCode Serve

The canonical browser URL is `https://code.mbastakis.com`. Its Route53 record points to atlas, where Traefik terminates the public certificate and connects to the designated Mac's Tailscale IP on port `443`. The `opencode-host` alias and a narrow ACL permit that one tagged-node-to-personal-node path. Traefik preserves the friendly HTTP host while using the Mac's `*.ts.net` name as backend TLS SNI, so certificate verification remains enabled.

The Mac uses `tailscale serve --bg` to publish only its loopback oauth2-proxy frontend. The raw OpenCode server remains on `127.0.0.1:4096`; oauth2-proxy listens on `127.0.0.1:4180` and requires the Authentik `opencode-users` group before forwarding. The Serve configuration is machine runtime state converged by chezmoi, while the Atlas-to-Mac access rule is part of this whole-tailnet policy document.

The general `autogroup:member` rule still permits tailnet members to reach untagged personal devices directly. Authentik supplies the Michail-only application boundary for OpenCode. The Atlas rule does not make that broader or narrower because ACL grants are additive; strict pre-authentication network isolation would require changing the general rule or tagging the Mac and explicitly recreating its required access.

## Commands

The API key is stored in BWS as `tailscale_api_key` and injected through the `tailscale-policy` target in `homeserver.bws.yaml`:

```bash
# Validate (checks syntax + ACL tests against the Tailscale API)
mise exec -- task network:policy:validate

# Plan and apply through the official provider
mise exec -- task network:policy:plan
mise exec -- task network:policy:apply
```

The one-time import used `mise exec -- task network:policy:import`. Do not run
that command again while `tailscale_acl.homeserver` is present in the dedicated
`homeserver/tailscale/terraform.tfstate` state.

The released provider does not yet call the remote validation API during plan,
so plan and apply run the validator first. The direct troubleshooting command
is:

```bash
infra/secrets/homeserver-secrets exec tailscale-policy -- bash infra/network/tailscale/manage-policy validate
```

`TAILSCALE_API_KEY` is an operator credential, not a homeserver runtime secret.
Only its BWS secret ID is committed and provider authentication is environment
based, so the credential is not written to OpenTofu state. The non-secret whole
policy document is expected to be present in state.

## Notes

The atlas and TrueNAS one-off auth keys were created after this policy added homeserver tag ownership, then stored in BWS as `tailscale_atlas_auth_key` and `tailscale_truenas_auth_key`. Only BWS secret IDs are committed.
