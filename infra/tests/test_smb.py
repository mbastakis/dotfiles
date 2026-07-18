from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from homeserver_iac.models.common import OperationKind
from homeserver_iac.runtime import OperationalError
from homeserver_iac.smb import apply_smb, load_smb_desired, plan_smb
from homeserver_iac.truenas import MidcltClient

FIXTURE = Path(__file__).parent / "fixtures/smb/current.json"


def current_state() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(FIXTURE.read_text()))


class FakeMidcltClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def call(self, method: str, *arguments: Any, job: bool = False) -> None:
        assert not job
        self.calls.append((method, arguments))


def test_smb_plan_ignores_runtime_owned_fields() -> None:
    current = current_state()

    plan = plan_smb(load_smb_desired(), current["service"], current["shares"])

    assert [(operation.kind, operation.resource_id) for operation in plan.operations] == [
        (OperationKind.UNCHANGED, "apple-originals-migration"),
        (OperationKind.UNCHANGED, "smb-service"),
    ]


def test_smb_plan_reports_only_managed_drift() -> None:
    current = current_state()
    current["shares"][0]["browsable"] = True

    plan = plan_smb(load_smb_desired(), current["service"], current["shares"])

    update = next(
        operation
        for operation in plan.operations
        if operation.resource_id == "apple-originals-migration"
    )
    assert update.kind is OperationKind.UPDATE
    assert update.changed_fields == ("browsable",)


def test_smb_apply_enables_service_and_creates_private_share() -> None:
    client = FakeMidcltClient()
    service = {"id": 4, "service": "cifs", "enable": False, "state": "STOPPED"}

    apply_smb(
        load_smb_desired(),
        service,
        [],
        cast(MidcltClient, client),
    )

    assert [method for method, _ in client.calls] == [
        "service.update",
        "sharing.smb.create",
        "service.start",
    ]
    payload = client.calls[1][1][0]
    assert payload["guestok"] is False
    assert payload["browsable"] is False
    assert "valid users = mbastakis" in payload["auxsmbconf"]
    assert "force user = apps" in payload["auxsmbconf"]


def test_smb_duplicate_casefolded_managed_name_fails_before_mutation() -> None:
    current = current_state()
    duplicate = {**current["shares"][0], "id": 99}
    duplicate["name"] = str(duplicate["name"]).swapcase()
    current["shares"].append(duplicate)
    desired = load_smb_desired()
    client = FakeMidcltClient()

    with pytest.raises(OperationalError, match=r"multiple SMB shares.*name"):
        plan_smb(desired, current["service"], current["shares"])
    with pytest.raises(OperationalError, match=r"multiple SMB shares.*name"):
        apply_smb(desired, current["service"], current["shares"], cast(MidcltClient, client))

    assert client.calls == []
