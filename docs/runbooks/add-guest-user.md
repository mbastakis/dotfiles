# Add a Guest User

A guest user gets FileBrowser-only access to an explicit guest folder
through Tailscale, Authentik, and `files.mbastakis.com`. They do **not**
get Syncthing, Obsidian, Backrest, TrueNAS admin, or any infra-surface
access.

## Prerequisites

- Operator access to this repo, BWS, Tailscale admin, and the Authentik
  admin UI.
- The guest's Tailscale account email.

## Steps

### 1. Create the guest file area

If this is the first guest, create the guests dataset in
`infra/truenas/tofu/datasets.tf`:

```hcl
resource "truenas_dataset" "data_files_guests" {
  pool          = data.truenas_pool.pool_4tb.name
  path          = "homeserver/data/files/guests"
  force_destroy = false

  depends_on = [truenas_dataset.data_files]

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

### 2. Add to Tailscale

1. Ask the guest to install Tailscale and sign in with their own account.
2. Approve their device in the Tailscale admin console.
3. Add their email to a new `group:homeserver-guests` in
   `infra/network/tailscale/policy.hujson`.
4. Add an ACL rule allowing guests to reach only `tag:homeserver-entry:443`:

   ```hujson
   "group:homeserver-guests": [
     "guest@example.com",
   ],
   ```

   ```hujson
   {
     "action": "accept",
     "src": ["group:homeserver-guests"],
     "dst": ["tag:homeserver-entry:443"],
   },
   ```

5. Add a test case asserting the guest cannot reach infra surfaces.
6. Validate and apply:

   ```bash
   mise exec -- task network:policy:validate
   mise exec -- task network:policy:apply
   ```

### 3. Create Authentik user + guest group

1. Create a BWS secret for the initial password (same pattern as
   [Add a Household User](add-household-user.md) step 3.1-3.2).

2. Add a `guests` group mapping in
   `infra/identity/authentik/tofu/user_groups.tf` — the `homeserver-files-guests`
   group already exists in the local map.

3. Add a guest-specific FileBrowser access policy or add the guests group
   to the FileBrowser Quantum OIDC `userGroups` if the app should accept
   them. For strict isolation, prefer a separate FileBrowser source scoped
   to `/guests/` with its own access policy.

4. Add the user to `local.homeserver_users` with group `["guests"]`.

5. Add the variable and BWS wiring (same pattern as household user).

6. Plan and apply:

   ```bash
   mise exec -- task identity:authentik:plan
   mise exec -- task identity:authentik:apply
   ```

### 4. Mount the guest folder in FileBrowser Quantum

If the guests dataset is new, add it as an additional storage mount in
`infra/truenas/apps/declarations/filebrowser-quantum.yaml` and add a
corresponding source in the config template at
`infra/truenas/apps/templates/filebrowser-quantum/config.yaml`.

Apply the app declaration:

```bash
mise exec -- task truenas:apps:apply -- filebrowser-quantum
```

### 5. Verify

- [ ] Guest can connect to Tailscale.
- [ ] Guest can reach `https://files.mbastakis.com` and log in through
      Authentik.
- [ ] Guest can see only the guest folder, not household or personal
      areas.
- [ ] Guest cannot reach TrueNAS admin, SSH, Syncthing, Backrest, or any
      infra surface over Tailscale.
- [ ] Guest has no Syncthing or Obsidian access.
