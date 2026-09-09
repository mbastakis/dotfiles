# Recurrence

Use recurrence for durable obligations. Establish first due/anchor date,
cadence, optional end (`until`), optional deferral lead time (`wait`), and any
month-end/leap-day requirements before creating. Do not invent a deadline just
to turn vague daily intent into a native recurring series.

Illustrative resolved dates below are not instructions to create Tasks. Establish
the server timezone and requested dates using [contract.md](contract.md) first;
run these commands in that timezone. Date-only deadlines use end-of-day and
deferral dates use midnight; preserve explicitly requested instants.

```bash
tw add due:2026-10-01T23:59:59 recur:monthly -- "Pay rent"
tw add due:2026-09-11T23:59:59 recur:weekly -- "Take out trash"
tw add due:2026-09-12T23:59:59 wait:2026-09-10T00:00:00 recur:weekly -- "Water plants"
```

- `recur` requires `due`; it creates a hidden template and generated child
  instances. Completing an instance updates series state; recurrence processing
  generates future instances. Never edit internal `mask`, `parent`, or `imask`.
- `until` cuts off future generation. Confirm before changing/deleting a series;
  distinguish the requested instance from its template deliberately.
- `wait` is deferral lead time; children preserve its offset from `due`.
  Inspect existing template/instance timestamps and their offset before changing
  either field in an offset-sensitive series; do not normalize an existing series
  to day boundaries without checking the requested effect on future instances.
- Avoid `scheduled` on recurring Tasks: Taskwarrior 3.4.2 copies the absolute
  value rather than recalculating its offset. Explain this when relevant to
  scheduling a series. Do not put daily-plan or current-blocker UDAs on templates
  expecting them to advance or reset automatically; inspect instance inheritance.
- Flag monthly anchors on the 29th–31st: invalid calendar dates can clamp and
  drift. Check the actual generated dates when those boundaries matter.
- Prefer `daily`, `weekdays`, `weekly`, `biweekly`, `monthly`, `quarterly`,
  `semiannual`, `annual`, or explicit `2w`, `2mo`, `2y`; not bare `recur:2`.

Inspect scope with `tw recurring`, `tw all +TEMPLATE`, and `tw all +INSTANCE`.
Target a discovered template UUID intentionally, for example:

```bash
tw <template-uuid> modify until:2026-12-31
```

Completion: verify the requested instance/template, anchor, cadence, cutoff,
server-local deadline/deferral boundaries, preserved explicit instants and
wait/due offset, and generated dates relevant to the request; do not report a series edit as
verified by reading only one unrelated child.
