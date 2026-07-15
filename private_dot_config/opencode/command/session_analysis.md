---
description: Export and analyze a previous OpenCode session by ID
agent: general
subtask: true
---

# Session Analysis

Analyze a previous OpenCode session from an exported transcript.

Use the exported session artifact as the source of truth. Do not rely on current
conversation memory except to understand this command invocation.

## Arguments

- Required: an OpenCode session ID, normally `ses_...`
- Optional: any text after the session ID is the user's focus question for the critique

Examples:

```text
/session_analysis ses_123abc
/session_analysis ses_123abc why did the debugging get stuck?
/session_analysis --session ses_123abc identify the critical mistakes
```

## Workflow

### Step 1: Parse `$ARGUMENTS`

Extract:

- `SESSION_ID`: the first token that starts with `ses_`, or the value after `--session`
- `FOCUS`: any remaining text after removing the session ID and `--session`

If `SESSION_ID` is missing, stop and return:

```text
Usage: /session_analysis <session-id> [focus question]
Example: /session_analysis ses_123abc why did this get stuck?
```

If `FOCUS` is empty, perform a general postmortem covering user intent,
critical issues, stuck points, and preventions.

### Step 2: Export the complete session

Run read-only shell commands. Prefer the user's `oc` command when available,
but fall back to `opencode` because shell aliases may not exist in noninteractive
tool shells.

Use this pattern, replacing `<SESSION_ID>` with the parsed session ID:

```bash
set -euo pipefail

SESSION_ID="<SESSION_ID>"

if command -v oc >/dev/null 2>&1; then
  OPENCODE_CLI="oc"
elif command -v opencode >/dev/null 2>&1; then
  OPENCODE_CLI="opencode"
else
  echo "Error: neither oc nor opencode was found in PATH" >&2
  exit 127
fi

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/opencode-session-critique.XXXXXX")"
export_file="$tmpdir/session-${SESSION_ID}.json"

"$OPENCODE_CLI" export "$SESSION_ID" > "$export_file"

printf 'tmpdir=%s\nexport_file=%s\ncli=%s\n' "$tmpdir" "$export_file" "$OPENCODE_CLI"
wc -c "$export_file"
```

If export fails, run this for diagnostics and return a concise error with the
session ID and command output:

```bash
"$OPENCODE_CLI" session list --format json -n 50
```

Important:

- Do not use `--sanitize` by default. This is a local forensic artifact and the
  user asked for all tool calls/system prompt data that OpenCode exports.
- Treat the export as sensitive. Do not paste secrets, access tokens, private
  keys, or large raw tool outputs into the final report.
- If the export does not contain hidden runtime/system layers, say so. Do not
  claim they were captured unless they are visible in the exported JSON.

### Step 3: Create readable analysis chunks

Create chunk files from the exported JSON before analysis. This avoids losing
context when the raw export is too large or contains very long JSON lines.

Run this pattern after setting `export_file`:

```bash
export EXPORT_FILE="$export_file"
python3 - <<'PY'
import json
import os
import pathlib
import textwrap

export_file = pathlib.Path(os.environ["EXPORT_FILE"])
tmpdir = export_file.parent
chunks_dir = tmpdir / "chunks"
chunks_dir.mkdir(exist_ok=True)

data = json.loads(export_file.read_text())
messages = data.get("messages", [])

def safe_json(value):
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)

def wrap_text(text, width=1000):
    if not text:
        return ""
    lines = []
    for line in str(text).splitlines() or [str(text)]:
        if len(line) <= width:
            lines.append(line)
        else:
            lines.extend(textwrap.wrap(line, width=width, replace_whitespace=False, drop_whitespace=False))
    return "\n".join(lines)

def format_message(index, message):
    info = message.get("info", {})
    parts = message.get("parts", [])
    role = info.get("role", "unknown")
    msg_id = info.get("id", "unknown")
    session_id = info.get("sessionID", info.get("sessionId", "unknown"))
    header = [
        f"## Message {index}",
        "",
        f"- id: `{msg_id}`",
        f"- role: `{role}`",
        f"- session: `{session_id}`",
        f"- parts: `{len(parts)}`",
        "",
        "### Message Info",
        "",
        "```json",
        wrap_text(safe_json(info)),
        "```",
        "",
    ]
    body = []
    for part_index, part in enumerate(parts, 1):
        part_type = part.get("type", "unknown")
        body.extend([
            f"### Part {part_index}: `{part_type}`",
            "",
            "```json",
            wrap_text(safe_json(part)),
            "```",
            "",
        ])
    return "\n".join(header + body)

manifest = tmpdir / "manifest.md"
part_counts = {}
for message in messages:
    for part in message.get("parts", []):
        part_counts[part.get("type", "unknown")] = part_counts.get(part.get("type", "unknown"), 0) + 1

manifest.write_text("\n".join([
    "# OpenCode Session Export Manifest",
    "",
    f"- export_file: `{export_file}`",
    f"- size_bytes: `{export_file.stat().st_size}`",
    f"- session_id: `{data.get('info', {}).get('id', 'unknown')}`",
    f"- title: `{data.get('info', {}).get('title', '')}`",
    f"- message_count: `{len(messages)}`",
    f"- part_counts: `{safe_json(part_counts)}`",
    "",
    "## Session Info",
    "",
    "```json",
    wrap_text(safe_json(data.get("info", {}))),
    "```",
    "",
]))

target_chars = 180_000
chunk_index = 1
current = []
current_chars = 0

def write_chunk(items):
    global chunk_index
    if not items:
        return
    path = chunks_dir / f"chunk-{chunk_index:04d}.md"
    path.write_text("\n\n".join(items))
    chunk_index += 1

for index, message in enumerate(messages, 1):
    rendered = format_message(index, message)
    if current and current_chars + len(rendered) > target_chars:
        write_chunk(current)
        current = []
        current_chars = 0
    current.append(rendered)
    current_chars += len(rendered)

write_chunk(current)

print(f"manifest={manifest}")
print(f"chunks_dir={chunks_dir}")
print(f"chunk_count={chunk_index - 1}")
PY
```

If `python3` is unavailable, continue with the raw `export_file` and read it in
offset chunks. Note the limitation in the final report.

### Step 4: Read the artifact fully enough to analyze

Read the files from the temp directory, not the current conversation.

Recommended strategy:

1. Read `manifest.md` first.
2. If the raw JSON is small enough for a single full Read, read `export_file` too.
3. Otherwise read every `chunks/chunk-*.md` file in numeric order.
4. If any chunk is too large for one Read call, continue with larger offsets until the chunk is complete.
5. Use Grep against the exported file and chunks for likely failure markers: `error`, `failed`, `failure`, `exception`, `timeout`, `denied`, `stuck`, `retry`, `blocked`, `cancelled`, `panic`, `traceback`, `not found`, `permission`, `invalid`, `TODO`, `question`.

Do not skip later chunks after finding an early issue. Critical problems often
come from repeated behavior over time.

### Step 5: Analyze with a postmortem mindset

Reconstruct the session timeline and identify:

- What the user was trying to accomplish and what they likely wanted to know
- Whether the optional `FOCUS` question changes the critique priority
- Major decisions the assistant made
- Tool calls, tool failures, permission denials, retries, loops, and dead ends
- Places where the assistant got stuck, chased the wrong problem, or lost the thread
- Missing context, incorrect assumptions, weak verification, or premature conclusions
- Agent/model routing problems, if visible
- Whether the final answer matched the user's actual need

Severity rules:

- Critical: caused wrong output, data loss risk, security risk, broken workflow, or major wasted time
- High: materially delayed progress or caused misleading analysis
- Medium: inefficient or incomplete, but recoverable
- Low: style, clarity, or small process issue

For each finding, include concrete evidence from the export: message number,
role, tool name, error text, or a short quoted excerpt. Keep excerpts short and
redact secrets.

### Step 6: Return the report

Use this structure:

```markdown
# Session Analysis: <SESSION_ID>

Artifact: `<export_file>`
Focus: <FOCUS or "general postmortem">

## Executive Summary

<3-6 bullets with the most important conclusions.>

## User Intent

<What the user wanted, including any shifts during the session.>

## Critical Issues

| Severity | Issue | Evidence | Impact | Prevention |
|---|---|---|---|---|
| Critical/High/... | ... | Message N / tool X / excerpt | ... | ... |

If there are no critical or high-severity issues, state that explicitly.

## Stuck Points

<Where the session stalled, looped, or failed to converge.>

## Tool And Agent Timeline

<Concise chronological summary of important tool calls and decisions.>

## What Went Well

<Useful behavior worth preserving.>

## Answer To Focus Question

<Direct answer if the user provided a focus question; otherwise omit this section.>

## Next Time

<Concrete prevention steps, better prompts, missing checks, or process changes.>

## Capture Limitations

<Mention anything the export did not expose, such as hidden runtime prompts, if relevant.>
```

<user-request>
$ARGUMENTS
</user-request>
