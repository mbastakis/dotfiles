# OpenWrt router runtime

This directory owns the offline-verifiable runtime and firmware inputs for the
Cudy WR3000E v1 stock flash layout. Generated overlays, images, manifests,
known-host data, transaction bundles, and backups belong under
`.local/openwrt/`; none are repository inputs.

## Safety boundary

- `homeserver-uci` accepts one bounded JSON envelope on stdin, calls libubus
  directly, allowlists methods, and defaults to withholding UCI values.
- SSH uses `-F /dev/null`, a dedicated known-host file, strict host-key checking,
  fixed remote argv, and stdin for every mutation. ProxyJump is read-only.
- Planning combines protected semantic operations with Ansible check/diff mode.
  Secret-bearing Ansible tasks use `no_log` and disable diff.
- Each protected capability has an exact package ACL, local and router lock, one rpcd
  session, staged comparison, one rollback-enabled apply, health-closure checks,
  same-SID confirmation, and no ambiguous retry. A failed bounded health check
  requests explicit same-SID rollback while connectivity remains; if that call
  is ambiguous, the controller preserves the lock and waits for rpcd timeout.
- Stage plans use field-level ownership. Shared resources such as trusted LAN,
  guest LAN, and WAN are projected so an earlier stage cannot treat fields from
  a later accepted stage as drift.
- Pinned `community.openwrt` modules own routine system, trusted DHCP/DNS and
  reservations, main Wi-Fi, SQM, and flow-offload fields. Stable `hs_*` names
  provide bounded exact-set pruning without whole-file ownership.
- DNS rebinding protection remains enabled. Routine convergence permits only the
  exact declared private-service FQDNs and publishes static local DNS for
  declared LAN reservations.
- Transaction state is serialized in memory and written only through the
  encryption stream. Its public index contains transaction identity, stage,
  timestamp, ciphertext filename, size, and checksum; revert validation checks
  ciphertext integrity, expected post-state, and parent lineage in memory.
- A verified clean rebuild preserves prior visible transaction directories by
  moving them, still encrypted, beneath a hidden
  `.generation-pre-clean-<timestamp>/` directory. Pending transactions block
  generation changes; hidden generations remain outside the active lineage.
- rpcd rollback is process-lifetime protection only. Reboot, power loss, or an
  rpcd/ubus failure can remove the timer and snapshots after config files change.
- Backups use a binary streaming encryption interface. Callers must supply an
  age encryptor/decryptor; plaintext files are not created by the runtime.

## Firmware

The builder is Linux amd64 and digest-pinned. It assembles Image Builder output;
it does not compile OpenWrt. On the arm64 Colima VM, extraction and Image Builder
run in the container's ephemeral case-sensitive filesystem; only the pinned
archive and generated two-file overlay are mounted read-only, and only finished
outputs are copied to `.local/openwrt/`. The repository, `$HOME`, BWS state, SSH
private key, and age identity are never mounted.

The firmware module pins OpenWrt 25.12.5,
`mediatek/filogic`, `cudy_wr3000e-v1`, validates upstream profile metadata,
creates only the public-key/helper overlay, and verifies local manifests without
network access. `ubootmod`, initramfs, missing packages, forbidden packages,
changed helper/key checksums, and unrecorded feed indexes are rejected.

Build and verify the ignored local bundle with:

```bash
mise exec -- task network:openwrt:firmware:build
mise exec -- task network:openwrt:firmware:verify
```

After local verification, copy and re-verify the already-built bundle at a new
path on genuinely separate private storage:

```bash
mise exec -- task network:openwrt:firmware:build -- \
  --archive-to /private/second-storage/openwrt-25.12.5-homeserver
```

The build records the immutable local builder image ID, Containerfile checksum,
upstream metadata checksums, all downloaded feed-index checksums, and all 171
resolved package versions. Verification runs the recorded image with networking
disabled, rechecks the checksum sidecar, `fwtool` CRC and metadata, sysupgrade
layout, FIT and squashfs markers, package sidecar, rootfs public key/helper bytes
and modes, and text-file secret markers.

Task is the only public interface. Ansible orchestrates routine convergence and
delegates reachability-critical base, WAN, guest, and IPv6 changes to the narrow
protected extension. The extension also retains transaction recovery, streaming
verified backups, firmware operations, host-key pinning, and root-password/LuCI
verification. The production ownership transfer completed with a zero-change
apply and second zero-change plan. The direct-wired clean rebuild completed on
2026-07-17 and converged successfully from an empty active transaction lineage.

The public operation forms are:

```bash
mise exec -- task network:openwrt:plan
mise exec -- task network:openwrt:validate
mise exec -- task network:openwrt:apply
mise exec -- task network:openwrt:recover -- --revert <transaction-id>
mise exec -- task network:openwrt:backup -- --kind config
mise exec -- task network:openwrt:backup -- --kind mtd --recovery-workflow
mise exec -- task network:openwrt:upgrade -- --image <verified-bundle-image>
mise exec -- task network:openwrt:clean-rebuild -- \
  --image <verified-bundle-image> --confirm CLEAN-REBUILD
```

`clean-rebuild` is the only supported clean-flash interface. It requires a
direct route and exact confirmation token, verifies the bundle artifact, creates
and pipe-verifies a current encrypted configuration backup, uploads through the
strict SSH uploader, verifies the remote SHA-256, requires `sysupgrade -T`, and
runs only `sysupgrade -n`. It never force-flashes and does not alter the
config-preserving `upgrade` workflow. An SSH disconnect during sysupgrade is
expected.

After the clean image boots, prepare the new lineage, establish trust, and prove
rpcd rollback before the mutating bootstrap:

```bash
mise exec -- task network:openwrt:bootstrap -- --prepare-clean-rebuild
mise exec -- task network:openwrt:bootstrap -- --test-rollback-only
mise exec -- task network:openwrt:bootstrap
```

Preparation is the sole host-key replacement path. It first refuses any pending
transaction, uses the existing physical fingerprint confirmation callback,
validates the exact clean-image identity and unsanitized default state, then
archives visible accepted/failed entries without decrypting or deleting them.
Ordinary `--pin-host-key-only` continues to refuse a different existing key.

An interrupted protected acceptance may be recovered only for one exact
pending `bootstrap-sanitize` journal whose live post-state, health, identity,
lineage, and absent router lock all verify:

```bash
mise exec -- task network:openwrt:bootstrap -- --recover-pending-sanitize-only
```

When clean-image inspection fails before mutation, capture only the allowlisted
management/radio diagnostics with `--inspect-clean-image-only`; it intentionally
skips planning and mutation but still requires direct host-key verification.

MTD backup is direct-wired and requires the explicit recovery flag. On the
signed intermediary it validates the pinned Cudy build directly through
`ubus`, encrypts the board and `/proc/mtd` metadata, then independently encrypts
and pipe-verifies all six partitions without requiring the custom image helper.
Root password rotation is also explicit:

```bash
mise exec -- task network:openwrt:bootstrap -- --rotate-root-password-only
```
