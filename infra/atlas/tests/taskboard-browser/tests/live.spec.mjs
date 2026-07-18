import { expect, test } from "@playwright/test";

test("deployed taskboard serves a healthy read-only board", async ({ page, request }) => {
  const mutations = [];
  await page.route("**/api/**", async (route) => {
    if (route.request().method() === "GET") {
      await route.continue();
      return;
    }
    mutations.push(`${route.request().method()} ${route.request().url()}`);
    await route.abort("blockedbyclient");
  });

  const health = await request.get("/healthz");
  expect(health.ok()).toBeTruthy();
  expect(await health.text()).toBe("ok\n");

  await page.goto("/");
  await expect(page).toHaveTitle("Sisyphus");
  await expect(page.locator(".column")).toHaveCount(5);
  await expect(page.locator("#status")).not.toContainText("Loading");
  await expect(page.locator("#readinessFilter")).toBeAttached();
  await expect(page.locator("#dueFilter")).toBeAttached();
  await expect(page.locator("#focusView")).toBeAttached();
  await expect(page.locator("#sortMode")).toBeAttached();
  await expect(page.locator("#selectVisible")).toBeAttached();
  await expect(page.locator("#editDelete")).toBeAttached();
  await expect(page.locator("#board")).not.toHaveAttribute("aria-live");
  await expect(page.locator("#boardAnnouncements")).toHaveAttribute("aria-live", "polite");
  await expect(page.locator("#status")).toHaveText(/^Synced (just now|\d+m ago)$/);
  await expect(page.locator("#boardStats")).toHaveText(/^\d+ tasks · \d+ columns · Updated (just now|\d+m ago)$/);
  const visualSystem = await page.evaluate(() => ({
    bodyBackground: getComputedStyle(document.body).backgroundImage,
    cardBackground: getComputedStyle(document.querySelector(".card")).backgroundImage,
    primaryBackground: getComputedStyle(document.querySelector(".primary-button")).backgroundImage,
    fontFamily: getComputedStyle(document.body).fontFamily,
    selectAppearance: getComputedStyle(document.querySelector("#focusView")).appearance,
    selectRadius: Number.parseFloat(getComputedStyle(document.querySelector("#focusView")).borderRadius),
    supportsCustomPicker: CSS.supports("appearance", "base-select"),
  }));
  expect(visualSystem.bodyBackground).toBe("none");
  expect(visualSystem.cardBackground).toBe("none");
  expect(visualSystem.primaryBackground).toBe("none");
  expect(visualSystem.fontFamily).not.toContain("JetBrains");
  expect(visualSystem.selectRadius).toBeGreaterThanOrEqual(6);
  if (visualSystem.supportsCustomPicker) {
    expect(visualSystem.selectAppearance).toBe("base-select");
  }

  const firstColumn = page.locator(".column").first();
  const indicatorAlignment = await firstColumn.locator(".column-title-row").evaluate((row) => {
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
  await firstColumn.locator(".column-label").click();
  const collapsedGeometry = await firstColumn.evaluate((column) => {
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
  expect(collapsedGeometry.width).toBeGreaterThanOrEqual(160);
  expect(collapsedGeometry.height).toBeLessThan(80);
  expect(collapsedGeometry.writingMode).toBe("horizontal-tb");
  expect(collapsedGeometry.dividerWidth).toBe(0);
  expect(collapsedGeometry.headerBorderWidth).toBeGreaterThanOrEqual(1);
  expect(collapsedGeometry.labelFits).toBeTruthy();
  await firstColumn.locator(".column-label").click();

  const board = await page.evaluate(() => fetch("/api/board").then((response) => response.json()));
  const tasks = board.columns.flatMap((column) => column.tasks);
  for (const task of tasks) {
    expect(typeof task.blocked).toBe("boolean");
    expect(Array.isArray(task.dependency_details)).toBeTruthy();
    expect(Array.isArray(task.dependent_tasks)).toBeTruthy();
  }
  const cardCount = await page.locator(".card").count();
  if (cardCount) {
    const firstCard = page.locator(".card").first();
    await expect(firstCard).toHaveAttribute("data-uuid", /^[0-9a-f-]{36}$/i);
    await firstCard.focus();
    const focusClearance = await firstCard.evaluate((card) => {
      const cardBox = card.getBoundingClientRect();
      const headerBox = card.closest(".column").querySelector(".column-header").getBoundingClientRect();
      return cardBox.top - headerBox.bottom;
    });
    expect(focusClearance).toBeGreaterThanOrEqual(3);
    await page.locator("#selectVisible").click();
    await expect(page.locator("#bulkCount")).not.toHaveText("0 selected");
    await page.locator("#clearSelection").click();
  }
  const blockedTask = tasks.find((task) => task.blocked);
  if (blockedTask) {
    const knownDependency = blockedTask.dependency_details.find((dependency) =>
      tasks.some((task) => task.uuid === dependency.uuid));
    if (knownDependency) {
      await page.locator("#searchInput").fill(knownDependency.description);
      await expect(page.locator(`[data-uuid="${knownDependency.uuid}"]`)).toBeVisible();
      await expect(page.locator(`[data-uuid="${blockedTask.uuid}"]`)).toBeVisible();
      await page.locator("#searchInput").fill("");
    }
    await expect(page.locator(`[data-uuid="${blockedTask.uuid}"]`)).toHaveClass(/is-blocked/);
    await expect(page.locator(`[data-uuid="${blockedTask.uuid}"] .card-relationships`)).toContainText("Blocked by");
    await page.locator(`[data-uuid="${blockedTask.uuid}"]`).click();
    await expect(page).toHaveURL(new RegExp(`task=${blockedTask.uuid}`));
    await expect(page.locator("#editDependencies .is-unresolved")).toHaveCount(
      blockedTask.dependency_details.filter((dependency) => !dependency.resolved).length,
    );
    if (knownDependency) {
      await page.locator("#editDependencySearch").fill(knownDependency.uuid);
      await expect(page.locator(`[data-selected-dependency="${knownDependency.uuid}"]`)).toContainText("Added");
    }
  } else {
    const unfinished = tasks.filter((task) => task.status !== "completed");
    const current = unfinished.find((task) => !(task.depends || []).length);
    const candidate = unfinished.find((task) => task.uuid !== current?.uuid && !(task.depends || []).includes(current?.uuid));
    if (current && candidate) {
      await page.locator(`[data-uuid="${current.uuid}"]`).click();
      await page.locator("#editDependencySearch").fill(candidate.uuid);
      await page.locator(`[data-add-dependency="${candidate.uuid}"]`).click();
      await expect(page.locator("#editDependencySearch")).toHaveValue(candidate.uuid);
      await expect(page.locator(`[data-selected-dependency="${candidate.uuid}"]`)).toContainText("Added");
    }
  }
  expect(mutations).toEqual([]);
});
