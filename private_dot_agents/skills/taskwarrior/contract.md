# Shared Taskwarrior / Sisyphus contract

This is the deployed agent contract for the accepted product direction in
Sisyphus ADRs 0005–0010. It defines task meaning and CLI writes, not backend
deployment status. Workstation UDA declarations live in `~/.config/task/taskrc`;
the container owns its own configuration. Do not require an app checkout at runtime.

## Canonical fields

| Field | Meaning |
|---|---|
| `due` | A real finish-by deadline; never planning, follow-up, or an urgency trick. |
| `wait` | Intentional deferral until a return date; never an external blocker. |
| `start` | Work in progress, set/cleared with native `start`/`stop`. |
| `depends` | Actual prerequisite Tasks, not preferred ordering. |
| `+next` | Commitment; the only permitted tag. |
| `sisyphus_plan` (date UDA) | Deliberately planned local calendar day. |
| `sisyphus_blocker` (string UDA) | Current external condition preventing progress. |
| `sisyphus_followup` (date UDA) | Date to review a blocker; never automatic unblocking. |

Native `scheduled` means the date after which work can be accomplished; it is
not daily intent. Preserve unrelated fields and existing provenance UDAs.
Do not guess whether old `due` or `wait` values once meant planning or blocking.
Migration requires explicit interpretation; do not rewrite existing Tasks en masse.

## Lifecycle and Today

- **Backlog:** retained but uncommitted work. Actionability, priority, or a
  deadline alone does not commit it. A prerequisite on a Backlog Task does not
  implicitly commit that Task or its prerequisite. Uncommitted blocked work stays
  Backlog; recording or resolving blocking facts never creates commitment.
- **Ready:** a small committed (`+next`), unstarted, non-deferred pool with no
  current external blocker or unfinished prerequisite. Commitment has no weekly expiry.
- **Doing:** started work. Keep it small (ideally one main Task; about three is
  a soft limit). Lunch and overnight pauses do not require stopping. Native
  `start` implies existing commitment even when an external client omitted
  `+next`; prior start overrides the missing tag when preserving commitment.
- **Waiting:** committed work blocked by an external condition or unfinished
  prerequisite. A blocker wins projection over Doing even if a stale `start`
  remains. Stop execution when it becomes blocked, preserving its commitment.
- **Done:** the Task's outcome has been achieved; abandonment is not completion.
- **Deferred:** a future `wait` hides work from normal actionable views, including
  Waiting. Preserve commitment and blocker information underneath the deferral.
  Native `+WAITING` describes deferral, not the Sisyphus Waiting column.

Today includes **all Doing**, including work started on earlier days without a
plan; **Chosen for today** contains Ready Tasks whose plan is today's local day.
Keep deadline attention distinct from daily selection. Due blocker follow-ups
need review with the condition visible; they do not clear it. Done-today history
and the remaining Ready pool can be shown separately without inventing Task state.

An old plan stays stored for unfinished-plan review, never silently rolls into
today. Offer selecting today or clearing the plan; either preserves commitment.
A blocked planned Task belongs in Waiting, not Chosen for today; retain its plan
as review context unless the user clears it or defers the Task.

## Writes and postconditions

Examples use a discovered `<uuid>` and resolved dates in the configured Sisyphus
**server timezone**. Resolve relative dates before writing. Date-only deadlines
use server-local end-of-day (`due:YYYY-MM-DDT23:59:59`); date-only plans,
follow-ups, and deferrals use server-local midnight (`YYYY-MM-DDT00:00:00`).
Preserve explicit instants instead of normalizing them to a day boundary.
If the server timezone is unknown or differs from the client's, establish the
intended timezone before writing; never invent one or substitute UTC midnight.
Run the CLI with that established timezone (for example `TZ=<server-zone> tw ...`)
or convert to the exact equivalent UTC instant. Exports use UTC timestamps:
verify the intended server-local date/time and any explicit instant after writing.

| Intent | Native commands / postcondition |
|---|---|
| Capture possible work | `tw add -- "Concrete outcome"`; Backlog, no invented attributes. |
| Commit next | `tw <uuid> modify +next`; Ready only if unblocked and not deferred. |
| Work on it today | For an unblocked, non-deferred Task: `tw <uuid> modify +next sisyphus_plan:YYYY-MM-DDT00:00:00`; no deadline change or start. |
| Begin execution | For available work: `tw <uuid> modify +next`, then `tw <uuid> start`; planning is not required. |
| Shelve unblocked Doing | Preserve explicit or start-inferred commitment, then `tw <uuid> stop`; return to Ready. |
| Record external blocker | Preserve explicit or start-inferred commitment as described below, then stop if started; `tw <uuid> modify "sisyphus_blocker:Specific condition"`. Optionally set `sisyphus_followup:YYYY-MM-DDT00:00:00`. An annotation may add context but is not the current condition field. |
| Record prerequisite | Preserve explicit or start-inferred commitment, then stop if started; `tw <uuid> modify depends:<prerequisite-uuid>`; preserve existing prerequisites. |
| Explicit move to Waiting / commit blocked work | Record the actual condition or prerequisite as above and `tw <uuid> modify +next`; this explicit commitment request authorizes adding `+next`. |
| Condition resolved | Preserve explicit or start-inferred commitment, then stop if started; `tw <uuid> modify sisyphus_blocker: sisyphus_followup:`; preserve dependencies and deferral; never auto-start. Committed work returns to Ready only when no other blocker or deferral remains; uncommitted work stays Backlog. |
| Review still blocked | Keep the condition; set the next follow-up if agreed. Passing a review date changes no blocker or dependency. |
| Defer | Preserve explicit or start-inferred commitment, then stop if started; `tw <uuid> modify sisyphus_plan: wait:YYYY-MM-DDT00:00:00`; retain blocker, follow-up, and prerequisites. |
| Clear daily selection | `tw <uuid> modify sisyphus_plan:`; commitment unchanged. |
| Withdraw commitment | Stop if started; `tw <uuid> modify -next sisyphus_plan:`; retain genuine blocker/prerequisite/deferral facts. |

Do not silently clear a blocker, dependency, or future deferral to satisfy a
start/Today request; resolve conflicting intent first. Verify multi-command
transitions in full, including any partial failure. Before a factual block,
resolve, or defer transition stops execution, capture the prior `start` and
`+next`. Existing commitment means **prior `start` OR prior `+next`**: preserve
the tag if present, or materialize it with `tw <uuid> modify +next` before stopping
when prior `start` exists without the tag. This preserves inferred commitment;
it does not create a new commitment. If neither existed, never add `+next`
unless the user explicitly requested commitment. Verify the resulting tag
against that prior-state rule and verify `start` is cleared where stopping is
required. A remaining blocker still wins projection over Doing; resolving one
condition does not override another blocker or deferral.

When deferral expires, normal visibility resumes in the preserved state:
Backlog if uncommitted, Ready if committed and unblocked, Waiting if committed
and still blocked. Expiry neither starts work nor creates a daily plan. Native
Taskwarrior may retain a past `wait` field; compare its time rather than treating
any nonempty `wait` as an active deferral. Unfinished dependency resolution comes
from prerequisite state; clearing an external condition never removes that graph.
