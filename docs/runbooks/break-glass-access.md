# Break-Glass Access: Authentik Application Outage

When Authentik is down, FileBrowser Quantum loses its only login method.
Immich remains accessible through its retained local administrator password.
This runbook describes the Michail-only break-glass procedures.

## When to use

- Authentik service is down on `atlas`.
- Traefik is up and can reach TrueNAS, but OIDC login fails.
- You need file access and cannot wait for Authentik recovery.

## Steady-state reminder

In steady state:

- FileBrowser Quantum password auth is **disabled**.
- OIDC through Authentik is the only login method.
- The `FILEBROWSER_ADMIN_PASSWORD` BWS secret exists as a catalog
  requirement but is inactive.
- Immich prefers Authentik OIDC but keeps local password login enabled.

## Immich break-glass

Open `https://photos.mbastakis.com/auth/login?autoLaunch=0` and sign in with
the existing `mbastakis@gmail.com` local administrator password. No config
change or redeployment is required. Repair Authentik before onboarding or
linking additional users.

## FileBrowser break-glass

### 1. Enable password auth in FileBrowser Quantum config

1. Edit `infra/truenas/apps/templates/filebrowser-quantum/config.yaml`:

   ```yaml
   auth:
     methods:
       password:
         enabled: true      # was false
         signup: false
         enforcedOtp: false
   ```

2. Redeploy the FileBrowser Quantum app with the BWS-sourced admin
   password:

   ```bash
   mise exec -- task truenas:apps:apply -- filebrowser-quantum
   ```

3. Log in to FileBrowser Quantum at
   `http://100.122.166.74:30334` (truenas Tailscale IP, admin-only) or
   through `https://files.mbastakis.com` with username `admin` and the
   BWS-sourced `filebrowser_quantum_admin_password`.

### 2. Use file access as needed

Password auth is app-global — it is active on both the direct port and
through Traefik. Household users who know the admin password could log
in this way, so keep the break-glass window short.

### 3. Return to OIDC-only

1. Edit the config template back:

   ```yaml
   auth:
     methods:
       password:
         enabled: false
   ```

2. Redeploy:

   ```bash
   mise exec -- task truenas:apps:apply -- filebrowser-quantum
   ```

3. Verify OIDC login works through `https://files.mbastakis.com`.
4. Rotate the admin password in BWS:
   `homeserver/truenas/filebrowser-quantum/admin-password`.

## Alternative: repair Authentik

If Authentik can be recovered, that is always preferable to break-glass.

1. SSH to atlas: `ssh atlas`.
2. Check the Docker Compose stack:

   ```bash
   cd /opt/homeserver
   docker compose ps
   docker compose logs authentik-server --tail=50
   docker compose logs authentik-worker --tail=50
   ```

3. Restart the stack if needed:

   ```bash
   docker compose restart authentik-server authentik-worker
   ```

4. If Authentik Postgres is the problem:

   ```bash
   docker compose logs postgres --tail=50
   docker compose restart postgres
   ```

5. Verify `https://auth.mbastakis.com` is reachable over Tailscale.

## Security notes

- Break-glass is Michail-only. Do not share the admin password.
- The admin account can see all mounted file areas (household, personal,
  guests if active).
- Document each break-glass use: date, reason, duration, and password
  rotation confirmation.
- The `FILEBROWSER_ADMIN_PASSWORD` must be rotated after any break-glass
  use, even if the password was not exposed to a non-admin user.
