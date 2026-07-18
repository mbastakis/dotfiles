export const UUIDS = {
  backlog: "11111111-1111-4111-8111-111111111111",
  ready: "22222222-2222-4222-8222-222222222222",
  doing: "33333333-3333-4333-8333-333333333333",
  blocked: "44444444-4444-4444-8444-444444444444",
  done: "55555555-5555-4555-8555-555555555555",
  long: "66666666-6666-4666-8666-666666666666",
};

function taskDate(offsetDays) {
  const date = new Date();
  date.setHours(0, 0, 0, 0);
  date.setDate(date.getDate() + offsetDays);
  return `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, "0")}${String(date.getDate()).padStart(2, "0")}T000000Z`;
}

function task(overrides) {
  return {
    status: "pending",
    project: "",
    priority: "",
    tags: [],
    due: "",
    wait: "",
    scheduled: "",
    entry: taskDate(-10),
    modified: taskDate(-1),
    end: "",
    start: "",
    urgency: 1,
    annotations: [],
    linear_id: "",
    linear_url: "",
    depends: [],
    dependency_details: [],
    dependent_tasks: [],
    blocked: false,
    recur: "",
    until: "",
    parent: "",
    ...overrides,
  };
}

export function makeBoard(overrides = {}) {
  const blocker = task({
    uuid: UUIDS.backlog,
    description: "Approve the deployment window",
    project: "work.release",
    priority: "H",
    tags: ["release"],
    due: taskDate(0),
    dependent_tasks: [{
      uuid: UUIDS.blocked,
      description: "Deploy the release",
      project: "work.release",
    }],
  });
  const ready = task({
    uuid: UUIDS.ready,
    description: "Prepare release notes",
    project: "work.release",
    tags: ["next", "writing"],
    due: taskDate(3),
  });
  const doing = task({
    uuid: UUIDS.doing,
    description: "Review production metrics",
    project: "work.operations",
    tags: ["next"],
    start: taskDate(0),
  });
  const completed = task({
    uuid: UUIDS.done,
    description: "Create deployment checklist",
    status: "completed",
    project: "work.release",
    end: taskDate(-1),
  });
  const blocked = task({
    uuid: UUIDS.blocked,
    description: "Deploy the release",
    project: "work.release",
    tags: ["waiting"],
    wait: taskDate(2),
    depends: [UUIDS.backlog, UUIDS.done],
    dependency_details: [
      {
        uuid: UUIDS.backlog,
        description: blocker.description,
        project: blocker.project,
        status: "pending",
        blocking: true,
        resolved: false,
      },
      {
        uuid: UUIDS.done,
        description: completed.description,
        project: completed.project,
        status: "completed",
        blocking: false,
        resolved: true,
      },
    ],
    blocked: true,
  });
  completed.dependent_tasks = [{
    uuid: UUIDS.blocked,
    description: blocked.description,
    project: blocked.project,
  }];
  const long = task({
    uuid: UUIDS.long,
    description: `Investigate ${"an-extremely-long-unbroken-identifier-".repeat(6)}`,
    project: "personal.admin",
    tags: ["research"],
  });

  const now = new Date().toISOString();
  return {
    columns: [
      { id: "backlog", title: "Backlog", tasks: [blocker, long] },
      { id: "ready", title: "Ready", tasks: [ready] },
      { id: "doing", title: "Doing", tasks: [doing] },
      { id: "waiting", title: "Waiting", tasks: [blocked] },
      { id: "done", title: "Done", tasks: [completed] },
    ],
    last_sync_attempt_at: now,
    last_sync_at: now,
    last_sync_error: null,
    generated_at: now,
    ...overrides,
  };
}

export async function mockApi(page, { board = makeBoard(), onMutation, syncResponses = [] } = {}) {
  let syncIndex = 0;
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === "/api/board" && request.method() === "GET") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(board) });
      return;
    }
    if (path === "/api/sync" && request.method() === "POST") {
      const response = syncResponses[Math.min(syncIndex, Math.max(syncResponses.length - 1, 0))];
      syncIndex += 1;
      if (response?.error) {
        await route.fulfill({ status: response.status || 502, contentType: "application/json", body: JSON.stringify({ error: response.error }) });
      } else {
        await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(response?.board || board) });
      }
      return;
    }
    const mutation = { method: request.method(), path, body: request.postDataJSON?.() };
    const response = await onMutation?.(mutation);
    await route.fulfill({
      status: response?.status || 200,
      contentType: "application/json",
      body: JSON.stringify(response?.body || board),
    });
  });
}

export async function openBoard(page) {
  await page.goto("/");
  await page.locator(".card:visible").first().waitFor();
}
