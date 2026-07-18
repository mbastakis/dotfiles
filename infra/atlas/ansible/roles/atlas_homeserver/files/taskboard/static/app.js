const STORAGE_KEYS = {
  columns: "sisyphus.collapsedColumns",
  filters: "sisyphus.filters",
  sidebar: "sisyphus.sidebarCollapsed",
  views: "sisyphus.savedViews",
  activeView: "sisyphus.activeView",
  sort: "sisyphus.sortMode",
  reauthDraft: "sisyphus.reauthDraft",
};
const SIDEBAR_DRAWER_QUERY = window.matchMedia("(max-width: 1120px)");
const MOBILE_QUERY = window.matchMedia("(max-width: 860px)");
const REDUCED_MOTION_QUERY = window.matchMedia("(prefers-reduced-motion: reduce)");
const AUTO_REFRESH_MS = 60_000;
const FRESHNESS_REFRESH_MS = 15_000;
const STALE_AFTER_MS = 5 * 60_000;

const MANAGED_TAGS = new Set(["next", "waiting"]);
const COLUMN_META = {
  backlog: { copy: "Captured, not yet committed.", icon: "inbox" },
  ready: { copy: "Selected next actions.", icon: "target" },
  doing: { copy: "Started and in motion.", icon: "play" },
  waiting: { copy: "Blocked, deferred, or delegated.", icon: "clock" },
  done: { copy: "Completed recently.", icon: "check" },
};
const ACTIONS = [
  ["backlog", "Backlog", "inbox"],
  ["ready", "Ready", "target"],
  ["doing", "Start", "play"],
  ["waiting", "Waiting", "clock"],
  ["done", "Done", "check"],
];
const BUILTIN_VIEWS = [
  ["today", "Today"],
  ["ready", "Ready"],
  ["blocked", "Blocked"],
  ["waiting", "Waiting"],
  ["triage", "Triage"],
];
const SORT_MODES = new Set(["due", "urgency", "modified", "entry", "description"]);
const storedViews = loadJson(STORAGE_KEYS.views, []);
const storedSort = localStorage.getItem(STORAGE_KEYS.sort) || "due";
const initialUrlState = readUrlState();
const storedFilters = loadJson(STORAGE_KEYS.filters, {});

const state = {
  board: null,
  busy: false,
  dragging: null,
  activeColumn: initialUrlState.column || null,
  focusedUuid: null,
  editDependencies: [],
  editSnapshot: null,
  editDirty: false,
  editExpectedModified: "",
  editOriginalTask: null,
  editReturnFocusUuid: null,
  conflictTask: null,
  reauthenticating: false,
  requestError: null,
  urlTask: initialUrlState.task,
  urlInitialized: false,
  taskSync: new Map(),
  taskSyncTimers: new Map(),
  selectedUuids: new Set(),
  savedViews: Array.isArray(storedViews) ? storedViews : [],
  activeView: initialUrlState.hasBoardState
    ? initialUrlState.view
    : localStorage.getItem(STORAGE_KEYS.activeView) || "",
  sortMode: initialUrlState.hasBoardState
    ? initialUrlState.sort
    : SORT_MODES.has(storedSort) ? storedSort : "due",
  collapsedColumns: new Set(loadJson(STORAGE_KEYS.columns, [])),
  filters: initialUrlState.hasBoardState
    ? initialUrlState.filters
    : { ...emptyFilters(), ...storedFilters },
};

const els = {
  board: document.querySelector("#board"),
  boardAnnouncements: document.querySelector("#boardAnnouncements"),
  columnTabs: document.querySelector("#columnTabs"),
  status: document.querySelector("#status"),
  boardStats: document.querySelector("#boardStats"),
  syncCard: document.querySelector(".sync-card"),
  sidebarToggle: document.querySelector("#sidebarToggle"),
  sidebarBackdrop: document.querySelector("#sidebarBackdrop"),
  shortcutsPanel: document.querySelector("#shortcutsPanel"),
  searchInput: document.querySelector("#searchInput"),
  projectFilter: document.querySelector("#projectFilter"),
  tagFilter: document.querySelector("#tagFilter"),
  priorityFilter: document.querySelector("#priorityFilter"),
  readinessFilter: document.querySelector("#readinessFilter"),
  dueFilter: document.querySelector("#dueFilter"),
  focusView: document.querySelector("#focusView"),
  sortMode: document.querySelector("#sortMode"),
  saveView: document.querySelector("#saveView"),
  deleteView: document.querySelector("#deleteView"),
  clearFilters: document.querySelector("#clearFilters"),
  syncButton: document.querySelector("#syncButton"),
  refreshButton: document.querySelector("#refreshButton"),
  expandColumns: document.querySelector("#expandColumns"),
  collapseEmptyColumns: document.querySelector("#collapseEmptyColumns"),
  quickAdd: document.querySelector("#quickAdd"),
  bulkPanel: document.querySelector("#bulkPanel"),
  bulkForm: document.querySelector("#bulkForm"),
  bulkCount: document.querySelector("#bulkCount"),
  selectVisible: document.querySelector("#selectVisible"),
  clearSelection: document.querySelector("#clearSelection"),
  bulkDueEnabled: document.querySelector("#bulkDueEnabled"),
  bulkDue: document.querySelector("#bulkDue"),
  editDialog: document.querySelector("#editDialog"),
  editForm: document.querySelector("#editForm"),
  editContext: document.querySelector("#editContext"),
  editStart: document.querySelector("#editStart"),
  editStop: document.querySelector("#editStop"),
  editComplete: document.querySelector("#editComplete"),
  editReopen: document.querySelector("#editReopen"),
  editDelete: document.querySelector("#editDelete"),
  editDirty: document.querySelector("#editDirty"),
  editSync: document.querySelector("#editSync"),
  editDependencies: document.querySelector("#editDependencies"),
  editDependents: document.querySelector("#editDependents"),
  editDependencySearch: document.querySelector("#editDependencySearch"),
  dependencyResults: document.querySelector("#dependencyResults"),
  dependencyCount: document.querySelector("#dependencyCount"),
  dependentCount: document.querySelector("#dependentCount"),
  editConflict: document.querySelector("#editConflict"),
  editConflictFields: document.querySelector("#editConflictFields"),
};

class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    redirect: "manual",
  });

  if (response.type === "opaqueredirect") {
    beginReauthentication();
    throw new Error("Session expired. Reauthenticating...");
  }

  const contentType = response.headers.get("Content-Type") || "";
  if (!contentType.includes("application/json")) {
    if (response.redirected || response.url.includes("/application/o/authorize/")) {
      throw new Error("Session expired. Refresh the page and sign in again.");
    }
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText || "request failed"}`);
    }
    throw new Error(`Expected JSON from ${path}, got ${contentType || "an empty response"}.`);
  }

  const payload = await response.json().catch(() => {
    throw new Error(`Invalid JSON response from ${path}.`);
  });
  if (!response.ok) throw new ApiError(payload.error || response.statusText, response.status, payload);
  return payload;
}

function beginReauthentication() {
  if (state.reauthenticating) return;
  state.reauthenticating = true;
  if (els.editDialog.open && state.editDirty) {
    sessionStorage.setItem(STORAGE_KEYS.reauthDraft, JSON.stringify({
      uuid: document.querySelector("#editUuid").value,
      values: editValues(),
      expectedModified: state.editExpectedModified,
      originalTask: state.editOriginalTask,
    }));
  }
  els.status.textContent = "Session expired. Reauthenticating...";
  window.location.assign("/");
}

function loadJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function readUrlState() {
  const params = new URL(window.location.href).searchParams;
  const hasBoardState = ["view", "q", "project", "tag", "priority", "readiness", "due", "sort", "column"]
    .some((key) => params.has(key));
  const sort = params.get("sort") || "due";
  return {
    hasBoardState,
    view: params.get("view") || "",
    sort: SORT_MODES.has(sort) ? sort : "due",
    column: params.get("column") || null,
    task: params.get("task") || null,
    filters: {
      search: params.get("q") || "",
      project: params.get("project") || "",
      tag: params.get("tag") || "",
      priority: params.get("priority") || "",
      readiness: params.get("readiness") || "",
      due: params.get("due") || "",
    },
  };
}

function syncUrl({ push = false, task } = {}) {
  const url = new URL(window.location.href);
  const values = {
    view: state.activeView,
    q: state.filters.search,
    project: state.filters.project,
    tag: state.filters.tag,
    priority: state.filters.priority,
    readiness: state.filters.readiness,
    due: state.filters.due,
    sort: state.sortMode === "due" ? "" : state.sortMode,
    column: state.activeColumn,
    task: task === undefined
      ? (els.editDialog.open ? document.querySelector("#editUuid").value : state.urlTask)
      : task,
  };
  Object.entries(values).forEach(([key, value]) => {
    if (value) {
      url.searchParams.set(key, value);
    } else {
      url.searchParams.delete(key);
    }
  });
  const historyState = { sisyphus: true, task: values.task || null };
  window.history[push ? "pushState" : "replaceState"](historyState, "", `${url.pathname}${url.search}${url.hash}`);
  state.urlTask = values.task || null;
}

function announce(message) {
  if (!els.boardAnnouncements) return;
  els.boardAnnouncements.textContent = "";
  window.requestAnimationFrame(() => {
    els.boardAnnouncements.textContent = message;
  });
}

function scrollBehavior() {
  return REDUCED_MOTION_QUERY.matches ? "auto" : "smooth";
}

function saveCollapsedColumns() {
  localStorage.setItem(STORAGE_KEYS.columns, JSON.stringify([...state.collapsedColumns]));
}

function setBusy(isBusy) {
  state.busy = isBusy;
  document.body.classList.toggle("is-busy", isBusy);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

function icon(name, extraClass = "") {
  const className = extraClass ? `icon ${extraClass}` : "icon";
  return `<svg class="${className}" aria-hidden="true"><use href="#icon-${name}"></use></svg>`;
}

function taskSyncLabel(status) {
  return {
    saving: "Saving...",
    saved: "Saved",
    conflict: "Conflict",
    offline: "Offline; retry",
    retry: "Not saved; retry",
  }[status] || "";
}

function taskSyncHtml(uuid) {
  const sync = state.taskSync.get(uuid);
  if (!sync) return "";
  const label = taskSyncLabel(sync.status);
  const retry = sync.retry && ["offline", "retry"].includes(sync.status);
  return retry
    ? `<button class="task-sync task-sync-${escapeHtml(sync.status)}" type="button" data-retry-task="${escapeHtml(uuid)}">${escapeHtml(label)}</button>`
    : `<span class="task-sync task-sync-${escapeHtml(sync.status)}">${escapeHtml(label)}</span>`;
}

function renderTaskSync(uuid) {
  const sync = state.taskSync.get(uuid);
  const label = sync ? taskSyncLabel(sync.status) : "";
  document.querySelectorAll(`[data-task-sync="${CSS.escape(uuid)}"]`).forEach((container) => {
    container.innerHTML = taskSyncHtml(uuid);
    container.hidden = !sync;
    container.closest(".card-state-row")?.classList.toggle(
      "is-empty",
      !sync && !container.closest(".card-state-row").querySelector(".card-relationships"),
    );
    container.querySelector("[data-retry-task]")?.addEventListener("click", () => {
      state.taskSync.get(uuid)?.retry?.();
    });
  });
  const card = [...els.board.querySelectorAll(".card")].find((candidate) => candidate.dataset.uuid === uuid);
  if (card) {
    card.classList.toggle("is-saving", sync?.status === "saving");
    card.classList.toggle("has-sync-error", ["conflict", "offline", "retry"].includes(sync?.status));
  }
  if (els.editDialog.open && document.querySelector("#editUuid").value === uuid) {
    els.editSync.textContent = label;
    els.editSync.hidden = !sync;
    els.editSync.className = `dialog-sync task-sync-${sync?.status || "idle"}`;
  }
}

function setTaskSync(uuid, status, { message = "", retry = null, clearAfter = 0 } = {}) {
  const existingTimer = state.taskSyncTimers.get(uuid);
  if (existingTimer) window.clearTimeout(existingTimer);
  state.taskSync.set(uuid, { status, message, retry });
  renderTaskSync(uuid);
  announce(`${findTask(uuid)?.description || `Task ${shortUuid(uuid)}`}: ${message || taskSyncLabel(status)}`);
  if (clearAfter) {
    const timer = window.setTimeout(() => clearTaskSync(uuid), clearAfter);
    state.taskSyncTimers.set(uuid, timer);
  }
}

function clearTaskSync(uuid) {
  const timer = state.taskSyncTimers.get(uuid);
  if (timer) window.clearTimeout(timer);
  state.taskSyncTimers.delete(uuid);
  state.taskSync.delete(uuid);
  renderTaskSync(uuid);
}

function setTaskMutationFailure(uuid, error, retry) {
  if (state.reauthenticating) return;
  if (error instanceof ApiError && error.status === 409) {
    setTaskSync(uuid, "conflict", { message: "Conflict. Review the latest task before retrying." });
    return;
  }
  const offline = !navigator.onLine || error instanceof TypeError;
  setTaskSync(uuid, offline ? "offline" : "retry", {
    message: offline ? "Offline. Retry when the connection returns." : "Not saved. Retry the action.",
    retry,
  });
}

function formatDate(value) {
  if (!value) return "";
  return String(value).replace(/T.*$/, "").replace(/^(\d{4})(\d{2})(\d{2}).*/, "$1-$2-$3");
}

function parseTimestamp(value) {
  if (!value) return null;
  const match = String(value).match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/);
  const date = match
    ? new Date(`${match[1]}-${match[2]}-${match[3]}T${match[4]}:${match[5]}:${match[6]}Z`)
    : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatTimestamp(value) {
  if (!value) return "";
  const date = parseTimestamp(value);
  return date ? date.toLocaleString() : formatDate(value);
}

function compactRelativeTimestamp(value) {
  const date = parseTimestamp(value);
  if (!date) return "never";
  const seconds = Math.max(0, Math.round((Date.now() - date.getTime()) / 1000));
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  if (seconds < 86_400) return `${Math.round(seconds / 3600)}h ago`;
  return `${Math.round(seconds / 86_400)}d ago`;
}

function parseDate(value) {
  const formatted = formatDate(value);
  if (!formatted) return null;
  const [year, month, day] = formatted.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function relativeDate(value) {
  const date = parseDate(value);
  if (!date) return "";
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((date - today) / 86_400_000);
  if (days === 0) return "today";
  if (days === 1) return "tomorrow";
  if (days === -1) return "yesterday";
  return days > 1 ? `in ${days} days` : `${Math.abs(days)} days ago`;
}

function dueClass(value) {
  const date = parseDate(value);
  if (!date) return "";
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return date < today ? "overdue" : "";
}

function isFutureDate(value) {
  const date = parseDate(value);
  if (!date) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return date > today;
}

function annotationDescription(annotation) {
  return typeof annotation === "string" ? annotation : annotation?.description || "";
}

function shortUuid(uuid) {
  return String(uuid || "").slice(0, 8);
}

function normalizeBoard(payload) {
  if (!payload || !Array.isArray(payload.columns)) {
    throw new Error("Board response was incomplete. Refresh the page and try again.");
  }
  return {
    ...payload,
    columns: payload.columns.map((column) => ({
      ...column,
      id: String(column.id || ""),
      title: String(column.title || column.id || "Untitled"),
      tasks: (Array.isArray(column.tasks) ? column.tasks : []).map((task) => ({
        ...task,
        depends: Array.isArray(task.depends) ? task.depends.map(String) : [],
        dependency_details: Array.isArray(task.dependency_details) ? task.dependency_details : null,
        dependent_tasks: Array.isArray(task.dependent_tasks) ? task.dependent_tasks : [],
      })),
    })),
  };
}

function render(payload) {
  const board = normalizeBoard(payload);
  state.board = board;
  state.requestError = null;
  renderStatus(board);
  renderFilterOptions(board);
  renderViewOptions();
  renderBoard();
  restoreReauthenticationDraft();
  restoreUrlTask();
  if (!state.urlInitialized) {
    state.urlInitialized = true;
    syncUrl();
  }
}

function restoreUrlTask() {
  if (!state.urlTask || els.editDialog.open) return;
  if (findTask(state.urlTask)) {
    openEdit(state.urlTask, { syncHistory: false });
  } else {
    announce(`Task ${shortUuid(state.urlTask)} is not available in this board window.`);
  }
}

function restoreReauthenticationDraft() {
  const raw = sessionStorage.getItem(STORAGE_KEYS.reauthDraft);
  if (!raw) return;
  sessionStorage.removeItem(STORAGE_KEYS.reauthDraft);
  try {
    const draft = JSON.parse(raw);
    if (!findTask(draft.uuid) || !draft.values) return;
    state.urlTask = draft.uuid;
    openEdit(draft.uuid, { syncHistory: false });
    document.querySelector("#editDescription").value = draft.values.description || "";
    document.querySelector("#editProject").value = draft.values.project || "";
    document.querySelector("#editTags").value = draft.values.tags || "";
    document.querySelector("#editPriority").value = draft.values.priority || "";
    document.querySelector("#editDue").value = draft.values.due || "";
    document.querySelector("#editWait").value = draft.values.wait || "";
    document.querySelector("#editScheduled").value = draft.values.scheduled || "";
    document.querySelector("#editAnnotation").value = draft.values.annotation || "";
    state.editDependencies = Array.isArray(draft.values.dependencies)
      ? draft.values.dependencies.map(String)
      : [];
    state.editExpectedModified = draft.expectedModified || state.editExpectedModified;
    state.editOriginalTask = draft.originalTask || state.editOriginalTask;
    renderDependencySelection();
    renderDependencyResults();
    updateEditDirty();
  } catch {
    sessionStorage.removeItem(STORAGE_KEYS.reauthDraft);
  }
}

function renderStatus(board) {
  const total = board.columns.reduce((sum, column) => sum + column.tasks.length, 0);
  const activeColumns = board.columns.filter((column) => column.tasks.length > 0).length;
  const hasError = Boolean(board.last_sync_error);
  const lastSuccess = parseTimestamp(board.last_sync_at);
  const stale = !lastSuccess || Date.now() - lastSuccess.getTime() > STALE_AFTER_MS;
  els.status.textContent = hasError
    ? `Sync failed · ${compactRelativeTimestamp(board.last_sync_attempt_at)}`
    : `Synced ${compactRelativeTimestamp(board.last_sync_at)}${stale ? " · stale" : ""}`;
  els.status.title = [
    `Last attempt: ${formatTimestamp(board.last_sync_attempt_at) || "not yet"}`,
    `Last successful sync: ${formatTimestamp(board.last_sync_at) || "not yet"}`,
  ].join(" | ");
  els.status.classList.toggle("error", hasError);
  els.syncCard.classList.toggle("error", hasError);
  els.syncCard.classList.toggle("stale", stale);
  els.boardStats.textContent = hasError
    ? `${board.last_sync_error} · Last success ${compactRelativeTimestamp(board.last_sync_at)}`
    : `${total} tasks · ${activeColumns} columns · Updated ${compactRelativeTimestamp(board.generated_at)}`;
  els.boardStats.title = [
    `Board generated: ${formatTimestamp(board.generated_at) || "unknown"}`,
    hasError ? `Sync error: ${board.last_sync_error}` : null,
  ].filter(Boolean).join(" | ");
}

function refreshFreshness() {
  if (state.board && !state.requestError) renderStatus(state.board);
}

function renderFilterOptions(board) {
  const projects = collectProjects(board);
  const tags = collectValues(board, (task) => (task.tags || []).filter((tag) => !MANAGED_TAGS.has(tag))).sort();
  updateGroupedSelect(els.projectFilter, [
    ["Active", projects.active],
    ["Recently completed", projects.completed],
  ], "All projects", state.filters.project);
  updateSelect(els.tagFilter, tags, "All tags", state.filters.tag);
}

function collectProjects(board) {
  const projects = new Map();
  for (const column of board.columns) {
    for (const task of column.tasks) {
      if (!task.project) continue;
      projects.set(task.project, projects.get(task.project) || column.id !== "done");
    }
  }

  return {
    active: [...projects].filter(([, active]) => active).map(([project]) => project).sort(),
    completed: [...projects].filter(([, active]) => !active).map(([project]) => project).sort(),
  };
}

function collectValues(board, getter) {
  const values = new Set();
  for (const column of board.columns) {
    for (const task of column.tasks) {
      const raw = getter(task);
      const items = Array.isArray(raw) ? raw : [raw];
      for (const item of items) {
        if (item) values.add(item);
      }
    }
  }
  return [...values];
}

function updateSelect(select, values, label, selected) {
  const savedOption = selected && !values.includes(selected)
    ? `<option value="${escapeHtml(selected)}">${escapeHtml(selected)} (saved)</option>`
    : "";
  select.innerHTML = [
    `<option value="">${escapeHtml(label)}</option>`,
    savedOption,
    ...values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`),
  ].join("");
  if (selected) select.value = selected;
}

function updateGroupedSelect(select, groups, label, selected) {
  const values = groups.flatMap(([, groupValues]) => groupValues);
  const savedOption = selected && !values.includes(selected)
    ? `<option value="${escapeHtml(selected)}">${escapeHtml(selected)} (saved)</option>`
    : "";
  select.innerHTML = [
    `<option value="">${escapeHtml(label)}</option>`,
    savedOption,
    ...groups.filter(([, groupValues]) => groupValues.length).map(([groupLabel, groupValues]) => `
      <optgroup label="${escapeHtml(groupLabel)}">
        ${groupValues.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join("")}
      </optgroup>`),
  ].join("");
  if (selected) select.value = selected;
}

function currentFocusView() {
  if (!state.activeView.startsWith("custom:")) return state.activeView;
  const saved = state.savedViews.find((view) => `custom:${view.id}` === state.activeView);
  return saved?.focus || "";
}

function renderViewOptions() {
  const builtins = BUILTIN_VIEWS.map(([value, label]) =>
    `<option value="${value}">${escapeHtml(label)}</option>`).join("");
  const custom = state.savedViews.length
    ? `<optgroup label="Saved">${state.savedViews.map((view) =>
      `<option value="custom:${escapeHtml(view.id)}">${escapeHtml(view.name)}</option>`).join("")}</optgroup>`
    : "";
  els.focusView.innerHTML = `<option value="">All tasks</option><optgroup label="Focus">${builtins}</optgroup>${custom}`;
  const known = [...els.focusView.options].some((option) => option.value === state.activeView);
  if (!known) {
    state.activeView = "";
    localStorage.removeItem(STORAGE_KEYS.activeView);
  }
  els.focusView.value = state.activeView;
  els.sortMode.value = state.sortMode;
  els.deleteView.hidden = !state.activeView.startsWith("custom:");
}

function viewMatches(task, columnId) {
  const focus = currentFocusView();
  if (!focus) return true;
  const unfinished = task.status !== "completed";
  if (focus === "today") {
    const due = parseDate(task.due);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return unfinished && (columnId === "doing" || Boolean(due && due <= today));
  }
  if (focus === "ready") return columnId === "ready";
  if (focus === "blocked") return unfinished && isTaskBlocked(task);
  if (focus === "waiting") return columnId === "waiting";
  if (focus === "triage") return columnId === "backlog";
  return true;
}

function timestampValue(value, missing) {
  return parseTimestamp(value)?.getTime() ?? missing;
}

function sortTasks(tasks) {
  const sorted = [...tasks];
  sorted.sort((left, right) => {
    if (state.sortMode === "urgency") {
      return Number(right.urgency || 0) - Number(left.urgency || 0)
        || timestampValue(left.due, Number.MAX_SAFE_INTEGER) - timestampValue(right.due, Number.MAX_SAFE_INTEGER);
    }
    if (state.sortMode === "modified") {
      return timestampValue(right.modified, 0) - timestampValue(left.modified, 0);
    }
    if (state.sortMode === "entry") {
      return timestampValue(right.entry, 0) - timestampValue(left.entry, 0);
    }
    if (state.sortMode === "description") {
      return String(left.description || "").localeCompare(String(right.description || ""));
    }
    return timestampValue(left.due, Number.MAX_SAFE_INTEGER) - timestampValue(right.due, Number.MAX_SAFE_INTEGER)
      || Number(right.urgency || 0) - Number(left.urgency || 0)
      || timestampValue(left.entry, Number.MAX_SAFE_INTEGER) - timestampValue(right.entry, Number.MAX_SAFE_INTEGER);
  });
  return sorted;
}

function renderBoard() {
  if (!state.board || !Array.isArray(state.board.columns)) return;
  const knownUuids = new Set(state.board.columns.flatMap((column) => column.tasks.map((task) => task.uuid)));
  state.selectedUuids = new Set([...state.selectedUuids].filter((uuid) => knownUuids.has(uuid)));
  ensureActiveColumn();
  ensureFocusedTask();
  renderColumnTabs();
  els.board.dataset.view = state.activeView || "all";
  els.board.innerHTML = state.board.columns.map((column) => columnHtml(column)).join("");
  attachBoardHandlers();
  renderBulkControls();
  window.requestAnimationFrame(updateBoardOverflow);
}

function updateBoardOverflow() {
  const maxScroll = els.board.scrollWidth - els.board.clientWidth;
  const scrollbarGutter = els.board.offsetWidth - els.board.clientWidth;
  const hasOverflow = !MOBILE_QUERY.matches && maxScroll > 2;
  els.board.classList.toggle("can-scroll-left", hasOverflow && els.board.scrollLeft > 2);
  els.board.classList.toggle("can-scroll-right", hasOverflow && els.board.scrollLeft < maxScroll - scrollbarGutter - 2);
}

function ensureActiveColumn() {
  if (state.board.columns.some((column) => column.id === state.activeColumn)) return;
  const preferred = state.board.columns.find((column) => column.id === "doing" && column.tasks.length);
  const firstWithTasks = state.board.columns.find((column) => column.tasks.length);
  state.activeColumn = (preferred || firstWithTasks || state.board.columns[0])?.id || null;
}

function navigableTasks() {
  return (state.board?.columns || []).flatMap((column) => {
    if (MOBILE_QUERY.matches && column.id !== state.activeColumn) return [];
    if (!MOBILE_QUERY.matches && state.collapsedColumns.has(column.id)) return [];
    return sortTasks(column.tasks.filter((task) => filterTask(task, column.id)));
  });
}

function ensureFocusedTask() {
  const tasks = navigableTasks();
  if (tasks.some((task) => task.uuid === state.focusedUuid)) return;
  state.focusedUuid = tasks[0]?.uuid || null;
}

function renderColumnTabs() {
  els.columnTabs.innerHTML = state.board.columns.map((column) => {
    const count = column.tasks.filter((task) => filterTask(task, column.id)).length;
    const active = column.id === state.activeColumn;
    const meta = COLUMN_META[column.id] || { icon: "inbox" };
    return `<button class="column-tab" type="button" data-column-tab="${escapeHtml(column.id)}" aria-pressed="${active}">
      ${icon(meta.icon)} <span>${escapeHtml(column.title)}</span> <span class="tab-count">${count}</span>
    </button>`;
  }).join("");
}

function columnHtml(column) {
  const tasks = sortTasks(column.tasks.filter((task) => filterTask(task, column.id)));
  const collapsed = !MOBILE_QUERY.matches && state.collapsedColumns.has(column.id);
  const active = column.id === state.activeColumn;
  const meta = COLUMN_META[column.id] || { copy: "", icon: "inbox" };
  const columnLabel = `${icon(meta.icon, "column-icon")}<span class="column-label" role="heading" aria-level="2">${escapeHtml(column.title)}</span>`;
  const columnControl = MOBILE_QUERY.matches
    ? `<span class="column-title-control">${columnLabel}</span>`
    : `<button class="column-title-control" type="button" data-column-toggle="${escapeHtml(column.id)}" aria-label="${collapsed ? "Expand" : "Collapse"} ${escapeHtml(column.title)}" aria-expanded="${collapsed ? "false" : "true"}">
        <span class="column-toggle" aria-hidden="true">${icon(collapsed ? "chevron-right" : "chevron-down")}</span>
        ${columnLabel}
      </button>`;
  return `
    <section class="column column-${escapeHtml(column.id)} ${collapsed ? "is-collapsed" : ""} ${active ? "is-active" : ""}" data-column="${escapeHtml(column.id)}">
      <header class="column-header">
        <div class="column-title-row">
          <span class="column-status" aria-hidden="true"></span>
          ${columnControl}
        </div>
        <span class="count">${tasks.length === column.tasks.length ? tasks.length : `${tasks.length}/${column.tasks.length}`}</span>
      </header>
      <div class="column-body">
        <div class="cards">
          ${tasks.length ? tasks.map((task) => cardHtml(task, column.id)).join("") : `<p class="empty-state">No matching tasks.</p>`}
        </div>
      </div>
    </section>`;
}

function dependencyDetails(task) {
  if (Array.isArray(task.dependency_details)) {
    return task.dependency_details.map((detail) => ({
      uuid: String(detail.uuid || ""),
      description: detail.description || detail.uuid || "Unknown task",
      project: detail.project || "",
      status: detail.status || "unknown",
      resolved: Boolean(detail.resolved),
      blocking: typeof detail.blocking === "boolean" ? detail.blocking : !detail.resolved,
    }));
  }
  return (task.depends || []).map((uuid) => {
    const dependency = findTask(uuid);
    return {
      uuid: String(uuid),
      description: dependency?.description || String(uuid),
      project: dependency?.project || "",
      status: dependency?.status || "unknown",
      resolved: ["completed", "deleted"].includes(dependency?.status),
      blocking: ["pending", "waiting"].includes(dependency?.status),
    };
  });
}

function dependentTasks(task) {
  return Array.isArray(task.dependent_tasks) ? task.dependent_tasks : [];
}

function isTaskBlocked(task) {
  const details = dependencyDetails(task);
  return details.length
    ? details.some((dependency) => dependency.blocking)
    : Boolean(task.blocked);
}

function relationshipSummaryHtml(task) {
  const dependencies = dependencyDetails(task);
  const unresolved = dependencies.filter((dependency) => dependency.blocking);
  const missing = dependencies.filter((dependency) => !dependency.blocking && !dependency.resolved);
  const dependents = dependentTasks(task);
  const summaries = [];
  if (unresolved.length) {
    const names = unresolved.map((dependency) => dependency.description || shortUuid(dependency.uuid));
    summaries.push(`<span class="relationship relationship-blocked" title="${escapeHtml(names.join(", "))}">${icon("link")} Blocked by ${escapeHtml(names[0])}${names.length > 1 ? ` +${names.length - 1}` : ""}</span>`);
  } else if (missing.length) {
    const names = missing.map((dependency) => dependency.description || shortUuid(dependency.uuid));
    summaries.push(`<span class="relationship" title="${escapeHtml(names.join(", "))}">${icon("link")} Missing prerequisite${names.length > 1 ? "s" : ""}: ${escapeHtml(names[0])}${names.length > 1 ? ` +${names.length - 1}` : ""}</span>`);
  } else if (dependencies.length) {
    const names = dependencies.map((dependency) => dependency.description || shortUuid(dependency.uuid));
    summaries.push(`<span class="relationship relationship-resolved" title="${escapeHtml(names.join(", "))}">${icon("check")} Prerequisites complete${names[0] ? `: ${escapeHtml(names[0])}${names.length > 1 ? ` +${names.length - 1}` : ""}` : ""}</span>`);
  }
  if (dependents.length) {
    const names = dependents.map((dependent) => dependent.description || shortUuid(dependent.uuid));
    summaries.push(`<span class="relationship relationship-blocks" title="${escapeHtml(names.join(", "))}">${icon("link")} Blocks ${escapeHtml(names[0])}${names.length > 1 ? ` +${names.length - 1}` : ""}</span>`);
  }
  return summaries.join("");
}

function relationshipDescription(task) {
  const dependencies = dependencyDetails(task);
  const unresolved = dependencies.filter((dependency) => dependency.blocking);
  const missing = dependencies.filter((dependency) => !dependency.blocking && !dependency.resolved);
  const dependents = dependentTasks(task);
  return [
    unresolved.length ? `Blocked by ${unresolved.map((dependency) => dependency.description).join(", ")}.` : "",
    missing.length ? `Missing prerequisites: ${missing.map((dependency) => dependency.description).join(", ")}.` : "",
    dependencies.length && !unresolved.length && !missing.length ? "All prerequisites are complete." : "",
    dependents.length ? `Blocks ${dependents.map((dependent) => dependent.description).join(", ")}.` : "",
  ].filter(Boolean).join(" ");
}

function dueState(task) {
  const date = parseDate(task.due);
  if (!date) return "none";
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (date < today) return "overdue";
  if (date.getTime() === today.getTime()) return "today";
  return "upcoming";
}

function filterTask(task, columnId = findTaskColumn(task.uuid)) {
  if (!viewMatches(task, columnId)) return false;
  const search = state.filters.search.trim().toLowerCase();
  if (search) {
    const haystack = [
      task.description,
      task.project,
      task.priority,
      task.uuid,
      task.linear_id,
      task.due,
      task.wait,
      task.scheduled,
      ...(task.tags || []),
      ...(task.depends || []),
      ...dependencyDetails(task).flatMap((dependency) => [dependency.description, dependency.project, dependency.status]),
      ...dependentTasks(task).flatMap((dependent) => [dependent.description, dependent.project]),
      ...(task.annotations || []).map(annotationDescription),
    ].join(" ").toLowerCase();
    if (!haystack.includes(search)) return false;
  }
  if (state.filters.project && task.project !== state.filters.project) return false;
  if (state.filters.tag && !(task.tags || []).includes(state.filters.tag)) return false;
  if (state.filters.priority && task.priority !== state.filters.priority) return false;
  if (state.filters.readiness) {
    const unfinished = task.status !== "completed";
    const deferred = unfinished && isFutureDate(task.wait);
    const matches = {
      ready: unfinished && !isTaskBlocked(task) && !deferred,
      blocked: unfinished && isTaskBlocked(task),
      deferred,
    };
    if (!matches[state.filters.readiness]) return false;
  }
  if (state.filters.due && dueState(task) !== state.filters.due) return false;
  return true;
}

function cardHtml(task, columnId) {
  const priority = task.priority || "none";
  const tags = (task.tags || []).filter((tag) => !MANAGED_TAGS.has(tag));
  const dependencies = dependencyDetails(task);
  const unresolvedCount = dependencies.filter((dependency) => dependency.blocking).length;
  const resolvedCount = dependencies.filter((dependency) => dependency.resolved).length;
  const blocksCount = dependentTasks(task).length;
  const blocked = isTaskBlocked(task);
  const selected = state.selectedUuids.has(task.uuid);
  const relationshipHtml = relationshipSummaryHtml(task);
  const relationshipText = relationshipDescription(task);
  const sync = state.taskSync.get(task.uuid);
  return `
    <article class="card priority-${escapeHtml(priority)} ${blocked ? "is-blocked" : ""} ${selected ? "is-selected" : ""} ${sync?.status === "saving" ? "is-saving" : ""} ${["conflict", "offline", "retry"].includes(sync?.status) ? "has-sync-error" : ""}" draggable="${MOBILE_QUERY.matches ? "false" : "true"}" tabindex="${state.focusedUuid === task.uuid ? "0" : "-1"}" data-uuid="${escapeHtml(task.uuid)}" aria-keyshortcuts="Enter ArrowUp ArrowDown ArrowLeft ArrowRight Shift+ArrowLeft Shift+ArrowRight Shift+H Shift+L 1 2 3 4 5 X" aria-label="${escapeHtml(task.description)}${relationshipText ? ` ${escapeHtml(relationshipText)}` : ""}">
      <div class="card-header">
        ${task.project ? `<span class="project-pill" title="${escapeHtml(task.project)}">${icon("folder")} <span class="truncate">${escapeHtml(task.project)}</span></span>` : `<span class="project-pill">${icon("folder")} <span class="truncate">No project</span></span>`}
        <button class="card-select" type="button" data-select-task="${escapeHtml(task.uuid)}" aria-pressed="${selected}" aria-label="${selected ? "Deselect" : "Select"} ${escapeHtml(task.description)}" title="${selected ? "Deselect task" : "Select for bulk triage"}">${icon("check")}</button>
        <span class="card-uuid">${icon("hash")} <span>${escapeHtml(shortUuid(task.uuid))}</span></span>
      </div>
      <h3 class="card-title">${escapeHtml(task.description)}</h3>
      <div class="card-state-row ${relationshipHtml || sync ? "" : "is-empty"}">
        ${relationshipHtml ? `<div class="card-relationships">${relationshipHtml}</div>` : ""}
        <div class="card-sync" data-task-sync="${escapeHtml(task.uuid)}" ${sync ? "" : "hidden"}>${taskSyncHtml(task.uuid)}</div>
      </div>
      <div class="card-meta">
        ${task.priority ? `<span class="pill priority">${icon("flag")} P:${escapeHtml(task.priority)}</span>` : ""}
        ${task.due ? `<span class="pill due ${dueClass(task.due)}">${icon("calendar")} Due ${escapeHtml(relativeDate(task.due))}</span>` : ""}
        ${task.wait ? `<span class="pill waiting">${icon("clock")} ${isFutureDate(task.wait) ? "Deferred" : "Wait date"} ${escapeHtml(relativeDate(task.wait))}</span>` : ""}
        ${unresolvedCount ? `<span class="pill blocked">${icon("link")} Blocked ${unresolvedCount}</span>` : ""}
        ${resolvedCount ? `<span class="pill resolved secondary-meta">${icon("check")} Resolved ${resolvedCount}</span>` : ""}
        ${blocksCount ? `<span class="pill blocks secondary-meta">${icon("link")} Blocks ${blocksCount}</span>` : ""}
        ${(task.annotations || []).length ? `<span class="pill notes secondary-meta">${icon("details")} ${task.annotations.length} ${task.annotations.length === 1 ? "note" : "notes"}</span>` : ""}
        ${Number(task.urgency || 0) > 0 ? `<span class="pill urgency secondary-meta">${icon("zap")} U:${Number(task.urgency || 0).toFixed(1)}</span>` : ""}
        ${tags.map((tag, index) => `<span class="pill tag ${index ? "secondary-meta" : ""}">${icon("tag")} ${escapeHtml(tag)}</span>`).join("")}
        ${task.linear_id ? `<span class="pill linear-id secondary-meta">${icon("link")} ${escapeHtml(task.linear_id)}</span>` : ""}
      </div>
      <details class="card-menu">
        <summary><span class="summary-label">${icon("details")} Actions</span></summary>
        <div class="card-actions">
          <button type="button" data-action="edit">${icon("pencil")} Edit</button>
          ${columnId !== "done" ? actionButtons(columnId) : ""}
        </div>
      </details>
    </article>`;
}

function actionButtons(columnId) {
  return ACTIONS
    .filter(([action]) => action !== columnId)
    .map(([action, label, iconName]) => `<button type="button" data-action="${action}">${icon(iconName)} ${label}</button>`)
    .join("");
}

function attachBoardHandlers() {
  els.columnTabs.querySelectorAll("[data-column-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeColumn = button.dataset.columnTab;
      renderBoard();
      syncUrl({ push: true });
    });
  });

  els.board.querySelectorAll("[data-column-toggle]").forEach((button) => {
    button.addEventListener("click", () => toggleColumn(button.dataset.columnToggle));
  });

  els.board.querySelectorAll(".card").forEach((card) => {
    let wasDragged = false;
    card.addEventListener("pointerdown", () => {
      wasDragged = false;
    });
    card.addEventListener("dragstart", (event) => {
      wasDragged = true;
      state.dragging = card.dataset.uuid;
      card.classList.add("dragging");
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", card.dataset.uuid);
    });
    card.addEventListener("dragend", () => {
      state.dragging = null;
      card.classList.remove("dragging");
    });
    card.addEventListener("focus", () => {
      state.focusedUuid = card.dataset.uuid;
      els.board.querySelectorAll(".card").forEach((candidate) => {
        candidate.tabIndex = candidate === card ? 0 : -1;
      });
    });
    card.addEventListener("click", (event) => {
      const fromControl = event.target instanceof Element && event.target.closest(".card-menu, .card-select, .task-sync");
      if (!wasDragged && !fromControl) requestOpenTask(card.dataset.uuid);
    });
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && event.target === card) {
        event.preventDefault();
        requestOpenTask(card.dataset.uuid);
      }
    });
    card.querySelector(".card-select").addEventListener("click", () => toggleTaskSelection(card.dataset.uuid));
    card.querySelectorAll(".card-menu button").forEach((button) => {
      button.addEventListener("click", () => handleCardAction(card.dataset.uuid, button.dataset.action));
    });
  });

  els.board.querySelectorAll("[data-retry-task]").forEach((button) => {
    button.addEventListener("click", () => state.taskSync.get(button.dataset.retryTask)?.retry?.());
  });

  els.board.querySelectorAll(".column").forEach((column) => {
    column.addEventListener("dragover", (event) => {
      event.preventDefault();
      column.classList.add("drop");
    });
    column.addEventListener("dragleave", () => column.classList.remove("drop"));
    column.addEventListener("drop", async (event) => {
      event.preventDefault();
      column.classList.remove("drop");
      if (state.dragging) await moveTask(state.dragging, column.dataset.column);
    });
  });
}

function toggleColumn(columnId, { focusControl = false } = {}) {
  if (state.collapsedColumns.has(columnId)) {
    state.collapsedColumns.delete(columnId);
  } else {
    state.collapsedColumns.add(columnId);
  }
  saveCollapsedColumns();
  renderBoard();
  const title = state.board?.columns.find((column) => column.id === columnId)?.title || "Column";
  announce(`${title} ${state.collapsedColumns.has(columnId) ? "collapsed" : "expanded"}.`);
  if (focusControl) {
    window.requestAnimationFrame(() => {
      els.board.querySelector(`[data-column-toggle="${CSS.escape(columnId)}"]`)?.focus();
    });
  }
}

async function loadBoard({ silent = false } = {}) {
  if (!silent) setBusy(true);
  try {
    render(await api("/api/board"));
  } catch (error) {
    showError(error);
  } finally {
    if (!silent) setBusy(false);
  }
}

async function syncNow() {
  setBusy(true);
  try {
    render(await api("/api/sync", { method: "POST", body: "{}" }));
  } catch (error) {
    showError(error);
  } finally {
    setBusy(false);
  }
}

function dependentNames(task) {
  return dependentTasks(task).map((dependent) => dependent.description || dependent.uuid);
}

function confirmCompletion(uuid) {
  const task = findTask(uuid);
  const names = task ? dependentNames(task) : [];
  if (!names.length) return true;
  return window.confirm(
    `Complete "${task.description}"?\n\nThis task currently blocks:\n- ${names.join("\n- ")}\n\nCompleting this task may make them actionable.`,
  );
}

function refocusTask(uuid) {
  window.requestAnimationFrame(() => {
    const card = [...els.board.querySelectorAll(".card")].find((candidate) => candidate.dataset.uuid === uuid);
    if (card && isVisible(card)) card.focus();
  });
}

async function moveTask(uuid, column, { refocus = false, completionConfirmed = false } = {}) {
  const currentColumn = findTaskColumn(uuid);
  const task = findTask(uuid);
  if (currentColumn === column) {
    if (state.taskSync.has(uuid)) {
      setTaskSync(uuid, "saved", { message: "Task is already in that column.", clearAfter: 1500 });
    }
    if (refocus) refocusTask(uuid);
    return true;
  }
  if (column === "done" && !completionConfirmed && !confirmCompletion(uuid)) return false;
  const retry = () => moveTask(uuid, column, { refocus: true, completionConfirmed });
  const destination = state.board?.columns.find((candidate) => candidate.id === column)?.title || column;
  setTaskSync(uuid, "saving", { message: `Moving to ${destination}.` });
  setBusy(true);
  try {
    const payload = await api(`/api/tasks/${encodeURIComponent(uuid)}/move`, {
      method: "POST",
      body: JSON.stringify({ column, expected_modified: task?.modified || "" }),
    });
    if (refocus && MOBILE_QUERY.matches) state.activeColumn = column;
    render(payload);
    setTaskSync(uuid, "saved", { message: "Move saved.", clearAfter: 2500 });
    syncUrl();
    if (refocus) refocusTask(uuid);
    return true;
  } catch (error) {
    setTaskMutationFailure(uuid, error, retry);
    if (!showEditConflict(error)) {
      showError(error);
      if (error instanceof ApiError && error.status === 409) await loadBoard({ silent: true });
    }
    return false;
  } finally {
    setBusy(false);
  }
}

function findTask(uuid) {
  const normalized = String(uuid || "").toLowerCase();
  for (const column of state.board?.columns || []) {
    const task = column.tasks.find((candidate) => String(candidate.uuid).toLowerCase() === normalized);
    if (task) return task;
  }
  return null;
}

function findTaskColumn(uuid) {
  const normalized = String(uuid || "").toLowerCase();
  return (state.board?.columns || []).find((column) =>
    column.tasks.some((task) => String(task.uuid).toLowerCase() === normalized))?.id || null;
}

function taskDependsOn(taskUuid, targetUuid, visited = new Set()) {
  const taskKey = String(taskUuid).toLowerCase();
  const targetKey = String(targetUuid).toLowerCase();
  if (taskKey === targetKey) return true;
  if (visited.has(taskKey)) return false;
  visited.add(taskKey);
  const task = findTask(taskUuid);
  return (task?.depends || []).some((uuid) => taskDependsOn(String(uuid), targetUuid, visited));
}

function dependencySearchMatches(query) {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return [];
  const currentUuid = document.querySelector("#editUuid").value;
  const currentKey = currentUuid.toLowerCase();
  return (state.board?.columns || [])
    .flatMap((column) => column.tasks)
    .filter((task) => {
      const taskKey = String(task.uuid).toLowerCase();
      if (task.status === "completed" || taskKey === currentKey) return false;
      if (taskDependsOn(task.uuid, currentUuid)) return false;
      return [task.description, task.project, task.uuid, ...(task.tags || [])]
        .join(" ")
        .toLowerCase()
        .includes(normalized);
    })
    .sort((left, right) => left.description.localeCompare(right.description))
    .slice(0, 8);
}

function dependencyMeta(task) {
  return `${task.project || "No project"} / ${shortUuid(task.uuid)}`;
}

function titleCase(value) {
  const text = String(value || "unknown");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function selectedDependencyDetail(uuid) {
  const editedTask = findTask(document.querySelector("#editUuid").value);
  const existing = editedTask && dependencyDetails(editedTask)
    .find((detail) => detail.uuid.toLowerCase() === String(uuid).toLowerCase());
  if (existing) return existing;
  const task = findTask(uuid);
  return {
    uuid: String(uuid),
    description: task?.description || `Task ${shortUuid(uuid)}`,
    project: task?.project || "",
    status: task?.status || "unknown",
    resolved: ["completed", "deleted"].includes(task?.status),
    blocking: ["pending", "waiting"].includes(task?.status),
  };
}

function renderDependencySelection() {
  document.querySelector("#editDepends").value = state.editDependencies.join(",");
  els.dependencyCount.textContent = String(state.editDependencies.length);
  els.editDependencies.innerHTML = state.editDependencies.length
    ? state.editDependencies.map((uuid) => {
      const task = findTask(uuid);
      const detail = selectedDependencyDetail(uuid);
      const stateLabel = detail.blocking ? "Unresolved" : detail.resolved ? "Resolved" : "Missing";
      const stateClass = detail.blocking ? "unresolved" : detail.resolved ? "resolved" : "missing";
      const name = detail.description || `Task ${shortUuid(uuid)}`;
      return `<article class="dependency-item is-${stateClass}">
        <div class="dependency-copy">
          ${task
            ? `<button class="dependency-open" type="button" data-open-task="${escapeHtml(task.uuid)}"><strong>${escapeHtml(name)}</strong></button>`
            : `<strong>${escapeHtml(name)}</strong>`}
          <span>${escapeHtml(detail.project || "No project")} / ${escapeHtml(shortUuid(uuid))} / ${escapeHtml(titleCase(detail.status))}</span>
        </div>
        <span class="dependency-state ${stateClass}">${stateLabel}</span>
        <button class="dependency-remove" type="button" data-remove-dependency="${escapeHtml(uuid)}" aria-label="Remove dependency ${escapeHtml(name)}" title="Remove dependency">${icon("x")}</button>
      </article>`;
    }).join("")
    : `<p class="empty-inline">No dependencies. This task can proceed independently.</p>`;
}

function renderDependents(task) {
  const dependents = dependentTasks(task);
  els.dependentCount.textContent = String(dependents.length);
  els.editDependents.innerHTML = dependents.length
    ? dependents.map((dependent) => {
      const known = findTask(dependent.uuid);
      const content = `<strong>${escapeHtml(dependent.description || dependent.uuid)}</strong><span>${escapeHtml(dependent.project || "No project")} / ${escapeHtml(shortUuid(dependent.uuid))}</span>`;
      return `<article class="dependent-item">
        ${known ? `<button class="dependent-open" type="button" data-open-task="${escapeHtml(dependent.uuid)}">${content}</button>` : `<div class="dependent-open">${content}</div>`}
      </article>`;
    }).join("")
    : `<p class="empty-inline">No unfinished tasks depend on this task.</p>`;
}

function renderDependencyResults() {
  const matches = dependencySearchMatches(els.editDependencySearch.value);
  const query = els.editDependencySearch.value.trim();
  const hasQuery = Boolean(query);
  const canCreate = hasQuery && !matches.some((task) =>
    task.description.trim().toLowerCase() === query.toLowerCase());
  els.dependencyResults.hidden = !hasQuery;
  els.editDependencySearch.setAttribute("aria-expanded", hasQuery ? "true" : "false");
  const resultHtml = matches.length
    ? matches.map((task) => {
      const selected = state.editDependencies.some((uuid) => uuid.toLowerCase() === String(task.uuid).toLowerCase());
      if (!selected) {
        return `<button type="button" role="option" data-add-dependency="${escapeHtml(task.uuid)}">
          <strong>${escapeHtml(task.description)}</strong>
          <span>${escapeHtml(dependencyMeta(task))}</span>
        </button>`;
      }
      return `<article class="dependency-result is-selected" data-selected-dependency="${escapeHtml(task.uuid)}">
        <button class="dependency-result-copy" type="button" data-open-task="${escapeHtml(task.uuid)}" title="View task">
          <strong>${escapeHtml(task.description)}</strong>
          <span>${escapeHtml(dependencyMeta(task))}</span>
        </button>
        <span class="dependency-state resolved">Added</span>
        <button class="dependency-remove" type="button" data-remove-dependency="${escapeHtml(task.uuid)}" aria-label="Remove dependency ${escapeHtml(task.description)}" title="Remove dependency">${icon("x")}</button>
      </article>`;
    }).join("")
    : hasQuery ? `<p class="empty-inline">No matching unfinished tasks.</p>` : "";
  const createHtml = canCreate
    ? `<button class="dependency-create" type="button" data-create-dependency="${escapeHtml(query)}">
        ${icon("plus")}<span><strong>Create “${escapeHtml(query)}”</strong><small>New Backlog task in this project, attached immediately</small></span>
      </button>`
    : "";
  els.dependencyResults.innerHTML = resultHtml + createHtml;
}

function addDependency(uuid) {
  const task = findTask(uuid);
  const currentUuid = document.querySelector("#editUuid").value;
  const uuidKey = String(uuid).toLowerCase();
  if (!task || task.status === "completed" || uuidKey === currentUuid.toLowerCase()) return;
  if (state.editDependencies.some((dependency) => dependency.toLowerCase() === uuidKey)) return;
  if (taskDependsOn(uuid, currentUuid)) return;
  state.editDependencies.push(uuid);
  renderDependencySelection();
  renderDependencyResults();
  updateEditDirty();
  els.editDependencySearch.focus();
}

function removeDependency(uuid) {
  state.editDependencies = state.editDependencies.filter((dependency) => dependency !== uuid);
  renderDependencySelection();
  renderDependencyResults();
  updateEditDirty();
}

function updateSnapshotDependency(uuid) {
  if (!state.editSnapshot) return;
  const snapshot = JSON.parse(state.editSnapshot);
  snapshot.dependencies = [...new Set([...(snapshot.dependencies || []), uuid])];
  state.editSnapshot = JSON.stringify(snapshot);
}

async function createDependency(description) {
  const uuid = document.querySelector("#editUuid").value;
  const retry = () => createDependency(description);
  setTaskSync(uuid, "saving", { message: "Creating and attaching dependency." });
  setBusy(true);
  try {
    const result = await api(`/api/tasks/${encodeURIComponent(uuid)}/dependencies`, {
      method: "POST",
      body: JSON.stringify({ description, expected_modified: state.editExpectedModified }),
    });
    render(result.board);
    const parent = findTask(uuid);
    state.editExpectedModified = parent?.modified || state.editExpectedModified;
    if (parent) state.editOriginalTask = structuredClone(parent);
    state.editDependencies = [...new Set([...state.editDependencies, result.created_uuid])];
    updateSnapshotDependency(result.created_uuid);
    renderDependencySelection();
    renderDependencyResults();
    updateEditDirty();
    els.editDependencySearch.focus();
    setTaskSync(uuid, "saved", { message: "Dependency attached.", clearAfter: 2500 });
  } catch (error) {
    setTaskMutationFailure(uuid, error, retry);
    if (!showEditConflict(error)) showError(error);
  } finally {
    setBusy(false);
  }
}

function editValues() {
  return {
    description: document.querySelector("#editDescription").value,
    project: document.querySelector("#editProject").value,
    tags: document.querySelector("#editTags").value,
    priority: document.querySelector("#editPriority").value,
    due: document.querySelector("#editDue").value,
    wait: document.querySelector("#editWait").value,
    scheduled: document.querySelector("#editScheduled").value,
    dependencies: [...state.editDependencies],
    annotation: document.querySelector("#editAnnotation").value,
  };
}

function updateEditDirty() {
  state.editDirty = Boolean(state.editSnapshot) && JSON.stringify(editValues()) !== state.editSnapshot;
  els.editDirty.hidden = !state.editDirty;
}

function confirmDiscard() {
  return !state.editDirty || window.confirm("Discard your unsaved changes?");
}

function closeEditWithoutWarning({ updateHistory = true, restoreFocus = true } = {}) {
  const returnUuid = state.editReturnFocusUuid || document.querySelector("#editUuid").value;
  state.editSnapshot = null;
  state.editDirty = false;
  state.editOriginalTask = null;
  state.conflictTask = null;
  els.editConflict.hidden = true;
  els.editDirty.hidden = true;
  els.editDialog.close();
  if (updateHistory) syncUrl({ task: null });
  if (restoreFocus) refocusTask(returnUuid);
  state.editReturnFocusUuid = null;
}

function attemptCloseEdit() {
  if (!confirmDiscard()) return false;
  closeEditWithoutWarning();
  return true;
}

function requestOpenTask(uuid) {
  if (els.editDialog.open && !confirmDiscard()) return;
  if (!els.editDialog.open) {
    state.editReturnFocusUuid = focusedCard()?.dataset.uuid || uuid;
  }
  openEdit(uuid);
}

function openEdit(uuid, { syncHistory = true } = {}) {
  const task = findTask(uuid);
  if (!task) return;
  const previousUuid = els.editDialog.open ? document.querySelector("#editUuid").value : null;
  state.editSnapshot = null;
  state.editDirty = false;
  state.editExpectedModified = task.modified || "";
  state.editOriginalTask = structuredClone(task);
  state.conflictTask = null;
  els.editConflict.hidden = true;
  els.editDirty.hidden = true;
  els.editSync.hidden = true;
  document.querySelector("#editUuid").value = task.uuid;
  document.querySelector("#editDescription").value = task.description || "";
  document.querySelector("#editProject").value = task.project || "";
  document.querySelector("#editTags").value = (task.tags || [])
    .filter((tag) => !MANAGED_TAGS.has(tag))
    .join(", ");
  document.querySelector("#editPriority").value = task.priority || "";
  document.querySelector("#editDue").value = formatDate(task.due || "");
  document.querySelector("#editWait").value = formatDate(task.wait || "");
  document.querySelector("#editScheduled").value = formatDate(task.scheduled || "");
  state.editDependencies = [...new Set((task.depends || []).map(String))];
  els.editDependencySearch.value = "";
  renderDependencySelection();
  renderDependencyResults();
  renderDependents(task);
  document.querySelector("#editAnnotation").value = "";
  renderAnnotations(task.annotations || []);
  renderNativeMeta(task);
  const column = state.board.columns.find((candidate) =>
    candidate.tasks.some((item) => item.uuid === task.uuid));
  els.editContext.textContent = `${column?.title || task.status} / ${task.project || "No project"} / ${shortUuid(task.uuid)}`;
  els.editStart.hidden = task.status === "completed" || Boolean(task.start);
  els.editStop.hidden = !task.start;
  els.editComplete.hidden = task.status === "completed";
  els.editReopen.hidden = task.status !== "completed";
  state.editSnapshot = JSON.stringify(editValues());
  if (!els.editDialog.open) els.editDialog.showModal();
  renderTaskSync(task.uuid);
  if (syncHistory && previousUuid !== task.uuid) syncUrl({ push: true, task: task.uuid });
}

function comparableTaskValue(task, field) {
  if (field === "tags" || field === "depends") {
    return [...(task?.[field] || [])].map(String).sort().join(", ") || "none";
  }
  return String(task?.[field] || "none");
}

function showEditConflict(error) {
  if (!els.editDialog.open
    || !(error instanceof ApiError)
    || error.status !== 409
    || !error.payload?.current_task) {
    return false;
  }
  const current = error.payload.current_task;
  if (String(current.uuid).toLowerCase() !== document.querySelector("#editUuid").value.toLowerCase()) {
    return false;
  }
  const labels = {
    description: "Description",
    project: "Project",
    tags: "Tags",
    priority: "Priority",
    due: "Due date",
    wait: "Wait date",
    scheduled: "Scheduled date",
    depends: "Dependencies",
  };
  const changed = Object.entries(labels).filter(([field]) =>
    comparableTaskValue(state.editOriginalTask, field) !== comparableTaskValue(current, field));
  els.editConflictFields.innerHTML = changed.length
    ? changed.map(([field, label]) => `<li><strong>${label}:</strong> ${escapeHtml(comparableTaskValue(current, field))}</li>`).join("")
    : `<li>The task timestamp changed; its editable fields currently match this form.</li>`;
  state.conflictTask = current;
  els.editConflict.hidden = false;
  setTaskSync(current.uuid, "conflict", { message: "Conflict. Choose how to continue." });
  els.editConflict.scrollIntoView({ block: "nearest", behavior: scrollBehavior() });
  return true;
}

async function reloadConflict() {
  const uuid = document.querySelector("#editUuid").value;
  setBusy(true);
  try {
    render(await api("/api/board"));
    openEdit(uuid);
    clearTaskSync(uuid);
  } catch (error) {
    showError(error);
  } finally {
    setBusy(false);
  }
}

function keepConflictEdits() {
  if (!state.conflictTask) return;
  state.editExpectedModified = state.conflictTask.modified || "";
  state.editOriginalTask = structuredClone(state.conflictTask);
  state.conflictTask = null;
  els.editConflict.hidden = true;
  clearTaskSync(document.querySelector("#editUuid").value);
}

function renderAnnotations(annotations) {
  document.querySelector("#annotationCount").textContent = String(annotations.length);
  document.querySelector("#editAnnotations").innerHTML = annotations.length
    ? annotations.map((annotation) => `
      <article class="annotation">
        <p>${escapeHtml(annotationDescription(annotation))}</p>
        ${annotation?.entry ? `<time>${escapeHtml(formatTimestamp(annotation.entry))}</time>` : ""}
      </article>`).join("")
    : `<p class="empty-inline">No annotations yet.</p>`;
}

function renderNativeMeta(task) {
  const details = [
    task.scheduled ? ["Scheduled", `${formatDate(task.scheduled)} (${relativeDate(task.scheduled)})`] : null,
    task.recur ? ["Recurrence", task.recur] : null,
    task.until ? ["Repeats until", formatDate(task.until)] : null,
    task.parent ? ["Recurring parent", shortUuid(task.parent)] : null,
    task.modified ? ["Last modified", formatTimestamp(task.modified)] : null,
  ].filter(Boolean);
  document.querySelector("#editNativeMeta").innerHTML = details.length
    ? details.map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("")
    : `<p class="empty-inline">No additional Taskwarrior metadata.</p>`;
}

async function handleDialogAction(column) {
  const uuid = document.querySelector("#editUuid").value;
  const needsCompletionWarning = column === "done" && findTaskColumn(uuid) !== "done";
  if (needsCompletionWarning && !confirmCompletion(uuid)) return;
  if (!confirmDiscard()) return;
  if (await moveTask(uuid, column, { completionConfirmed: needsCompletionWarning })) closeEditWithoutWarning();
}

async function handleCardAction(uuid, action) {
  if (action === "edit") {
    requestOpenTask(uuid);
    return;
  }
  await moveTask(uuid, action);
}

async function deleteTaskFromDialog() {
  const uuid = document.querySelector("#editUuid").value;
  const task = findTask(uuid);
  if (!task) return;
  const names = dependentNames(task);
  let message = `Delete "${task.description}"?\n\nThis cannot be undone.`;
  if (names.length) {
    message += `\n\nThis task currently blocks:\n- ${names.join("\n- ")}\n\nTheir dependency will become unresolved.`;
  }
  if (!window.confirm(message)) return;
  if (!confirmDiscard()) return;

  setTaskSync(uuid, "saving", { message: "Deleting task." });
  setBusy(true);
  try {
    render(await api(`/api/tasks/${encodeURIComponent(uuid)}`, {
      method: "DELETE",
      body: JSON.stringify({ expected_modified: state.editExpectedModified }),
    }));
    closeEditWithoutWarning();
  } catch (error) {
    setTaskMutationFailure(uuid, error, deleteTaskFromDialog);
    if (!showEditConflict(error)) showError(error);
  } finally {
    setBusy(false);
  }
}

function showError(error) {
  state.requestError = error.message || String(error);
  els.status.textContent = `Request failed: ${state.requestError}`;
  els.status.title = state.requestError;
  els.status.classList.add("error");
  els.syncCard.classList.add("error");
}

function saveFilters() {
  if (Object.values(state.filters).some(Boolean)) {
    localStorage.setItem(STORAGE_KEYS.filters, JSON.stringify(state.filters));
  } else {
    localStorage.removeItem(STORAGE_KEYS.filters);
  }
}

function emptyFilters() {
  return { search: "", project: "", tag: "", priority: "", readiness: "", due: "" };
}

function persistActiveView() {
  if (state.activeView) {
    localStorage.setItem(STORAGE_KEYS.activeView, state.activeView);
  } else {
    localStorage.removeItem(STORAGE_KEYS.activeView);
  }
}

function applyView(value) {
  state.activeView = value;
  const saved = value.startsWith("custom:")
    ? state.savedViews.find((view) => `custom:${view.id}` === value)
    : null;
  state.filters = { ...emptyFilters(), ...(saved?.filters || {}) };
  if (saved && SORT_MODES.has(saved.sort)) state.sortMode = saved.sort;
  if (!saved) state.filters = emptyFilters();
  persistActiveView();
  localStorage.setItem(STORAGE_KEYS.sort, state.sortMode);
  saveFilters();
  renderFilterOptions(state.board);
  restoreFilterControls();
  renderViewOptions();
  renderBoard();
  syncUrl({ push: true, task: null });
}

function saveCurrentView() {
  const name = window.prompt("Name this view:", "");
  if (!name?.trim()) return;
  const normalized = name.trim();
  const existing = state.savedViews.find((view) => view.name.toLowerCase() === normalized.toLowerCase());
  const view = {
    id: existing?.id || `${Date.now()}`,
    name: normalized,
    focus: currentFocusView(),
    filters: { ...state.filters },
    sort: state.sortMode,
  };
  state.savedViews = existing
    ? state.savedViews.map((candidate) => candidate.id === existing.id ? view : candidate)
    : [...state.savedViews, view];
  state.activeView = `custom:${view.id}`;
  localStorage.setItem(STORAGE_KEYS.views, JSON.stringify(state.savedViews));
  persistActiveView();
  renderViewOptions();
  renderBoard();
  syncUrl({ push: true });
}

function deleteCurrentView() {
  if (!state.activeView.startsWith("custom:")) return;
  const id = state.activeView.slice("custom:".length);
  const view = state.savedViews.find((candidate) => candidate.id === id);
  if (!view || !window.confirm(`Delete saved view “${view.name}”?`)) return;
  state.savedViews = state.savedViews.filter((candidate) => candidate.id !== id);
  state.activeView = "";
  localStorage.setItem(STORAGE_KEYS.views, JSON.stringify(state.savedViews));
  persistActiveView();
  renderViewOptions();
  renderBoard();
  syncUrl({ push: true });
}

function updateSort() {
  state.sortMode = SORT_MODES.has(els.sortMode.value) ? els.sortMode.value : "due";
  localStorage.setItem(STORAGE_KEYS.sort, state.sortMode);
  if (state.activeView.startsWith("custom:")) {
    state.activeView = "";
    persistActiveView();
  }
  renderViewOptions();
  renderBoard();
  syncUrl({ push: true });
}

function updateFilters({ push = false } = {}) {
  state.filters.search = els.searchInput.value;
  state.filters.project = els.projectFilter.value;
  state.filters.tag = els.tagFilter.value;
  state.filters.priority = els.priorityFilter.value;
  state.filters.readiness = els.readinessFilter.value;
  state.filters.due = els.dueFilter.value;
  if (state.activeView.startsWith("custom:")) {
    state.activeView = "";
    persistActiveView();
    renderViewOptions();
  }
  saveFilters();
  renderBoard();
  syncUrl({ push });
}

function clearFilters() {
  state.activeView = "";
  persistActiveView();
  els.searchInput.value = "";
  els.projectFilter.value = "";
  els.tagFilter.value = "";
  els.priorityFilter.value = "";
  els.readinessFilter.value = "";
  els.dueFilter.value = "";
  updateFilters({ push: true });
  renderViewOptions();
}

function restoreFilterControls() {
  els.searchInput.value = state.filters.search || "";
  els.projectFilter.value = state.filters.project || "";
  els.tagFilter.value = state.filters.tag || "";
  els.priorityFilter.value = state.filters.priority || "";
  els.readinessFilter.value = state.filters.readiness || "";
  els.dueFilter.value = state.filters.due || "";
}

function expandColumns() {
  state.collapsedColumns.clear();
  saveCollapsedColumns();
  renderBoard();
}

function collapseEmptyColumns() {
  if (!state.board || !Array.isArray(state.board.columns)) return;
  state.board.columns.forEach((column) => {
    if (column.tasks.filter((task) => filterTask(task, column.id)).length === 0) {
      state.collapsedColumns.add(column.id);
    }
  });
  saveCollapsedColumns();
  renderBoard();
}

function visibleTasks() {
  return (state.board?.columns || []).flatMap((column) =>
    column.tasks.filter((task) => filterTask(task, column.id)));
}

function renderBulkControls() {
  const count = state.selectedUuids.size;
  els.bulkCount.textContent = `${count} selected`;
  els.bulkForm.hidden = count === 0;
  els.clearSelection.hidden = count === 0;
  els.selectVisible.disabled = visibleTasks().length === 0;
  els.bulkPanel.classList.toggle("has-selection", count > 0);
}

function toggleTaskSelection(uuid) {
  if (state.selectedUuids.has(uuid)) {
    state.selectedUuids.delete(uuid);
  } else {
    state.selectedUuids.add(uuid);
  }
  renderBoard();
}

function selectVisibleTasks() {
  visibleTasks().forEach((task) => state.selectedUuids.add(task.uuid));
  renderBoard();
}

function clearTaskSelection() {
  state.selectedUuids.clear();
  renderBoard();
}

function bulkChanges() {
  const changes = {};
  const project = document.querySelector("#bulkProject").value.trim();
  const tags = document.querySelector("#bulkTags").value.trim();
  const priority = document.querySelector("#bulkPriority").value;
  const column = document.querySelector("#bulkColumn").value;
  if (project) changes.project = project;
  if (tags) changes.tags = tags;
  if (priority !== "__unchanged__") changes.priority = priority;
  if (els.bulkDueEnabled.checked) changes.due = els.bulkDue.value;
  if (column) changes.column = column;
  return changes;
}

function resetBulkForm() {
  els.bulkForm.reset();
  document.querySelector("#bulkPriority").value = "__unchanged__";
  els.bulkDue.disabled = true;
}

async function submitBulkChanges(event) {
  event.preventDefault();
  const changes = bulkChanges();
  if (!Object.keys(changes).length) {
    showError(new Error("Choose at least one bulk change."));
    return;
  }
  const tasks = [...state.selectedUuids].map((uuid) => findTask(uuid)).filter(Boolean);
  if (changes.column === "done") {
    const blockers = tasks.filter((task) => dependentTasks(task).length);
    if (blockers.length && !window.confirm(
      `Complete ${tasks.length} selected tasks?\n\n${blockers.length} currently block unfinished work.`,
    )) return;
  }
  const retry = () => els.bulkForm.requestSubmit();
  tasks.forEach((task) => setTaskSync(task.uuid, "saving", { message: "Applying bulk changes." }));
  setBusy(true);
  try {
    const payload = await api("/api/tasks/bulk", {
      method: "POST",
      body: JSON.stringify({
        tasks: tasks.map((task) => ({ uuid: task.uuid, expected_modified: task.modified || "" })),
        changes,
      }),
    });
    state.selectedUuids.clear();
    resetBulkForm();
    render(payload);
    tasks.forEach((task) => setTaskSync(task.uuid, "saved", { message: "Bulk changes saved.", clearAfter: 2500 }));
  } catch (error) {
    tasks.forEach((task) => setTaskMutationFailure(task.uuid, error, retry));
    showError(error);
  } finally {
    setBusy(false);
  }
}

function setSidebarCollapsed(collapsed) {
  document.body.classList.toggle("sidebar-collapsed", collapsed);
  localStorage.setItem(STORAGE_KEYS.sidebar, collapsed ? "1" : "0");
  els.sidebarToggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
}

function toggleSidebar() {
  setSidebarCollapsed(!document.body.classList.contains("sidebar-collapsed"));
}

function restoreSidebarState() {
  if (SIDEBAR_DRAWER_QUERY.matches || localStorage.getItem(STORAGE_KEYS.sidebar) === "1") {
    setSidebarCollapsed(true);
  }
}

function focusNewTask() {
  const input = document.querySelector("#newDescription");
  input.scrollIntoView({ block: "center", behavior: scrollBehavior() });
  input.focus();
}

function focusSearch() {
  setSidebarCollapsed(false);
  els.searchInput.focus();
  els.searchInput.select();
}

function toggleShortcutsPanel() {
  setSidebarCollapsed(false);
  els.shortcutsPanel.open = !els.shortcutsPanel.open;
  els.shortcutsPanel.scrollIntoView({ block: "nearest", behavior: scrollBehavior() });
}

function isTextEntryTarget(target) {
  return target instanceof Element && target.matches("input, textarea, select, [contenteditable='true']");
}

function isVisible(element) {
  return Boolean(element && element.getClientRects().length && getComputedStyle(element).visibility !== "hidden");
}

function focusCard(card) {
  if (!card) return;
  state.focusedUuid = card.dataset.uuid;
  els.board.querySelectorAll(".card").forEach((candidate) => {
    candidate.tabIndex = candidate === card ? 0 : -1;
  });
  card.focus();
  card.scrollIntoView({ block: "nearest", inline: "nearest", behavior: scrollBehavior() });
}

function focusFirstCard() {
  focusCard([...els.board.querySelectorAll(".card")].find(isVisible));
}

function focusedCard() {
  return document.activeElement?.classList?.contains("card") ? document.activeElement : null;
}

function moveCardFocusWithinColumn(card, offset) {
  const cards = [...card.closest(".column").querySelectorAll(".card")].filter(isVisible);
  const index = cards.indexOf(card);
  const target = cards[index + offset];
  if (target) {
    focusCard(target);
  } else if (offset < 0) {
    card.closest(".column").querySelector("[data-column-toggle]")?.focus();
  }
}

function focusCardFromColumnControl(control) {
  const card = [...control.closest(".column").querySelectorAll(".card")].find(isVisible);
  focusCard(card);
}

function focusAdjacentColumnControl(control, offset) {
  const controls = [...els.board.querySelectorAll("[data-column-toggle]")].filter(isVisible);
  const index = controls.indexOf(control);
  controls[index + offset]?.focus();
}

function focusCardInAdjacentColumn(card, offset) {
  const currentColumnId = card.closest(".column")?.dataset.column;
  const columns = (state.board?.columns || []).filter((column) => {
    if (!column.tasks.some((task) => filterTask(task, column.id))) return false;
    return MOBILE_QUERY.matches || !state.collapsedColumns.has(column.id);
  });
  const currentIndex = columns.findIndex((column) => column.id === currentColumnId);
  const target = columns[currentIndex + offset];
  if (!target) return;
  const cardIndex = [...card.closest(".column").querySelectorAll(".card")].indexOf(card);
  if (MOBILE_QUERY.matches) {
    state.activeColumn = target.id;
    renderBoard();
    syncUrl();
  }
  window.requestAnimationFrame(() => {
    const targetColumn = [...els.board.querySelectorAll(".column")]
      .find((column) => column.dataset.column === target.id);
    const targetCards = [...(targetColumn?.querySelectorAll(".card") || [])].filter(isVisible);
    focusCard(targetCards[Math.min(Math.max(cardIndex, 0), targetCards.length - 1)]);
  });
}

async function moveFocusedTaskByOffset(card, offset) {
  const currentIndex = ACTIONS.findIndex(([column]) => column === findTaskColumn(card.dataset.uuid));
  const target = ACTIONS[currentIndex + offset];
  if (!target) return;
  await moveTask(card.dataset.uuid, target[0], { refocus: true });
}

function openDatePicker(event) {
  const input = document.querySelector(`#${event.currentTarget.dataset.datePicker}`);
  if (!input) return;
  input.focus();
  if (typeof input.showPicker === "function") {
    input.showPicker();
  } else {
    input.click();
  }
}

async function handleGlobalShortcut(event) {
  if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey) return;
  if (document.querySelector("dialog[open]") || isTextEntryTarget(event.target)) return;

  const key = event.key.toLowerCase();
  const card = focusedCard();
  const columnControl = document.activeElement?.matches?.("[data-column-toggle]")
    ? document.activeElement
    : null;
  if (columnControl) {
    const columnId = columnControl.dataset.columnToggle;
    if (key === "x") {
      event.preventDefault();
      toggleColumn(columnId, { focusControl: true });
      return;
    }
    if (key === "arrowdown" || key === "j") {
      event.preventDefault();
      focusCardFromColumnControl(columnControl);
      return;
    }
    if (["arrowleft", "h", "arrowright", "l"].includes(key)) {
      event.preventDefault();
      focusAdjacentColumnControl(columnControl, ["arrowleft", "h"].includes(key) ? -1 : 1);
      return;
    }
  }
  if (card && event.shiftKey && ["arrowleft", "arrowright", "h", "l"].includes(key)) {
    event.preventDefault();
    await moveFocusedTaskByOffset(card, ["arrowleft", "h"].includes(key) ? -1 : 1);
    return;
  }
  if (card && key === "x") {
    event.preventDefault();
    toggleColumn(card.closest(".column").dataset.column, { focusControl: true });
    return;
  }
  const movement = {
    h: () => focusCardInAdjacentColumn(card, -1),
    arrowleft: () => focusCardInAdjacentColumn(card, -1),
    l: () => focusCardInAdjacentColumn(card, 1),
    arrowright: () => focusCardInAdjacentColumn(card, 1),
    j: () => moveCardFocusWithinColumn(card, 1),
    arrowdown: () => moveCardFocusWithinColumn(card, 1),
    k: () => moveCardFocusWithinColumn(card, -1),
    arrowup: () => moveCardFocusWithinColumn(card, -1),
  };
  if (card && movement[key]) {
    event.preventDefault();
    movement[key]();
    return;
  }
  if (card && /^[1-5]$/.test(key)) {
    event.preventDefault();
    await moveTask(card.dataset.uuid, ACTIONS[Number(key) - 1][0], { refocus: true });
    return;
  }

  const shortcuts = {
    "/": focusSearch,
    "?": toggleShortcutsPanel,
    b: toggleSidebar,
    c: collapseEmptyColumns,
    e: expandColumns,
    g: focusFirstCard,
    n: focusNewTask,
    r: loadBoard,
    s: syncNow,
  };
  const action = shortcuts[key];
  if (action) {
    event.preventDefault();
    action();
  }
}

function applyUrlFromHistory() {
  const urlState = readUrlState();
  const currentTask = els.editDialog.open ? document.querySelector("#editUuid").value : null;
  if (els.editDialog.open && currentTask !== urlState.task && !confirmDiscard()) {
    syncUrl({ push: true, task: currentTask });
    return;
  }

  state.urlTask = urlState.task;
  state.activeView = urlState.view;
  state.sortMode = urlState.sort;
  state.filters = urlState.filters;
  state.activeColumn = urlState.column;
  persistActiveView();
  localStorage.setItem(STORAGE_KEYS.sort, state.sortMode);
  saveFilters();
  if (!state.board) return;

  renderFilterOptions(state.board);
  restoreFilterControls();
  renderViewOptions();
  renderBoard();
  if (urlState.task && findTask(urlState.task)) {
    if (currentTask !== urlState.task) {
      if (els.editDialog.open) closeEditWithoutWarning({ updateHistory: false, restoreFocus: false });
      state.editReturnFocusUuid = state.focusedUuid;
      openEdit(urlState.task, { syncHistory: false });
    }
  } else if (els.editDialog.open) {
    closeEditWithoutWarning({ updateHistory: false });
  }
  announce("Board view restored from browser history.");
}

function bindEvents() {
  els.sidebarToggle.addEventListener("click", toggleSidebar);
  els.sidebarBackdrop.addEventListener("click", () => setSidebarCollapsed(true));
  els.syncButton.addEventListener("click", syncNow);
  els.refreshButton.addEventListener("click", loadBoard);
  els.expandColumns.addEventListener("click", expandColumns);
  els.collapseEmptyColumns.addEventListener("click", collapseEmptyColumns);
  els.focusView.addEventListener("change", () => applyView(els.focusView.value));
  els.sortMode.addEventListener("change", updateSort);
  els.saveView.addEventListener("click", saveCurrentView);
  els.deleteView.addEventListener("click", deleteCurrentView);
  els.searchInput.addEventListener("input", () => updateFilters());
  els.projectFilter.addEventListener("change", () => updateFilters({ push: true }));
  els.tagFilter.addEventListener("change", () => updateFilters({ push: true }));
  els.priorityFilter.addEventListener("change", () => updateFilters({ push: true }));
  els.readinessFilter.addEventListener("change", () => updateFilters({ push: true }));
  els.dueFilter.addEventListener("change", () => updateFilters({ push: true }));
  els.clearFilters.addEventListener("click", clearFilters);
  els.selectVisible.addEventListener("click", selectVisibleTasks);
  els.clearSelection.addEventListener("click", clearTaskSelection);
  els.bulkForm.addEventListener("submit", submitBulkChanges);
  els.bulkDueEnabled.addEventListener("change", () => {
    els.bulkDue.disabled = !els.bulkDueEnabled.checked;
    if (els.bulkDueEnabled.checked) els.bulkDue.focus();
  });
  els.editDependencySearch.addEventListener("input", renderDependencyResults);
  els.editDependencySearch.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      const firstMatch = dependencySearchMatches(els.editDependencySearch.value)[0];
      const selected = firstMatch && state.editDependencies.some((uuid) => uuid.toLowerCase() === String(firstMatch.uuid).toLowerCase());
      if (firstMatch && !selected) addDependency(firstMatch.uuid);
      if (!firstMatch && els.editDependencySearch.value.trim()) {
        createDependency(els.editDependencySearch.value.trim());
      }
    } else if (event.key === "Escape") {
      event.preventDefault();
      els.editDependencySearch.value = "";
      renderDependencyResults();
    }
  });
  els.editDependencies.addEventListener("click", (event) => {
    const removeButton = event.target instanceof Element && event.target.closest("[data-remove-dependency]");
    const openButton = event.target instanceof Element && event.target.closest("[data-open-task]");
    if (removeButton) removeDependency(removeButton.dataset.removeDependency);
    if (openButton) requestOpenTask(openButton.dataset.openTask);
  });
  els.editDependents.addEventListener("click", (event) => {
    const button = event.target instanceof Element && event.target.closest("[data-open-task]");
    if (button) requestOpenTask(button.dataset.openTask);
  });
  els.dependencyResults.addEventListener("click", (event) => {
    const addButton = event.target instanceof Element && event.target.closest("[data-add-dependency]");
    const removeButton = event.target instanceof Element && event.target.closest("[data-remove-dependency]");
    const openButton = event.target instanceof Element && event.target.closest("[data-open-task]");
    const createButton = event.target instanceof Element && event.target.closest("[data-create-dependency]");
    if (addButton) addDependency(addButton.dataset.addDependency);
    if (removeButton) removeDependency(removeButton.dataset.removeDependency);
    if (openButton) requestOpenTask(openButton.dataset.openTask);
    if (createButton) createDependency(createButton.dataset.createDependency);
  });
  document.querySelectorAll("[data-date-picker]").forEach((button) => {
    button.addEventListener("click", openDatePicker);
  });
  document.addEventListener("keydown", handleGlobalShortcut);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) refreshIfIdle();
  });
  SIDEBAR_DRAWER_QUERY.addEventListener("change", (event) => {
    if (event.matches) setSidebarCollapsed(true);
  });
  MOBILE_QUERY.addEventListener("change", () => {
    renderBoard();
  });
  els.board.addEventListener("scroll", updateBoardOverflow, { passive: true });
  window.addEventListener("resize", updateBoardOverflow);
  window.addEventListener("popstate", applyUrlFromHistory);
  window.addEventListener("online", () => {
    state.taskSync.forEach((sync, uuid) => {
      if (sync.status !== "offline") return;
      state.taskSync.set(uuid, { ...sync, status: "retry" });
      renderTaskSync(uuid);
    });
    announce("Connection restored. Retry any unsaved task actions.");
  });

  els.editForm.addEventListener("input", (event) => {
    if (event.target !== els.editDependencySearch) updateEditDirty();
  });
  els.editForm.addEventListener("change", (event) => {
    if (event.target !== els.editDependencySearch) updateEditDirty();
  });
  document.querySelector("#cancelEdit").addEventListener("click", attemptCloseEdit);
  document.querySelector("#closeEdit").addEventListener("click", attemptCloseEdit);
  els.editStart.addEventListener("click", () => handleDialogAction("doing"));
  els.editStop.addEventListener("click", () => handleDialogAction("ready"));
  els.editComplete.addEventListener("click", () => handleDialogAction("done"));
  els.editReopen.addEventListener("click", () => handleDialogAction("backlog"));
  els.editDelete.addEventListener("click", deleteTaskFromDialog);
  document.querySelector("#reloadConflict").addEventListener("click", reloadConflict);
  document.querySelector("#keepConflictEdits").addEventListener("click", keepConflictEdits);
  els.editDialog.addEventListener("click", (event) => {
    if (event.target === els.editDialog) attemptCloseEdit();
  });
  els.editDialog.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    event.preventDefault();
    attemptCloseEdit();
  });
  els.editDialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    attemptCloseEdit();
  });
  els.editDialog.addEventListener("close", () => {
    state.editSnapshot = null;
    state.editDirty = false;
    state.editOriginalTask = null;
    state.conflictTask = null;
    els.editConflict.hidden = true;
    els.editDirty.hidden = true;
    els.editSync.hidden = true;
  });
  window.addEventListener("beforeunload", (event) => {
    if (!state.editDirty) return;
    event.preventDefault();
    event.returnValue = "";
  });

  els.quickAdd.addEventListener("submit", async (event) => {
    event.preventDefault();
    const column = document.querySelector("#newColumn").value;
    const payload = {
      description: document.querySelector("#newDescription").value,
      column,
      project: document.querySelector("#newProject").value,
      tags: document.querySelector("#newTags").value,
      priority: document.querySelector("#newPriority").value,
      due: document.querySelector("#newDue").value,
    };
    setBusy(true);
    try {
      render(await api("/api/tasks", { method: "POST", body: JSON.stringify(payload) }));
      event.target.reset();
      document.querySelector("#newColumn").value = column;
    } catch (error) {
      showError(error);
    } finally {
      setBusy(false);
    }
  });

  els.editForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const uuid = document.querySelector("#editUuid").value;
    const payload = {
      description: document.querySelector("#editDescription").value,
      project: document.querySelector("#editProject").value,
      tags: document.querySelector("#editTags").value,
      priority: document.querySelector("#editPriority").value,
      due: document.querySelector("#editDue").value,
      wait: document.querySelector("#editWait").value,
      scheduled: document.querySelector("#editScheduled").value,
      depends: document.querySelector("#editDepends").value,
      annotation: document.querySelector("#editAnnotation").value,
      expected_modified: state.editExpectedModified,
    };
    const retry = () => els.editForm.requestSubmit();
    setTaskSync(uuid, "saving", { message: "Saving task changes." });
    setBusy(true);
    try {
      render(await api(`/api/tasks/${encodeURIComponent(uuid)}`, { method: "PATCH", body: JSON.stringify(payload) }));
      setTaskSync(uuid, "saved", { message: "Changes saved.", clearAfter: 2500 });
      closeEditWithoutWarning();
    } catch (error) {
      setTaskMutationFailure(uuid, error, retry);
      if (!showEditConflict(error)) showError(error);
    } finally {
      setBusy(false);
    }
  });
}

function refreshIfIdle() {
  if (document.hidden || state.busy || els.editDialog.open) return;
  loadBoard({ silent: true });
}

restoreSidebarState();
restoreFilterControls();
bindEvents();
loadBoard();
window.setInterval(refreshIfIdle, AUTO_REFRESH_MS);
window.setInterval(refreshFreshness, FRESHNESS_REFRESH_MS);
