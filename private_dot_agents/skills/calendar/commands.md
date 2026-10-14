# Commands

Verified with plann 1.2.0. Personal is the default; add `--config-section focus` before the command for Focus.

## Read

Replace example dates with the requested window. Repeat for Focus when checking availability.

```bash
plann select --event --start '2026-10-12T00:00' \
  --end '2026-10-13T00:00' list --ics
plann select --uid "$event_uid" --abort-on-missing-uid list --ics
```

Interpret ICS timezones, recurrence, cancellation, and transparent/free events. All-day DTEND is exclusive. There is no native JSON output.

## Create

```bash
plann add event 'Appointment' '2026-10-12T18:00+30m'
plann --config-section focus add event 'Weekly review' '2026-10-12T19:00+1h'
```

Capture the returned `uid=…` and read it back in the same calendar. All-day syntax: `2026-10-12+1d`; verify DATE-valued boundaries.

## Edit title

```bash
plann select --uid "$event_uid" --abort-on-missing-uid \
  edit --set-summary 'Updated appointment'
plann select --uid "$event_uid" --abort-on-missing-uid list --ics
```

Use `event_uid`, not the shell's read-only `UID`. Time-editing failures observed: `--postpone` was a no-op, `--set-dtstart` left the old end, and `--set-dtend`/`--set-duration` raised dependency errors. Do not silently delete/recreate to work around rescheduling.

## Delete

```bash
plann select --uid "$event_uid" --abort-on-missing-uid delete
plann select --uid "$event_uid" --ignore-missing-uid list --ics
```

Readback must succeed without a matching event; a missing-UID warning is expected. Avoid broad selections for mutations.
