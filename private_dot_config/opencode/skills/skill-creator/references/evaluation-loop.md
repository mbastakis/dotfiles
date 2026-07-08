# Evaluation Loop

Use this branch only when the user asks for evals, benchmarks, comparison evidence, or review artifacts, or when a skill change needs objective verification.

## Gate

Before starting, confirm the eval loop is the right tool:

- Use evals for objectively checkable outputs, deterministic workflows, risky rewrites, and explicit benchmark requests.
- Use qualitative review for subjective style changes, small description edits, or quick skill comparisons.
- If improving an existing skill and evals are likely, snapshot the old skill before editing.

Completion criterion: evals are justified, or the task is routed back to Create, Improve, Description, or Blind Comparison.

## Workspace Layout

Create the workspace as a sibling to the skill directory:

```text
<skill-name>-workspace/
  iteration-1/
    runs/
      eval-0-short-name/
        eval_metadata.json
        with_skill/
          run-1/
            eval_metadata.json
            outputs/
            grading.json
            timing.json
        without_skill/
          run-1/
            eval_metadata.json
            outputs/
            grading.json
            timing.json
    benchmark.json
    benchmark.md
    review.html
```

For improving an existing skill, use `new_skill/` and `old_skill/` instead of `with_skill/` and `without_skill/`. Keep the new/current skill configuration alphabetically before the baseline so benchmark deltas read in the useful direction.

Write `eval_metadata.json` both at the eval directory and in each `run-*` directory. The aggregator reads the eval-level file; the review viewer can read the run-level file.

## Step 1: Create Eval Cases

Draft 2-3 realistic prompts first. Prefer prompts a real user would type, with concrete paths, messy context, and expected outputs.

Save them in `evals/evals.json` under the skill directory:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 0,
      "prompt": "User's task prompt",
      "expected_output": "What a successful result should contain",
      "files": [],
      "expectations": []
    }
  ]
}
```

If the user has not already approved the eval set, show the prompts and ask for confirmation before launching expensive runs.

Completion criterion: each eval has an id, prompt, expected output, input files if any, and an eval directory with matching metadata.

## Step 2: Launch Runs

Launch with-skill and baseline runs for each eval in the same turn when feasible. Use `subagent_type="general"`.

Use this prompt shape for a current-skill run:

```text
Execute this skill eval run.
- Skill path: <path-to-skill>
- Eval prompt: <eval prompt>
- Input files: <files or none>
- Save final deliverables to: <run-dir>/outputs/
- Save a concise transcript to: <run-dir>/outputs/transcript.md
- Save uncertainties, workarounds, and human-review needs to: <run-dir>/outputs/user_notes.md if any exist.

Before starting, read the SKILL.md at the skill path and follow its instructions.
```

For a new-skill baseline, omit the skill path and tell the agent to solve the same eval without a skill. For an existing-skill baseline, point the agent at the snapshot.

When a Task result includes timing or token data, immediately write `<run-dir>/timing.json`:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

Completion criterion: every eval has a current-skill run and a baseline run, with outputs saved under the planned run directories.

## Step 3: Draft Expectations While Runs Execute

Use the wait time to write objective `expectations`. Good expectations are discriminating: they fail when the work is superficial and pass when the task is genuinely done.

Avoid expectations that only check a filename, a keyword, or a claim in the transcript. Prefer checks against the produced artifact.

Update `evals/evals.json` and each `eval_metadata.json` with the final expectations.

Completion criterion: every eval has expectations, or a written note explains why qualitative review is the right standard.

## Step 4: Grade Runs

Grade each run after outputs exist. Use scripts for programmatically checkable expectations; otherwise launch a grader agent using `agents/grader.md`.

Save `<run-dir>/grading.json`. The viewer and aggregator require expectation objects with these fields:

```json
{
  "text": "The output includes the requested columns with correct values",
  "passed": true,
  "evidence": "Verified in outputs/result.csv rows 2-10"
}
```

Completion criterion: every run has `grading.json`, or the blocker is captured in the run directory.

## Step 5: Aggregate And Analyze

Run the aggregator from the skill-creator directory:

```bash
python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name> --skill-path <path-to-skill>
```

This writes `benchmark.json` and `benchmark.md`. Then do an analyst pass with `agents/analyzer.md`, using the "Analyzing Benchmark Results" section, and add useful notes to `benchmark.json` if patterns are not visible from the summary numbers.

Completion criterion: `benchmark.json` exists and contains the run configurations, pass rates, timing, tokens, expectations, and analyst notes when available.

## Step 6: Generate The Review Viewer

Generate the viewer before making your own final judgment so the human can inspect outputs quickly:

```bash
python <skill-creator-path>/eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "<skill-name>" \
  --benchmark <workspace>/iteration-N/benchmark.json \
  --static <workspace>/iteration-N/review.html
```

For iteration 2 and later, add:

```bash
--previous-workspace <workspace>/iteration-<N-1>
```

Open it on macOS:

```bash
open <workspace>/iteration-N/review.html
```

Completion criterion: the review HTML is opened, or the exact viewer generation error is reported.

## Step 7: Read Feedback And Iterate

When the user says review is complete, read `feedback.json`. Empty feedback means the user accepted that output. Specific complaints drive the next revision.

Apply improvements to the skill, then rerun the same eval set into `iteration-<N+1>/` if another evidence loop is warranted.

Completion criterion: feedback has been reflected in either a skill edit, a new eval iteration, or a clear stop decision.

## Reference Files

- `references/schemas.md`: JSON structures for evals, grading, metrics, timing, benchmark, comparison, and analysis files.
- `agents/grader.md`: grader prompt for expectation checks and eval critique.
- `agents/analyzer.md`: benchmark notes and post-hoc analysis.
- `agents/comparator.md`: blind A/B judging.
