import { mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

const stateHome = process.env.XDG_STATE_HOME || join(homedir(), ".local", "state");
const baseDir = join(stateHome, "opencode", "tmux-session-state");
const sessionDir = join(baseDir, "sessions");
const paneDir = join(baseDir, "panes");
const tmuxPane = process.env.TMUX_PANE || "";
const processID = process.pid;

const sessions = new Map();

function safeName(value) {
  return value.replace(/[^A-Za-z0-9_.%-]/g, "_");
}

function readJSON(path) {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch {
    return {};
  }
}

function writeJSON(path, value) {
  mkdirSync(dirname(path), { recursive: true });
  const tmp = `${path}.${processID}.tmp`;
  writeFileSync(tmp, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  renameSync(tmp, path);
}

function sessionPath(sessionID) {
  return join(sessionDir, `${safeName(sessionID)}.json`);
}

function panePath(paneID) {
  return join(paneDir, `${safeName(paneID)}.json`);
}

function normalizeSessionInfo(info = {}) {
  const model = info.model
    ? [info.model.providerID, info.model.id].filter(Boolean).join("/")
    : undefined;

  return {
    sessionID: info.id,
    title: info.title,
    directory: info.directory,
    parentID: info.parentID,
    agent: info.agent,
    model,
    timeCreated: info.time?.created,
    timeUpdated: info.time?.updated,
    timeArchived: info.time?.archived,
  };
}

function writeSession(sessionID, patch) {
  if (!sessionID) return;

  const path = sessionPath(sessionID);
  const current = {
    ...readJSON(path),
    ...sessions.get(sessionID),
    ...patch,
    version: 1,
    sessionID,
    tmuxPane,
    processID,
    processCwd: process.cwd(),
    lastUpdated: Date.now(),
  };

  sessions.set(sessionID, current);
  writeJSON(path, current);

  if (tmuxPane) {
    writeJSON(panePath(tmuxPane), {
      version: 1,
      sessionID,
      tmuxPane,
      processID,
      status: current.status || "unknown",
      statusText: current.statusText,
      title: current.title,
      directory: current.directory,
      lastUpdated: current.lastUpdated,
    });
  }
}

function statusPatch(status, event, statusText) {
  return {
    status,
    statusText,
    lastEvent: event.type,
    lastEventID: event.id,
    lastEventTime: Date.now(),
  };
}

export default async function () {
  mkdirSync(sessionDir, { recursive: true });
  mkdirSync(paneDir, { recursive: true });

  return {
    event: async ({ event }) => {
      const properties = event.properties || {};
      const sessionID = properties.sessionID || properties.info?.id;

      switch (event.type) {
        case "session.created":
        case "session.updated":
          writeSession(sessionID, {
            ...normalizeSessionInfo(properties.info),
            lastEvent: event.type,
            lastEventID: event.id,
            lastEventTime: Date.now(),
          });
          return;

        case "session.deleted":
          writeSession(sessionID, {
            ...normalizeSessionInfo(properties.info),
            ...statusPatch("deleted", event, "deleted"),
          });
          return;

        case "session.status": {
          const type = properties.status?.type || "unknown";
          const status = type === "busy" ? "working" : type === "retry" ? "working" : "done";
          const label = type === "retry" ? `retry ${properties.status.attempt}` : type;
          writeSession(sessionID, statusPatch(status, event, label));
          return;
        }

        case "session.idle":
          writeSession(sessionID, statusPatch("done", event, "idle"));
          return;

        case "permission.asked":
          writeSession(sessionID, statusPatch("blocked", event, "permission"));
          return;

        case "question.asked":
          writeSession(sessionID, statusPatch("blocked", event, "question"));
          return;

        case "permission.replied":
        case "question.replied":
        case "question.rejected":
          writeSession(sessionID, statusPatch("working", event, "resuming"));
          return;

        case "session.error": {
          const errorName = properties.error?.name || "error";
          writeSession(sessionID, statusPatch("error", event, errorName));
          return;
        }

        case "session.next.prompted":
        case "session.next.step.started":
        case "session.next.text.started":
        case "session.next.tool.input.started":
        case "session.next.tool.called":
          writeSession(sessionID, statusPatch("working", event, "working"));
          return;

        case "session.next.step.ended":
          writeSession(sessionID, statusPatch("done", event, properties.finish || "done"));
          return;

        case "session.next.step.failed":
        case "session.next.tool.failed":
          writeSession(sessionID, statusPatch("error", event, properties.error?.message || "failed"));
          return;

        case "message.updated":
        case "message.part.updated":
          writeSession(sessionID, {
            lastEvent: event.type,
            lastEventID: event.id,
            lastEventTime: Date.now(),
          });
          return;
      }
    },
  };
}
