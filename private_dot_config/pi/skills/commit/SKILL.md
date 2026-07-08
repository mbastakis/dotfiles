---
name: commit
description: Commit current git repository changes through a review-plan-approval gate. Use when the user asks to commit current changes or split them into multiple git commits.
metadata:
  requires_user_approval: true
  staging: explicit-files-only
---

# Commit

Commit only reviewed, user-approved changes. Treat the commit as a ledger entry: every included path must be inspected, classified, and intentionally grouped before anything is staged.

## Process

1. **Survey the repository.**
   - Review the conversation for what was intentionally changed in this session.
   - Run `git status --short`, `git diff --stat`, `git diff`, `git diff --cached`, and `git log --oneline -10`.
   - Inspect untracked files before including them.
   - Completion: every changed path, including already-staged content, is classified as `commit N`, `leave untouched`, or `ask user`.

2. **Design the commit set.**
   - Prefer one commit unless the changes are independent enough to review or revert separately.
   - Group files by cohesive change, not by file type.
   - If a file contains mixed concerns, call that out and ask before attempting a split.
   - Draft imperative commit messages that explain the change clearly; add a body only when the subject cannot carry the reason.
   - Completion: each planned commit has an exact file list and message, and no included file contains unaccounted-for changes.

3. **Pass the approval gate.**
   - Present each planned commit with its message and exact files.
   - List any changed files that will be left untouched.
   - Mention already-staged changes and mixed-concern files explicitly.
   - Ask: `I plan to create [N] commit(s) with this exact plan. Shall I proceed?`
   - Completion: the user explicitly approves the exact plan. If the user changes the plan, revise it and ask again.

4. **Commit the approved files.**
   - Stage only approved files with explicit pathspecs: `git add -- <path> ...`.
   - Never use `git add -A`, `git add .`, broad directory pathspecs, or `--no-verify`.
   - Before each commit, run `git diff --cached --stat` and `git diff --cached`; stop if the staged diff does not match the approved commit.
   - Run `git commit` with the approved message.
   - If a hook fails, inspect the failure. Fix it only when it is in scope; otherwise report the blocker.
   - Completion: `git log --oneline -n [N]` shows the new commit(s), and `git status --short` shows only expected leftover changes.

## Commit Message Rules

- Write as the user, with no AI attribution.
- Do not add `Co-Authored-By` lines.
- Do not include `Generated with Claude`, `Generated with AI`, or similar text.
- Keep subjects concise and imperative.
