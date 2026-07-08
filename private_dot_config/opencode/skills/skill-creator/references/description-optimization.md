# Description Optimization

Use this branch when the user asks about skill triggering, invocation, `description`, `disable-model-invocation`, under-triggering, over-triggering, or description quality.

## Step 1: Choose Invocation Mode

Decide whether the skill should be model-invoked or user-invoked.

- Model-invoked: omit `disable-model-invocation`; write a model-facing `description` that states the skill and its trigger branches.
- User-invoked: set `disable-model-invocation: true`; keep `description` as a short human-facing summary.

Use model invocation only when the agent must reach the skill autonomously or another skill must route to it. Otherwise make it user-invoked and avoid permanent context load.

Completion criterion: the invocation mode is explicit and justified by reach, not habit.

## Step 2: Draft Trigger Evals For Model-Invoked Skills

For model-invoked skills, create 16-20 realistic trigger queries. Use a balanced mix of should-trigger and should-not-trigger cases.

Each query should be concrete enough that a user might actually type it: include paths, surrounding context, messy phrasing, adjacent domains, or competing skills when useful.

Good should-trigger cases cover distinct branches, not synonyms for the same branch. Good should-not-trigger cases are near-misses, not obviously unrelated prompts.

Save the set as JSON:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "near-miss prompt", "should_trigger": false}
]
```

Completion criterion: every trigger branch has coverage and every negative case is a plausible false positive.

## Step 3: Review Trigger Evals With The User

Use `assets/eval_review.html` to let the user edit the trigger set:

1. Read the template.
2. Replace `__EVAL_DATA_PLACEHOLDER__` with the JSON array, without wrapping it in quotes.
3. Replace `__SKILL_NAME_PLACEHOLDER__` with the skill name.
4. Replace `__SKILL_DESCRIPTION_PLACEHOLDER__` with the current description.
5. Write the result to a temp HTML file and open it with `open <file>`.

The user exports `eval_set.json` from the browser. Use the most recent exported file if several exist.

Completion criterion: the reviewed trigger set is available, or the user explicitly skips human review.

## Step 4: Rewrite The Description Manually

OpenCode cannot use the upstream `claude -p` description scripts directly, so rewrite by hand.

Apply these rules:

- Front-load the leading word or phrase users actually use for the skill.
- Include one trigger per branch.
- Remove synonyms that rename the same branch.
- Keep identity and detailed mechanics in the body, not the description.
- Include a reach clause only when another skill should route to this one.
- Preserve `disable-model-invocation: true` for user-invoked skills.

Completion criterion: each sentence in the description changes invocation behavior; no sentence only summarizes body content.

## Step 5: Apply And Report

Update the skill frontmatter. Show the before and after descriptions, then explain which trigger branches each phrase covers and which near-misses it avoids.

For high-stakes routing changes, ask the user to test selected trigger evals in a fresh session.

Completion criterion: the updated frontmatter is saved and the invocation tradeoff is documented.
