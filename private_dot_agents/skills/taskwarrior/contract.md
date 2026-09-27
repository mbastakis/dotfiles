# Shared Taskwarrior / Sisyphus contract

This agent contract follows Sisyphus ADR 0011. It defines native task meaning
and CLI writes, not backend deployment status. Workstation configuration lives
in `~/.config/task/taskrc`; the container owns its own configuration. No app
checkout is required at runtime.

## Canonical fields

| Field | Meaning |
|---|---|
| `due` | A real finish-by deadline, never an urgency trick. |
| `scheduled` | Earliest opportunity to accomplish work, not a daily selection. |
| `wait` | Deferral until a specified return date, not dependency or external blocking. |
| `start` | Activity recorded by native `start`/`stop`, not an exclusive execution claim. |
| `depends` | Actual prerequisite Tasks, not preferred ordering. |
| `priority` | Explicit user priority, independent of column placement. |
| `+next` | Ordinary native urgency tag; no column or commitment meaning. |
| Annotations | Supporting steps, links, completion criteria, and external-condition context. |

Preserve native fields, tags (including `next`), recurrence, annotations and
unrelated UDAs, including `linear_*` provenance. Do not invent tags or add
`+next` automatically. Do not recreate `sisyphus_plan`, `sisyphus_blocker`,
`sisyphus_followup`, `sisyphus_rank_lifecycle`, or `sisyphus_rank_project`.
Their removal from stored Tasks is a separately authorized cleanup; never
translate discarded values into native dates, dependencies, or replacement UDAs.

## Native board projection

For executable Tasks, apply this precedence:

- **Done:** completed work; the outcome has been achieved, not abandoned.
  The board normally shows seven days, with older history available.
- **Waiting:** unfinished work with a future `wait`, even if `start` remains.
- **Doing:** other unfinished work with `start`.
- **To do:** remaining unfinished work, including tasks with unfinished
  prerequisites or future `scheduled` dates. These receive Blocked or Scheduled
  indicators, not separate columns.

Deleted Tasks and recurring templates are excluded; generated instances are
ordinary Tasks. Priority, tags and dependency blocking do not select columns.
The optional Only actionable tasks filter uses native readiness and excludes
completed work; the unfiltered board retains blocked and future-scheduled work.
Calendar shows separate Scheduled, Due and Returns markers for native dates.
There is no Today workflow, custom commitment, or manual ranking. Unfinished
columns sort by native urgency descending; Done sorts by completion time.

When `wait` expires, deferral ends without changing a deadline or starting work.
A retained `start` becomes visible as Doing. Native Taskwarrior may retain a
past `wait`; compare its timestamp rather than treating any value as deferral.

## Writes and postconditions

Examples use discovered UUIDs and dates resolved in the configured Sisyphus
**server timezone**. Resolve relative dates before writing. Date-only deadlines
use server-local end-of-day (`due:YYYY-MM-DDT23:59:59`); date-only scheduled and
return dates use midnight (`YYYY-MM-DDT00:00:00`). Preserve explicit instants.
If the server timezone is unknown or differs from the client's, establish the
intended timezone first. Run the CLI with that timezone (for example
`TZ=<server-zone> tw ...`) or convert to the equivalent UTC instant. Exports use
UTC timestamps: verify the intended local date/time after writing. Moving a
calendar marker changes only its corresponding field, preserving an explicit
local time across calendar days and daylight-saving changes.

| Intent | Native commands / postcondition |
|---|---|
| Capture | `tw add -- "Concrete outcome"`; To do, no invented attributes. |
| Begin execution | `tw <uuid> start`; no automatic tag, priority, or date change. |
| Stop execution / Doing → To do | `tw <uuid> stop`; preserve other fields. |
| Defer / To do or Doing → Waiting | Require a future return date; `tw <uuid> modify wait:YYYY-MM-DDT00:00:00`, then stop if started. Preserve other dates and dependencies. |
| Waiting → To do | `tw <uuid> modify wait:`; clear only wait. A retained start reveals Doing; report it rather than silently changing another field. |
| Schedule earliest opportunity | `tw <uuid> modify scheduled:YYYY-MM-DDT00:00:00`. |
| Set deadline | `tw <uuid> modify due:YYYY-MM-DDT23:59:59`. |
| Record prerequisite | `tw <uuid> modify depends:<prerequisite-uuid>`; include existing prerequisite UUIDs in the comma-separated list so they are preserved. |
| Record external condition | `tw <uuid> annotate -- "Specific condition and context"`; no automatic wait, dependency, or stop. |
| Complete | `tw <uuid> done`; verify outcome and persisted completion. |
| Capture already-completed work | `tw log -- "Achieved outcome"`; verify the created UUID and completion. |

Do not silently clear dependencies, scheduled dates, or future deferral to satisfy
a start request; resolve conflicting intent first. Dependency readiness follows
prerequisite state; annotations do not change it. Verify multi-command transitions
in full, including partial failures. If capture succeeds but a later start or
date write fails, report the existing UUID instead of repeating capture.
