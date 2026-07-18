import importlib
import io
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

TASKBOARD_DIR = Path(__file__).parents[1] / "atlas/ansible/roles/atlas_homeserver/files/taskboard"
FIXTURE_PATH = Path(__file__).parent / "fixtures/taskboard_export.json"
TASKBOARD_MODULES = (
    "taskboard",
    "taskboard_board",
    "taskboard_runtime",
    "taskboard_service",
    "taskboard_validation",
)


def load_taskboard() -> ModuleType:
    for name in TASKBOARD_MODULES:
        sys.modules.pop(name, None)
    sys.path.insert(0, str(TASKBOARD_DIR))
    try:
        return importlib.import_module("taskboard")
    finally:
        sys.path.remove(str(TASKBOARD_DIR))


def loaded_module(name: str) -> ModuleType:
    return sys.modules[name]


def fixture_tasks() -> list[dict[str, object]]:
    return json.loads(FIXTURE_PATH.read_text())


def board_tasks_by_uuid(board: dict[str, object]) -> dict[str, dict[str, object]]:
    return {task["uuid"]: task for column in board["columns"] for task in column["tasks"]}


def test_entrypoint_delegates_to_focused_modules() -> None:
    taskboard = load_taskboard()

    assert taskboard.build_board.__module__ == "taskboard_board"
    assert taskboard.update_task.__module__ == "taskboard_service"
    assert taskboard.env_bool.__module__ == "taskboard_validation"
    assert taskboard.TaskCommandError.__module__ == "taskboard_runtime"


def test_build_board_maps_and_enriches_taskwarrior_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_taskboard()
    board_module = loaded_module("taskboard_board")
    runtime = loaded_module("taskboard_runtime")
    monkeypatch.setattr(runtime, "export_tasks", fixture_tasks)
    monkeypatch.setattr(runtime, "export_task", lambda uuid: None)
    monkeypatch.setattr(runtime, "iso_now", lambda: "2026-07-12T12:00:00+00:00")
    runtime.STATE.update(
        {
            "last_sync_attempt_at": "2026-07-12T11:59:58+00:00",
            "last_sync_at": "2026-07-12T11:59:59+00:00",
            "last_sync_error": None,
        }
    )

    board = board_module.build_board(sync=False)

    columns = {column["id"]: column["tasks"] for column in board["columns"]}
    assert [task["description"] for task in columns["backlog"]] == ["Clarify captured task"]
    assert [task["description"] for task in columns["ready"]] == ["Selected next action"]
    assert [task["description"] for task in columns["doing"]] == ["Work in progress"]
    assert [task["description"] for task in columns["waiting"]] == ["Deferred until next week"]
    assert [task["description"] for task in columns["done"]] == ["Recently completed task"]
    assert columns["waiting"][0]["scheduled"] == "20260719T080000Z"
    assert columns["waiting"][0]["modified"] == "20260712T080000Z"
    assert columns["waiting"][0]["annotations"][0]["description"].startswith("Review")
    assert board["last_sync_attempt_at"] == "2026-07-12T11:59:58+00:00"
    assert board["last_sync_at"] == "2026-07-12T11:59:59+00:00"
    assert board["last_sync_error"] is None
    assert board["generated_at"] == "2026-07-12T12:00:00+00:00"

    tasks = board_tasks_by_uuid(board)
    waiting = tasks["44444444-4444-4444-8444-444444444444"]
    assert waiting["blocked"] is True
    assert waiting["dependency_details"] == [
        {
            "uuid": "11111111-1111-4111-8111-111111111111",
            "description": "Clarify captured task",
            "project": "planning",
            "status": "pending",
            "blocking": True,
            "resolved": False,
        },
        {
            "uuid": "55555555-5555-4555-8555-555555555555",
            "description": "Recently completed task",
            "project": "archive",
            "status": "completed",
            "blocking": False,
            "resolved": True,
        },
        {
            "uuid": "99999999-9999-4999-8999-999999999999",
            "description": "99999999-9999-4999-8999-999999999999",
            "project": "",
            "status": "missing",
            "blocking": False,
            "resolved": False,
        },
    ]
    dependent = {
        "uuid": waiting["uuid"],
        "description": waiting["description"],
        "project": waiting["project"],
    }
    assert tasks["11111111-1111-4111-8111-111111111111"]["dependent_tasks"] == [dependent]
    assert tasks["55555555-5555-4555-8555-555555555555"]["dependent_tasks"] == [dependent]
    assert tasks["22222222-2222-4222-8222-222222222222"]["blocked"] is False


def test_dependency_lookup_classifies_off_board_and_dangling_tasks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_taskboard()
    board_module = loaded_module("taskboard_board")
    runtime = loaded_module("taskboard_runtime")
    task_uuid = "11111111-1111-4111-8111-111111111111"
    completed_uuid = "22222222-2222-4222-8222-222222222222"
    deleted_uuid = "33333333-3333-4333-8333-333333333333"
    missing_uuid = "44444444-4444-4444-8444-444444444444"
    waiting_uuid = "55555555-5555-4555-8555-555555555555"
    blocked_uuid = "66666666-6666-4666-8666-666666666666"
    displayed = [
        {
            "uuid": task_uuid,
            "description": "Actionable despite old links",
            "status": "pending",
            "tags": ["next"],
            "depends": [completed_uuid, deleted_uuid, missing_uuid],
        },
        {
            "uuid": blocked_uuid,
            "description": "Still blocked",
            "status": "pending",
            "tags": ["next"],
            "depends": [waiting_uuid],
        },
    ]
    fetched = {
        completed_uuid: {
            "uuid": completed_uuid,
            "description": "Old completed prerequisite",
            "status": "completed",
        },
        deleted_uuid: {
            "uuid": deleted_uuid,
            "description": "Deleted prerequisite",
            "status": "deleted",
        },
        waiting_uuid: {
            "uuid": waiting_uuid,
            "description": "Deferred prerequisite",
            "status": "waiting",
        },
    }
    lookups: list[str] = []
    monkeypatch.setattr(runtime, "export_tasks", lambda: displayed)
    monkeypatch.setattr(
        runtime,
        "export_task",
        lambda uuid: lookups.append(uuid) or fetched.get(uuid),
    )

    result = board_module.build_board(sync=False)
    tasks = board_tasks_by_uuid(result)

    assert set(lookups) == {completed_uuid, deleted_uuid, missing_uuid, waiting_uuid}
    assert tasks[task_uuid]["blocked"] is False
    assert [detail["status"] for detail in tasks[task_uuid]["dependency_details"]] == [
        "completed",
        "deleted",
        "missing",
    ]
    assert [detail["resolved"] for detail in tasks[task_uuid]["dependency_details"]] == [
        True,
        True,
        False,
    ]
    assert tasks[blocked_uuid]["blocked"] is True
    columns = {
        column["id"]: [task["uuid"] for task in column["tasks"]] for column in result["columns"]
    }
    assert task_uuid in columns["ready"]
    assert blocked_uuid in columns["waiting"]


def test_sync_state_records_failures_and_later_success(monkeypatch: pytest.MonkeyPatch) -> None:
    load_taskboard()
    runtime = loaded_module("taskboard_runtime")
    timestamps = iter(
        [
            "2026-07-12T12:00:00+00:00",
            "2026-07-12T12:01:00+00:00",
            "2026-07-12T12:01:01+00:00",
        ]
    )
    results = iter(
        [
            SimpleNamespace(returncode=1, stdout="", stderr="network unavailable\n"),
            SimpleNamespace(returncode=0, stdout="sync complete\n", stderr=""),
        ]
    )
    runtime.STATE.update(
        {
            "last_sync_attempt_at": None,
            "last_sync_at": "2026-07-12T11:00:00+00:00",
            "last_sync_error": None,
        }
    )
    monkeypatch.setattr(runtime, "iso_now", lambda: next(timestamps))
    monkeypatch.setattr(runtime, "run_task", lambda args, allow_failure: next(results))

    runtime.sync_tasks(allow_failure=True)
    assert runtime.STATE == {
        "last_sync_attempt_at": "2026-07-12T12:00:00+00:00",
        "last_sync_at": "2026-07-12T11:00:00+00:00",
        "last_sync_error": "network unavailable",
    }

    runtime.sync_tasks(allow_failure=True)
    assert runtime.STATE == {
        "last_sync_attempt_at": "2026-07-12T12:01:00+00:00",
        "last_sync_at": "2026-07-12T12:01:01+00:00",
        "last_sync_error": None,
    }


def test_moving_completed_task_reopens_before_assigning_column() -> None:
    load_taskboard()
    service = loaded_module("taskboard_service")
    task = {
        "uuid": "55555555-5555-4555-8555-555555555555",
        "status": "completed",
        "tags": [],
        "start": "",
    }

    assert service.command_for_column(task, "ready") == [
        [task["uuid"], "modify", "status:pending"],
        [task["uuid"], "modify", "+next", "-waiting", "wait:"],
    ]


def test_clean_dependencies_requires_stable_uuids() -> None:
    load_taskboard()
    validation = loaded_module("taskboard_validation")
    uuid = "11111111-1111-4111-8111-111111111111"

    assert validation.clean_dependencies(f"{uuid}, {uuid}") == [uuid]
    with pytest.raises(ValueError, match="invalid task uuid"):
        validation.clean_dependencies("12")


def test_update_task_uses_uuid_modify_then_annotation(monkeypatch: pytest.MonkeyPatch) -> None:
    load_taskboard()
    board_module = loaded_module("taskboard_board")
    runtime = loaded_module("taskboard_runtime")
    service = loaded_module("taskboard_service")
    uuid = "44444444-4444-4444-8444-444444444444"
    dependency = "11111111-1111-4111-8111-111111111111"
    commands: list[list[str]] = []
    monkeypatch.setattr(runtime, "sync_tasks", lambda allow_failure: None)
    monkeypatch.setattr(runtime, "export_tasks", fixture_tasks)
    monkeypatch.setattr(runtime, "run_task", lambda args: commands.append(args))
    monkeypatch.setattr(board_module, "build_board", lambda sync: {"sync": sync})

    result = service.update_task(
        uuid,
        {
            "description": "Review project:danger +surprise as one description",
            "wait": "2026-07-20",
            "scheduled": "2026-07-19",
            "depends": dependency,
            "annotation": "Waiting for supplier confirmation",
            "expected_modified": "20260712T080000Z",
        },
    )

    assert commands == [
        [
            uuid,
            "modify",
            "wait:2026-07-20",
            "scheduled:2026-07-19",
            f"depends:{dependency}",
            "--",
            "Review project:danger +surprise as one description",
        ],
        [uuid, "annotate", "Waiting for supplier confirmation"],
    ]
    assert result == {"sync": False}


def test_task_creation_places_description_after_terminator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_taskboard()
    board_module = loaded_module("taskboard_board")
    runtime = loaded_module("taskboard_runtime")
    service = loaded_module("taskboard_service")
    description = "Ship project:danger +surprise as one description"
    commands: list[list[str]] = []
    monkeypatch.setattr(runtime, "sync_tasks", lambda allow_failure: None)
    monkeypatch.setattr(
        runtime,
        "run_task",
        lambda args: (
            commands.append(args)
            or SimpleNamespace(stdout="Created task 12\n", stderr="", returncode=0)
        ),
    )
    monkeypatch.setattr(board_module, "build_board", lambda sync: {"sync": sync})

    service.add_task(
        {
            "description": description,
            "project": "release",
            "tags": ["review"],
            "column": "ready",
        }
    )

    assert commands == [["add", "project:release", "+review", "+next", "--", description]]


def test_inline_dependency_creation_places_description_after_terminator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_taskboard()
    board_module = loaded_module("taskboard_board")
    runtime = loaded_module("taskboard_runtime")
    service = loaded_module("taskboard_service")
    parent_uuid = "11111111-1111-4111-8111-111111111111"
    created_uuid = "77777777-7777-4777-8777-777777777777"
    description = "Obtain project:danger +approval as one description"
    commands: list[list[str]] = []

    def run_task(args, allow_failure=False):
        commands.append(args)
        if args[0] == "add":
            return SimpleNamespace(stdout="Created task 12\n", stderr="", returncode=0)
        if args[0] == "_get":
            return SimpleNamespace(stdout=f"{created_uuid}\n", stderr="", returncode=0)
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(runtime, "sync_tasks", lambda allow_failure: None)
    monkeypatch.setattr(runtime, "export_tasks", fixture_tasks)
    monkeypatch.setattr(runtime, "run_task", run_task)
    monkeypatch.setattr(board_module, "build_board", lambda sync: {"sync": sync})

    service.create_dependency(
        parent_uuid,
        {"description": description, "expected_modified": "20260712T070000Z"},
    )

    assert commands[0] == ["add", "project:planning", "--", description]
    assert commands[1] == ["_get", "12.uuid"]
    assert commands[2] == [parent_uuid, "modify", f"depends:{created_uuid}"]


def test_update_task_rejects_indirect_dependency_cycle(monkeypatch: pytest.MonkeyPatch) -> None:
    load_taskboard()
    runtime = loaded_module("taskboard_runtime")
    service = loaded_module("taskboard_service")
    uuid = "11111111-1111-4111-8111-111111111111"
    dependency = "44444444-4444-4444-8444-444444444444"
    monkeypatch.setattr(runtime, "sync_tasks", lambda allow_failure: None)
    monkeypatch.setattr(runtime, "export_tasks", fixture_tasks)

    with pytest.raises(ValueError, match="dependency cycle detected"):
        service.update_task(
            uuid,
            {"depends": [dependency], "expected_modified": "20260712T070000Z"},
        )

    with pytest.raises(ValueError, match="a task cannot depend on itself"):
        service.update_task(
            uuid,
            {"depends": [uuid], "expected_modified": "20260712T070000Z"},
        )


def test_update_task_preserves_unknown_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    load_taskboard()
    board_module = loaded_module("taskboard_board")
    runtime = loaded_module("taskboard_runtime")
    service = loaded_module("taskboard_service")
    uuid = "11111111-1111-4111-8111-111111111111"
    dependency = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    commands: list[list[str]] = []
    monkeypatch.setattr(runtime, "sync_tasks", lambda allow_failure: None)
    monkeypatch.setattr(runtime, "export_tasks", fixture_tasks)
    monkeypatch.setattr(runtime, "run_task", lambda args: commands.append(args))
    monkeypatch.setattr(board_module, "build_board", lambda sync: {"sync": sync})

    service.update_task(
        uuid,
        {"depends": [dependency], "expected_modified": "20260712T070000Z"},
    )

    assert commands == [[uuid, "modify", f"depends:{dependency}"]]


def test_delete_task_verifies_and_deletes_exact_uuid(monkeypatch: pytest.MonkeyPatch) -> None:
    load_taskboard()
    board_module = loaded_module("taskboard_board")
    runtime = loaded_module("taskboard_runtime")
    service = loaded_module("taskboard_service")
    uuid = "22222222-2222-4222-8222-222222222222"
    commands: list[list[str]] = []
    sync_calls: list[bool] = []
    monkeypatch.setattr(
        runtime, "sync_tasks", lambda allow_failure: sync_calls.append(allow_failure)
    )
    monkeypatch.setattr(runtime, "export_tasks", fixture_tasks)
    monkeypatch.setattr(runtime, "run_task", lambda args: commands.append(args))
    monkeypatch.setattr(board_module, "build_board", lambda sync: {"sync": sync})

    result = service.delete_task(uuid, {"expected_modified": "20260712T071000Z"})

    assert commands == [[uuid, "delete"]]
    assert sync_calls == [True, True]
    assert result == {"sync": False}


def test_bulk_update_rejects_stale_batch_before_mutating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_taskboard()
    runtime = loaded_module("taskboard_runtime")
    service = loaded_module("taskboard_service")
    commands: list[list[str]] = []
    monkeypatch.setattr(runtime, "sync_tasks", lambda allow_failure: None)
    monkeypatch.setattr(runtime, "export_tasks", fixture_tasks)
    monkeypatch.setattr(runtime, "run_task", lambda args: commands.append(args))

    with pytest.raises(service.TaskConflictError, match="changed in another Taskwarrior client"):
        service.bulk_update(
            {
                "tasks": [
                    {
                        "uuid": "11111111-1111-4111-8111-111111111111",
                        "expected_modified": "20260712T070000Z",
                    },
                    {
                        "uuid": "22222222-2222-4222-8222-222222222222",
                        "expected_modified": "20260712T000000Z",
                    },
                ],
                "changes": {"priority": "H"},
            }
        )

    assert commands == []


def test_delete_route_returns_board(monkeypatch: pytest.MonkeyPatch) -> None:
    taskboard = load_taskboard()
    uuid = "22222222-2222-4222-8222-222222222222"
    expected = {"columns": [], "generated_at": "2026-07-12T12:00:00+00:00"}
    deleted: list[tuple[str, dict[str, str]]] = []
    monkeypatch.setenv("TASKBOARD_ALLOW_NO_AUTH", "1")
    monkeypatch.setattr(
        taskboard,
        "delete_task",
        lambda value, payload: deleted.append((value, payload)) or expected,
    )

    handler = object.__new__(taskboard.TaskboardHandler)
    handler.command = "DELETE"
    handler.path = f"/api/tasks/{uuid}"
    body = json.dumps({"expected_modified": "20260712T071000Z"}).encode()
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = io.BytesIO(body)
    handler.wfile = io.BytesIO()
    statuses: list[int] = []
    handler.send_response = lambda status: statuses.append(status)
    handler.send_header = lambda name, value: None
    handler.end_headers = lambda: None

    taskboard.TaskboardHandler.do_DELETE(handler)

    assert deleted == [(uuid, {"expected_modified": "20260712T071000Z"})]
    assert statuses == [200]
    assert json.loads(handler.wfile.getvalue()) == expected


@pytest.mark.parametrize("error", [BrokenPipeError(), ConnectionResetError()])
def test_safe_dispatch_ignores_client_disconnect(error: OSError) -> None:
    taskboard = load_taskboard()

    class DisconnectedHandler:
        def dispatch(self) -> None:
            raise error

    taskboard.TaskboardHandler.safe_dispatch(DisconnectedHandler())
