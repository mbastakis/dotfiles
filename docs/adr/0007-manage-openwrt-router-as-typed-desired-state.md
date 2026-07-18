# Manage OpenWrt From One Contract With Risk-Tiered Convergence

## Status

Accepted on 2026-07-17. Direct-wired bootstrap, production cutover, the
Ansible-first ownership migration, rpcd rollback proof, and a settings-free
clean rebuild all passed. The post-rebuild apply and second convergence plan
reported zero changes. The seven-day observation window remains an operational
gate for retiring the Speedport fallback, not for accepting this decision.

## Context

The production Cudy WR3000E hardware version 1.0 preserves the flat
`192.168.1.0/24` trusted LAN, atlas at `.19`, TrueNAS at `.74`, and COSMOTE PPPoE
over VLAN 835. It also introduces Wi-Fi-only guest isolation, native IPv6, CAKE
SQM, and LAN-only administration without public ingress or router-hosted
Tailscale.

Raw UCI files mix stable intent with board-generated and runtime state. LuCI and
unchecked shell scripts do not provide a reviewable ownership boundary, safe
secret handling, or dependable connectivity protection.

The first implementation applied every capability through a custom Python
transaction controller. That provided strong cutover safety but duplicated
policy across models, UCI mappings, health projections, tests, and documentation.
The official `community.openwrt` collection now provides Pythonless idempotent
UCI modules for routine configuration, but not rpcd timed apply, encrypted
transaction evidence, or functional rollback gates.

## Decision

OpenWrt is a bounded domain at `infra/network/openwrt/`, owned as
`network.openwrt` and operated only through `network:openwrt:*` Task commands.
`router.yaml` is the single human-edited policy contract. Ansible and the
protected safety extension consume it directly; executor variables and prose do
not become competing policy stores.

Pinned `community.openwrt` modules own routine system identity, trusted
DHCP/DNS and reservations, main Wi-Fi, SQM, and flow-offload convergence.
Managed sections use stable names and bounded pruning. Secret-bearing tasks
resolve BWS aliases immediately before execution and run with `no_log` and diff
disabled.

The control-side Python extension owns only reachability-critical
`bootstrap-sanitize`, `base` LAN/management, `wan`, complete isolated `guest`,
and `ipv6` transactions. These use encrypted pre-change evidence, rpcd timed
rollback, focused health gates, and same-session confirmation. The controller
rejects routine Ansible stages. Routine applies trust idempotent module success
and create no transaction bundles.

DNS rebinding protection remains enabled globally. Only the exact Route53
private-service FQDNs that intentionally resolve into Tailscale are exempted;
there is no zone-wide or wildcard exception. Declared reservations publish
static local forward/reverse DNS records independently of lease timing.

Firmware uses the official Image Builder in a digest-pinned local container.
The stock Cudy flash layout is retained. The overlay contains only the managed
public SSH key and an audited non-secret stdin-to-libubus helper; credentials are
resolved from BWS after boot and never enter Git, firmware, argv, or diagnostics.
Every artifact is checksum-verified and archived with its resolved manifest.

The firmware is a minimal management image containing pinned packages, the
administrator public key, and the non-secret protected-apply helper. It contains
no site policy or secrets. Direct-wired bootstrap establishes trust and the
protected base before Ansible completes routine configuration.

Normal point upgrades preserve configuration, then verify identity/packages and
reconcile desired state. Clean flash is reserved for initial installation,
recovery, or an explicit rebuild drill.

## Safety Boundary

- Never use a WR3000E v2, another Cudy model, an `ubootmod` image, force-flash,
  `mtd write`, `mtd erase`, `ubiformat`, or `kmod-mtd-rw`.
- Bootstrap, apply, revert, upgrade, host-key pinning, password rotation, and MTD
  backup require a direct wired path. Strict SSH host-key checking remains on.
- Ansible and the protected extension must never mutate the same UCI field or
  managed section. Ownership moves only as a complete capability slice.
- rpcd rollback is process-lifetime connectivity protection, not firmware or
  power-failure rollback. Reboot, power loss, or rpcd/ubus restart can destroy
  its timer and snapshots after `/etc/config` was committed.
- Never reboot, restart rpcd, retry an ambiguous apply, or issue a second apply
  while protected rollback is pending. Validate externally, confirm, explicitly
  roll back, or wait for timeout.
- The configured Speedport and physical cabling rollback remain the protection
  for core WAN/LAN failure. TFTP stock recovery and UART RAM boot protect the
  device recovery path.

## Consequences

- The trusted wired LAN remains flat because the TL-SG108 is unmanaged. Guest
  segmentation is Wi-Fi-only and requires both AP and bridge-port isolation.
- SSH is key-only and trusted-LAN-bound; LuCI is HTTPS-only, trusted-LAN-only,
  and break-glass. UI drift must be codified or reverted immediately.
- Runtime leases, WAN addresses, delegated prefixes, counters, logs, host keys,
  TLS certificates, calibration data, and device-specific boot state remain
  runtime-owned.
- `network:openwrt:plan` combines a protected semantic plan with Ansible
  check/diff mode; `network:openwrt:apply` runs one Ansible-orchestrated lifecycle.
- IPv4-only operation is a safe intermediate state, not final acceptance. Guest
  IPv4/IPv6 isolation, distinct delegated `/64`s, and SQM must also pass.

## Rejected Alternatives

- Official image plus post-boot package installation: WAN/package availability
  would be required before the router has its complete management surface.
- GitHub Actions or atlas as firmware builder: expands secret/trust scope and
  makes a local recovery artifact depend on another service.
- Full raw-UCI replacement: would overwrite board and runtime-owned state and
  make staged ownership unsafe.
- Pure Ansible convergence: cannot provide the accepted rpcd timed rollback and
  encrypted evidence for reachability-critical changes.
- A custom Python controller for every capability: duplicates standard
  configuration-management behavior and makes routine changes harder to review.
- LuCI as a second owner: creates unreviewed drift and bypasses protected apply.
- `ubootmod`: rewrites boot components and NAND layout without benefit here.
- Router Tailscale, UPnP, NAT-PMP, DMZ, or public forwards: conflict with the
  device-level Tailscale and no-public-ingress architecture.

## References

- [OpenWrt cutover](../runbooks/openwrt-router-cutover.md)
- [OpenWrt recovery](../runbooks/openwrt-router-recovery.md)
- [Homeserver ownership](../architecture/homeserver-ownership.md)
