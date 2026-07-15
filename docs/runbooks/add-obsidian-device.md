# Add an Obsidian Device

A new Obsidian sync device joins the Syncthing folder `obsidian-michail`
on the TrueNAS always-on peer. Only Michail sync devices are allowed in
phase 1 (Tailscale `group:obsidian-sync`).

## Prerequisites

- The new device has Tailscale installed and is signed in with
  `mbastakis@gmail.com`.
- The device is listed in `group:obsidian-sync` in the Tailscale policy.
- Syncthing is installed on the device (macOS: Brewfile; other platforms:
  official installer).

## Steps

### 1. Ensure Tailscale access

1. Confirm the device is approved in the Tailscale admin console.
2. If the device uses a different Tailscale account, add that account to
   `group:obsidian-sync` in `infra/network/tailscale/policy.hujson` and apply:

   ```bash
   mise exec -- task network:policy:validate
   mise exec -- task network:policy:apply
   ```

### 2. Install and start Syncthing

On macOS, Syncthing is already in the Brewfile. On other platforms,
install from the official source.

Start Syncthing and note the device ID from the Web UI
(`http://127.0.0.1:8384`):

```
Device ID: XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX
```

### 3. Register the device in code

Add the new device to `infra/sync/syncthing/config.yaml` under a new key:

```yaml
newdevice:
  device_id: "XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX-XXXXXXX"
  name: "new-device-name"
  addresses: ["dynamic"]
  api_url: "http://127.0.0.1:8384"
```

### 4. Add the device to the Syncthing folder

Add the device ID to the folder's `devices` list in `config.yaml` (if
the configure script supports per-folder device lists), or accept the
folder share invitation from the Syncthing UI after applying the config.

### 5. Apply Syncthing configuration

The existing peers (mac + truenas) need to know about the new device:

```bash
mise exec -- task sync:configure:all
```

Then on the new device, apply its own config:

```bash
infra/sync/syncthing/configure-syncthing --host newdevice
```

> If the configure script does not yet support the new host, accept the
> device and folder share requests manually through the Syncthing Web UI
> on the new device. The folder ID is `obsidian-michail`.

### 6. Point Obsidian at the synced folder

Set the local Syncthing folder path to the Obsidian vault location on
the new device. The folder ID must be `obsidian-michail`.

For iPhone, use Mobius Sync Pro:

1. Install Mobius Sync Pro from the App Store.
2. Connect it to the Tailscale network.
3. Share the `obsidian-michail` folder from an existing Syncthing peer.
4. In Mobius, accept the folder and set it to an Obsidian-accessible
   location.
5. Open Obsidian and point it at that folder.

### 7. Configure `.stignore`

Copy `infra/sync/syncthing/stignore` to the new device's Syncthing folder
root. It excludes `.obsidian/` and `.git/` from sync.

### 8. Verify

- [ ] New device appears in the Syncthing Web UI on truenas and mac.
- [ ] Folder `obsidian-michail` shows as connected and synced on all
      peers.
- [ ] A test edit on the new device propagates to truenas and mac.
- [ ] A test edit on truenas propagates to the new device.
- [ ] `.obsidian/` is not synced (check Syncthing ignores).
- [ ] Remote sync works over Tailscale (disconnect from LAN and test).
