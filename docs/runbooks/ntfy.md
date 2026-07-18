# ntfy Notifications

ntfy is the central tailnet-private notification service at `https://push.mbastakis.com`. Atlas runs the pinned container behind Traefik; native ntfy authentication protects both publishing and subscriptions. Interactive Authentik middleware is intentionally absent because an iOS notification extension cannot complete OIDC while the app is suspended.

## Delivery Path

```text
OpenCode and future producers
  -> push.mbastakis.com on Atlas Traefik
  -> ntfy write-only topic ACL
  -> hashed poll request through ntfy.sh
  -> APNs wakes the ntfy iOS app
  -> iPhone fetches message content directly from Atlas
```

The upstream relay receives the hashed topic URL and message ID, not the notification title or body. The phone must still be connected to Tailscale and able to resolve and reach `push.mbastakis.com` after APNs wakes it.

## iPhone Setup

1. Apply DNS, the OpenWrt rebind allowlist, and the Atlas homeserver stack.
2. Install the official ntfy app from the App Store.
3. Add `https://push.mbastakis.com` as the default server.
4. Use username `michail` and copy the BWS-backed password without printing it:

   ```bash
   infra/secrets/homeserver-secrets exec ntfy-client -- \
     sh -c 'printf %s "$NTFY_PASSWORD" | pbcopy'
   ```

5. Subscribe to the `opencode` topic.
6. Allow notifications and test with the phone locked, the OpenCode PWA closed, Wi-Fi disabled, and Tailscale connected.

## Deployment

```bash
mise exec -- task aws:dns:plan
mise exec -- task aws:dns:apply
mise exec -- task atlas:ntfy:plan
mise exec -- task atlas:ntfy:apply
chezmoi apply
```

The OpenWrt desired state also includes `push.mbastakis.com` in the exact DNS-rebind allowlist. Apply that routine change through the normal `network:openwrt:plan` and `network:openwrt:apply` gates before testing from LAN clients.

## Verification

```bash
curl --fail https://push.mbastakis.com/v1/health
ssh atlas sudo docker compose --project-directory /opt/homeserver/ntfy ps ntfy
```

After `chezmoi apply` restarts the OpenCode server, run a short OpenCode request and verify one completion notification. Error runs emit an error notification and suppress the following idle/completion notification.

## Operations

- `/opt/homeserver/ntfy/config/server.yml` is mode `0600` and contains BWS-rendered hashes and the OpenCode publisher token.
- `/opt/homeserver/ntfy/data/user.db` is regenerable from declarative BWS-backed desired state.
- `/opt/homeserver/ntfy/data/cache.db` is a temporary 12-hour missed-message cache, not a durable notification archive.
- Producers receive separate users and least-privilege topic ACLs; do not reuse the OpenCode token.
- Notification bodies must contain summaries and authenticated links, not credentials or sensitive logs.
- Critical infrastructure alerts need an independent off-home-server fallback because ntfy cannot report an Atlas, router, power, DNS, or tailnet outage that also makes ntfy unreachable.

Rotate credentials through [Homeserver Secret Rotation](homeserver-secret-rotation.md).
