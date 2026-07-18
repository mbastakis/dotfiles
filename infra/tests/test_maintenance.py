from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from homeserver_iac.maintenance import (
    apply_maintenance,
    load_maintenance_desired,
    plan_maintenance,
)
from homeserver_iac.models.common import OperationKind
from homeserver_iac.runtime import OperationalError
from homeserver_iac.truenas import MidcltClient

FIXTURES = Path(__file__).parent / "fixtures/maintenance"


def current_state() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((FIXTURES / "current.json").read_text()))


class FakeMidcltClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def call(self, method: str, *arguments: Any, job: bool = False) -> None:
        assert not job
        self.calls.append((method, arguments))


def test_maintenance_policy_separates_disk_intensive_work() -> None:
    desired = load_maintenance_desired()
    tests = {test.type: test for test in desired.smart_tests}

    assert desired.scrub.threshold == 35
    assert desired.scrub.schedule.dow == "7"
    assert desired.smartd.enabled is True
    assert desired.smartd.running is True
    assert tests["SHORT"].schedule.dow == "2"
    assert tests["LONG"].schedule.dow == "5"
    assert tests["LONG"].schedule.dom == "1-7"


def test_maintenance_plan_ignores_runtime_fields() -> None:
    state = current_state()

    plan = plan_maintenance(
        load_maintenance_desired(),
        state["pools"],
        state["scrubs"],
        state["services"],
        state["smart_tests"],
    )

    assert all(operation.kind is OperationKind.UNCHANGED for operation in plan.operations)


def test_maintenance_plan_reports_missing_smart_tasks_and_scrub_drift() -> None:
    state = current_state()
    state["scrubs"][0]["schedule"]["hour"] = "00"
    state["smart_tests"] = []

    plan = plan_maintenance(
        load_maintenance_desired(),
        state["pools"],
        state["scrubs"],
        state["services"],
        state["smart_tests"],
    )

    assert (OperationKind.UPDATE, "pool-4tb-scrub") in [
        (operation.kind, operation.resource_id) for operation in plan.operations
    ]
    assert {
        operation.resource_id
        for operation in plan.operations
        if operation.kind is OperationKind.CREATE
    } == {"all-disks-short", "all-disks-long"}


def test_maintenance_apply_refuses_degraded_pool() -> None:
    state = current_state()
    state["pools"][0]["status"] = "DEGRADED"
    client = FakeMidcltClient()

    with pytest.raises(OperationalError, match="pool is not ONLINE"):
        apply_maintenance(
            load_maintenance_desired(),
            state["pools"],
            state["scrubs"],
            state["services"],
            state["smart_tests"],
            cast(MidcltClient, client),
        )

    assert client.calls == []


def test_maintenance_apply_updates_scrub_and_creates_smart_tasks() -> None:
    state = current_state()
    state["scrubs"][0]["schedule"]["hour"] = "00"
    state["smart_tests"] = []
    client = FakeMidcltClient()

    apply_maintenance(
        load_maintenance_desired(),
        state["pools"],
        state["scrubs"],
        state["services"],
        state["smart_tests"],
        cast(MidcltClient, client),
    )

    assert [
        (method, arguments[0] if method == "pool.scrub.update" else None)
        for method, arguments in client.calls
    ] == [
        ("smart.test.create", None),
        ("smart.test.create", None),
        ("pool.scrub.update", 1),
    ]


def test_maintenance_plan_reports_stopped_smartd() -> None:
    state = current_state()
    state["services"][0]["state"] = "STOPPED"

    plan = plan_maintenance(
        load_maintenance_desired(),
        state["pools"],
        state["scrubs"],
        state["services"],
        state["smart_tests"],
    )

    operation = next(
        operation for operation in plan.operations if operation.resource_id == "smartd-service"
    )
    assert operation.kind is OperationKind.UPDATE
    assert operation.changed_fields == ("running",)


def test_maintenance_apply_enables_and_starts_smartd() -> None:
    state = current_state()
    state["services"][0].update(enable=False, state="STOPPED")
    client = FakeMidcltClient()

    apply_maintenance(
        load_maintenance_desired(),
        state["pools"],
        state["scrubs"],
        state["services"],
        state["smart_tests"],
        cast(MidcltClient, client),
    )

    assert client.calls == [
        ("service.update", ("smartd", {"enable": True})),
        ("service.start", ("smartd", {"silent": False})),
    ]
