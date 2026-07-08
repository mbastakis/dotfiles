---
name: skill-creator
description: Skill-creator workflow for building and validating Agent Skills. Use when the user wants to create or revise a skill, run skill evals or benchmarks, compare skill versions, or tune a skill description for invocation.
---

# Skill Creator

Operational workflow for creating, improving, and evaluating Agent Skills in OpenCode. Keep this file as the branch router; load reference files only when that branch needs their mechanics.

## First Decision

Classify the request before acting:

- Create: user wants a new skill or says "turn this into a skill".
- Improve: user wants an existing skill edited, optimized, pruned, split, or reviewed.
- Evaluate: user asks to test, benchmark, run evals, compare performance, or produce review artifacts.
- Description: user asks about triggering, invocation, under-triggering, over-triggering, `description`, or `disable-model-invocation`.
- Blind comparison: user asks whether one skill, output, or version is actually better without bias.

Do not run the eval loop for a lightweight comparison or design question unless the user asks for evidence from runs. Completion criterion: one branch is selected and the work ends with either a changed skill, an opened review artifact, or a direct recommendation.

## Shared Rules

- Edit the chezmoi source when present: `private_dot_config/opencode/skills/<name>/` for OpenCode-only skills, or `private_dot_agents/skills/<name>/` for shared skills.
- Preserve an existing skill's directory name and `name` frontmatter unless the user explicitly asks to rename it.
- Snapshot an existing skill before editing if you expect to benchmark old versus new.
- Prefer small, load-bearing edits over rewrites. Remove no-ops instead of rephrasing them.
- Treat evals as a branch, not a ritual. Use them when outputs are objectively checkable, the user asks for benchmarks, or the change is risky enough to need evidence.
- Use `expectations` for verifiable eval checks; the grader, aggregator, and schemas all use that field.
- If the task is specifically about skill-writing doctrine, or the user invokes `writing-great-skills`, read `/Users/mbastakis/.agents/skills/writing-great-skills/SKILL.md` and apply its vocabulary.

## Create Branch

1. Capture intent from the conversation first: what the skill should do, when it should trigger, expected outputs, required tools, and whether tests are useful. Ask only for missing information that blocks a correct draft.
Completion criterion: name, invocation mode, main branches, expected output, and success criteria are known or explicitly marked unknown.

2. Draft the skill with the smallest useful structure: frontmatter, ordered steps when process matters, reference sections only when needed, and bundled resources for repeated deterministic work.
Completion criterion: `SKILL.md` exists with valid frontmatter and every step has a checkable completion criterion.

3. Decide whether to evaluate. If the skill has objectively verifiable behavior or the user wants proof, continue to the Evaluate branch. Otherwise do a qualitative pass against the Shared Rules and finish.
Completion criterion: either evals are launched or the draft is reviewed for invocation, hierarchy, pruning, and obvious failure modes.

## Improve Branch

1. Read the existing skill and relevant bundled resources. Identify concrete issues: wrong invocation mode, bloated description, unclear completion criteria, sprawl, duplication, sediment, no-ops, missing scripts, or eval/tooling drift.
Completion criterion: every proposed issue maps to a specific edit or is discarded.

2. Edit only the load-bearing parts. Keep stable names, schemas, scripts, and workspace layouts unless they are the defect.
Completion criterion: the diff changes behavior or maintainability without unrelated churn.

3. Verify at the lightest sufficient level. Use markdown/schema inspection for prose-only changes; use the Evaluate branch for behavioral claims.
Completion criterion: verification matches the risk of the change.

## Evaluate Branch

Read `references/evaluation-loop.md` and follow it end to end. Use it for eval creation, with-skill/baseline runs, grading, benchmark aggregation, analyzer notes, and `eval-viewer/generate_review.py`.

Completion criterion: the review HTML is generated and opened, or a clear blocker explains why it could not be.

## Description Branch

Read `references/description-optimization.md` before changing frontmatter. Use it for invocation-mode decisions, trigger eval query design, human review of trigger cases, and manual description rewrite.

Completion criterion: the frontmatter matches the selected invocation mode and the before/after description is explainable by trigger branches.

## Blind Comparison Branch

Use this only when the user wants a rigorous A/B judgment between outputs or skill versions.

1. Read `agents/comparator.md` and prepare anonymized A/B inputs.
2. Run the comparator with `Task(subagent_type="general")` or inline if small.
3. Read `agents/analyzer.md` and unblind the result to explain why the winner won.
4. Apply improvements only after the comparison result is saved.

Completion criterion: comparison output and analysis are saved, with a recommendation grounded in the evidence.

## OpenCode Mechanics

- Use the Task tool's `general` subagent for eval execution, grading, analyzer, and comparator work.
- Launch independent eval runs in the same turn when possible so with-skill and baseline runs finish together.
- On macOS, open generated HTML with `open <path>`.
- Do not use `claude -p` dependent scripts in OpenCode. Description optimization is manual here.
- Reference schemas in `references/schemas.md` before writing `evals.json`, `grading.json`, or `benchmark.json`.
