# Homeserver Secrets

Logical Bitwarden Secrets Manager aliases for homeserver automation.

- `homeserver.bws.yaml` commits schema version 1, bounded ownership, BWS project/secret IDs, owner/lifecycle/consumer/generation/rotation metadata, and typed target `secret_ref` aliases, never secret values.
- `homeserver-secrets` is a thin shim over the typed Python BWS client. It resolves values at runtime for child processes or restricted env files with a bounded subprocess timeout.
- Use `bin/chezmoi-bws` or `BWS_ACCESS_TOKEN` for BWS authentication.

## Commands

```bash
infra/secrets/homeserver-secrets list-targets
infra/secrets/homeserver-secrets list-secrets
infra/secrets/homeserver-secrets render-env truenas-filebrowser-quantum --output /tmp/filebrowser.env
infra/secrets/homeserver-secrets exec atlas-tailscale -- bash -lc 'cd infra/atlas/ansible && ansible-playbook playbooks/atlas-tailscale.yml'
infra/secrets/homeserver-secrets exec terraform-authentik -- tofu plan
```

`list-secrets` prints aliases and IDs only. Secret values are not printed by default.
The Python helper preserves the existing command and output surface; operational
failures use exit code `4`, and rendered files are atomically installed with mode
`0600`.

Validate the metadata and all cross-file aliases without contacting BWS:

```bash
mise exec -- task infra:desired:validate
```

The generated contract is `infra/schemas/secret-metadata.schema.json`.

## External secrets

Generated secrets created for this implementation already have BWS IDs in `homeserver.bws.yaml`.
Provider-created secrets are recorded with an empty `id` until the real value is created in that provider and stored in BWS. `homeserver-secrets` can resolve those aliases by BWS key lookup inside the homeserver project; commit the resulting BWS secret ID afterward for deterministic direct lookup.

Stored provider-created secrets so far:

- atlas one-off Tailscale preauth key
- TrueNAS one-off Tailscale preauth key
- Traefik Route53 ACME AWS access key ID and secret access key from `infra/aws/stacks/foundation`
- Backrest/restic AWS access key ID and secret access key from `infra/aws/stacks/foundation`
- Homepage TrueNAS widget API key from `infra/truenas/tofu`

Generated runtime secrets so far:

- TaskChampion sync encryption secret (`taskwarrior_sync_encryption_secret`)
- Audiobookshelf root bootstrap/break-glass password (`audiobookshelf_root_password`)
- Audiobookshelf native OIDC client secret (`audiobookshelf_oidc_client_secret`)
- OpenCode OIDC client and oauth2-proxy cookie secrets (`opencode_oidc_client_secret`, `opencode_cookie_secret`)
- ntfy subscriber password/hash and OpenCode publisher hash/token (`ntfy_*`)

Rotation procedures and the value-free inventory are documented in
`docs/runbooks/homeserver-secret-rotation.md`. The retired Taskboard Basic Auth
secret is intentionally absent from desired state.
