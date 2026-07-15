import { mkdirSync, renameSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

const paneID = process.env.TMUX_PANE || "";
const stateHome = process.env.XDG_STATE_HOME || join(homedir(), ".local", "state");
const paneDir = join(stateHome, "opencode", "tmux-session-state", "panes");

function safeName(value) {
  return value.replace(/[^A-Za-z0-9_.%-]/g, "_");
}

function publish(sessionID) {
  const path = join(paneDir, `${safeName(paneID)}.json`);
  const temporary = `${path}.${process.pid}.tmp`;

  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(
    temporary,
    `${JSON.stringify(
      {
        version: 1,
        sessionID,
        tmuxPane: paneID,
        processID: process.pid,
        status: "unknown",
        directory: process.cwd(),
        lastUpdated: Date.now(),
      },
      null,
      2,
    )}\n`,
    "utf8",
  );
  renameSync(temporary, path);
}

async function tui(api) {
  if (!paneID) return;

  let previousSessionID;
  const update = () => {
    const route = api.route.current;
    if (route.name !== "session") return;

    const sessionID = route.params?.sessionID;
    if (!sessionID || sessionID === previousSessionID) return;

    previousSessionID = sessionID;
    publish(sessionID);
  };

  update();
  setInterval(update, 250);
}

export default {
  id: "local.tmux-current-session",
  tui,
};
