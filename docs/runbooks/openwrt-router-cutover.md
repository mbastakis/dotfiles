# OpenWrt Router Cutover

> **Status: production accepted and clean-rebuilt 2026-07-17.** The Cudy is the
> active router. Keep the configured Speedport powered off and unchanged through
> the seven-day observation window. Observation started on 2026-07-17 and can
> close no earlier than 2026-07-24; retirement remains open until then.

Use this runbook only for a Cudy WR3000E **hardware 1.0**, board ID **R53**, using
the stock flash layout and the verified OpenWrt 25.12.5
`cudy_wr3000e-v1` artifact. Perform all bootstrap, flash, apply, and recovery work
over wired Ethernet with stable power.

## Absolute Stops

- Never use WR3000E v2, WR3000/WR3000S/H/P, any `ubootmod` artifact, force
  flashing, `sysupgrade -F`, `mtd write`, `mtd erase`, `ubiformat`, or
  `kmod-mtd-rw`.
- Never put credentials in Git, firmware, argv, screenshots, logs, fixtures, or
  plaintext backups. Browser exports go directly to a mode-0700 staging folder,
  are immediately age-encrypted and pipe-verified, then every plaintext/browser
  copy is removed.
- Never disable SSH host-key checking. Pin each intermediary or clean-image key
  only after physically confirming the directly connected router.
- Never reboot/restart rpcd, start a second apply, or retry an ambiguous apply
  while rollback is pending. Close LuCI and allow no other UCI writer.
- Stop on board/package/checksum mismatch, unexplained stale/delete/WAN exposure,
  required reservation conflict, or secret-bearing output.

## Gate 0: Production And Recovery Readiness

- Inventory and encrypt the Speedport export, all clients/reservations, Wi-Fi,
  WAN/IPv6/MAP-E, UPnP, NAT-PMP, forwards, DMZ, and remote administration state.
- Put the new PPPoE password in BWS and the Speedport; force a controlled
  Speedport reconnect and require successful CHAP, public IPv4, DNS, and normal
  service. Do not remove an untested Speedport from production.
- Require classic PPPoE service, not unresolved MAP-E, and no required public
  ingress.
- Confirm Cudy label `WR3000E 1.0`, board `R53`, and date code. Units dated
  `2543` or newer must not use an old intermediary, OpenWrt older than 24.10.5,
  or Cudy 2.3.x.
- Verify all OpenWrt, intermediary, and stock-recovery checksums. Prepare local
  artifacts, TFTP, static-IP/firewall instructions, stable power, wired Mac,
  cellular test phone, and two controllable Wi-Fi clients.
- Record wired throughput/latency/MTU baselines and select committed GR channels:
  1/6/11 at 20 MHz and 36/40/44/48 at 80 MHz.

Any failed item blocks physical work.

## Gate 1: Isolated Stock-To-OpenWrt Migration

Keep the Speedport serving production. Isolate Cudy from the ONT and TL-SG108;
wire the Mac directly to Cudy LAN and disable Mac Wi-Fi.

1. Encrypt and pipe-verify a Cudy stock settings export; remove plaintext copies.
2. Re-verify and flash `cudy_wr3000e-v1-sysupgrade_20251119.bin` from stock UI
   without retaining settings. Do not interrupt power.
3. Confirm WR3000E v1/R53, set the BWS root password, add the public key, and pin
   the physically verified intermediary host key separately.
4. Require this exact `/proc/mtd` map before proceeding:

| Device | Label | Bytes |
|---|---|---:|
| `mtd0` | `BL2` | 1,048,576 |
| `mtd1` | `u-boot-env` | 524,288 |
| `mtd2` | `Factory` | 2,097,152 |
| `mtd3` | `bdinfo` | 262,144 |
| `mtd4` | `FIP` | 2,097,152 |
| `mtd5` | `ubi` | 67,108,864 |

5. Read-only stream-encrypt all six MTD partitions, record size/hash, decrypt to
   a pipe, and verify each. Never restore `Factory` or `bdinfo` from another
   device.

   ```bash
   mise exec -- task network:openwrt:backup -- \
     --kind mtd --recovery-workflow
   ```
6. Prepare Cudy stock `recovery.bin` and TFTP before custom flash. Do not trigger
   recovery merely to test transfer.
7. Run `mise exec -- task network:openwrt:firmware:verify`, require
   the ignored `.local/openwrt/artifacts/25.12.5/homeserver/` bundle and its
   second private copy to have matching checksums, require `sysupgrade -T`
   success, then use the guarded clean-rebuild operation and wait without
   interrupting power:

   ```bash
   mise exec -- task network:openwrt:clean-rebuild -- \
     --image .local/openwrt/artifacts/25.12.5/homeserver/<verified-image> \
     --confirm CLEAN-REBUILD
   ```

   This direct-route-only task creates and pipe-verifies a current encrypted
   config backup, uploads with strict pinned-key SSH, verifies the remote hash,
   runs `sysupgrade -T`, and runs `sysupgrade -n`. It never uses force. An
   expected SSH disconnect is acceptable.
8. Require a clean OpenWrt 25.12.5 boot at `192.168.1.1`, Wi-Fi disabled, and no
   retained Cudy/intermediary settings.

Stop on any mismatch, failed backup verification, or failed return after flash.
Use the [recovery runbook](openwrt-router-recovery.md), not improvisation.

## Gate 2: Direct-Wired Offline Bootstrap

Keep ONT and production switch disconnected from Cudy.

If the clean-image trust gate rejects observed state, run the read-only,
secret-free `network:openwrt:bootstrap -- --inspect-clean-image-only` mode and
reconnect the production router before reviewing its redacted output. Do not
weaken a safety check from memory or continue to rollback/apply.

If a confirmed post-state remains only as an encrypted pending sanitize journal
after a controller read failure, do not rerun sanitize. Use the explicit
`--recover-pending-sanitize-only` mode only after reviewing the failure. It
requires exactly one matching integrity-verified journal, exact clean sanitized
state, stable repeated reads, matching board identity and health, and no router
lock before atomically accepting the journal. Failure diagnostics may include a
stage, transaction ID, operation, and bounded UCI paths, but never values, SIDs,
raw UCI changes, or request/response bodies.

1. Physically verify the clean-image host fingerprint and prepare its new
   lineage with
   `network:openwrt:bootstrap -- --prepare-clean-rebuild`. This is the only mode
   allowed to replace an existing pin. It refuses pending transactions,
   validates exact clean-image identity and defaults, and moves prior visible
   accepted/failed transaction directories into an encrypted hidden
   `.generation-pre-clean-<timestamp>/` archive. Ordinary
   `--pin-host-key-only` refuses a changed key.
2. Verify board, release, package manifest, forbidden-package absence, and
   listeners.
3. Run `network:openwrt:bootstrap -- --test-rollback-only` to prove rpcd timeout
   rollback with a harmless temporary hostname change. Never test it with LAN,
   firewall, or firmware changes.
4. Run `network:openwrt:bootstrap`. It performs protected
   `bootstrap-sanitize` and `base`, then Ansible converges routine system,
   trusted DHCP/DNS/reservations, and main Wi-Fi configuration.
5. Confirm only after wired SSH, `.1` LAN, DHCP/DNS/firewall/listeners, and
   removal of default untagged WAN/WAN6 pass. Final WAN and guest remain absent.
6. Set root password through stdin; verify LuCI HTTPS works on trusted LAN while
   Dropbear password authentication does not.
7. Stream-encrypt and verify the clean base config backup.

## Gate 3: Core Physical Cutover

Pause transfers and confirm atlas, TrueNAS, Internet, DNS, and Tailscale are
healthy. Keep the credential-tested Speedport powered off and immediately
available. Start early enough to roll back.

1. Disconnect the Speedport PPP session if supported, then power it off.
2. Move ONT Ethernet from Speedport WAN to Cudy WAN.
3. Move the TL-SG108 uplink from Speedport LAN to Cudy LAN.
4. Keep the controller wired on trusted LAN; power on Cudy and wait for boot.
5. Do not connect both routers to the ONT or attempt parallel PPPoE.
6. Run `network:openwrt:plan`, require that only the expected WAN capability is
   pending, then run `network:openwrt:apply`.
7. Confirm only after VLAN 835 PPPoE, public IPv4, peer DNS, MTU 1492,
   `pppoe-wan`, WAN firewall/no administration, and wired management pass.

Then require atlas `.19`, TrueNAS `.74`, NFS, Syncthing, applications, LAN SSH,
both Tailscale nodes, cellular Tailscale access, and no public router port. Any
failure in PPPoE, core LAN addresses, NFS, or remote Tailscale is a physical
rollback condition.

## Gate 4: Staged Convergence

`network:openwrt:apply` orchestrates protected capabilities as separate
transactions before routine Ansible convergence. A failed protected health gate
is not confirmed; wait for rollback. Routine tasks rely on idempotent module
success and create no transaction bundles.

| Capability | Convergence | Required acceptance |
|---|---|---|
| Main Wi-Fi | Routine Ansible | Both radios are correct; selected clients join trusted LAN; DNS, Internet, atlas, and TrueNAS work; WPS, 802.11r, and client/bridge isolation remain off. |
| Guest | Protected | Guest Internet works; router, trusted clients, SSH, and LuCI are blocked; same-BSS and cross-radio isolation pass. |
| IPv6 | Protected | ISP delegation, distinct trusted/guest prefixes, DNS/Internet, required ICMPv6, isolation, and fail-closed WAN administration pass. |
| SQM | Routine Ansible | CAKE uses the contracted interface/rates/overhead/MPU with no MQ or flow offload; loaded-latency and CPU checks pass. |

Guest Internet alone is not acceptance. IPv4-only service is an allowed
intermediate state, not the final target.

## Final Acceptance

Run:

```bash
mise exec -- task network:openwrt:status
mise exec -- task network:openwrt:plan
mise exec -- task network:status
mise exec -- task infra:status
mise exec -- task network:openwrt:backup -- --kind config
```

Require a converged plan, every staged gate above, no WAN administration/public
forward/DMZ/UPnP/NAT-PMP/router Tailscale, and a verified encrypted post-cutover
backup. Keep the unchanged Speedport for at least seven days while monitoring
PPPoE, IPv6 PD, DHCP, Wi-Fi, SQM, logs, atlas, TrueNAS, and later-day Tailscale.
Production topology documentation should reflect the accepted live topology;
do not retire Speedport rollback procedures until the observation window passes.

The accepted baseline uses exact dnsmasq rebinding exceptions for the ten
Route53 private-service names and static forward/reverse DNS for the atlas and
TrueNAS reservations. Transaction `tx_20260717T102356Z_64c5b740e555` is the
current base-stage head and `tx_20260717T102628Z_6887fe62eb46` is the final
protected-stage head. The verified post-rebuild backup is
`.local/openwrt/backups/cudy-wr3000e-v1/config-20260717T103132Z.tar.age`.

The clean rebuild was completed on 2026-07-17. Its prior active transaction
lineage is preserved, still encrypted, at
`.local/openwrt/transactions/.generation-pre-clean-20260717T100701Z/`; normal
rollback proof and bootstrap then created a fresh active lineage and the router
returned healthy and converged. Main Wi-Fi, guest isolation, client Internet,
DNS, atlas and TrueNAS reservations, and direct Tailscale reachability passed.

## Physical Rollback

1. Wait for pending UCI rollback or explicitly roll back while connected.
2. Power off Cudy; do not factory-reset either router.
3. Move ONT and TL-SG108 cables back to Speedport WAN and LAN.
4. Power on the already credential-tested Speedport and wait for PPPoE.
5. Power-cycle ONT only if a stale session persists after a documented wait.
6. Verify `.1`, atlas `.19`, TrueNAS `.74`, NFS, DNS, and Tailscale.
7. Preserve Cudy logs/config for offline diagnosis.
