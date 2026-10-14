---
name: calendar
description: Calendar operations with plann. Use to read schedules, find available time, or create, edit, and delete Personal or Focus events.
---

# Calendar

Use `plann` for Personal; add `--config-section focus` for Focus. Authentication is configured; Tailscale must be connected. Timezone defaults to the Mac's local zone. If it differs from the intended zone, pass `--implicit-timezone Europe/Athens` (or the requested zone).

1. **Resolve** — Use Personal for appointments and ordinary events; Focus for planned work. Resolve relative dates against the current time. Default to Europe/Athens. _Done when the read window or event title, calendar, start, and duration are established._
2. **Inspect** — For availability, read both calendars; Google is outside scope. Before editing/deleting, identify the calendar and UID and inspect its ICS. _Done when the relevant schedule or unique target is known._
3. **Act and read back** — Use [commands.md](commands.md). Verify every creation/edit by UID and stored fields, and every deletion by absence after a successful query. After an ambiguous write failure, inspect before retrying. _Done when server state confirms the requested result; report the calendar and local date/time._

## Limits

- Rescheduling is broken in the verified plann installation; use Apple Calendar. Title editing works.
- Recurring UIDs identify whole series; date filters do not isolate occurrences. Use Apple Calendar for single-occurrence changes.
- Focus is not permission to rearrange blocks automatically. Vikunja owns tasks.
- Server errors are not empty schedules or successful writes.
