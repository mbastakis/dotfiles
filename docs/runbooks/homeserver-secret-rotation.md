# Homeserver Secret Rotation

`infra/secrets/homeserver.bws.yaml` is the authoritative value-free inventory. It records every secret's owner, BWS ID, consumers, generation method, and this runbook. Never place a secret value in Git, command output, a plan file, or OpenTofu state.

## Common Procedure

1. Run `mise exec -- task infra:desired:validate` and identify every declared consumer.
2. Create the replacement in its owning provider or with a cryptographically secure generator. Keep the old credential active when the provider supports overlap.
3. Update the existing BWS secret value. If a new BWS object is required, update only its committed ID after creation.
4. Run the affected domain plan, apply only the intended consumer changes, then run a second plan.
5. Test the consumer before revoking the old credential. Record the rotation date in the operator change record, not in Git metadata.

## Inventory

| Alias / BWS ID | Owner and consumers | Generation | Rotation-specific action |
|---|---|---|---|
| `authentik_secret_key` / `acdabc87-03da-475c-b86a-b47500159a33` | `identity.authentik`; atlas Authentik/homeserver | CSPRNG | Update BWS and apply `atlas:homeserver`; expect existing sessions/tokens to become invalid. |
| `authentik_postgres_password` / `0a43c34d-fef2-4891-b5d2-b47500159b49` | `identity.authentik`; atlas Authentik/homeserver | Password CSPRNG | Change the database role and BWS value in one maintenance window, then converge Atlas and verify Authentik. |
| `authentik_bootstrap_admin_password` / `3969e1e0-42c8-4360-a3a9-b47500159c6f` | `identity.authentik`; atlas bootstrap | Password CSPRNG | Replace before a fresh bootstrap; active administrator passwords are runtime-owned after bootstrap. |
| `authentik_bootstrap_api_token` / `3ff2e9f2-04f7-48a4-bda8-b47500159dd8` | `identity.authentik`; Atlas and Authentik OpenTofu | Authentik admin API | Create a replacement token, update BWS, require a clean `identity:authentik:plan`, then revoke the old token. |
| `authentik_user_michail_initial_password` / `8e63b430-3048-4080-8e72-b47500159f71` | `identity.authentik`; Authentik OpenTofu | Password CSPRNG | Replace only before initial creation; afterward reset the runtime password in Authentik and preserve first-login semantics. |
| `authentik_user_chara_initial_password` / `b49709a8-4779-489c-bdd1-b4750015a095` | `identity.authentik`; Authentik OpenTofu | Password CSPRNG | Replace only before initial creation; afterward reset the runtime password in Authentik and preserve first-login semantics. |
| `opencode_oidc_client_secret` / `3ec743d4-2730-4722-9f8d-b48601267e32` | `identity.authentik`; Authentik and the Mac oauth2-proxy | CSPRNG | Update BWS, apply Authentik, run `chezmoi apply` on the OpenCode host, and verify a fresh OIDC login before ending the maintenance window. |
| `opencode_cookie_secret` / `ecaf6c2a-1044-4d47-a776-b48601267e58` | `opencode.remote_access`; Mac oauth2-proxy | 32 random bytes as unpadded base64url | Update BWS and run `chezmoi apply` on the OpenCode host; all existing OpenCode browser sessions are invalidated. |
| `filebrowser_quantum_admin_password` / `ab02a371-c172-4cf4-89dc-b4750015a1d2` | `truenas.catalog_apps`; FileBrowser | Password CSPRNG | Update BWS and apply the FileBrowser app if password authentication is enabled; it is currently only a required seed. |
| `filebrowser_quantum_oidc_client_secret` / `c34e3b41-5fe3-48b9-bbe7-b4750015a2c8` | `identity.authentik`; Authentik and FileBrowser | CSPRNG | Update BWS, apply Authentik and FileBrowser in one window, then test the OIDC login flow. |
| `filebrowser_quantum_jwt_token_secret` / `cd6d5252-6b59-4473-a6d8-b4750015a3ee` | `truenas.catalog_apps`; FileBrowser | CSPRNG | Update BWS and apply FileBrowser; expect existing FileBrowser sessions to be invalidated. |
| `audiobookshelf_root_password` / `2ce43f51-973f-48b9-b4f6-b485014feecc` | `truenas.audiobookshelf_config`; Audiobookshelf reconciler | Password CSPRNG | Change the local root password in Audiobookshelf and BWS together, then require a clean `truenas:audiobookshelf:plan`; this credential is also the OIDC break-glass path. |
| `audiobookshelf_oidc_client_secret` / `0303443c-e0d4-4ea2-8afe-b485014fef5c` | `identity.authentik`; Authentik and Audiobookshelf | CSPRNG | Update BWS, apply Authentik and Audiobookshelf in one window, then test web and mobile OIDC callbacks. |
| `backrest_admin_password` / `905858f5-fea9-4116-944c-b4750015a56f` | `truenas.catalog_apps`; Backrest and Homepage | Password CSPRNG | Update BWS, apply the Backrest app and Atlas Homepage, then verify UI and widget access. |
| `backrest_restic_repo_password` / `a2c252de-e08d-4f4a-9cd4-b4750015a681` | `truenas.backrest_policy`; Backrest | Password CSPRNG | Use restic's repository key-password change first, update BWS/app environment, and verify `snapshots` plus `check` before removing the old key. |
| `truenas_api_key` / `35e303f1-b598-43e8-947d-b483008d7689` | `truenas.tofu`; Homepage | TrueNAS API-key publisher | Create a replacement in TrueNAS, update BWS, converge Homepage, verify the widget, then delete the old TrueNAS key. |
| `tailscale_atlas_auth_key` / `3c422c6c-af92-48cd-bab1-b47500244ab0` | `network.tailscale`; Atlas enrollment | Tailscale tagged preauth key | Create and store a new one-off key only when Atlas must re-enroll; revoke unused/old keys after node identity is healthy. |
| `tailscale_truenas_auth_key` / `69f4fe6f-c2aa-454e-ab2d-b47500393c83` | `network.tailscale`; TrueNAS enrollment | Tailscale tagged preauth key | Create and store a new one-off key only when TrueNAS must re-enroll; revoke unused/old keys after node identity is healthy. |
| `tailscale_api_key` / `51d14a5b-9e3e-4199-8f06-b48200276b9f` | `network.tailscale`; policy provider and Homepage | Tailscale admin API | Create a replacement, update BWS, run `network:policy:plan`, converge Homepage, then revoke the old API key. |
| `taskwarrior_sync_encryption_secret` / `ad735d27-1aee-4f1d-a319-b48200ffed7b` | `atlas.taskchampion`; all Taskwarrior/Taskboard replicas | CSPRNG | Back up sync data, update every replica in one window, and re-enroll or rebuild sync state as required; mixed keys cannot synchronize. |
| `immich_postgres_password` / `01da3b5d-82f7-4c7d-b87e-b4830164df94` | `atlas.immich`; dedicated Atlas Immich deployment | Password CSPRNG | Change the Immich database role and BWS value in one maintenance window, apply `atlas:immich`, and verify database-backed operations. |
| `immich_postgres_password` / `01da3b5d-82f7-4c7d-b87e-b4830164df94` | `atlas.immich`; Immich server/database | Password CSPRNG | Change the `immich` database role and BWS value in one maintenance window, apply `atlas:immich`, then verify the server ping and database backup job. |
| `immich_oidc_client_secret` / `d962b5a8-163a-4d23-abb7-b48401882849` | `identity.authentik`; Authentik and Immich | CSPRNG | Update BWS, apply Authentik and Immich in one window, then test web login, account linking, and the mobile callback. |
| `traefik_route53_access_key_id` / `20f028dc-1f79-416d-9ca8-b4750029cfe6` | `aws.foundation`; Traefik | AWS IAM stack output | Rotate together with its secret key, publish both BWS values, converge Atlas, verify DNS-01, then retire the old IAM key. |
| `traefik_route53_secret_access_key` / `c64153e3-51d7-481b-a1ce-b4750029d057` | `aws.foundation`; Traefik | AWS IAM stack output | Rotate as the Traefik Route53 credential pair; never rotate only one half. |
| `backrest_aws_access_key_id` / `b57d3fbe-0908-4c1a-bb72-b4750029d0eb` | `aws.foundation`; Backrest/restic | AWS IAM stack output | Rotate together with its secret key, publish both BWS values, converge Backrest, run a backup/check, then retire the old IAM key. |
| `backrest_aws_secret_access_key` / `3cf5a20c-8139-48da-b2b2-b4750029d175` | `aws.foundation`; Backrest/restic | AWS IAM stack output | Rotate as the Backrest S3 credential pair; never rotate only one half. |

The retired Taskboard Basic Auth secret is no longer part of desired state. Delete its BWS object separately only after confirming no external consumer remains.
