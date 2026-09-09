---
name: taskwarrior
description: Taskwarrior and Sisyphus task management. Use for `tw`, life/project task capture and updates, Today planning, commitment, blockers, deferral, recurrence, triage, housekeeping, or replica sync; exclude ordinary coding tasks unless this task system is intended.
---

# Taskwarrior

Invoke Taskwarrior as `tw`; the global `task` command belongs to go-task.
Taskwarrior is the system of record. Read [the shared contract](contract.md)
before interpreting or changing lifecycle, dates, commitment, or task creation.
It is bundled with this skill; no Sisyphus checkout is required. This workstation
contract does not establish which Sisyphus backend features are deployed.

## Workflow

1. **Discover** — Scope the requested outcomes. Read narrowly with
   `tw rc.color=off <filter> export`, `tw <uuid> information`, and
   `tw rc.color=off _projects`. Before creating, search for equivalent outcomes
   and reuse or extend an existing Task. Check `tw context` when its filters or
   add/log defaults could affect the result; do not silently change context.
   _Done when reuse versus creation is resolved for every outcome, and every
   existing target has a UUID and current relevant fields._
2. **Shape** — Give each Task one meaningful, independently finishable outcome
   with a concrete action title. Put supporting steps, links, and any missing
   completion criteria in annotations. Split only independently completable or
   independently blocked outcomes. Reuse discovered project names; introduce a
   new grouping only when the request establishes it. Ask a focused question
   when ambiguity changes the durable task shape.
   _Done when execution and completion are understandable for every Task._
3. **Classify** — Translate intent through the shared contract. Do not invent
   project, priority, deadline, daily intent, dependencies, or categorization
   tags. Capture defaults to Backlog; only `+next` is an allowed tag.
   For triage or ambiguous/broad changes, show UUID, title, current state,
   proposed field changes, and rationale before writing.
   _Done when every proposed field has a reason grounded in user intent or the
   contract, and ambiguous identities or requested outcomes are resolved._
4. **Write** — Target UUIDs; numeric IDs are temporary (use one only if the user
   just supplied or confirmed it). Use the smallest commands from the contract.
   Explicit, unambiguous single-Task requests authorize their writes. Confirm
   broad/multi-Task changes, ambiguous completion, deletion, series changes,
   import, context/config changes, or purge before proceeding.
   Use `tw add <attributes> -- "Literal description"` for capture, `tw log`
   for already-completed work, and `tw <uuid> done` for completion.
   _Done when all authorized commands have finished and their outputs are captured._
5. **Verify** — Re-read each affected UUID. Compare persisted title/project,
   lifecycle, daily intent, deadline, priority, dependencies, blocker/follow-up,
   deferral, and tags with the intended result. For creation, resolve the new
   UUID from command output or a narrow export; never assume the next ID.
   Report UUIDs, actual changes, and verification. `tw undo` reverts the most
   recent action, not an entire multi-command transition; inspect before and
   after each undo, and never suggest blindly repeating it. When cross-device
   visibility is requested, follow the sync reference and report sync separately.
   _Done when every affected Task matches intent or a concrete mismatch is
   reported, and the user knows the scope of recovery._

## Branch references

- Before creating or editing **recurrence**, read [recurrence.md](recurrence.md)
  for anchors, instances, series scope, and date caveats.
- For **reviews, housekeeping, reranking, project navigation, sync, import, or
  permanent removal**, read [operations.md](operations.md).
- Native `ready`, `next`, `waiting`, and `blocked` reports are discovery aids,
  not definitions of the Sisyphus columns. Apply [contract.md](contract.md) to
  the exported fields, including UDAs and unfinished prerequisites.
