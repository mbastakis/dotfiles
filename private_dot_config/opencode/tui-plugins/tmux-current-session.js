import {
  mkdirSync,
  readFileSync,
  renameSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

const paneID = process.env.TMUX_PANE || "";
const stateHome = process.env.XDG_STATE_HOME || join(homedir(), ".local", "state");
const paneDir = join(stateHome, "opencode", "tmux-session-state", "panes");
const clientDir = join(stateHome, "opencode", "tmux-session-state", "clients");
const clientPath = join(clientDir, `${process.pid}.json`);

function safeName(value) {
  return value.replace(/[^A-Za-z0-9_.%-]/g, "_");
}

function writeJSON(path, value) {
  const temporary = `${path}.${process.pid}.tmp`;

  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  renameSync(temporary, path);
}

function removeOwned(path) {
  try {
    const state = JSON.parse(readFileSync(path, "utf8"));
    if (state.processID === process.pid) rmSync(path, { force: true });
  } catch {
    // Missing or concurrently replaced state needs no cleanup.
  }
}

function clear() {
  removeOwned(clientPath);
  if (paneID) removeOwned(join(paneDir, `${safeName(paneID)}.json`));
}

function publish(sessionID) {
  const state = {
    version: 1,
    sessionID,
    tmuxPane: paneID,
    processID: process.pid,
    directory: process.cwd(),
    lastUpdated: Date.now(),
  };

  writeJSON(clientPath, state);
  if (paneID) writeJSON(join(paneDir, `${safeName(paneID)}.json`), state);
}

async function tui(api) {
  process.once("exit", clear);

  let previousSessionID = null;
  const update = () => {
    const route = api.route.current;
    const sessionID = route.name === "session" ? route.params?.sessionID || "" : "";
    if (sessionID === previousSessionID) return;

    previousSessionID = sessionID;
    if (!sessionID) {
      clear();
      return;
    }

    publish(sessionID);
  };

  update();
  setInterval(update, 250);
}

export default {
  id: "local.tmux-current-session",
  tui,
};
