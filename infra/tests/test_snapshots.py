from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from homeserver_iac.models.common import OperationKind
from homeserver_iac.runtime import OperationalError
from homeserver_iac.snapshots import apply_snapshots, load_snapshot_desired, plan_snapshots
from homeserver_iac.truenas import MidcltClient

FIXTURES = Path(__file__).parent / "fixtures/snapshots"


def current_tasks() -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], json.loads((FIXTURES / "current.json").read_text()))


class FakeMidcltClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def call(self, method: str, *arguments: Any, job: bool = False) -> None:
        assert not job
        self.calls.append((method, arguments))


def test_snapshot_plan_ignores_runtime_owned_fields_from_live_fixture() -> None:
    plan = plan_snapshots(load_snapshot_desired(), current_tasks())

    assert [(operation.kind, operation.resource_id) for operation in plan.operations] == [
        (OperationKind.UNCHANGED, "daily"),
        (OperationKind.UNCHANGED, "hourly"),
        (OperationKind.UNCHANGED, "weekly"),
    ]


def test_snapshot_plan_reports_managed_field_drift_only() -> None:
    current = current_tasks()
    current[0]["lifetime_value"] = 12

    plan = plan_snapshots(load_snapshot_desired(), current)

    update = next(
        operation for operation in plan.operations if operation.kind is OperationKind.UPDATE
    )
    assert update.resource_id == "hourly"
    assert update.changed_fields == ("lifetime_value",)


def test_snapshot_plan_matches_schema_within_the_desired_dataset() -> None:
    photo_desired = load_snapshot_desired(Path("infra/truenas/snapshots/photo-snapshot-tasks.yaml"))

    plan = plan_snapshots(photo_desired, current_tasks())

    assert [(operation.kind, operation.resource_id) for operation in plan.operations] == [
        (OperationKind.CREATE, "daily"),
        (OperationKind.CREATE, "hourly"),
        (OperationKind.CREATE, "weekly"),
    ]


def test_audiobookshelf_snapshot_policies_match_data_lifecycles() -> None:
    app_state = load_snapshot_desired(
        Path("infra/truenas/snapshots/audiobookshelf-snapshot-tasks.yaml")
    )
    books = load_snapshot_desired(Path("infra/truenas/snapshots/books-snapshot-tasks.yaml"))

    assert app_state.dataset == "pool_4tb/homeserver/apps/audiobookshelf"
    assert [task.id for task in app_state.tasks] == ["weekly", "monthly"]
    assert books.dataset == "pool_4tb/homeserver/data/books"
    assert [task.id for task in books.tasks] == ["monthly"]


def test_snapshot_prune_is_explicit_and_bounded_to_dataset() -> None:
    current = current_tasks()
    current.extend(
        [
            {
                "id": 40,
                "dataset": "pool_4tb/homeserver/data/obsidian",
                "naming_schema": "retired-%Y-%m-%d_%H-%M",
            },
            {
                "id": 41,
                "dataset": "pool_4tb/unmanaged",
                "naming_schema": "unmanaged-%Y-%m-%d_%H-%M",
            },
        ]
    )

    safe_plan = plan_snapshots(load_snapshot_desired(), current)
    prune_plan = plan_snapshots(load_snapshot_desired(), current, prune=True)

    assert (OperationKind.STALE, "snapshot-40") in [
        (operation.kind, operation.resource_id) for operation in safe_plan.operations
    ]
    assert (OperationKind.DELETE, "snapshot-40") in [
        (operation.kind, operation.resource_id) for operation in prune_plan.operations
    ]
    assert all(operation.resource_id != "snapshot-41" for operation in prune_plan.operations)


def test_snapshot_apply_calls_only_create_update_and_explicit_delete() -> None:
    current = current_tasks()
    current[0]["lifetime_value"] = 12
    current.append(
        {
            "id": 40,
            "dataset": "pool_4tb/homeserver/data/obsidian",
            "naming_schema": "retired-%Y-%m-%d_%H-%M",
        }
    )
    client = FakeMidcltClient()

    apply_snapshots(
        load_snapshot_desired(),
        current,
        cast(MidcltClient, client),
        prune=True,
    )

    assert [(method, arguments[0]) for method, arguments in client.calls] == [
        ("pool.snapshottask.update", 1),
        ("pool.snapshottask.delete", 40),
    ]


def test_snapshot_duplicate_dataset_and_schema_fails_before_mutation() -> None:
    current = current_tasks()
    current.append({**current[0], "id": 99})
    desired = load_snapshot_desired()
    client = FakeMidcltClient()

    with pytest.raises(OperationalError, match="multiple periodic snapshot tasks"):
        plan_snapshots(desired, current)
    with pytest.raises(OperationalError, match="multiple periodic snapshot tasks"):
        apply_snapshots(desired, current, cast(MidcltClient, client))

    assert client.calls == []
