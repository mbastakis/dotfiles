# Reviews and operations

## Discovery and triage

Use narrow exports for analysis and `information` for one UUID. Useful native
reports include `overdue`, `waiting`, `blocked`, `blocking`, `recurring`,
`summary`, and `completed end.after:today-30d`. `tw rc.color=off _projects`,
`_tags`, and `_unique project` help discover existing metadata. Inspect deleted
Tasks with `tw rc.color=off status:deleted export` only when needed.

Native `waiting` finds deferred work and `blocked` finds unfinished prerequisites;
`ready`/`next` are discovery reports, not column definitions. For a scoped review, export
unfinished candidates including deferred Tasks, then classify their fields
using [contract.md](contract.md). Tested Taskwarrior 3.4.2 and 3.5.0 both export
deferred Tasks as `status:pending` with a future `wait`. Detect active
deferral from future `wait` / `+WAITING`, not status alone. Inspect dependency UUIDs to determine
which prerequisites remain unfinished. Avoid an active context hiding candidates.

Review upcoming scheduled dates, expired deferrals, overdue deadlines,
duplicate-looking outcomes, vague titles, and recurring templates needing changes.
Ask whether an overdue deadline actually changed; never move it merely to tidy
a report. Do not automatically remove `next`, clear dependencies, or delete Tasks.

Urgency is native and derived, with no manual ranks. Change only fields supported
by user intent: priority, genuine dates/prerequisites, or explicitly requested tags.
Never invent metadata to manipulate the score. Urgency settings are replica-local;
CLI/server ordering requires matching settings and Taskwarrior versions.
Present exact UUID/field changes for approval when a review produces new
recommendations. A clearly specified batch request already authorizes its scope.

## Project navigation interpretation

Project scope includes its exact name and dot-delimited descendants: `work.web`
includes `work.web.redesign`, not `work.web-other`. Capture in a selected project
uses that exact project, never an inferred descendant. Counts include all unfinished
descendants. Infer Active when unfinished work is not entirely deferred or
future-scheduled; Later when it all is; History when completed work exists and no
unfinished Tasks remain. Dependency blocking alone does not imply Later. Search all groups
and older completed history, not only recent Done retention. Say “No unfinished
tasks,” not “Project completed.” These are derived views, not new project
statuses, tags, or reasons to mutate Tasks. Exclude recurring templates and
template-only projects; generated instances remain ordinary Tasks. Omit deleted-only projects.

## Sync and recovery

Replicas use a TaskChampion sync server. The core workflow owns sync timing.
If refresh fails, continue clear requests against available local state and
identify it as potentially stale. Pause only when missing/current remote state
is necessary to resolve the target or operation. If publication fails, report
which changes are locally verified but not confirmed synced; do not recreate
them or claim Sisyphus has received them. A successful sync establishes replica
exchange, not proof that an open browser has refreshed.

TaskChampion handles sync conflict transformation. If a post-sync re-read differs
from intent, report the discrepancy and resolve it instead of blindly reapplying
writes or overwriting replicas. For an explicit sync-only request, sync once and
report the result; no task mutation is implied.

`tw undo` reverts the most recent action, not an entire multi-command transition.
Inspect before and after each undo; never blindly repeat it.

`tw import` can update existing UUIDs: inspect its records and establish the
explicitly authorized scope before executing it.
Resolve deletion targets and any series scope first. `tw purge` permanently removes
already-deleted Tasks locally and is not routine housekeeping; use only for an
explicit permanent-removal request with understood scope. `tw start`/`stop`
mark ongoing work, with no time-tracking integration.

For command verification, use an isolated temporary TASKRC and TASKDATA with
hooks disabled and no sync credentials; never test by mutating user Tasks.
