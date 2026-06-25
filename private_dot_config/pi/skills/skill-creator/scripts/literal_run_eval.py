#!/usr/bin/env python3
"""Run trigger evaluation for a Pi skill description.

Tests whether a skill's description causes pi to trigger (read the skill's
SKILL.md) for a set of queries. Outputs results as JSON.
"""

import argparse
import json
import os
import re
import select
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

SKILL_CREATOR_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_CREATOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_CREATOR_ROOT))

from scripts.utils import parse_skill_md


def find_project_root() -> Path:
    """Find a reasonable cwd for pi runs by walking up to the git root."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    return current


def normalize_skill_name(name: str, unique_id: str) -> str:
    """Return a valid, unique Pi skill name within the 64-char limit."""
    base = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-") or "skill"
    base = re.sub(r"-+", "-", base).strip("-") or "skill"
    suffix = f"trigger-{unique_id}"
    max_base_len = 64 - len(suffix) - 1
    base = base[:max_base_len].strip("-") or "skill"
    return f"{base}-{suffix}"


def make_temp_skill(parent: Path, skill_name: str, skill_description: str) -> tuple[Path, Path, str]:
    """Create a temporary Pi skill and return (skill_dir, skill_file, clean_name)."""
    unique_id = uuid.uuid4().hex[:8]
    clean_name = normalize_skill_name(skill_name, unique_id)
    skill_dir = parent / clean_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "SKILL.md"

    indented_desc = "\n  ".join(skill_description.split("\n"))
    skill_file.write_text(
        f"---\n"
        f"name: {clean_name}\n"
        f"description: |\n"
        f"  {indented_desc}\n"
        f"---\n\n"
        f"# {skill_name}\n\n"
        f"This temporary skill exists only for trigger evaluation.\n"
        f"If you read this file, the trigger evaluation should count the skill as triggered.\n"
    )
    return skill_dir, skill_file, clean_name


def event_reads_skill(event: dict, skill_file: Path, skill_dir: Path, clean_name: str) -> bool:
    """Return True when a pi JSON event shows the model reading this skill."""
    if event.get("type") != "tool_execution_start":
        return False

    tool_name = str(event.get("toolName", "")).lower()
    if tool_name != "read":
        return False

    args = event.get("args", {})
    args_text = json.dumps(args, sort_keys=True)
    skill_file_str = str(skill_file)
    skill_dir_str = str(skill_dir)

    return (
        skill_file_str in args_text
        or skill_dir_str in args_text
        or clean_name in args_text and "SKILL.md" in args_text
    )


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Run a single query and return whether the Pi skill was triggered.

    A temporary skill is loaded explicitly with ``--skill`` while normal skill
    discovery is disabled with ``--no-skills``. The run uses ``--mode json`` so
    we can watch tool events and return as soon as pi reads that skill's
    SKILL.md.
    """
    with tempfile.TemporaryDirectory(prefix="pi-skill-trigger-") as tmp:
        skill_dir, skill_file, clean_name = make_temp_skill(
            Path(tmp), skill_name, skill_description
        )

        cmd = [
            "pi",
            "--mode",
            "json",
            "--no-session",
            "--no-context-files",
            "--no-prompt-templates",
            "--no-skills",
            "--skill",
            str(skill_dir),
        ]
        if model:
            cmd.extend(["--model", model])
        cmd.append(query)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=project_root,
            env=os.environ.copy(),
        )

        start_time = time.time()
        buffer = ""

        try:
            while time.time() - start_time < timeout:
                if process.poll() is not None:
                    remaining = process.stdout.read() if process.stdout else b""
                    if remaining:
                        buffer += remaining.decode("utf-8", errors="replace")
                    break

                ready, _, _ = select.select([process.stdout], [], [], 1.0)
                if not ready:
                    continue

                chunk = os.read(process.stdout.fileno(), 8192)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="replace")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if event_reads_skill(event, skill_file, skill_dir, clean_name):
                        return True

            # Process any trailing JSON lines collected after process exit.
            for line in buffer.splitlines():
                try:
                    event = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                if event_reads_skill(event, skill_file, skill_dir, clean_name):
                    return True

            return False
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return results."""
    results = []

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_triggers:
                query_triggers[query] = []
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                print(f"Warning: query failed: {e}", file=sys.stderr)
                query_triggers[query].append(False)

    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(triggers),
            "runs": len(triggers),
            "pass": did_pass,
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a Pi skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=4, help="Number of parallel pi processes")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Pi model pattern to use (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, _content = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root()

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    if args.verbose:
        summary = output["summary"]
        print(f"Results: {summary['passed']}/{summary['total']} passed", file=sys.stderr)
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            print(f"  [{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
