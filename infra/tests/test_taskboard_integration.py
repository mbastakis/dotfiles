import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

TASKBOARD_DIR = Path(__file__).parents[1] / "atlas/ansible/roles/atlas_homeserver/files/taskboard"


def request_json(base_url: str, path: str, method: str = "GET", payload: dict | None = None):
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def board_tasks(board: dict) -> dict[str, dict]:
    return {task["uuid"]: task for column in board["columns"] for task in column["tasks"]}


def taskwarrior_binary() -> str | None:
    candidates = [
        os.environ.get("TASKBOARD_TASK_BIN"),
        "/opt/homebrew/bin/task",
        "/usr/local/bin/task",
        shutil.which("task"),
    ]
    for candidate in filter(None, candidates):
        result = subprocess.run(
            [candidate, "--version"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0 and result.stdout.strip()[:1].isdigit():
            return candidate
    return None


@pytest.fixture
def taskboard_server(tmp_path: Path) -> Iterator[str]:
    task_bin = taskwarrior_binary()
    if task_bin is None:
        pytest.skip("Taskwarrior is not installed")

    data_dir = tmp_path / "taskwarrior"
    data_dir.mkdir()
    taskrc = tmp_path / "taskrc"
    taskrc.write_text(
        "\n".join(
            [
                f"data.location={data_dir}",
                "confirmation=off",
                "recurrence.confirmation=off",
                "verbose=off",
                "",
            ]
        )
    )
    with socket.socket() as listener:
        try:
            listener.bind(("127.0.0.1", 0))
        except PermissionError:
            pytest.skip("loopback sockets are unavailable in this validation sandbox")
        port = listener.getsockname()[1]

    env = {
        **os.environ,
        "TASKRC": str(taskrc),
        "TASKBOARD_ALLOW_NO_AUTH": "1",
        "TASKBOARD_DONE_DAYS": "3650",
        "TASKBOARD_HOST": "127.0.0.1",
        "TASKBOARD_PORT": str(port),
        "TASKBOARD_SYNC_ENABLED": "0",
        "TASKBOARD_TASK_BIN": task_bin,
    }
    process = subprocess.Popen(
        [sys.executable, "taskboard.py"],
        cwd=TASKBOARD_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(50):
            try:
                with urllib.request.urlopen(f"{base_url}/healthz", timeout=0.2) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.1)
        else:
            output = process.communicate(timeout=2)[0]
            pytest.fail(f"taskboard server did not start:\n{output}")
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def test_real_taskwarrior_mutation_lifecycle(taskboard_server: str) -> None:
    status, board = request_json(
        taskboard_server,
        "/api/tasks",
        "POST",
        {"description": "Integration parent", "project": "sisyphus.test", "column": "backlog"},
    )
    assert status == 200, board
    parent = next(
        task for task in board_tasks(board).values() if task["description"] == "Integration parent"
    )

    time.sleep(1.1)
    status, board = request_json(
        taskboard_server,
        f"/api/tasks/{parent['uuid']}",
        "PATCH",
        {
            "description": "Integration parent updated",
            "priority": "M",
            "expected_modified": parent["modified"],
        },
    )
    assert status == 200, board
    updated_parent = board_tasks(board)[parent["uuid"]]
    assert updated_parent["description"] == "Integration parent updated"
    assert updated_parent["priority"] == "M"

    status, conflict = request_json(
        taskboard_server,
        f"/api/tasks/{parent['uuid']}",
        "PATCH",
        {"description": "Stale overwrite", "expected_modified": parent["modified"]},
    )
    assert status == 409
    assert conflict["current_task"]["description"] == "Integration parent updated"

    status, created = request_json(
        taskboard_server,
        f"/api/tasks/{parent['uuid']}/dependencies",
        "POST",
        {
            "description": "Integration blocker",
            "expected_modified": updated_parent["modified"],
        },
    )
    assert status == 200, created
    blocker_uuid = created["created_uuid"]
    tasks = board_tasks(created["board"])
    assert blocker_uuid in tasks[parent["uuid"]]["depends"]
    assert tasks[blocker_uuid]["project"] == "sisyphus.test"

    status, board = request_json(
        taskboard_server,
        "/api/tasks/bulk",
        "POST",
        {
            "tasks": [
                {"uuid": uuid, "expected_modified": tasks[uuid]["modified"]}
                for uuid in (parent["uuid"], blocker_uuid)
            ],
            "changes": {"priority": "H", "tags": "integration"},
        },
    )
    assert status == 200
    tasks = board_tasks(board)
    for uuid in (parent["uuid"], blocker_uuid):
        assert tasks[uuid]["priority"] == "H"
        assert "integration" in tasks[uuid]["tags"]

    status, board = request_json(
        taskboard_server,
        f"/api/tasks/{blocker_uuid}/move",
        "POST",
        {"column": "ready", "expected_modified": tasks[blocker_uuid]["modified"]},
    )
    assert status == 200
    tasks = board_tasks(board)
    assert "next" in tasks[blocker_uuid]["tags"]

    status, board = request_json(
        taskboard_server,
        f"/api/tasks/{blocker_uuid}",
        "DELETE",
        {"expected_modified": tasks[blocker_uuid]["modified"]},
    )
    assert status == 200
    assert blocker_uuid not in board_tasks(board)
