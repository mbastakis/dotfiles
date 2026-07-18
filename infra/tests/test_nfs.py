from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from homeserver_iac.models.common import OperationKind
from homeserver_iac.nfs import apply_nfs, load_nfs_desired, plan_nfs
from homeserver_iac.runtime import OperationalError
from homeserver_iac.truenas import MidcltClient

FIXTURE = Path(__file__).parent / "fixtures/nfs/current.json"


def current_state() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(FIXTURE.read_text()))


class FakeMidcltClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def call(self, method: str, *arguments: Any, job: bool = False) -> None:
        assert not job
        self.calls.append((method, arguments))


def test_nfs_plan_ignores_runtime_owned_fields() -> None:
    current = current_state()

    plan = plan_nfs(load_nfs_desired(), current["service"], current["shares"])

    assert [(operation.kind, operation.resource_id) for operation in plan.operations] == [
        (OperationKind.UNCHANGED, "immich-media"),
        (OperationKind.UNCHANGED, "nfs-service"),
    ]


def test_nfs_plan_reports_only_managed_drift() -> None:
    current = current_state()
    current["shares"][0]["hosts"] = ["192.168.1.20"]

    plan = plan_nfs(load_nfs_desired(), current["service"], current["shares"])

    update = next(
        operation for operation in plan.operations if operation.resource_id == "immich-media"
    )
    assert update.kind is OperationKind.UPDATE
    assert update.changed_fields == ("hosts",)


def test_nfs_apply_enables_service_and_creates_missing_share() -> None:
    client = FakeMidcltClient()
    service = {"id": 9, "service": "nfs", "enable": False, "state": "STOPPED"}

    apply_nfs(
        load_nfs_desired(),
        service,
        [],
        cast(MidcltClient, client),
    )

    assert [method for method, _ in client.calls] == [
        "service.update",
        "service.start",
        "sharing.nfs.create",
    ]
    assert client.calls[2][1][0]["hosts"] == ["192.168.1.19"]
    assert client.calls[2][1][0]["mapall_user"] == "apps"


def test_nfs_duplicate_managed_path_fails_plan_and_apply_before_mutation() -> None:
    current = current_state()
    current["shares"].append({**current["shares"][0], "id": 99})
    desired = load_nfs_desired()
    client = FakeMidcltClient()

    with pytest.raises(OperationalError, match=r"multiple NFS shares.*path"):
        plan_nfs(desired, current["service"], current["shares"])
    with pytest.raises(OperationalError, match=r"multiple NFS shares.*path"):
        apply_nfs(desired, current["service"], current["shares"], cast(MidcltClient, client))

    assert client.calls == []
