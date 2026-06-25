/**
 * Pi Notify Extension
 *
 * Sends a native notification when Pi agent is done and waiting for input.
 * Supports multiple terminal / desktop protocols:
 * - macOS Notification Center: osascript display notification with sound
 * - OSC 777: Ghostty, WezTerm, rxvt-unicode
 * - OSC 9: iTerm2
 * - OSC 99: Kitty
 * - tmux passthrough wrapper for OSC notifications
 * - Windows toast: Windows Terminal (WSL)
 * - Optional sound hook via PI_NOTIFY_SOUND_CMD
 *
 * Blacksmith-local behavior:
 * - macOS defaults to osascript instead of OSC so notifications also work in
 *   Terminal.app, tmux, and integrated terminals that ignore OSC notifications.
 * - set PI_NOTIFY_TRANSPORT=auto|macos|osc777|osc9|osc99|windows to override.
 * - set PI_NOTIFY_MACOS_SOUND_NAME=none to disable the default macOS sound.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

type NotifyTransport = "macos" | "osc777" | "osc9" | "osc99" | "windows";

const VALID_TRANSPORTS = new Set(["macos", "osc777", "osc9", "osc99", "windows"]);

function windowsToastScript(title: string, body: string): string {
    const type = "Windows.UI.Notifications";
    const mgr = `[${type}.ToastNotificationManager, ${type}, ContentType = WindowsRuntime]`;
    const template = `[${type}.ToastTemplateType]::ToastText01`;
    const toast = `[${type}.ToastNotification]::new($xml)`;
    return [
        `${mgr} > $null`,
        `$xml = [${type}.ToastNotificationManager]::GetTemplateContent(${template})`,
        `$xml.GetElementsByTagName('text')[0].AppendChild($xml.CreateTextNode('${body}')) > $null`,
        `[${type}.ToastNotificationManager]::CreateToastNotifier('${title}').Show(${toast})`,
    ].join("; ");
}

function appleScriptString(value: string): string {
    return `"${value.replace(/\\/g, "\\\\").replace(/"/g, '\\"')}"`;
}

function wrapForTmux(sequence: string): string {
    if (!process.env.TMUX) return sequence;

    // tmux passthrough: wrap in DCS and escape inner ESC bytes.
    const escaped = sequence.split("\x1b").join("\x1b\x1b");
    return `\x1bPtmux;${escaped}\x1b\\`;
}

function writeTerminalSequence(sequence: string): void {
    const wrapped = wrapForTmux(sequence);

    try {
        const { openSync, closeSync, writeSync } = require("node:fs");
        const fd = openSync("/dev/tty", "w");
        try {
            writeSync(fd, wrapped);
        } finally {
            closeSync(fd);
        }
    } catch {
        process.stdout.write(wrapped);
    }
}

function notifyOSC777(title: string, body: string): void {
    writeTerminalSequence(`\x1b]777;notify;${title};${body}\x07`);
}

function notifyOSC9(message: string): void {
    writeTerminalSequence(`\x1b]9;${message}\x07`);
}

function notifyOSC99(title: string, body: string): void {
    // Kitty OSC 99: i=notification id, d=0 means not done yet, p=body for second part
    writeTerminalSequence(`\x1b]99;i=1:d=0;${title}\x1b\\`);
    writeTerminalSequence(`\x1b]99;i=1:p=body;${body}\x1b\\`);
}

function notifyWindows(title: string, body: string): void {
    const { execFile } = require("node:child_process");
    execFile("powershell.exe", ["-NoProfile", "-Command", windowsToastScript(title, body)], () => undefined);
}

function macOSSoundName(): string | undefined {
    const value = process.env.PI_NOTIFY_MACOS_SOUND_NAME?.trim();
    if (value === undefined) return "Glass";

    const normalized = value.toLowerCase();
    if (!value || normalized === "none" || normalized === "off" || normalized === "false" || normalized === "0") {
        return undefined;
    }

    return value;
}

function notifyMacOS(title: string, body: string): void {
    const { execFile } = require("node:child_process");
    const soundName = macOSSoundName();
    const soundClause = soundName ? ` sound name ${appleScriptString(soundName)}` : "";

    execFile(
        "/usr/bin/osascript",
        ["-e", `display notification ${appleScriptString(body)} with title ${appleScriptString(title)}${soundClause}`],
        () => undefined,
    );
}

function runSoundHook(): void {
    const command = process.env.PI_NOTIFY_SOUND_CMD?.trim();
    if (!command) return;

    try {
        const { spawn } = require("node:child_process");
        const child = spawn(command, {
            shell: true,
            detached: true,
            stdio: "ignore",
        });
        child.unref();
    } catch {
        // Ignore hook errors to avoid breaking notifications
    }
}

function configuredTransport(): NotifyTransport | undefined {
    const value = process.env.PI_NOTIFY_TRANSPORT?.trim().toLowerCase();
    if (!value || value === "auto") return undefined;
    if (VALID_TRANSPORTS.has(value)) return value as NotifyTransport;
    return undefined;
}

function detectTransport(): NotifyTransport {
    const configured = configuredTransport();
    if (configured) return configured;

    const isIterm2 = process.env.TERM_PROGRAM === "iTerm.app" || Boolean(process.env.ITERM_SESSION_ID);

    if (process.env.WT_SESSION) return "windows";

    // Blacksmith-local default: on macOS, OS-native notifications are more
    // reliable than terminal OSC notifications across Terminal.app, tmux,
    // Ghostty, VS Code/Cursor integrated terminals, and other wrappers.
    if (process.platform === "darwin") return "macos";

    if (process.env.KITTY_WINDOW_ID) return "osc99";
    if (isIterm2) return "osc9";
    return "osc777";
}

function notify(title: string, body: string): NotifyTransport {
    const transport = detectTransport();

    if (transport === "windows") {
        notifyWindows(title, body);
    } else if (transport === "macos") {
        notifyMacOS(title, body);
    } else if (transport === "osc99") {
        notifyOSC99(title, body);
    } else if (transport === "osc9") {
        notifyOSC9(`${title}: ${body}`);
    } else {
        notifyOSC777(title, body);
    }

    runSoundHook();
    return transport;
}

export default function (pi: ExtensionAPI) {
    pi.on("agent_end", async (_event, ctx) => {
        // Avoid emitting notifications in non-interactive batch / RPC modes.
        if (ctx.mode !== "tui") return;

        notify("Pi", "Ready for input");
    });
}
