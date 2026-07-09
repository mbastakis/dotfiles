import { execFile, spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { basename, join } from "node:path";

const CONFIG_PATH = join(homedir(), ".config", "opencode", "clickable-notifier.json");
const FOCUS_HELPER = join(homedir(), "bin", "opencode-focus-session");
const TMUX_PANE = process.env.TMUX_PANE || "";

const DEFAULT_CONFIG = {
  sound: true,
  notification: true,
  showProjectName: true,
  showSessionTitle: false,
  timeout: 5,
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

const EVENT_BY_TYPE = {
  "permission.asked": "permission",
  "question.asked": "question",
  "session.idle": "complete",
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

function eventLabel(eventName) {
  switch (eventName) {
    case "permission":
      return "Permission required";
    case "question":
      return "Question waiting";
    case "complete":
      return "Ready for input";
    case "error":
      return "Error";
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

function notificationText(config, eventName, properties) {
  const project = projectName(properties);
  const title = config.showProjectName ? `OpenCode - ${project}` : "OpenCode";
  const label = eventLabel(eventName);
  const session = sessionTitle(properties);
  const message = config.showSessionTitle ? `${label}: ${session}` : `${label}. Click to jump to tmux.`;

  return { title, message };
}

function focusCommand(sessionID) {
  const args = [FOCUS_HELPER];
  if (sessionID) args.push("--session", sessionID);
  if (TMUX_PANE) args.push("--pane", TMUX_PANE);
  return args.map(shellQuote).join(" ");
}

function notifyWithTerminalNotifier(config, sessionID, title, message) {
  const terminalNotifier = findExecutable("terminal-notifier");
  const args = [
    "-title",
    title,
    "-message",
    message,
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
    notifyWithOsaScript(title, message);
  });
}

function notifyWithOsaScript(title, message) {
  execFile(
    "/usr/bin/osascript",
    ["-e", `display notification ${appleScriptString(message)} with title ${appleScriptString(title)}`],
    () => undefined,
  );
}

function notify(config, eventName, sessionID, properties) {
  playSound(config, eventName);
  if (!notificationEnabled(config, eventName)) return;

  const { title, message } = notificationText(config, eventName, properties);
  if (config.notificationSystem === "osascript") {
    notifyWithOsaScript(title, message);
    return;
  }

  notifyWithTerminalNotifier(config, sessionID, title, message);
}

export default async function () {
  const config = readConfig();

  return {
    event: async ({ event }) => {
      const eventName = EVENT_BY_TYPE[event.type];
      if (!eventName) return;

      const properties = event.properties || {};
      const sessionID = properties.sessionID || properties.info?.id || "";
      notify(config, eventName, sessionID, properties);
    },
  };
}
