# Reviews and operations

## Discovery and triage

Use narrow exports for analysis and `information` for one UUID. Useful native
reports include `overdue`, `waiting`, `blocked`, `blocking`, `recurring`,
`summary`, and `completed end.after:today-30d`. `tw rc.color=off _projects`,
`_tags`, and `_unique project` help discover existing metadata. Inspect deleted
Tasks with `tw rc.color=off status:deleted export` only when needed.

Native reports do not implement the UDA contract. In particular `waiting`
finds deferred work, `blocked` finds prerequisites, and `ready`/`next` do not
fully account for `sisyphus_blocker` or daily intent. For a scoped review, export
unfinished candidates including deferred Tasks, then classify their fields
using [contract.md](contract.md). Tested Taskwarrior 3.4.2 and 3.5.0 both export
deferred Tasks as `status:pending` with a future `wait`. Detect active
deferral from future `wait` / `+WAITING`, not status alone. Inspect dependency UUIDs to determine
which prerequisites remain unfinished. Avoid an active context hiding candidates.

Review old daily plans, due follow-ups, expired deferrals, overdue deadlines,
duplicate-looking outcomes, vague titles, and recurring templates needing changes.
Ask whether an overdue deadline actually changed; never move it merely to tidy
a report. No automatic weekly `-next`, daily rollover, unblocking, or deletion.

Urgency is derived. Rerank only with supported intent: stated `priority`,
commitment, genuine deadlines/prerequisites, or intentional deferral. Never
invent metadata to manipulate the score. Present exact UUID/field changes and
resolve broad-write confirmation before executing a review's changes.

## Project navigation interpretation

Exact Taskwarrior project names define groupings; Boards can overlap without
copying Tasks. Infer Active when a project has non-deferred Ready, Doing, or
Waiting work; Later when its unfinished work is all Backlog/deferred; History
when completed work exists and no unfinished Tasks remain. Search all groups
and older completed history, not only recent Done retention. Say “No unfinished
tasks,” not “Project completed.” These are derived views, not new project
statuses, tags, or reasons to mutate Tasks. Recurring templates preserve a project
in Later when it has no committed instances; do not expose templates as executable
Tasks. Omit deleted-only projects.

## Sync and recovery

Replicas use a TaskChampion sync server. Run `tw sync` after writes when the user
wants cross-device visibility; report local verification and sync success/failure
separately. TaskChampion handles sync conflict transformation; do not manually
overwrite replicas to resolve apparent conflicts. Do not sync disposable test replicas.

`tw import` can update existing UUIDs: inspect scope and obtain confirmation.
Confirm deletion and any series scope first. `tw purge` permanently removes
already-deleted Tasks locally and is not routine housekeeping; use only for an
explicit permanent-removal request with understood scope. `tw start`/`stop`
mark ongoing work, with no time-tracking integration.

For command verification, use an isolated temporary TASKRC and TASKDATA with
hooks disabled and no sync credentials; never test by mutating user Tasks.
