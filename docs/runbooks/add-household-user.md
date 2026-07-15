# Add a Household User

A household user gets Tailscale device access, an Authentik identity, and
FileBrowser Quantum access to the shared household area plus a personal
folder. They do **not** get Syncthing/Obsidian, Backrest, or infra-surface
access.

## Prerequisites

- Operator access to this repo, BWS, Tailscale admin, and the Authentik
  admin UI (`https://auth.mbastakis.com/if/admin/`).
- The new user's Tailscale account email.
- The new user's preferred display name.

## Steps

### 1. Add to Tailscale

1. Ask the user to install Tailscale and sign in with their own Tailscale
   account (not a shared account).
2. Approve their device in the Tailscale admin console.
3. Add their Tailscale account email to `group:homeserver-household` in
   `infra/network/tailscale/policy.hujson`.
4. Validate and apply the policy:

   ```bash
   mise exec -- task network:policy:validate
   mise exec -- task network:policy:apply
   ```

### 2. Create a TrueNAS personal dataset

Add a `truenas_dataset` resource for the user's personal folder in
`infra/truenas/tofu/datasets.tf`:

```hcl
resource "truenas_dataset" "data_files_users_NEWUSER" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/files/users/newuser"
  force_destroy = false

  depends_on = [truenas_dataset.data_files_users]

  lifecycle {
    prevent_destroy = true
  }
}
```

Apply:

```bash
mise exec -- task truenas:tofu:plan
mise exec -- task truenas:tofu:apply
```

### 3. Create Authentik user + group membership

1. Generate a unique initial password and store it in BWS:

   ```bash
   bws secret create \
     --project-id b6b2ed62-40f0-446b-b39f-b475001583b9 \
     "homeserver/authentik/users/newuser-initial-password" \
     "$(openssl rand -base64 24)"
   ```

2. Add the BWS secret ID to `infra/secrets/homeserver.bws.yaml` under
   `secrets:`:

   ```yaml
   authentik_user_newuser_initial_password:
     key: homeserver/authentik/users/newuser-initial-password
     id: "<BWS secret ID>"
     owner: identity.authentik
     lifecycle: generated
     consumers: [terraform-authentik]
     generation_method: Generate with a password CSPRNG before creating the user.
     rotation_runbook: docs/runbooks/homeserver-secret-rotation.md
     purpose: Unique onboarding password for the Authentik newuser user.
   ```

3. Add the alias to the `terraform-authentik` target:

   ```yaml
   targets:
     terraform-authentik:
       # ...existing entries...
       TF_VAR_newuser_initial_password:
         secret_ref:
           alias: authentik_user_newuser_initial_password
   ```

4. Add a `variable` block in `infra/identity/authentik/tofu/variables.tf`:

   ```hcl
   variable "newuser_initial_password" {
     description = "Unique onboarding password for the Authentik newuser user."
     type        = string
     sensitive   = true
   }
   ```

5. Add the user to `local.homeserver_users` in
   `infra/identity/authentik/tofu/users.tf`:

   ```hcl
   newuser = {
     username = "newuser"
     name     = "New User"
     groups   = ["household"]
   }
   ```

6. Add the initial password mapping in
   `local.homeserver_user_initial_passwords`:

   ```hcl
   newuser = var.newuser_initial_password
   ```

7. Plan and apply:

   ```bash
   mise exec -- task identity:authentik:plan
   mise exec -- task identity:authentik:apply
   ```

The new user will be created with `reset_password = true` and will be
forced to change their password on first login through the homeserver
authentication flow.

### 4. Verify

- [ ] User can connect to Tailscale from their device.
- [ ] User can reach `https://files.mbastakis.com` over Tailscale.
- [ ] User is redirected to Authentik, logs in with the initial password,
      and is forced to set a new password.
- [ ] User can see the `Household` source and their own personal folder
      under the `Personal` source.
- [ ] User cannot reach TrueNAS admin, SSH, Syncthing, Backrest, or any
      other infra surface over Tailscale.
