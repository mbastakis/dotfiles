---
name: taskwarrior
description: Taskwarrior task management through `tw` and Sisyphus. Use for task capture and updates, executing tracked tasks, recurrence, reviews, housekeeping, or replica sync; exclude ordinary coding work unless tracking in this system is intended.
---

# Taskwarrior

Invoke Taskwarrior as `tw`; the global `task` command belongs to go-task.
Taskwarrior is the system of record. Read [the shared contract](contract.md)
before interpreting or changing lifecycle, dates, dependencies, or task creation.
It is bundled with this skill; no Sisyphus checkout is required. This workstation
contract does not establish which Sisyphus backend features are deployed.

## Workflow

Read-only requests use Refresh → Discover → Report; do not manufacture changes
to complete the write steps. Capture and updates follow the full workflow.

1. **Refresh** — Run `tw sync` before discovery, once per operation rather than
   before every command. Use [Sync and recovery](operations.md#sync-and-recovery)
   for failure handling or an explicit sync request. Disposable test replicas
   never sync.
   _Done when synchronization succeeded or local-only operation is identified._
2. **Discover** — Scope the requested outcomes. Read narrowly with
   `tw rc.color=off <filter> export`, `tw <uuid> information`, and
   `tw rc.color=off _projects`. Before creating, search for equivalent outcomes
   and reuse or extend an existing Task. Check `tw context` when its filters or
   add/log defaults could affect the result; do not silently change context.
   _Done when reuse versus creation is resolved for every outcome, and every
   existing target has a UUID and current relevant fields._
3. **Shape** — Give each Task one meaningful, independently finishable outcome
   with a concrete action title. Put supporting steps, links, and any missing
   completion criteria in annotations. Split only independently completable or
   independently blocked outcomes. Reuse discovered project names; introduce a
   new grouping only when the request establishes it. Ask a focused question
   when ambiguity changes the durable task shape.
   _Done when execution and completion are understandable for every Task._
4. **Classify** — Translate intent through the shared contract. Use established
   conversation context and discovered Tasks to resolve projects, stated dates,
   and actual prerequisites. Ask when plausible alternatives change the outcome;
   leave unsupported fields empty. Capture defaults to To do
   with no automatic priority or `+next`. Preserve existing tags and unrelated UDAs.
   For agent-proposed triage changes, show UUID, title, current state,
   proposed field changes, and rationale for approval before writing.
   _Done when every proposed field has a reason grounded in user intent or the
   contract, and ambiguous identities or requested outcomes are resolved._
5. **Write** — Target UUIDs; numeric IDs are temporary (use one only if the user
   just supplied or confirmed it). Use the smallest commands from the contract.
   Explicit requests authorize the specified single- or multi-Task writes;
   do not ask again solely because several Tasks are affected. Resolve ambiguous
   targets, completion, or recurrence scope first. Deletion, import, purge, and
   context/config changes require explicit intent and understood scope, not
   an inference from a request to tidy or review tasks.
   Use `tw rc.verbose=new-uuid add <attributes> -- "Literal description"`
   for capture, `tw rc.verbose=new-uuid log -- "Achieved outcome"`
   for already-completed work, and `tw <uuid> done` for completion.
   _Done when all authorized commands have finished and their outputs are captured._
6. **Verify** — Re-read each affected UUID. Compare persisted title/project,
   lifecycle, start, scheduled/due/wait dates, priority, dependencies, annotations,
   and tags with the intended result. For creation, resolve the new
   UUID from command output and re-read that UUID; never use `+LATEST` or assume
   the next ID. If identity is uncertain, resolve it before annotations or other
   follow-up writes; do not repeat capture.
   _Done when every affected Task matches intent or a concrete mismatch is recorded._
7. **Publish** — After each batch of writes, including partial success, run
   `tw sync`. Re-read affected UUIDs after successful sync to catch changed state.
   Report task titles, UUIDs, actual changes, and local verification separately
   from sync status. Follow [Sync and recovery](operations.md#sync-and-recovery)
   when either fails.
   _Done when persistence and synchronization outcomes are reported, with any
   mismatch or remaining local-only changes explicit._

## Executing tracked work

When the user asks you to execute a clearly identified tracked Task, use native
`start` when work begins and sync that transition so Sisyphus shows Doing.
Discussion, estimation, and planning alone do not change lifecycle. Follow the
contract when existing deferral or prerequisites conflict with execution.
Mark it done only after verifying its stated outcome, not merely because the
agent turn ended. If execution stops unfinished, stop activity you started and
report what remains; do not stop another actor's existing activity by inference.
Do not invent a return date for blocked work. Apply Write → Verify → Publish to
each lifecycle transition. Native start is not an exclusive claim.

## Branch references

- Before creating or editing **recurrence**, read [recurrence.md](recurrence.md)
  for anchors, instances, series scope, and date caveats.
- For **reviews, housekeeping, urgency, project navigation, sync, import, or
  permanent removal**, read [operations.md](operations.md).
- Native `ready`, `next`, `waiting`, and `blocked` reports are discovery aids,
  not definitions of the Sisyphus columns. Apply [contract.md](contract.md) to
  the exported native fields and unfinished prerequisites.
