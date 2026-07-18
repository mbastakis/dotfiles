# TrueNAS Disk Maintenance

Code-owned SMART daemon state, scrub policy, and SMART self-test schedules for
the TrueNAS storage appliance.

## Policy

| Work | Schedule | Effective cadence |
|---|---|---|
| ZFS scrub eligibility check | Sunday 06:00 | About every five weeks because `threshold` is 35 days |
| SMART short test | Tuesday 06:00 | Weekly, all SMART-enabled disks |
| SMART extended test | First Friday 06:00 | Monthly, all SMART-enabled disks |

The jobs are separated because TrueNAS does not coordinate ZFS scrubs with
SMART self-tests. The schedules also start after the normal Backrest backup
window. SMART tests include the boot disk as well as current and future pool
members; this avoids binding policy to a replaceable disk serial number.

The reconciler requires `smartd` to be enabled at boot and running, adopts the
existing scrub by pool identity, and adopts all-disk SMART tests by test type.
It enables and starts `smartd` before changing schedules, while unmanaged tests
are preserved with warnings. Apply refuses to change maintenance policy unless
`pool_4tb` reports `ONLINE`.

## Commands

```bash
mise exec -- task truenas:maintenance:plan
mise exec -- task truenas:maintenance:apply
```

Do not apply the policy during a degraded-pool incident. Replace the failed
member, wait for resilvering, run the post-replacement scrub, and confirm the
pool is `ONLINE` first. The daemon start is a single reconciliation action;
TrueNAS systemd supervision and native alerts remain responsible for ongoing
runtime monitoring.
