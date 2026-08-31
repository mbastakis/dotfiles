const usageURL = "https://ai.whocaressoftware.com/wcs/usage";

function percent(value) {
  return Number.isFinite(value) ? `${Math.round(value * 10) / 10}%` : "?";
}

function resetText(value) {
  if (!value) return "reset unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "reset unknown";
  return `resets ${date.toLocaleString()}`;
}

function accountLines(account) {
  const lines = [account.account || "Unknown account"];
  if (account.unavailable) {
    lines.push(`  unavailable: ${account.unavailable}`);
    return lines;
  }
  const windows = Array.isArray(account.windows) ? account.windows : [];
  if (!windows.length) {
    lines.push("  quota unavailable");
    return lines;
  }
  for (const window of windows) {
    const exhausted = window.exhausted ? "  EXHAUSTED" : "";
    lines.push(
      `  ${window.name || "window"}: ${percent(window.remaining_percent)} remaining, ${resetText(window.reset_at)}${exhausted}`,
    );
  }
  return lines;
}

function formatReport(report) {
  const generated = report.generated_at ? new Date(report.generated_at) : null;
  const lines = [
    generated && !Number.isNaN(generated.getTime())
      ? `Updated ${generated.toLocaleString()}`
      : "Updated just now",
    "",
    "GPT OAuth",
  ];
  const gpt = Array.isArray(report.gpt) ? report.gpt : [];
  if (gpt.length) {
    for (const account of gpt) lines.push(...accountLines(account), "");
  } else {
    lines.push("  no configured accounts", "");
  }
  lines.push("OpenCode Go");
  const go = Array.isArray(report.opencode_go) ? report.opencode_go : [];
  if (go.length) {
    for (const account of go) lines.push(...accountLines(account), "");
  } else {
    lines.push("  quota credentials not configured");
  }
  return lines.join("\n").trimEnd();
}

async function showUsage(context) {
  const token = process.env.WCS_API_KEY;
  if (!token) {
    context.ui.toast({
      title: "WCS Usage",
      message: "WCS_API_KEY is not set in the OpenCode environment.",
      variant: "warning",
    });
    return;
  }

  try {
    const response = await fetch(usageURL, {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${token}`,
      },
      signal: AbortSignal.timeout(20000),
    });
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.toLowerCase().includes("application/json")) {
      throw new Error(
        `WCS gateway returned HTTP ${response.status} (${contentType || "unknown content type"}).`,
      );
    }
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body?.error?.message || `HTTP ${response.status}`);
    }
    if (!Array.isArray(body.gpt) || !Array.isArray(body.opencode_go)) {
      throw new Error("The WCS usage endpoint returned an invalid report.");
    }
    context.ui.toast({
      title: "WCS Provider Usage",
      message: formatReport(body),
      variant: "success",
      duration: 15000,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    context.ui.toast({
      title: "WCS Usage Unavailable",
      message,
      variant: "error",
    });
  }
}

function tui(context) {
  context.keymap.registerLayer({
    mode: "base",
    commands: [
      {
        name: "wcs.usage",
        title: "Show WCS provider usage",
        desc: "Fetch all WCS provider quotas without using an LLM",
        category: "WCS",
        namespace: "palette",
        slashName: "usage",
        run: () => showUsage(context),
      },
    ],
  });
}

export default {
  id: "local.wcs-usage",
  tui,
};
