# Router Hardening: Disable UPnP

The Speedport Plus 2 router supports UPnP, which allows LAN devices to
automatically request port forwards. This is a security risk because any
compromised LAN device can open services to the public internet without
operator knowledge.

## Rationale

Phase 1 of the homeserver architecture does not require any public
internet exposure. All remote access goes through Tailscale. UPnP
should be disabled after Tailscale/private access is confirmed working.

Reference: `specs/homeserver-target-architecture.md` §2.

## Prerequisites

- Tailscale is working from outside the house (tested with a mobile
  hotspot or cellular connection).
- `files.mbastakis.com` and `auth.mbastakis.com` are reachable over
  Tailscale.
- No LAN device depends on UPnP for a legitimate service (check before
  disabling).

## Check for UPnP dependencies

Before disabling, check what port forwards UPnP has created:

1. Log in to the Speedport Plus 2 admin UI (typically
   `http://192.168.1.1`).
2. Navigate to the port forwarding / UPnP section.
3. Note any existing UPnP-created port mappings.
4. Identify which devices requested them and whether they are still
   needed.

If a mapping is needed, convert it to a manual port mapping before
disabling UPnP. If no mapping is needed, proceed.

## Disable UPnP

1. In the Speedport Plus 2 admin UI, find the UPnP setting.
2. Disable UPnP (and UPnP NAT-PMP if separately listed).
3. Save and apply.

## Verify

- [ ] No new UPnP port mappings appear after disabling.
- [ ] Tailscale still works from outside the house.
- [ ] `files.mbastakis.com` is reachable over Tailscale from a remote
      device.
- [ ] `auth.mbastakis.com` is reachable over Tailscale from a remote
      device.
- [ ] Manual port mappings remain empty unless a future public-ingress
      decision explicitly introduces one.
- [ ] No household device or service broke after disabling UPnP.

## Notes

- This is a manual UI-only step on the Speedport router. The router does
  not have a code-managed API.
- If the router is replaced, document the UPnP state on the new device.
- A future public-ingress decision (e.g. running a public service) would
  require an explicit manual port mapping, not UPnP re-enablement.
