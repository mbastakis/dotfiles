# Pi-hole DNS Filtering

Pi-hole runs on atlas and listens for DNS only on `192.168.1.19:53`. Clients do
not query it directly. OpenWrt remains the LAN and guest resolver, preserving
`*.home` names and keeping guest-to-trusted isolation intact.

OpenWrt uses strict ordered upstreams:

1. Pi-hole at `192.168.1.19`
2. Cloudflare at `1.1.1.1`
3. Cloudflare at `1.0.0.1`

The public resolvers are outage fallbacks. An OpenWrt procd watchdog probes
Pi-hole every five seconds with a two-second deadline. It removes Pi-hole from
dnsmasq's upstream list after three consecutive failures and restores it after
two consecutive successes. This hysteresis avoids resolver churn during a
single slow query. Queries during the detection window can still fail, but DNS
then continues without filtering. Pi-hole forwards directly to Cloudflare
rather than back to OpenWrt, preventing a resolver loop.

Pi-hole validates DNSSEC, retains 90 days of query history, and permits 10,000
queries per 60 seconds from the apparent client. The higher-than-default limit
is deliberate: because OpenWrt forwards client queries, the whole network can
share one Pi-hole client identity. The container drops `NET_RAW`, disallows new
privileges, disables its unused DHCP and NTP services, and persists writable
state under `/opt/homeserver/pihole/etc-pihole`.

The administration UI is available at
`https://pihole.mbastakis.com/admin/` over Tailscale and is protected by
Authentik forward-auth. Pi-hole's internal web password is deliberately disabled
because its web port is not published on the host.

## Deploy

```bash
mise exec -- task aws:dns:apply -- -auto-approve
mise exec -- task identity:authentik:apply -- -auto-approve
mise exec -- task atlas:pihole:apply
mise exec -- task network:openwrt:dns:apply
mise exec -- task atlas:pihole:verify
```

Apply OpenWrt last. This ensures Pi-hole is healthy before the router starts
using it as the primary upstream.

## Verify

```bash
ssh atlas sudo docker compose --project-directory /opt/homeserver ps pihole
dig @192.168.1.19 pi.hole
dig +tcp @192.168.1.19 pi.hole
dig @192.168.1.1 pi.hole
```

Confirm an ordinary client still uses `192.168.1.1` as its DNS server. To test
fallback, stop Pi-hole briefly, resolve a public hostname through OpenWrt, and
start Pi-hole again:

```bash
ssh atlas sudo docker stop homeserver-pihole-1
dig @192.168.1.1 example.com
ssh atlas sudo docker start homeserver-pihole-1
```

The fallback test intentionally bypasses filtering while Pi-hole is stopped.

## Upgrade and backup

Keep the image pinned to an explicit Pi-hole release and upgrade manually after
reading its release notes; do not use an unattended container updater for DNS.
Before an upgrade or significant UI-managed list/group change, export a
Teleporter archive from **Settings > Teleporter** and store it outside atlas.
The Compose and router configuration are declarative, but custom Pi-hole lists,
groups, and query history live only in `/etc/pihole`; they are not currently in
the TrueNAS/restic backup scope.

Pi-hole's native password is currently empty because only Traefik can reach the
web port and Authentik protects that route. A BWS-managed native/application
password would add defense in depth and authenticated API access, but requires a
deliberate secret lifecycle and recovery path before enabling it.
