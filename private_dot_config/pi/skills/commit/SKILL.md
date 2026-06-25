---
name: commit
description: Create git commits with user approval. Use when the user asks to review, stage, and commit current repository changes.
agent: commit
subtask: true
metadata:
  requires_user_approval: true
  staging: explicit-files-only
---

# Commit Changes

You are tasked with creating git commits for the changes made during this session.

## Process

1. **Think about what changed:**
   - Review the conversation history and understand what was accomplished.
   - Run `git status` to see current changes.
   - Run `git diff` to understand the modifications.
   - Consider whether changes should be one commit or multiple logical commits.

2. **Plan your commit(s):**
   - Identify which files belong together.
   - Draft clear, descriptive commit messages.
   - Use imperative mood in commit messages.
   - Focus on why the changes were made, not just what changed.

3. **Present your plan to the user:**
   - List the files you plan to add for each commit.
   - Show the commit message(s) you'll use.
   - Ask: "I plan to create [N] commit(s) with these changes. Shall I proceed?"

4. **Execute only upon confirmation:**
   - Use `git add` with specific files. Never use `git add -A`, `git add .`, or broad pathspecs.
   - Create commits with your planned messages.
   - Show the result with `git log --oneline -n [number]`.

## Important

- **NEVER add co-author information or AI attribution.**
- Commits should be authored solely by the user.
- Do not include any "Generated with Claude", "Generated with AI", or similar messages.
- Do not add `Co-Authored-By` lines.
- Write commit messages as if the user wrote them.

## Remember

- You have the full context of what was done in this session.
- Group related changes together.
- Keep commits focused and atomic when possible.
- The user trusts your judgment — they asked you to commit.
