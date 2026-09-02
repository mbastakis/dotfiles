---
name: taskwarrior
description: Use this skill for Taskwarrior (`tw` CLI) workflows: creating, querying, reranking, triaging, housekeeping, and completing tasks for the user's life and projects. Trigger whenever the user mentions Taskwarrior or `tw`, recurring tasks, task triage, housekeeping, reranking, or asks to update life/project tasks in this environment; do not use for ordinary software-development "tasks" unless the local Taskwarrior system is implied.
---

# Taskwarrior

Use this workflow when working with the user's local Taskwarrior data. Taskwarrior tracks tasks across their life and projects, so safety and exact identity matter more than speed.

Invoke it as `tw`, not `task` — the global `task` command is go-task (a build-tool runner), and Taskwarrior is reached through the `tw` wrapper instead. Never run a bare `task` command for this skill.

The core discipline is _discover_ before _mutate_: read the current state, classify what you find, _propose_ exact changes, then execute the smallest safe command.

## Operating Workflow

Use this loop unless the user asks for one narrow command:

1. **Scope** — name the project, area of life, date range, context, or report being worked. _Done when you can state in one sentence what subset of the task system this request touches._
2. **Read** — use read-only commands to collect candidates and current state. _Done when you have UUIDs and current field values for every task the request could affect._
3. **Classify** — separate capture, actionable next actions, waiting/deferred work, recurring templates, and stale/housekeeping items. _Done when every candidate is assigned to one category._
4. **Propose** — show exact target identities and proposed changes before broad or ambiguous writes. _Done when the user can see exactly what will change and on which tasks._
5. **Mutate** — run the smallest safe commands, targeting UUIDs. _Done when each command has exited and you have captured its output._
6. **Verify** — re-read narrowly and report undo commands. _Done when the post-write state matches the proposal and the user knows how to undo._

For triage or reranking, produce a compact table before writing:

```text
| uuid | task | current state | proposed change | rationale | confidence |
```

Taskwarrior urgency is derived, not editable. Rerank by changing explicit fields: `priority`, `due`, `wait`, `scheduled`, project, `+next`, or dependencies. `+next` is the only tag in use; never add other tags.

## Board Contract

Treat the Kanban columns as a commitment workflow, not four equivalent task categories:

| Column | Meaning | Taskwarrior state |
|---|---|---|
| Backlog | An idea or possible task worth retaining, but not prioritized or committed for the current week. | Pending, not active, without `+next`, a `wait:` date, or an unfinished dependency |
| Ready | Prioritized work committed for the current week and available to start. Keep this list intentionally small and realistic. | Pending with `+next`, not active or blocked |
| Doing | Work currently being executed. | Started with `tw <uuid> start` |
| Waiting | Work that was being pursued but cannot progress because it is blocked by a person, event, prerequisite, or external condition. Record the blocker. | A `wait:` date (native waiting state) or an unfinished dependency |

Apply these transitions consistently:

- New ideas and unprioritized tasks enter Backlog by default; do not add `+next` merely because a task is actionable.
- Promote Backlog to Ready with `+next` only when the user prioritizes it for the current week.
- Move Ready to Doing with `tw <uuid> start`; keep `+next` so stopping an unblocked task returns it to Ready.
- Move Doing to Waiting when blocked: stop it, preserve `+next`, set a `wait:` date or the blocking dependency, and annotate what is blocking progress and the next follow-up when known.
- When a blocker clears, remove the waiting state and return the task to Ready; start it only when work actually resumes.
- During weekly planning, remove `+next` from unfinished tasks that are no longer a current-week commitment so they return to Backlog.
- Use `wait:` for work intentionally hidden until a future date. Do not use the Waiting column for ordinary deferral, lack of priority, or someday/maybe ideas.

## Identity

Taskwarrior UUIDs are stable. Numeric task IDs are temporary UI handles that can change between reads.

**For any mutation, target the UUID, not the numeric ID** — unless the user just supplied or confirmed a displayed numeric ID.

```bash
tw <uuid> modify project:Work +next    # safe
tw 12 modify project:Work +next        # risky unless 12 was just displayed
```

When explaining a mutation plan, say plainly: _numeric IDs are temporary; use UUIDs for mutations._

## Creating Tasks

Create tasks with enough structure to make later querying useful, but do not invent metadata. A good task has a clear verb, optional project, optional due/wait date, and no tags other than `+next`.

Use `--` before a literal description that could be parsed as attributes:

```bash
tw add project:personal.finance due:friday -- "Pay credit card"
tw add project:Work +next wait:tomorrow -- "Draft launch checklist"
tw add -- "project:Home needs scheduling"
```

Use `tw log` to record already-completed work as a completed task:

```bash
tw log project:Work -- "Submitted monthly report"
```

Ask one short question before adding when the answer materially changes the durable task shape:

- Is this a one-off task or recurring obligation?
- What is the first due date or review date?
- Which project/area owns it?
- Should it be hidden until a lead time (`wait:`)?

## Recurring Tasks

Use recurring tasks for durable obligations, not vague intentions. Before creating one, establish:

- First due date or anchor date.
- Cadence.
- Whether it should end (`until:`).
- Whether it should stay hidden until a lead time (`wait:`).
- Whether month-end or leap-day behavior matters.

Safe creation pattern:

```bash
tw add "Pay rent" due:1st recur:monthly
tw add "Take out trash" due:fri recur:weekly
tw add "Water plants" due:saturday wait:thursday recur:weekly
tw add "Submit expense report" due:eom recur:monthly until:2026-12-31
```

Rules:

- `recur:` requires `due:`. Do not create `tw add "Thing" recur:daily`.
- `due:` + `recur:` creates a hidden recurring template; visible work appears as child instances.
- Completing an instance updates the template state; future instances are generated by recurrence processing.
- Use `until:` to stop future generation after a cutoff.
- Use `wait:` for lead time; recurring children preserve the wait-minus-due offset.
- **Avoid `scheduled:` on recurring tasks.** Taskwarrior 3.4.2 copies it as an absolute value rather than recalculating it relative to each due date. Include this caveat in recurring-task answers even when the proposed commands do not use `scheduled:`.
- Warn on monthly tasks anchored on the 29th, 30th, or 31st; calendar-month stepping can clamp invalid dates and drift.
- Never edit internal recurrence fields such as `mask`, `parent`, or `imask`.
- Prefer readable recurrence values: `daily`, `weekdays`, `weekly`, `biweekly`, `monthly`, `quarterly`, `semiannual`, `annual`, or explicit forms like `2w`, `2mo`, `2y`. Do not use bare integers like `recur:2`.

Inspect recurring templates intentionally:

```bash
tw recurring
tw all +TEMPLATE
tw all +INSTANCE
```

For recurring series edits, target the template intentionally. Ask before changing or deleting a series.

```bash
tw <template-uuid> modify project:Finance
tw <template-uuid> modify until:2026-12-31
tw <template-uuid> delete
```

## Reads

Prefer machine-readable `export` for analysis and `information` for detail on a single task:

```bash
tw rc.color=off <narrow-filter> export
tw rc.color=off <uuid> information
tw rc.color=off _projects
tw rc.color=off _tags
tw rc.color=off _unique project
tw rc.color=off summary
```

Use the narrowest useful date range, project, tag, status, or UUID. Avoid dumping all tasks unless the user asks for a broad review.

Current Taskwarrior context can filter results and affect `add` or `log`. If results look surprisingly empty, inspect context before concluding there are no tasks:

```bash
tw context
```

## Mutations

For `modify`, `annotate`, `append`, `prepend`, `start`, `stop`, and `done`, use a UUID and verify after the command.

```bash
tw <uuid> annotate "Waiting for Alex reply"
tw <uuid> done
tw <uuid> start
tw <uuid> stop
```

`tw start` and `tw stop` mark active work; there is no time-tracking integration.

Require explicit confirmation before:

- Mutating more than one task.
- Mutating by broad filter, for example `project:Work modify ...`.
- Marking ambiguous candidates done.
- Changing contexts or Taskwarrior config.
- Running `tw import`, because matching UUIDs can update existing tasks.
- Running `tw delete`.
- Running `tw purge`.

Treat `tw purge` as break-glass only. It permanently removes already-deleted tasks, is local-only, and is not a normal cleanup command.

## Query, Triage, And Rerank

Use queries to _discover_ the system before changing it:

```bash
tw rc.color=off ready
tw rc.color=off next
tw rc.color=off waiting
tw rc.color=off overdue
tw rc.color=off status:pending project.none: export
tw rc.color=off status:pending due.none: export
tw rc.color=off status:pending +next export
```

For triage, classify each task as:

- **Do now or next** — clear action, available, worth surfacing.
- **Schedule/defer** — real task, not actionable until a date.
- **Waiting** — blocked by someone/something else.
- **Someday/maybe** — keep but hide from near-term action.
- **Clarify** — description is not actionable yet.
- **Delete/done** — no longer relevant or already completed.

For reranking, _propose_ exact field changes rather than vague priority advice:

```bash
tw <uuid> modify priority:H +next due:friday
tw <uuid> modify wait:monday -next
tw <uuid> modify project:personal.finance
tw <uuid> modify depends:<blocking-uuid>
```

Use `priority` sparingly. Prefer `due`, `wait`, `+next`, and dependencies when those better express reality.

## Housekeeping

Housekeeping is a review workflow, not a blind cleanup. Start read-only, group candidates, then ask before broad changes.

Useful inspections:

```bash
tw rc.color=off overdue
tw rc.color=off waiting
tw rc.color=off blocked
tw rc.color=off blocking
tw rc.color=off recurring
tw rc.color=off completed end.after:today-30d
tw rc.color=off status:deleted export
```

Good housekeeping outputs:

- Stale waiting items and proposed follow-up dates.
- Overdue items to reschedule, do, or delete.
- Pending tasks with no project or vague descriptions.
- Duplicate-looking captures.
- Recurring templates that need `until:` or cadence correction.

Do not purge as housekeeping. Only propose `purge` when the user explicitly asks for permanent deletion and understands that it is local-only and irreversible in normal workflows.

## Sync

The user's Taskwarrior replicas sync against a TaskChampion sync server. After writes that the user wants visible on other devices, run `tw sync` to push changes. Sync conflicts are resolved by TaskChampion's operational transformation; the agent does not need to resolve them manually.

## After Writes

After a write, verify with a narrow read:

```bash
tw rc.color=off <uuid> information
```

Report the result and include: _Undo with `tw undo` if this was wrong. Do not run undo twice without checking, because undo is itself not reversible._

## Response Pattern

For read-only requests, answer with:

- Scope inspected.
- Key results.
- Caveats such as active context or ambiguous dates.
- Suggested next action only if useful.

For writes, answer with:

- Exact target identity (UUID).
- Exact command run, or exact command proposed if confirmation is required.
- Verification result.
- Undo command.

## Ask Before Proceeding When

- The request could match multiple tasks.
- A broad filter would mutate multiple tasks.
- The current Taskwarrior context may hide relevant tasks.
- The user gave vague dates like "last Monday morning" and a precise timestamp matters.
- The command is destructive, permanent, or hard to unwind.
