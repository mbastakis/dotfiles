from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class OperationalError(Exception):
    """An external command or API failed without exposing sensitive output."""


def run_command(
    command: Sequence[str],
    *,
    timeout: float,
    input_text: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            input=input_text,
            timeout=timeout,
            env=environment,
        )
    except FileNotFoundError as error:
        raise OperationalError(f"command not found: {command[0]}") from error
    except subprocess.TimeoutExpired as error:
        raise OperationalError(f"command timed out after {timeout:g}s: {command[0]}") from error

    if result.returncode != 0:
        raise OperationalError(
            f"command failed with exit {result.returncode}: {Path(command[0]).name}"
        )
    return result.stdout


def run_json_command(
    command: Sequence[str],
    *,
    timeout: float,
    input_text: str | None = None,
    environment: Mapping[str, str] | None = None,
    allow_python_literals: bool = False,
) -> Any:
    output = run_command(
        command,
        timeout=timeout,
        input_text=input_text,
        environment=environment,
    )
    try:
        return json.loads(output)
    except json.JSONDecodeError as error:
        if allow_python_literals:
            literals = {"True": True, "False": False, "None": None}
            if output.strip() in literals:
                return literals[output.strip()]
        raise OperationalError(f"command returned invalid JSON: {Path(command[0]).name}") from error
