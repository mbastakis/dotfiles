from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from homeserver_iac.models.common import OperationKind
from homeserver_iac.syncthing import (
    SyncthingClient,
    SyncthingIgnoreFiles,
    apply_syncthing,
    load_syncthing_desired,
    plan_syncthing,
)

FIXTURES = Path(__file__).parent / "fixtures/syncthing"
IGNORE = ".obsidian\n.git\n"


def state(host: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((FIXTURES / f"{host}.json").read_text()))


class FakeSyncthingClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def post(self, path: str, payload: dict[str, Any]) -> None:
        self.calls.append(("POST", path, payload))

    def put(self, path: str, payload: dict[str, Any]) -> None:
        self.calls.append(("PUT", path, payload))


class FakeIgnoreFiles:
    def __init__(self) -> None:
        self.writes: list[tuple[str, str]] = []

    def desired_content(self) -> str:
        return IGNORE

    def write(self, folder: Any, content: str) -> None:
        self.writes.append((folder.id, content))


def test_syncthing_mac_plan_reports_corrected_relay_option_only() -> None:
    plan = plan_syncthing(load_syncthing_desired(), "mac", state("mac"), IGNORE)

    drift = [operation for operation in plan.operations if operation.kind is OperationKind.UPDATE]
    assert [(operation.resource_id, operation.changed_fields) for operation in drift] == [
        ("options", ("relaysEnabled",))
    ]


def test_syncthing_truenas_preserves_unmanaged_device_and_folder_binding() -> None:
    plan = plan_syncthing(load_syncthing_desired(), "truenas", state("truenas"), IGNORE)

    assert (OperationKind.UPDATE, "options") in [
        (operation.kind, operation.resource_id) for operation in plan.operations
    ]
    assert (OperationKind.UPDATE, "ignore-obsidian-michail") in [
        (operation.kind, operation.resource_id) for operation in plan.operations
    ]
    assert (OperationKind.UNCHANGED, "obsidian-michail") in [
        (operation.kind, operation.resource_id) for operation in plan.operations
    ]
    assert any(operation.kind is OperationKind.WARNING for operation in plan.operations)
    assert all(operation.kind is not OperationKind.DELETE for operation in plan.operations)


def test_syncthing_apply_updates_only_drifted_resources() -> None:
    client = FakeSyncthingClient()
    ignore_files = FakeIgnoreFiles()

    apply_syncthing(
        load_syncthing_desired(),
        "truenas",
        state("truenas"),
        cast(SyncthingClient, client),
        cast(SyncthingIgnoreFiles, ignore_files),
    )

    assert [(method, path) for method, path, _ in client.calls] == [("PUT", "/rest/config/options")]
    assert ignore_files.writes == [("obsidian-michail", IGNORE)]


def test_syncthing_folder_update_preserves_unmanaged_device_binding() -> None:
    current = state("truenas")
    current["folders"][0]["label"] = "Wrong label"
    client = FakeSyncthingClient()
    ignore_files = FakeIgnoreFiles()

    apply_syncthing(
        load_syncthing_desired(),
        "truenas",
        current,
        cast(SyncthingClient, client),
        cast(SyncthingIgnoreFiles, ignore_files),
    )

    folder_payload = next(
        payload for _, path, payload in client.calls if path.endswith("/obsidian-michail")
    )
    device_ids = {device["deviceID"] for device in folder_payload["devices"]}
    assert "R43WCNY-3RFNOKV-OSKFPR2-4RSPBGH-WMMVP5J-LUU3UKH-ULVVGOF-ZOOPEA3" in device_ids


def test_syncthing_ignore_rule_order_is_semantic() -> None:
    plan = plan_syncthing(
        load_syncthing_desired(),
        "truenas",
        state("truenas"),
        ".git\n.obsidian\n",
    )

    assert (OperationKind.UPDATE, "ignore-obsidian-michail") in [
        (operation.kind, operation.resource_id) for operation in plan.operations
    ]
