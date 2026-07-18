# Sisyphus

Sisyphus is the private Kanban UI for Taskwarrior at `https://taskboard.mbastakis.com`. The deployment, hostname, Compose service, and env vars still use the `taskboard` identifier.

## Model

Taskwarrior remains the source of truth. Sisyphus is a view/controller over a local Taskwarrior replica on atlas and syncs through the existing TaskChampion server.

| Board column | Taskwarrior state |
|---|---|
| Backlog | `status:pending` without `+next`, active `start`, `+waiting`, or an unfinished dependency |
| Ready | `status:pending +next` |
| Doing | active tasks started with `task <uuid> start` |
| Waiting | `+waiting`, native waiting state, or a pending/waiting dependency |
| Done | recently completed tasks |

Drag/drop and card buttons run normal Taskwarrior commands. There is no separate board-state database.

Selecting a card opens a task detail drawer. In addition to description, project, tags, priority, and due date, the drawer exposes native Taskwarrior annotations, `wait`, `scheduled`, and `depends` fields. Date fields accept keyboard entry or open the browser's calendar from their calendar button. Dependencies use a searchable picker over unfinished board tasks while storing stable Taskwarrior UUIDs. After selection, the matching search result remains visible as an Added task card with View and Remove actions instead of disappearing from the picker. A query without an exact match can create a new Backlog task in the current project and attach it atomically; attachment failure removes the new task. Direct UUID lookup enriches dependencies outside the recent Done window: pending and waiting tasks block, completed and deleted tasks resolve, and dangling UUIDs remain visible as Missing without blocking work. Dependency and dependent names link to their task when it is in the displayed window. Recurrence and parent metadata are shown read-only so recurring internals are not accidentally changed.

Cards default to decision-critical context: project, priority, due or deferred state, unresolved blockers, and the first user tag. Compact relationship lines name the first unfinished prerequisite and the first task that a card blocks; counts indicate additional relationships, while the drawer retains the complete dependency detail. Triage exposes all secondary card metadata, while Blocked and Waiting expose additional relationship context. Unresolved dependencies give the whole card a blocked treatment. Search includes annotations, dependency and dependent names, UUIDs, and task dates in addition to the visible description, project, tags, and identifiers.

Lifecycle actions can start, stop, complete, reopen, or delete a task; reopening moves the completed task back to Backlog. Completing a task that blocks unfinished work names those tasks before confirmation. Deletion always requires confirmation and warns when it would leave unresolved dependencies. Every mutation targets a stable Taskwarrior UUID. The backend validates dependency cycles again even though the picker already removes cycle-producing candidates.

The drawer tracks its editable values. Closing it, following a task relationship, or running a lifecycle action prompts before discarding unsaved changes. A successful save closes without another prompt.

Every edit, move, delete, dependency creation, and bulk change includes the task's last observed Taskwarrior `modified` timestamp. The backend syncs and verifies all timestamps before writing. A stale edit returns a conflict instead of overwriting another replica; the drawer names remotely changed fields and requires either Reload latest or Keep my edits. Bulk changes preflight every selected task and reject the whole batch before mutation when any task is stale.

The project filter lists active projects first and recently completed projects second, with alphabetical sorting inside each group. A project remains active while any displayed task is unfinished; completed-only projects remain available while their tasks are retained in the Done column.

Search, project, tag, priority, readiness, and due-state filters persist in browser storage and are reflected in the URL with the active focus view, sort, mobile column, and open task. Reloading or sharing a URL restores that state, while Back and Forward move through filter/view changes and open task drawers. Readiness can isolate actionable tasks, unresolved blockers, or tasks deferred by a future `wait` date. Due-state filters cover overdue, today, upcoming, and undated work. Clear filters removes the saved values.

The Views panel provides Today, Ready, Blocked, Waiting, and Triage focus views. Custom named views capture the current focus, filters, and card sort order in browser storage. Sorting can use due date, Taskwarrior urgency, recent modification, recent entry, or description; it changes presentation only and never writes task state.

Each card has an explicit selection control. Select visible or individual cards, then bulk-apply project, tags, priority, due date, or board column. Bulk operations use stable UUIDs and optimistic timestamps and execute under the same Taskwarrior lock as single-task mutations.

The compact sync card shows the last successful sync, task/column counts, and board freshness. Exact attempt, success, and generation timestamps remain in hover text. Failed syncs retain the last successful timestamp and show the Taskwarrior error; data older than five minutes is marked stale. Mutations also show Saving, Saved, Conflict, Offline, or retry feedback on the affected card and in an open drawer. Connection recovery keeps failed work explicit and offers the action again instead of implying it was saved.

API requests do not follow Authentik authorization redirects as cross-origin fetches. When the browser session expires, Sisyphus preserves a dirty task drawer in session storage, performs a top-level reauthentication, and restores the draft after returning. The public manifest and app icon bypass forward-auth because they contain no task data; task HTML and APIs remain protected.

## Visual system

The interface applies Linear's documented design principles without copying its brand: dense alignment, neutral application chrome, progressive disclosure, keyboard-first interaction, and hierarchy from surface contrast rather than decoration. Catppuccin Mocha remains the palette. Crust and Mantle define the application shell, Base is the workspace, Surface colors provide controls and cards, Lavender is the interaction accent, and semantic colors are reserved for task state. The UI uses no gradients or glass effects; low-contrast borders separate surfaces, while shadows are limited to floating menus and drawers.

The board is intentionally the dominant surface. Quick capture is a compact command row, sidebar sections are flat controls, and bulk triage becomes prominent only after selection. Cards omit secondary metadata in normal views to reduce scanning cost; short UUIDs appear only on hover or keyboard focus and remain available in the task drawer. Empty columns use a quiet inline state instead of a large placeholder. Desktop column headers stay visible while their cards scroll, with enough clearance to preserve the complete first-card focus ring. Collapsed columns become self-contained horizontal summaries rather than narrow full-height columns; each retains the status, title, count, and expand control without a trailing divider. Subtle edge shadows indicate horizontal overflow without gradients. Select menus use the browser's customizable picker with the same line chevron as column controls when available and retain a styled native fallback. A single polite status region announces board actions instead of re-announcing the full board after each render. Drawer close restores the originating card, reduced-motion preferences remove animated scrolling, responsive breakpoints support browser zoom reflow, and increased-contrast/forced-color modes strengthen native borders and focus outlines. This direction follows Linear's [UI redesign](https://linear.app/now/how-we-redesigned-the-linear-ui), [board layout](https://linear.app/docs/board-layout), [display options](https://linear.app/docs/display-options), and [Peek](https://linear.app/docs/peek) documentation.

## Mobile behavior

At widths up to 1120px, the filter sidebar becomes a hamburger menu drawer so search and filters remain reachable on tablet layouts. At widths up to 860px, the board also shows one column at a time behind horizontally scrollable column tabs. Sisyphus opens the Doing column first when it contains tasks, otherwise it opens the first non-empty column.

Touch layouts disable card dragging in favor of the card Actions menu, where tasks can be edited or moved between columns. The edit form opens as a scrollable bottom sheet so its actions remain reachable on short viewports and above mobile keyboards.

Keyboard navigation uses one tab stop for the current card. `G` focuses the first visible card, `J`/`K` or vertical arrows move within a column, and `H`/`L` or horizontal arrows move between columns. Moving above the first card focuses its column header; `X` collapses or expands that column and Down returns to its first card. `Shift` plus horizontal arrows or `H`/`L` moves the task one adjacent column, while number keys `1` through `5` move it directly through Backlog, Ready, Doing, Waiting, and Done. `Enter` opens the focused task. Dependent-aware completion confirmation still applies.

While the page is visible and no edit is in progress, Sisyphus refreshes and syncs every 60 seconds. Returning to a visible tab also triggers a refresh, allowing changes from Taskchamp, the Mac replica, or an agent using the Taskwarrior CLI to appear without a manual reload.

## Deployment

Sisyphus browser access is protected by Authentik forward-auth. Apply the Authentik proxy provider/application first, then run DNS and atlas deployment:

```bash
mise exec -- task identity:authentik:apply
mise exec -- task aws:dns:apply

cd infra/atlas/ansible
HOMESERVER_ACME_EMAIL="you@example.com" \
  ../secrets/homeserver-secrets exec atlas-homeserver -- \
  ansible-playbook playbooks/atlas-homeserver.yml
```

The first atlas deploy builds the local `homeserver-taskboard:local` image from `/opt/homeserver/taskboard/app`, including Taskwarrior 3.x from the official release tarball. Later deploys rebuild when source changes. `atlas:homeserver:apply` finishes with a read-only Playwright smoke test over an SSH tunnel directly to the running container; non-GET API requests are blocked by the test.

## Verification

```bash
mise exec -- task atlas:taskboard:test
mise exec -- task atlas:taskboard:smoke:live
curl -fsS https://taskboard.mbastakis.com/healthz
curl -fsSI https://taskboard.mbastakis.com/
ssh atlas 'docker compose -f /opt/homeserver/compose.yml ps taskboard'
ssh atlas 'docker compose -f /opt/homeserver/compose.yml logs --tail=100 taskboard'
```

`/healthz` intentionally bypasses Authentik so Homepage can monitor it without task access. Unauthenticated browser/API requests should be redirected into the Authentik outpost flow.

`atlas:taskboard:test` first starts Sisyphus against an isolated temporary Taskwarrior database and exercises create, stale-edit rejection, inline dependency creation, bulk update, move, and delete through HTTP. It then runs deterministic mocked browser regressions for URL/history restoration, filters, views, sorting, relationships, per-task mutation feedback, conflicts, bulk triage, inline dependencies, keyboard movement, focus restoration, reduced motion, forced colors, high-zoom reflow, sync failures, deletion warnings, and mobile layout. The locked browser environment lives under `infra/atlas/tests/taskboard-browser/`; `atlas:taskboard:browser:sync` installs its npm dependencies and Chromium. The deployed smoke remains read-only.

## Operations

Sisyphus runtime paths on atlas:

| Path | Purpose |
|---|---|
| `/opt/homeserver/taskboard/app` | Ansible-copied app source, Dockerfile, and static UI assets |
| `/opt/homeserver/taskboard/config` | Generated Taskwarrior config inside the container mount |
| `/opt/homeserver/taskboard/data` | Local Taskwarrior/TaskChampion replica cache |
| `/opt/homeserver/env/taskboard.env` | Root-only environment file with sync settings and `TASKBOARD_ALLOW_NO_AUTH=1`; Traefik/Authentik enforce browser auth |

The container entrypoint remains `taskboard.py`. Adjacent modules separate HTTP routing, Taskwarrior execution and sync state, board projection, validation, and UUID-targeted mutations so those concerns can be tested independently.

Manual sync check:

```bash
ssh atlas 'sudo docker compose -f /opt/homeserver/compose.yml exec taskboard task sync'
```

The durable task history is still the TaskChampion sync server and its existing SQLite backup path. The Sisyphus data directory is useful cache/state but should be recoverable by recreating the container and syncing again.
