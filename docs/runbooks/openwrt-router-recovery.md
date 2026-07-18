# OpenWrt Router Recovery

> **Status: production recovery path.** Protected rollback and the configured
> Speedport fallback were prepared during the accepted cutover. Destructive
> TFTP/UART recovery remains intentionally unexercised; do not test it against a
> healthy production router. The guarded clean rebuild completed successfully
> on 2026-07-17.

Use the least destructive applicable layer. UCI rollback, transaction revert,
Speedport physical rollback, stock TFTP recovery, and UART RAM boot solve
different failures and are not interchangeable.

## Recovery Matrix

| Failure | First response | Recovery target |
|---|---|---|
| Protected apply fails health checks | Do not confirm; wait for rpcd timeout | Prior `/etc/config` |
| Post-confirm protected failure | `network:openwrt:recover -- --revert <id>` | Captured pre-stage fields |
| Routine Ansible failure | Fix the contract/task and rerun plan/apply | Canonical routine state |
| PPPoE/core LAN outage | Restore physical Speedport cabling | Tested router at `.1` |
| OpenWrt boot failure | Cudy stock TFTP `recovery.bin` | Stock UI at `.10.1` |
| TFTP failure | UART boot stock-layout OpenWrt initramfs in RAM | Diagnostic/recovery shell |
| Calibration/boot damage | Stop all writes | Expert recovery using this device's backups |

## Protected Configuration Recovery

- While an rpcd rollback is pending, do not reboot, power-cycle, restart rpcd or
  ubus, retry an ambiguous apply, issue a second apply, or let LuCI/root write
  UCI. Reconnect on the old and expected paths and wait or explicitly roll back.
- rpcd protection exists only while its process, timer, and snapshots survive.
  Power loss, kernel failure, reboot, or rpcd/ubus restart can remove protection
  after committed files changed. It is not ACID, firmware rollback, or physical
  recovery.
- A transaction revert accepts an exact transaction ID only. It must decrypt the
  age bundle in memory and refuse if current owned state differs from that
  transaction's expected post-state or lineage. There is no forced historical
  restore override.
- After rollback/revert, verify wired SSH, restored protected fields, and all
  dependent capabilities. Routine Ansible changes have no transaction ID and
  are corrected by reconverging the canonical contract.
- The controller refuses a new protected apply while any transaction is pending.
  Generic pending recovery brackets two identical state reads with three absent
  lock checks. An exact post-state with the applicable normal/revert health
  closure is accepted; an exact pre-state is moved to a hidden
  `.failed-rolled-back` archive. Intermediate, ambiguous, changing, or locked
  outcomes remain pending.

If protected recovery cannot restore core WAN/LAN service, use the configured
Speedport rollback in the cutover runbook. Preserve Cudy diagnostics; do not
factory-reset it during outage recovery.

## Configuration Restore And Clean Rebuild

Configuration archives and transaction bundles under
`.local/openwrt/backups/<device-id>/` and `.local/openwrt/transactions/` must
remain age-encrypted. Verify by decrypting to a pipe; do not leave plaintext.
The accepted post-rebuild configuration checkpoint is
`config-20260717T103132Z.tar.age` with its adjacent manifest.

For a normal point upgrade, create a current encrypted backup, verify local and
remote image hashes, require `sysupgrade -T`, use config-preserving sysupgrade
without force, wait up to five minutes for SSH and the board endpoint to return,
then verify board/release/packages and run plan/apply/status.

For an explicit clean rebuild, direct-wire the controller and use only:

```bash
mise exec -- task network:openwrt:clean-rebuild -- \
  --image <verified-bundle-image> --confirm CLEAN-REBUILD
```

The task verifies the exact bundle image, creates and pipe-verifies a current
encrypted config backup, uploads through the strict uploader, checks the remote
SHA-256, requires `sysupgrade -T`, and clean-flashes with `sysupgrade -n`. Never
force. The SSH session may disconnect as the router reboots.

After boot, keep the router directly wired and physically confirm the displayed
fingerprint before entering `yes`:

```bash
mise exec -- task network:openwrt:bootstrap -- --prepare-clean-rebuild
mise exec -- task network:openwrt:bootstrap -- --test-rollback-only
mise exec -- task network:openwrt:bootstrap
```

Preparation refuses pending transactions and only replaces the old host pin
after the physical callback. It validates exact clean-image identity and
pre-sanitize defaults before moving prior visible transaction entries, without
decryption or deletion, into a hidden generation. The 2026-07-17 rebuild history
is preserved at
`.local/openwrt/transactions/.generation-pre-clean-20260717T100701Z/`; hidden
generations are ignored by the active journal. Resolve credentials from BWS,
connect the production WAN path, then run plan/apply/status. Protected
capabilities use separate rollback-enabled transactions; routine capabilities
use Ansible. New host keys and LuCI certificates are expected runtime identity.
Do not restore MTD partitions for normal rebuild.

## Off-Host Recovery Archive

Keep one checksum-bound recovery archive in Michail's personal File Browser
tree for the lifetime of the WR3000E. The accepted 2026-07-17 copy is visible in
File Browser under `Personal/Backup/OpenWrt/WR3000E-v1/2026-07-17/` and stored on
TrueNAS at:

```text
/mnt/pool_4tb/homeserver/data/files/users/michail/Backup/OpenWrt/WR3000E-v1/2026-07-17/
```

The archive is `openwrt-recovery-20260717T111633Z.tar.gz`; its adjacent
`.sha256` sidecar records SHA-256
`51d30df5f437e7a624a0ab0b31d0af712e7eccfc1f447d97815bf5229a563ce1`.
TrueNAS independently verified both the checksum and gzip stream after upload.

It contains the passphrase-encrypted age identity, encrypted device/Speedport
exports, device-specific encrypted MTD partitions, encrypted current and
historical transaction generations, current and intermediary host pins, the
verified custom image bundle, stock TFTP recovery image, UART initramfs, vendor
firmware archives, canonical contract, public SSH key, and these recovery
runbooks. It contains no plaintext configuration export or credential value.

Retain this archive and its sidecar until the physical router is retired and
all encrypted backups are intentionally destroyed. Create and verify a new
dated archive after replacing the router, rotating the age identity, changing
the recovery firmware set, or establishing a new accepted configuration
generation. File Browser provides an off-Mac copy on TrueNAS, but it is not a
geographically offsite backup; disaster recovery still requires a second copy
outside this TrueNAS pool.

## Stock-Layout TFTP Recovery

Use only the independently checksum-verified **Cudy stock/recovery inner image**
for WR3000E 1.0/R53. Its recorded filename is
`WR3000E-R53-2.4.7-20250528-182254-sysupgrade.bin` and recorded SHA-256 is
`d75ba5b186e78b22d3f7b8270fc4bbde9aa643fc88bdbe46903f8ccc9682a80f`.
Cudy did not publish this checksum; it was independently computed from the
official download on 2026-07-15, so re-verify provenance before use.

1. Extract the verified Cudy stock ZIP and copy the inner image to the TFTP root
   as `recovery.bin`.
2. Set workstation Ethernet to `192.168.1.88/24` with no gateway. Disable Wi-Fi
   and all other adapters; permit the TFTP server through the firewall.
3. Connect the workstation directly to a Cudy **LAN** port. The bootloader's
   expected TFTP client address is `192.168.1.112`.
4. Power off Cudy. Hold RESET, power on, and keep holding RESET.
5. Release RESET when TFTP transfer begins.
6. Wait approximately two minutes after transfer and do not interrupt power.
7. Return workstation networking to DHCP.
8. Open restored stock firmware at `http://192.168.10.1/`.

Do not upload the Cudy stock image through OpenWrt LuCI merely because its name
contains `sysupgrade`. Never force it and never use `ubootmod` recovery images.

### Prepared Atlas Server

The managed Mac firewall blocks inbound TFTP. Atlas is the verified recovery
server, but its only Ethernet interface normally serves production. Before a
recovery, while Atlas is still connected to the production switch, run:

```bash
sudo ip address add 192.168.1.88/24 dev enp3s0
sudo systemctl start tftpd-hpa
sha256sum /srv/tftp/openwrt/recovery.bin
sudo ss -lunp | grep ':69 '
```

The checksum must be
`d75ba5b186e78b22d3f7b8270fc4bbde9aa643fc88bdbe46903f8ccc9682a80f`.
Then disconnect Atlas Ethernet from the production switch and connect it
directly to a Cudy LAN port before triggering recovery. Atlas is intentionally
offline from production during recovery. Afterward, stop TFTP, remove the
temporary address, and restore the production cable:

```bash
sudo systemctl stop tftpd-hpa
sudo ip address del 192.168.1.88/24 dev enp3s0
```

The disabled-by-default service was proven by retrieving `recovery.bin` through
the temporary `.88` address from a second host and matching its full SHA-256.

## UART Fallback

UART is last resort after TFTP fails and requires opening the router. Use a
**3.3 V TTL** adapter at **115200 8N1**. Connect GND and crossed TX/RX; leave VCC
disconnected. Never connect a 5 V serial adapter.

Serve the official stock-layout OpenWrt initramfs as `cudy3000e.bin`, then use
the bootloader to load and boot it entirely from RAM:

```text
tftpboot 0x46000000 cudy3000e.bin
bootm 0x46000000
```

Use the RAM system to inspect, back up, or perform a separately reviewed
stock-layout recovery. Do not write BL2, FIP, `Factory`, or `bdinfo` unless an
expert recovery plan specifically requires it. `Factory` contains unique Wi-Fi
calibration and `bdinfo` contributes MAC data; restore them only from encrypted,
hash-verified backups of this exact device. Stop all writes if the partition map
differs from the recorded stock layout.
