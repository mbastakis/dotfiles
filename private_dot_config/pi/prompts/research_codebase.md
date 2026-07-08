---
description: Document codebase as-is with optional thoughts/ historical context
argument-hint: "[research question]"
---

# Research Codebase As-Is

Research query from template arguments:

<research_query>
$ARGUMENTS
</research_query>

You are tasked with conducting comprehensive research across the current codebase and answering the user's question by documenting what exists today. Use live code as the primary source of truth and use any `thoughts/` directory only as supplementary historical context.

## CRITICAL: DOCUMENT AND EXPLAIN THE CODEBASE AS IT EXISTS TODAY

- DO NOT suggest improvements or changes unless the user explicitly asks for them.
- DO NOT perform root-cause analysis unless the user explicitly asks for it.
- DO NOT propose future enhancements unless the user explicitly asks for them.
- DO NOT critique the implementation or identify problems.
- DO NOT recommend refactoring, optimization, or architectural changes.
- ONLY describe what exists, where it exists, how it works, and how components interact.
- You are creating a technical map/documentation of the existing system.

## Pi-specific operating rules

- Pi prompt templates support `description`, `argument-hint`, and positional arguments; do not assume a prompt template can select the model.
- Use Pi's available tools directly:
  - Use `read` for file contents.
  - Use `bash` for repository discovery (`rg`, `find`, `git`, `date`, etc.).
  - Use `web_search`/`fetch_content` only when the user explicitly asks for external/web research.
  - Use `write`/`edit` only for the research document; do not modify implementation code.
- Pi core does not provide Claude-style `Task` or `TodoWrite` tools. If a `subagent` tool is available, use it for parallel research. If no subagent tool is available, perform the same steps yourself with `bash`/`read` and keep a concise inline plan.
- When using `subagent`, call it with `{ "action": "list" }` first and only use executable agents listed in the result. Prefer:
  - `scout` for fast codebase location/reconnaissance.
  - `delegate` for focused read-only analysis of specific files/components.
  - `researcher` only for external/web research explicitly requested by the user.
  - `reviewer` only to verify evidence and coverage, not to critique or propose changes.
- All subagent tasks must be read-only and must explicitly state: "Document what exists; do not evaluate, critique, or recommend changes."

## Initial setup

1. Inspect `<research_query>` after argument expansion.
2. If it is empty, respond exactly:

```text
I'm ready to research the codebase. Please provide your research question or area of interest, and I'll analyze it thoroughly by exploring relevant components and connections.
```

Then wait for the user's research query.

3. If it is non-empty, begin research immediately on that query.

## Steps after receiving the research query

### 1. Read directly mentioned files first

- If the user mentions specific files, tickets, docs, JSON, configs, or paths, read those files yourself in the main context before spawning any subagents.
- Use `read` without `offset`/`limit` first. If the tool reports truncation, continue with `offset`/`limit` until you have the full relevant file.
- This step must happen before decomposing the work or launching subagents.

### 2. Analyze and decompose the question

Before searching broadly, identify:

- The literal question asked.
- The concrete system/component/concept being researched.
- The likely directories, file types, config files, or architectural seams involved.
- A small set of independent research areas that can run in parallel.

Keep this as a concise internal plan or visible bullet list. Do not rely on `TodoWrite`.

### 3. Run live codebase research

Use fresh codebase research every time. Do not rely only on existing research documents.

If `subagent` is available:

1. Call `{ "action": "list" }`.
2. Launch parallel read-only tasks for independent research areas.
3. Start with locator/recon tasks, then run focused analyzer tasks on the most relevant findings.
4. Wait for all subagents to complete before synthesizing.

If `subagent` is not available:

1. Use `rg`, `find`, `git grep`, and targeted `read` calls yourself.
2. Keep the search broad enough to cover related components.
3. Capture concrete `path:line` references.

Research areas commonly include:

- Where relevant files/components live.
- How the current implementation works.
- Existing patterns and examples of the same behavior.
- Configuration, runtime entrypoints, scripts, tests, docs, and generated artifacts that connect to the topic.

### 4. Search `thoughts/` for historical context when present

- If a `thoughts/` directory exists, search all of it for relevant historical context, not just `thoughts/shared/research/`.
- Treat live code as primary truth and `thoughts/` as supplemental context.
- If a `thoughts/searchable/` path is found, remove only the `searchable/` segment when documenting the path:
  - `thoughts/searchable/allison/old_stuff/notes.md` -> `thoughts/allison/old_stuff/notes.md`
  - `thoughts/searchable/shared/prs/123.md` -> `thoughts/shared/prs/123.md`
  - `thoughts/searchable/global/shared/templates.md` -> `thoughts/global/shared/templates.md`
- Preserve all other directory names exactly. Never convert a personal directory to `shared/` or vice versa.

### 5. Synthesize findings

- Wait for all subagents/searches to finish before final synthesis.
- Connect findings across components.
- Include specific file paths and line numbers.
- Explain how components interact.
- Clearly distinguish live-code findings from historical notes.
- Answer the user's specific question with concrete evidence.
- Do not include recommendations unless explicitly requested.

### 6. Gather metadata before writing a research document

If `thoughts/` exists, create or update a research document under `thoughts/shared/research/`. Before writing it, gather metadata with real commands; never use placeholder values.

Prefer project metadata scripts when present:

```bash
if [[ -x hack/spec_metadata.sh ]]; then
  hack/spec_metadata.sh
fi
```

Also gather portable fallback metadata as needed:

```bash
date +"%Y-%m-%dT%H:%M:%S%z"
date +"%Y-%m-%d"
git rev-parse HEAD 2>/dev/null || true
git branch --show-current 2>/dev/null || true
basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
git config user.name 2>/dev/null || whoami
```

Filename format:

- `thoughts/shared/research/YYYY-MM-DD-ENG-XXXX-description.md` when an `ENG-XXXX` ticket is part of the research.
- `thoughts/shared/research/YYYY-MM-DD-description.md` when there is no ticket.
- Use a brief kebab-case description of the topic.

If no `thoughts/` directory exists, do not create one unless the user explicitly asks; present the research in chat only.

### 7. Research document structure

When creating/updating a research document, use this structure:

```markdown
---
date: [Current date and time with timezone]
researcher: [Researcher name]
git_commit: [Current commit hash]
branch: [Current branch name]
repository: [Repository name]
topic: "[User's question/topic]"
tags: [research, codebase, relevant-component-names]
status: complete
last_updated: [YYYY-MM-DD]
last_updated_by: [Researcher name]
---

# Research: [User's Question/Topic]

**Date**: [Current date and time with timezone]
**Researcher**: [Researcher name]
**Git Commit**: [Current commit hash]
**Branch**: [Current branch name]
**Repository**: [Repository name]

## Research Question

[Original user query]

## Summary

[High-level documentation of what was found, answering the user's question by describing what exists]

## Detailed Findings

### [Component/Area 1]

- Description of what exists (`file.ext:line`)
- How it connects to other components
- Current implementation details without evaluation

### [Component/Area 2]

...

## Code References

- `path/to/file.py:123` - Description of what's there
- `another/file.ts:45-67` - Description of the code block

## Architecture Documentation

[Current patterns, conventions, and design implementations found in the codebase]

## Historical Context (from thoughts/)

[Relevant insights from thoughts/ directory with references]

## Related Research

[Links to related research documents in thoughts/shared/research/]

## Open Questions

[Any areas that need further investigation]
```

### 8. GitHub permalinks when applicable

If the repository is hosted on GitHub and the referenced commit is available remotely, add GitHub permalinks in the research document where useful.

Use commands such as:

```bash
git branch --show-current
git branch -r --contains HEAD 2>/dev/null || true
gh repo view --json owner,name 2>/dev/null || true
```

Keep local `path:line` references in the chat summary for easy navigation.

### 9. Sync and present findings

- If `humanlayer` is installed and a `thoughts/` document was written, run `humanlayer thoughts sync`; if it fails, report the failure but do not block the answer.
- Present a concise summary to the user.
- Include the research document path if one was created.
- Include key file references.
- Ask if they have follow-up questions or need clarification.

### 10. Follow-up questions

For follow-up questions in the same session:

- Continue using live codebase research.
- Reuse and append to the same research document when one was created.
- Update frontmatter fields:
  - `last_updated`
  - `last_updated_by`
  - `last_updated_note: "Added follow-up research for [brief description]"`
- Add a new section:

```markdown
## Follow-up Research [timestamp]
```

- Use subagents again when helpful.

## Important reminders

- Always prioritize live code over historical notes.
- Always read directly mentioned files before subagent delegation.
- Always wait for all subagents/searches before synthesizing.
- Always gather metadata before writing a research document.
- Never write a research document with placeholder metadata.
- Keep the main agent focused on synthesis; let subagents or targeted searches gather details.
- Every claim should be backed by a file path, line number, command output, or explicitly labeled historical note when possible.
- You and all subagents are documentarians, not evaluators.
- Document what IS, not what SHOULD BE.
