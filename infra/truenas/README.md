# TrueNAS Automation

Source-only automation for the `truenas` homeserver. TrueNAS is storage-first and runs only minimal storage-adjacent apps.

## Layout

| Path | Purpose |
|---|---|
| `bootstrap-ssh-key.sh` | One-time helper that adds the managed `id_ed25519.pub` key to the TrueNAS user before OpenTofu can connect |
| `apps/` | Repository-owned catalog app declarations applied through the TrueNAS API wrapper |

## SSH Bootstrap

The TrueNAS OpenTofu provider needs key-based SSH before it can manage anything, so the first key installation is intentionally outside the Terraform state.

Run the bootstrap from this repo. It uses the current password-capable SSH login, sends an `account user update` command to the TrueNAS CLI shell, creates the user home under `/mnt/pool_4tb`, adds `private_dot_ssh/id_ed25519.pub` to the TrueNAS `mbastakis` user, sets the login shell to `/usr/bin/bash`, enables passwordless sudo for the same admin user, and then tests `~/.ssh/id_ed25519` plus `sudo -n true`:

```bash
mise exec -- task truenas:bootstrap-ssh-key
```

TrueNAS requires a dataset-backed home path before it accepts `sshpubkey` on user update. With the default options, `home_create=true` creates `/mnt/pool_4tb/mbastakis`.

The OpenTofu tasks read `~/.ssh/id_ed25519` at runtime and export the provider's private-key variable automatically. Set `TRUENAS_SSH_PRIVATE_KEY_PATH` before running `task tf:truenas:plan` or `task tf:truenas:apply` only if you need a different key file.

After it succeeds, both of these should use the managed SSH key:

```bash
ssh truenas true
ssh mbastakis@192.168.1.74 true
```

## Boundaries

- Use stable TrueNAS catalog apps where they fit.
- Use custom Compose only when no suitable catalog app exists.
- Pin catalog app versions in declarations.
- Keep secrets out of app YAML and inject them from Bitwarden or environment variables at apply time.
- Do not create SMB or NFS shares until a real client workflow requires them.
- Keep first-access bootstrap helpers out of the persistent OpenTofu state.
