import { expect, test } from "@playwright/test";

import { makeBoard, mockApi, openBoard, UUIDS } from "./fixture.mjs";

test("persists readiness and due filters", async ({ page }) => {
  await mockApi(page);
  await openBoard(page);

  await expect(page.locator("#status")).toHaveText("Synced just now");
  await expect(page.locator("#boardStats")).toHaveText("6 tasks · 5 columns · Updated just now");

  await page.locator("#readinessFilter").selectOption("blocked");
  await expect(page.locator(`[data-uuid="${UUIDS.blocked}"]`)).toBeVisible();
  await expect(page.locator(`[data-uuid="${UUIDS.backlog}"]`)).toHaveCount(0);

  await page.locator("#readinessFilter").selectOption("");
  await page.locator("#dueFilter").selectOption("today");
  await expect(page.locator(`[data-uuid="${UUIDS.backlog}"]`)).toBeVisible();
  await expect(page.locator(`[data-uuid="${UUIDS.ready}"]`)).toHaveCount(0);

  await page.locator("#projectFilter").selectOption("work.release");
  await page.locator("#tagFilter").selectOption("release");
  await page.reload();
  await expect(page.locator("#dueFilter")).toHaveValue("today");
  await expect(page.locator("#projectFilter")).toHaveValue("work.release");
  await expect(page.locator("#tagFilter")).toHaveValue("release");

  await page.locator("#clearFilters").click();
  await expect(page.locator(".card")).toHaveCount(6);
  await expect.poll(() => page.evaluate(() => localStorage.getItem("sisyphus.filters"))).toBeNull();
});

test("navigates dependency relationships and protects dirty edits", async ({ page }) => {
  await mockApi(page);
  await openBoard(page);

  await page.locator(`[data-uuid="${UUIDS.blocked}"]`).click();
  await expect(page.locator(`[data-uuid="${UUIDS.blocked}"] .card-relationships`)).toContainText("Blocked by Approve the deployment window");
  await expect(page.locator("#editDependencies .is-unresolved")).toContainText("Approve the deployment window");
  await expect(page.locator("#editDependencies .is-resolved")).toContainText("Create deployment checklist");
  await page.locator(`[data-open-task="${UUIDS.backlog}"]`).click();
  await expect(page.locator("#editDescription")).toHaveValue("Approve the deployment window");
  await expect(page.locator("#editDependents")).toContainText("Deploy the release");

  await page.locator("#editDescription").fill("Changed but not saved");
  await expect(page.locator("#editDirty")).toBeVisible();
  page.once("dialog", async (dialog) => dialog.dismiss());
  await page.locator("#closeEdit").click();
  await expect(page.locator("#editDialog")).toBeVisible();
  await expect(page.locator("#editDescription")).toHaveValue("Changed but not saved");

  page.once("dialog", async (dialog) => dialog.accept());
  await page.locator("#closeEdit").click();
  await expect(page.locator("#editDialog")).not.toBeVisible();
  await expect(page.locator(`[data-uuid="${UUIDS.blocked}"]`)).toBeFocused();

  await page.locator(`[data-uuid="${UUIDS.blocked}"]`).click();
  await page.locator("#editDependencySearch").fill(UUIDS.ready);
  await page.locator("#editDependencySearch").press("Enter");
  await expect(page.locator("#editDepends")).toHaveValue(new RegExp(UUIDS.ready));
  await expect(page.locator("#editDependencySearch")).toHaveValue(UUIDS.ready);
  await expect(page.locator(`[data-selected-dependency="${UUIDS.ready}"]`)).toContainText("Added");
  await expect(page.locator(`[data-selected-dependency="${UUIDS.ready}"]`)).toContainText("Prepare release notes");
  await expect(page.locator("#editDirty")).toBeVisible();
  await page.locator("#editDependencySearch").fill("temporary query");
  await page.locator("#editDependencySearch").press("Escape");
  await expect(page.locator("#editDependencySearch")).toHaveValue("");
});

test("surfaces dangling dependencies without treating them as blockers", async ({ page }) => {
  const board = makeBoard();
  const ready = board.columns.flatMap((column) => column.tasks)
    .find((task) => task.uuid === UUIDS.ready);
  const missingUuid = "99999999-9999-4999-8999-999999999999";
  ready.depends = [missingUuid];
  ready.dependency_details = [{
    uuid: missingUuid,
    description: missingUuid,
    project: "",
    status: "missing",
    blocking: false,
    resolved: false,
  }];
  ready.blocked = false;
  await mockApi(page, { board });
  await openBoard(page);

  await page.locator("#readinessFilter").selectOption("ready");
  await expect(page.locator(`[data-uuid="${UUIDS.ready}"]`)).toBeVisible();
  await page.locator(`[data-uuid="${UUIDS.ready}"]`).click();
  await expect(page.locator("#editDependencies .is-missing")).toContainText(missingUuid);
  await expect(page.locator("#editDependencies .dependency-state.missing")).toHaveText("Missing");
});

test("supports keyboard navigation and guarded triage", async ({ page }) => {
  const mutations = [];
  await mockApi(page, { onMutation: (mutation) => mutations.push(mutation) });
  await openBoard(page);

  await page.keyboard.press("g");
  await expect(page.locator(`[data-uuid="${UUIDS.backlog}"]`)).toBeFocused();
  await page.keyboard.press("j");
  await expect(page.locator(`[data-uuid="${UUIDS.long}"]`)).toBeFocused();
  await page.keyboard.press("l");
  await expect(page.locator(`[data-uuid="${UUIDS.ready}"]`)).toBeFocused();
  await page.keyboard.press("ArrowUp");
  await expect(page.locator('[data-column-toggle="ready"]')).toBeFocused();
  await page.keyboard.press("x");
  await expect(page.locator(".column-ready")).toHaveClass(/is-collapsed/);
  await expect(page.locator('[data-column-toggle="ready"]')).toBeFocused();
  await page.keyboard.press("x");
  await page.keyboard.press("ArrowDown");
  await expect(page.locator(`[data-uuid="${UUIDS.ready}"]`)).toBeFocused();
  await page.keyboard.press("Shift+ArrowRight");
  await expect.poll(() => mutations.some((mutation) => mutation.path.endsWith(`${UUIDS.ready}/move`) && mutation.body.column === "doing")).toBeTruthy();
  await page.keyboard.press("Enter");
  await expect(page.locator("#editDialog")).toBeVisible();
  await expect(page).toHaveURL(new RegExp(`task=${UUIDS.ready}`));
  await page.locator("#closeEdit").click();
  await expect(page.locator(`[data-uuid="${UUIDS.ready}"]`)).toBeFocused();
  await page.keyboard.press("4");
  await expect.poll(() => mutations.some((mutation) => mutation.path.endsWith(`${UUIDS.ready}/move`) && mutation.body.column === "waiting")).toBeTruthy();

  await page.locator(`[data-uuid="${UUIDS.backlog}"]`).focus();
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Deploy the release");
    await dialog.dismiss();
  });
  await page.keyboard.press("5");
  expect(mutations.some((mutation) => mutation.path.endsWith(`${UUIDS.backlog}/move`))).toBeFalsy();
});

test("restores views, filters, search, and open tasks from the URL", async ({ page }) => {
  await mockApi(page);
  const query = new URLSearchParams({
    view: "blocked",
    q: "Deploy",
    project: "work.release",
    sort: "description",
    column: "waiting",
    task: UUIDS.blocked,
  });
  await page.goto(`/?${query}`);
  await page.locator(".card:visible").first().waitFor();

  await expect(page.locator("#focusView")).toHaveValue("blocked");
  await expect(page.locator("#searchInput")).toHaveValue("Deploy");
  await expect(page.locator("#projectFilter")).toHaveValue("work.release");
  await expect(page.locator("#sortMode")).toHaveValue("description");
  await expect(page.locator("#editDialog")).toBeVisible();

  await page.locator("#closeEdit").click();
  await expect(page).not.toHaveURL(/task=/);
  await page.reload();
  await expect(page.locator("#searchInput")).toHaveValue("Deploy");
  await expect(page.locator("#editDialog")).toBeHidden();

  await page.locator("#clearFilters").click();
  await expect(page.locator("#focusView")).toHaveValue("");
  await page.goBack();
  await expect(page.locator("#focusView")).toHaveValue("blocked");
  await expect(page.locator("#searchInput")).toHaveValue("Deploy");

  await page.locator(`[data-uuid="${UUIDS.blocked}"]`).click();
  await expect(page.locator("#editDialog")).toBeVisible();
  await page.goBack();
  await expect(page.locator("#editDialog")).toBeHidden();
  await page.goForward();
  await expect(page.locator("#editDescription")).toHaveValue("Deploy the release");
});

test("supports focus views, saved views, and persistent sorting", async ({ page }) => {
  const board = makeBoard();
  const longTask = board.columns.flatMap((column) => column.tasks)
    .find((task) => task.uuid === UUIDS.long);
  longTask.urgency = 25;
  await mockApi(page, { board });
  await openBoard(page);

  await page.locator("#focusView").selectOption("today");
  await expect(page.locator(`[data-uuid="${UUIDS.backlog}"]`)).toBeVisible();
  await expect(page.locator(`[data-uuid="${UUIDS.doing}"]`)).toBeVisible();
  await expect(page.locator(`[data-uuid="${UUIDS.ready}"]`)).toHaveCount(0);

  await page.locator("#focusView").selectOption("blocked");
  page.once("dialog", async (dialog) => dialog.accept("Release risks"));
  await page.locator("#saveView").click();
  await expect(page.locator("#focusView")).toHaveValue(/^custom:/);
  await page.reload();
  await expect(page.locator("#focusView")).toHaveValue(/^custom:/);
  await expect(page.locator(`[data-uuid="${UUIDS.blocked}"]`)).toBeVisible();
  await expect(page.locator(`[data-uuid="${UUIDS.backlog}"]`)).toHaveCount(0);

  await page.locator("#clearFilters").click();
  await page.locator("#sortMode").selectOption("urgency");
  await expect(page.locator(".column-backlog .card").first()).toHaveAttribute("data-uuid", UUIDS.long);
  await page.reload();
  await expect(page.locator("#sortMode")).toHaveValue("urgency");
  await expect(page.locator(".column-backlog .card").first()).toHaveAttribute("data-uuid", UUIDS.long);
});

test("uses flat surfaces and progressively reveals card metadata", async ({ page }) => {
  await mockApi(page, { board: makeBoard() });
  await openBoard(page);

  await expect(page.locator(".card .secondary-meta").first()).toBeHidden();
  const visualSystem = await page.evaluate(() => ({
    bodyBackground: getComputedStyle(document.body).backgroundImage,
    cardBackground: getComputedStyle(document.querySelector(".card")).backgroundImage,
    primaryBackground: getComputedStyle(document.querySelector(".primary-button")).backgroundImage,
    fontFamily: getComputedStyle(document.body).fontFamily,
  }));
  expect(visualSystem.bodyBackground).toBe("none");
  expect(visualSystem.cardBackground).toBe("none");
  expect(visualSystem.primaryBackground).toBe("none");
  expect(visualSystem.fontFamily).not.toContain("JetBrains");

  await page.locator("#focusView").selectOption("triage");
  await expect(page.locator('.board[data-view="triage"] .secondary-meta').first()).toBeVisible();
});

test("keeps board controls compact and progressively discloses chrome", async ({ page }) => {
  const board = makeBoard();
  const backlog = board.columns.find((column) => column.id === "backlog");
  const template = backlog.tasks[0];
  for (let index = 0; index < 12; index += 1) {
    backlog.tasks.push({
      ...structuredClone(template),
      uuid: `70000000-0000-4000-8000-${String(index).padStart(12, "0")}`,
      description: `Additional backlog task ${index + 1}`,
    });
  }
  board.columns.find((column) => column.id === "waiting").tasks = [];
  await mockApi(page, { board });
  await openBoard(page);

  const selectStyle = await page.locator("#focusView").evaluate((select) => ({
    appearance: getComputedStyle(select).appearance,
    pickerIcon: getComputedStyle(select, "::picker-icon").backgroundImage,
    radius: Number.parseFloat(getComputedStyle(select).borderRadius),
    supportsCustomPicker: CSS.supports("appearance", "base-select"),
  }));
  expect(selectStyle.radius).toBeGreaterThanOrEqual(6);
  if (selectStyle.supportsCustomPicker) {
    expect(selectStyle.appearance).toBe("base-select");
    expect(selectStyle.pickerIcon).toContain("url(");
  }

  const emptyState = page.locator(".column-waiting .empty-state");
  await expect(emptyState).toHaveCSS("border-top-width", "0px");
  await expect(emptyState).toHaveCSS("text-align", "start");

  const card = page.locator(`[data-uuid="${UUIDS.backlog}"]`);
  const cardUuid = card.locator(".card-uuid");
  const headerHeight = await card.locator(".card-header").evaluate((header) => header.getBoundingClientRect().height);
  await expect(cardUuid).toHaveCSS("opacity", "0");
  await card.focus();
  const focusClearance = await card.evaluate((element) => {
    const cardBox = element.getBoundingClientRect();
    const headerBox = element.closest(".column").querySelector(".column-header").getBoundingClientRect();
    return cardBox.top - headerBox.bottom;
  });
  expect(focusClearance).toBeGreaterThanOrEqual(3);
  await card.hover();
  await expect(cardUuid).toHaveCSS("opacity", "1");
  expect(await card.locator(".card-header").evaluate((header) => header.getBoundingClientRect().height)).toBe(headerHeight);

  const boardElement = page.locator("#board");
  await expect(boardElement).toHaveClass(/can-scroll-right/);
  await boardElement.evaluate((element) => element.scrollTo({ left: element.scrollWidth }));
  await expect(boardElement).toHaveClass(/can-scroll-left/);
  await expect(boardElement).not.toHaveClass(/can-scroll-right/);
  await boardElement.evaluate((element) => element.scrollTo({ left: 0, top: 200 }));
  await expect.poll(() => boardElement.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
  const stickyOffset = await page.locator(".column-backlog .column-header").evaluate((header) => {
    const boardBox = header.closest(".board").getBoundingClientRect();
    return Math.abs(header.getBoundingClientRect().top - boardBox.top);
  });
  expect(stickyOffset).toBeLessThanOrEqual(1);

  const indicatorAlignment = await page.locator(".column-doing .column-title-row").evaluate((row) => {
    const status = row.querySelector(".column-status").getBoundingClientRect();
    const toggle = row.querySelector(".column-toggle").getBoundingClientRect();
    return {
      centerOffset: Math.abs((status.top + status.height / 2) - (toggle.top + toggle.height / 2)),
      gap: toggle.left - status.right,
    };
  });
  expect(indicatorAlignment.centerOffset).toBeLessThanOrEqual(1);
  expect(indicatorAlignment.gap).toBeGreaterThanOrEqual(4);
  expect(indicatorAlignment.gap).toBeLessThanOrEqual(8);

  const titleControl = page.locator('.column-doing [data-column-toggle="doing"]');
  await expect(titleControl).toHaveCSS("min-height", "32px");
  await titleControl.locator(".column-label").click();
  const collapsedColumn = page.locator(".column-doing");
  await expect(collapsedColumn).toHaveClass(/is-collapsed/);
  const geometry = await collapsedColumn.evaluate((column) => {
    const box = column.getBoundingClientRect();
    return {
      width: box.width,
      height: box.height,
      writingMode: getComputedStyle(column.querySelector(".column-label")).writingMode,
      dividerWidth: Number.parseFloat(getComputedStyle(column).borderRightWidth),
      headerBorderWidth: Number.parseFloat(getComputedStyle(column.querySelector(".column-header")).borderTopWidth),
      labelFits: column.querySelector(".column-label").scrollWidth <= column.querySelector(".column-label").clientWidth,
    };
  });
  expect(geometry.width).toBeGreaterThanOrEqual(160);
  expect(geometry.height).toBeLessThan(80);
  expect(geometry.writingMode).toBe("horizontal-tb");
  expect(geometry.dividerWidth).toBe(0);
  expect(geometry.headerBorderWidth).toBeGreaterThanOrEqual(1);
  expect(geometry.labelFits).toBeTruthy();
});

test("bulk triages selected cards with stable versions", async ({ page }) => {
  const mutations = [];
  await mockApi(page, { onMutation: (mutation) => mutations.push(mutation) });
  await openBoard(page);

  await page.locator(`[data-select-task="${UUIDS.ready}"]`).click();
  await page.locator(`[data-select-task="${UUIDS.doing}"]`).click();
  await expect(page.locator("#bulkCount")).toHaveText("2 selected");
  await page.locator("#bulkProject").fill("work.launch");
  await page.locator("#bulkTags").fill("release, reviewed");
  await page.locator("#bulkPriority").selectOption("H");
  await page.locator("#bulkDueEnabled").check();
  await page.locator("#bulkDue").fill("2026-07-20");
  await page.locator("#bulkColumn").selectOption("waiting");
  await page.locator("#bulkForm button[type=submit]").click();

  await expect.poll(() => mutations.find((mutation) => mutation.path === "/api/tasks/bulk")).toBeTruthy();
  const bulk = mutations.find((mutation) => mutation.path === "/api/tasks/bulk");
  expect(bulk.body.changes).toEqual({
    project: "work.launch",
    tags: "release, reviewed",
    priority: "H",
    due: "2026-07-20",
    column: "waiting",
  });
  expect(bulk.body.tasks).toEqual(expect.arrayContaining([
    expect.objectContaining({ uuid: UUIDS.ready, expected_modified: expect.any(String) }),
    expect.objectContaining({ uuid: UUIDS.doing, expected_modified: expect.any(String) }),
  ]));
  await expect(page.locator("#bulkForm")).toBeHidden();
});

test("creates and attaches a dependency without closing edits", async ({ page }) => {
  const board = makeBoard();
  const createdUuid = "77777777-7777-4777-8777-777777777777";
  const updatedBoard = structuredClone(board);
  const tasks = updatedBoard.columns.flatMap((column) => column.tasks);
  const parent = tasks.find((task) => task.uuid === UUIDS.blocked);
  const template = tasks.find((task) => task.uuid === UUIDS.ready);
  const createdTask = {
    ...structuredClone(template),
    uuid: createdUuid,
    description: "Collect security approval",
    project: parent.project,
    tags: [],
    modified: "20260713T080000Z",
  };
  parent.depends.push(createdUuid);
  parent.dependency_details.push({
    uuid: createdUuid,
    description: createdTask.description,
    project: createdTask.project,
    status: "pending",
    blocking: true,
    resolved: false,
  });
  parent.modified = "20260713T080001Z";
  updatedBoard.columns.find((column) => column.id === "backlog").tasks.push(createdTask);

  await mockApi(page, {
    board,
    onMutation: (mutation) => mutation.path.endsWith("/dependencies")
      ? { body: { board: updatedBoard, created_uuid: createdUuid } }
      : undefined,
  });
  await openBoard(page);
  await page.locator(`[data-uuid="${UUIDS.blocked}"]`).click();
  await page.locator("#editDescription").fill("Deploy after all approvals");
  await page.locator("#editDependencySearch").fill("Collect security approval");
  await expect(page.locator("[data-create-dependency]")).toContainText("Create");
  await page.locator("[data-create-dependency]").click();

  await expect(page.locator("#editDialog")).toBeVisible();
  await expect(page.locator("#editDescription")).toHaveValue("Deploy after all approvals");
  await expect(page.locator(`#editDependencies [data-open-task="${createdUuid}"]`)).toContainText("Collect security approval");
  await expect(page.locator(`[data-selected-dependency="${createdUuid}"]`)).toContainText("Added");
  await expect(page.locator("#editDirty")).toBeVisible();
});

test("shows remote changes and requires an explicit conflict choice", async ({ page }) => {
  const board = makeBoard();
  const ready = board.columns.flatMap((column) => column.tasks)
    .find((task) => task.uuid === UUIDS.ready);
  const patches = [];
  const current = { ...structuredClone(ready), description: "Remote release notes", modified: "20260713T090000Z" };
  await mockApi(page, {
    board,
    onMutation: (mutation) => {
      if (mutation.method !== "PATCH") return undefined;
      patches.push(mutation);
      return patches.length === 1
        ? { status: 409, body: { error: "changed elsewhere", current_task: current } }
        : { body: board };
    },
  });
  await openBoard(page);
  await page.locator(`[data-uuid="${UUIDS.ready}"]`).click();
  await page.locator("#editDescription").fill("Local release notes");
  await page.locator("#editForm button[type=submit]").click();

  await expect(page.locator("#editConflict")).toBeVisible();
  await expect(page.locator("#editSync")).toHaveText("Conflict");
  await expect(page.locator("#editConflictFields")).toContainText("Remote release notes");
  await page.locator("#keepConflictEdits").click();
  await expect(page.locator("#editConflict")).toBeHidden();
  await page.locator("#editForm button[type=submit]").click();
  await expect(page.locator("#editDialog")).toBeHidden();
  expect(patches[0].body.expected_modified).toBe(ready.modified);
  expect(patches[1].body.expected_modified).toBe(current.modified);
});

test("shows per-task saving, saved, offline, and retry feedback", async ({ page, context }) => {
  let releaseMutation;
  let mutationCount = 0;
  await mockApi(page, {
    onMutation: async () => {
      mutationCount += 1;
      if (mutationCount === 1) {
        await new Promise((resolve) => { releaseMutation = resolve; });
      }
      if (mutationCount === 2) return { status: 503, body: { error: "connection unavailable" } };
      return { body: makeBoard() };
    },
  });
  await openBoard(page);

  const readyCard = page.locator(`[data-uuid="${UUIDS.ready}"]`);
  await readyCard.focus();
  await page.keyboard.press("Shift+ArrowRight");
  await expect(readyCard.locator(".task-sync")).toHaveText("Saving...");
  await expect(page.locator("#boardAnnouncements")).toContainText("Moving to Doing");
  releaseMutation();
  await expect(readyCard.locator(".task-sync")).toHaveText("Saved");

  await context.setOffline(true);
  const doingCard = page.locator(`[data-uuid="${UUIDS.doing}"]`);
  await doingCard.focus();
  await page.keyboard.press("Shift+ArrowRight");
  await expect(doingCard.locator(".task-sync")).toHaveText("Offline; retry");
  await context.setOffline(false);
  await expect(doingCard.locator(".task-sync")).toHaveText("Not saved; retry");
  await doingCard.locator("[data-retry-task]").click();
  await expect(doingCard.locator(".task-sync")).toHaveText("Saved");
});

test("warns before deleting a blocker", async ({ page }) => {
  const mutations = [];
  await mockApi(page, { onMutation: (mutation) => mutations.push(mutation) });
  await openBoard(page);
  await page.locator(`[data-uuid="${UUIDS.backlog}"]`).click();

  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Approve the deployment window");
    expect(dialog.message()).toContain("Deploy the release");
    expect(dialog.message()).toContain("unresolved");
    await dialog.dismiss();
  });
  await page.locator("#editDelete").click();
  expect(mutations).toHaveLength(0);

  page.once("dialog", async (dialog) => dialog.accept());
  await page.locator("#editDelete").click();
  await expect.poll(() => mutations.some((mutation) => mutation.method === "DELETE" && mutation.path.endsWith(UUIDS.backlog))).toBeTruthy();
  await expect(page.locator("#editDialog")).not.toBeVisible();
});

test("reports sync failure and recovery", async ({ page }) => {
  const failedBoard = makeBoard({
    last_sync_attempt_at: new Date(Date.now() - 10 * 60_000).toISOString(),
    last_sync_at: new Date(Date.now() - 20 * 60_000).toISOString(),
    last_sync_error: "TaskChampion unavailable",
  });
  const healthyBoard = makeBoard();
  await mockApi(page, {
    board: failedBoard,
    syncResponses: [
      { status: 502, error: "sync command timed out" },
      { board: healthyBoard },
    ],
  });
  await openBoard(page);

  await expect(page.locator("#status")).toContainText("Sync failed");
  await expect(page.locator("#boardStats")).toContainText("Last success");
  await expect(page.locator(".sync-card")).toHaveClass(/stale/);
  await page.locator("#syncButton").click();
  await expect(page.locator("#status")).toContainText("Request failed: sync command timed out");
  await page.locator("#syncButton").click();
  await expect(page.locator("#status")).toContainText("Synced");
  await expect(page.locator("#boardStats")).toContainText("Updated");
  await expect(page.locator(".sync-card")).not.toHaveClass(/error|stale/);
});

test("reauthenticates after an auth redirect and restores unsaved edits", async ({ page }) => {
  const board = makeBoard();
  let patchAttempts = 0;
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === "/api/board" && request.method() === "GET") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(board) });
      return;
    }
    if (request.method() === "PATCH") {
      patchAttempts += 1;
      await route.fulfill({ status: 302, headers: { Location: "/" }, body: "" });
      return;
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(board) });
  });
  await openBoard(page);
  await page.locator(`[data-uuid="${UUIDS.ready}"]`).click();
  await page.locator("#editDescription").fill("Unsaved notes survive login");
  await page.locator("#editForm button[type=submit]").click();

  await expect.poll(() => patchAttempts).toBe(1);
  await expect(page.locator("#editDialog")).toBeVisible();
  await expect(page.locator("#editDescription")).toHaveValue("Unsaved notes survive login");
  await expect(page.locator("#editDirty")).toBeVisible();
  await expect.poll(() => page.evaluate(() => sessionStorage.getItem("sisyphus.reauthDraft"))).toBeNull();
});

test("keeps mobile board and drawer within the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page);
  await openBoard(page);

  await expect(page.locator(".column:visible")).toHaveCount(1);
  await expect(page.locator(".card:visible").first()).toHaveAttribute("draggable", "false");
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy();

  await page.locator(`[data-column-tab="backlog"]`).click();
  await page.locator(`[data-uuid="${UUIDS.long}"]`).click();
  await expect(page.locator("#editDialog")).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy();
  const dialogBox = await page.locator("#editDialog").boundingBox();
  expect(dialogBox.x).toBeGreaterThanOrEqual(0);
  expect(dialogBox.x + dialogBox.width).toBeLessThanOrEqual(390);
});

test("supports reduced motion, forced colors, and high-zoom reflow", async ({ page }) => {
  await page.setViewportSize({ width: 640, height: 720 });
  await page.emulateMedia({ reducedMotion: "reduce", forcedColors: "active" });
  await mockApi(page);
  await openBoard(page);

  await expect(page.locator("#board")).not.toHaveAttribute("aria-live");
  await expect(page.locator("#boardAnnouncements")).toHaveAttribute("aria-live", "polite");
  await expect(page.locator(".column:visible")).toHaveCount(1);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy();
  const accessibilityStyles = await page.locator(".card:visible").first().evaluate((card) => ({
    borderWidth: Number.parseFloat(getComputedStyle(card).borderTopWidth),
    transitionDuration: getComputedStyle(card).transitionDuration,
  }));
  expect(accessibilityStyles.borderWidth).toBeGreaterThanOrEqual(1);
  expect(Math.max(...accessibilityStyles.transitionDuration.split(",").map(Number.parseFloat))).toBeLessThanOrEqual(0.00001);

  await page.locator(`[data-column-tab="backlog"]`).click();
  await page.locator(`[data-uuid="${UUIDS.long}"]`).click();
  const dialogBox = await page.locator("#editDialog").boundingBox();
  expect(dialogBox.x).toBeGreaterThanOrEqual(0);
  expect(dialogBox.x + dialogBox.width).toBeLessThanOrEqual(640);
});
