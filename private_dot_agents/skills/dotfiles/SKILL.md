---
name: dotfiles
description: "Dotfiles ownership for persistent workstation configuration. Use when changing user- or machine-wide tool configuration, shell/editor/terminal settings, packages, macOS preferences, agent skills, or durable files under the home directory on this workstation."
---

# Dotfiles

This workstation is source-managed by chezmoi. For persistent workstation configuration, resolve the active source with `chezmoi source-path` and change it first; never make a live-only edit and plan to import it later.

## Workflow

1. **Classify ownership** - Decide whether the request changes durable user- or machine-wide workstation behavior. Project-local configuration, homeserver configuration, credentials, auth/session files, caches, histories, generated artifacts, and CLI-owned runtime state are outside this skill. Existing documented template, encryption, or bootstrap-seed patterns remain valid. _Done when every requested path is classified as chezmoi-owned or excluded with its actual owner stated._
2. **Inspect mapping** - Resolve the active repository with `chezmoi source-path`, then read its `AGENTS.md`, relevant source and live target, and `.chezmoiignore` when ownership or deployment is unclear. Use `chezmoi source-path <target>` and `chezmoi target-path <source>` to check mappings, but edit only inside the resolved source repository. _Done when every requested live target maps to a specific source path and its template/runtime behavior is understood._
3. **Guard new ownership** - If chezmoi does not already manage a requested target, inspect it for sensitive or runtime-generated content and ask the user before adding it. Do not introduce a new secret, credential, auth/session, cache, history, generated, or runtime-state pattern. _Done when every target is either already managed or the user has approved a safe new source mapping._
4. **Edit source-first** - Make the smallest change in the chezmoi source. Preserve existing templates, encryption, OS/profile guards, bootstrap-seed behavior, and repository conventions. Check the Docs Maintenance Rule in `AGENTS.md` and update mapped docs only when the change warrants it. _Done when every requested persistent change exists in source and no live target was edited directly._
5. **Preview targets** - Run `chezmoi apply --dry-run --force <target>...` with only the requested target paths. Inspect the complete preview for side effects. Do not use an unscoped apply. _Done when the dry run succeeds and contains no unrelated target changes or unintended lifecycle effects._
6. **Apply narrowly** - If the user asked to make the change and the preview is isolated, run `chezmoi apply --force <target>...` for those same targets only. Otherwise stop after the preview and explain the blocker. _Done when the targeted apply succeeds or a concrete scope/safety blocker is reported._
7. **Verify convergence** - Re-read the changed live targets and use a target-scoped `chezmoi diff` or dry run to confirm rendered source and live state agree. _Done when every requested target matches source and no unrelated path was applied._

## Hard Rules

- Never edit a persistent workstation target directly.
- Never run bare `chezmoi apply`; always name the intended target paths.
- Never capture unmanaged secrets or runtime state. Ask before expanding chezmoi ownership.
- Do not treat this repository as the owner of project-local or homeserver configuration.
