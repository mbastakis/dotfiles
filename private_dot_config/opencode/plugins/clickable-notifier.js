import { execFile, execFileSync, spawn } from "node:child_process";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { basename, join } from "node:path";

const CONFIG_PATH = join(homedir(), ".config", "opencode", "clickable-notifier.json");
const FOCUS_HELPER = join(homedir(), "bin", "opencode-focus-session");
const STATE_HOME = process.env.XDG_STATE_HOME || join(homedir(), ".local", "state");
const PANE_STATE_DIR = join(STATE_HOME, "opencode", "tmux-session-state", "panes");
const TMUX_PANE = process.env.TMUX_PANE || "";
const sessionMeta = new Map();
const activeSessions = new Set();
const failedSessions = new Set();

const DEFAULT_CONFIG = {
  sound: true,
  notification: true,
  showProjectName: true,
  summaryLength: 240,
  timeout: 5,
  webPush: { enabled: false },
  events: {
    permission: { sound: true, notification: true },
    complete: { sound: true, notification: true },
    error: { sound: true, notification: true },
    question: { sound: true, notification: true },
  },
  sounds: {
    permission: "/System/Library/Sounds/Glass.aiff",
    complete: "/System/Library/Sounds/Bottle.aiff",
    error: "/System/Library/Sounds/Funk.aiff",
    question: "/System/Library/Sounds/Hero.aiff",
  },
  volumes: {
    permission: 0.5,
    complete: 0.6,
    error: 0.7,
    question: 0.5,
  },
};

function setSessionInfo(sessionInfo) {
  if (!sessionInfo?.id) return;

  sessionMeta.set(sessionInfo.id, {
    parentID: sessionInfo.parentID || "",
    title: sessionInfo.title || "",
    directory: sessionInfo.directory || "",
  });
}

function clearSessionInfo(sessionID) {
  if (sessionID) {
    sessionMeta.delete(sessionID);
  }
}

const EVENT_BY_TYPE = {
  "permission.asked": "permission",
  "question.asked": "question",
  "session.error": "error",
  "session.next.step.failed": "error",
};

function readConfig() {
  try {
    const config = JSON.parse(readFileSync(CONFIG_PATH, "utf8"));
    return {
      ...DEFAULT_CONFIG,
      ...config,
      events: { ...DEFAULT_CONFIG.events, ...(config.events || {}) },
      sounds: { ...DEFAULT_CONFIG.sounds, ...(config.sounds || {}) },
      volumes: { ...DEFAULT_CONFIG.volumes, ...(config.volumes || {}) },
      webPush: { ...DEFAULT_CONFIG.webPush, ...(config.webPush || {}) },
    };
  } catch {
    return DEFAULT_CONFIG;
  }
}

function shellQuote(value) {
  return `'${String(value).replace(/'/g, `'\\''`)}'`;
}

function appleScriptString(value) {
  return `"${String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

function findExecutable(name) {
  for (const path of [`/opt/homebrew/bin/${name}`, `/usr/local/bin/${name}`]) {
    if (existsSync(path)) return path;
  }
  return name;
}

function spawnDetached(command, args) {
  try {
    const child = spawn(command, args, { detached: true, stdio: "ignore" });
    child.unref();
  } catch {
    // Notification failures should never break OpenCode hooks.
  }
}

function playSound(config, eventName) {
  const eventConfig = config.events[eventName] || {};
  if (config.sound === false || eventConfig.sound === false) return;

  const sound = config.sounds[eventName];
  if (!sound) return;

  const volume = String(config.volumes[eventName] ?? 0.5);
  spawnDetached("/usr/bin/afplay", ["-v", volume, sound]);
}

function notificationEnabled(config, eventName) {
  const eventConfig = config.events[eventName] || {};
  return config.notification !== false && eventConfig.notification !== false;
}

function pushEnabled(config, eventName) {
  const eventConfig = config.events[eventName] || {};
  return eventConfig.push !== false;
}

function eventLabel(eventName) {
  switch (eventName) {
    case "permission":
      return "Permission needed";
    case "question":
      return "Question waiting";
    case "complete":
      return "Finished";
    case "error":
      return "Failed";
    default:
      return eventName;
  }
}

function sessionTitle(properties) {
  return properties.info?.title || properties.title || "OpenCode session";
}

function projectName(properties) {
  const directory = properties.info?.directory || properties.directory || process.cwd();
  return basename(directory) || directory || "project";
}

function plainText(value) {
  return String(value || "")
    .replace(/```[\s\S]*?```/g, " code block ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/!?(?:\[([^\]]+)\])\([^)]*\)/g, "$1")
    .replace(/^[#>*+-]+\s*/gm, "")
    .replace(/\s+/g, " ")
    .trim();
}

function truncate(value, maxLength) {
  const text = plainText(value);
  if (!maxLength || text.length <= maxLength) return text;

  const shortened = text.slice(0, Math.max(1, maxLength - 3));
  const lastSpace = shortened.lastIndexOf(" ");
  return `${lastSpace > maxLength / 2 ? shortened.slice(0, lastSpace) : shortened}...`;
}

function readPaneState(sessionID) {
  if (!sessionID || !existsSync(PANE_STATE_DIR)) return "";

  let best = null;
  try {
    for (const file of readdirSync(PANE_STATE_DIR)) {
      if (!file.endsWith(".json")) continue;
      try {
        const state = JSON.parse(readFileSync(join(PANE_STATE_DIR, file), "utf8"));
        if (state.sessionID !== sessionID || !state.tmuxPane) continue;
        if (!best || (state.lastUpdated || 0) > (best.lastUpdated || 0)) best = state;
      } catch {
        // Ignore stale or partially written pane state.
      }
    }
  } catch {
    return "";
  }

  return best;
}

function paneStateIsLive(state) {
  if (!state?.processID || !state.tmuxPane) return false;

  try {
    process.kill(state.processID, 0);
    const processTTY = execFileSync("/bin/ps", ["-p", String(state.processID), "-o", "tty="], {
      encoding: "utf8",
      timeout: 1000,
    }).trim();
    const paneTTY = execFileSync(findExecutable("tmux"), [
      "display-message",
      "-p",
      "-t",
      state.tmuxPane,
      "#{pane_tty}",
    ], { encoding: "utf8", timeout: 1000 }).trim();
    return Boolean(processTTY) && basename(paneTTY) === processTTY;
  } catch {
    return false;
  }
}

function tmuxTarget(sessionID) {
  const paneState = readPaneState(sessionID);
  const pane = TMUX_PANE || (paneStateIsLive(paneState) ? paneState.tmuxPane : "");
  if (!pane) return "not attached";

  try {
    return execFileSync(findExecutable("tmux"), [
      "display-message",
      "-p",
      "-t",
      pane,
      "#{session_name}:#{window_index}.#{pane_index}",
    ], { encoding: "utf8", timeout: 1000 }).trim() || "not attached";
  } catch {
    return "not attached";
  }
}

async function latestAssistantSummary(client, directory, sessionID, maxLength) {
  try {
    const result = await client.session.messages({
      path: { id: sessionID },
      query: { directory, limit: 20 },
    });
    const messages = result.data || [];
    const latest = messages.findLast((message) => message.info?.role === "assistant" && !message.info.summary);
    const text = latest?.parts
      ?.filter((part) => part.type === "text" && !part.ignored)
      .at(-1)?.text;
    return truncate(text, maxLength);
  } catch {
    return "";
  }
}

function eventDetail(eventName, properties, summary) {
  if (eventName === "complete") return summary ? `Summary: ${summary}` : "OpenCode is ready for your next prompt.";
  if (eventName === "question") {
    const questions = properties.questions || [];
    const first = questions[0]?.question;
    const suffix = questions.length > 1 ? ` (+${questions.length - 1} more)` : "";
    return first ? `Question: ${first}${suffix}` : "OpenCode is waiting for an answer.";
  }
  if (eventName === "permission") {
    const request = properties.patterns?.join(", ") || properties.permission;
    return request ? `Request: ${request}` : "OpenCode needs permission to continue.";
  }
  if (eventName === "error") {
    const error = properties.error;
    const message = error?.data?.message || error?.message || error?.name;
    return message ? `Error: ${message}` : "OpenCode stopped because of an error.";
  }
  return "";
}

function notificationPayload(config, eventName, sessionID, properties, summary) {
  const project = projectName(properties);
  const state = eventLabel(eventName);
  const task = truncate(sessionTitle(properties), 100);
  const tmux = tmuxTarget(sessionID);
  const title = `OpenCode: ${state}`;
  const subtitle = [config.showProjectName ? project : "", `tmux ${tmux}`].filter(Boolean).join(" | ");
  const detail = truncate(eventDetail(eventName, properties, summary), config.summaryLength);
  const message = [task, detail].filter(Boolean).join("\n");

  return { title, subtitle, message, project, state, task, tmux, detail, sessionID };
}

async function sessionInfo(client, directory, sessionID) {
  if (!sessionID) return null;

  let info = sessionMeta.get(sessionID);
  if (!info) {
    try {
      const result = await client.session.get({
        path: { id: sessionID },
        query: { directory },
      });
      setSessionInfo(result.data);
      info = sessionMeta.get(sessionID);
    } catch {
      return null;
    }
  }

  return info || null;
}

async function primarySession(client, directory, sessionID) {
  const visited = new Set();
  let currentID = sessionID;

  while (currentID && !visited.has(currentID)) {
    visited.add(currentID);
    const info = await sessionInfo(client, directory, currentID);
    if (!info) return null;
    if (!info.parentID) return { id: currentID, ...info };
    currentID = info.parentID;
  }

  return null;
}

async function isPrimarySession(client, directory, sessionID) {
  const primary = await primarySession(client, directory, sessionID);
  return primary?.id === sessionID;
}

function focusCommand(sessionID) {
  const args = [FOCUS_HELPER];
  if (sessionID) args.push("--session", sessionID);
  if (TMUX_PANE) args.push("--pane", TMUX_PANE);
  return args.map(shellQuote).join(" ");
}

function notifyWithTerminalNotifier(config, sessionID, payload) {
  const terminalNotifier = findExecutable("terminal-notifier");
  const args = [
    "-title",
    payload.title,
    "-subtitle",
    payload.subtitle,
    "-message",
    payload.message,
    "-group",
    sessionID ? `opencode-${sessionID}` : "opencode",
    "-timeout",
    String(config.timeout ?? 5),
  ];

  if (existsSync(FOCUS_HELPER)) {
    args.push("-execute", focusCommand(sessionID));
  }

  execFile(terminalNotifier, args, (error) => {
    if (!error) return;
    notifyWithOsaScript(payload);
  });
}

function notifyWithOsaScript(payload) {
  execFile(
    "/usr/bin/osascript",
    [
      "-e",
      `display notification ${appleScriptString(payload.message)} with title ${appleScriptString(payload.title)} subtitle ${appleScriptString(payload.subtitle)}`,
    ],
    () => undefined,
  );
}

async function notify(client, directory, config, eventName, sessionID, properties) {
  playSound(config, eventName);
  const summary = eventName === "complete"
    ? await latestAssistantSummary(client, directory, sessionID, config.summaryLength)
    : "";
  const payload = notificationPayload(config, eventName, sessionID, properties, summary);

  if (notificationEnabled(config, eventName)) {
    if (config.notificationSystem === "osascript") {
      notifyWithOsaScript(payload);
    } else {
      notifyWithTerminalNotifier(config, sessionID, payload);
    }
  }

  if (pushEnabled(config, eventName) && config.webPush?.enabled === true) {
    publishWebPush(config, payload);
  }
}

function publishWebPush(config, payload) {
  const { helper, externalUrl } = config.webPush;
  if (!helper || !externalUrl || !payload.sessionID) return;
  const serverKey = Buffer.from(externalUrl).toString("base64url");
  const url = `${externalUrl}/server/${serverKey}/session/${encodeURIComponent(payload.sessionID)}`;
  const body = [
    `Project: ${payload.project}`,
    `Tmux: ${payload.tmux}`,
    `Task: ${payload.task}`,
    payload.detail,
  ].filter(Boolean).join("\n");
  const child = spawn(findExecutable("node"), [helper, "publish"], { stdio: ["pipe", "ignore", "inherit"] });
  child.on("error", () => undefined);
  child.stdin.on("error", () => undefined);
  child.stdin.end(JSON.stringify({
    title: `${payload.title} | ${payload.project}`,
    body,
    url,
    tag: `opencode-${payload.sessionID}`,
  }));
}

export default async function ({ client, directory }) {
  const config = readConfig();

  return {
    event: async ({ event }) => {
      const properties = event.properties || {};
      const sessionID = properties.sessionID || properties.info?.id || "";

      if (event.type === "session.created" || event.type === "session.updated") {
        setSessionInfo(properties.info);
      } else if (event.type === "session.deleted") {
        clearSessionInfo(sessionID);
        activeSessions.delete(sessionID);
        failedSessions.delete(sessionID);
        return;
      }

      if (event.type === "session.status") {
        const status = properties.status?.type;
        if (status === "busy" || status === "retry") {
          activeSessions.add(sessionID);
          if (status === "busy") failedSessions.delete(sessionID);
          return;
        }
        if (status !== "idle" || !activeSessions.delete(sessionID)) return;

        if (!(await isPrimarySession(client, directory, sessionID))) return;
        if (failedSessions.delete(sessionID)) return;
        await notify(client, directory, config, "complete", sessionID, {
          ...properties,
          info: { id: sessionID, ...sessionMeta.get(sessionID) },
        });
        return;
      }

      const eventName = EVENT_BY_TYPE[event.type];
      if (!eventName) return;

      const primary = await primarySession(client, directory, sessionID);
      if (!primary) return;
      if (primary.id !== sessionID && eventName !== "permission" && eventName !== "question") return;
      if (eventName === "error") failedSessions.add(primary.id);
      await notify(client, directory, config, eventName, primary.id, {
        ...properties,
        info: primary,
      });
    },
  };
}
