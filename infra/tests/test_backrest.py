from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from homeserver_iac.backrest import (
    BackrestClient,
    apply_backrest,
    build_backrest_config,
    load_backrest_desired,
    plan_backrest,
)
from homeserver_iac.models.common import OperationKind, serialize_plan

FIXTURES = Path(__file__).parent / "fixtures/backrest"


def current_config() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((FIXTURES / "current.json").read_text()))


class FakeBackrestClient:
    def __init__(self, current: dict[str, Any]) -> None:
        self.current = current
        self.added: list[dict[str, Any]] = []
        self.updated: list[dict[str, Any]] = []

    def add_repo(self, repository: dict[str, Any]) -> None:
        self.added.append(repository)
        runtime_repository = {**repository, "guid": "runtime-guid"}
        runtime_repository.pop("password", None)
        self.current.setdefault("repos", []).append(runtime_repository)

    def get_config(self) -> dict[str, Any]:
        return self.current

    def set_config(self, config: dict[str, Any]) -> None:
        self.updated.append(config)
        self.current = config


def test_backrest_plan_ignores_runtime_repository_guid() -> None:
    plan = plan_backrest(load_backrest_desired(), current_config())

    assert all(operation.kind is OperationKind.UNCHANGED for operation in plan.operations)


def test_audiobookshelf_backup_policy_is_deliberately_low_frequency() -> None:
    desired = load_backrest_desired()
    plans = {plan.id: plan for plan in desired.plans}

    app_state = plans["homeserver-audiobookshelf-weekly"]
    books = plans["homeserver-books-monthly"]

    assert app_state.paths == ("/source/audiobookshelf-backups",)
    assert app_state.schedule.cron == "30 3 * * 0"
    assert app_state.retention.policy_time_bucketed.weekly == 8
    assert books.paths == ("/source/books",)
    assert books.schedule.cron == "30 4 1 * *"
    assert books.retention.policy_time_bucketed.monthly == 6


def test_photo_backups_follow_native_immich_database_dump() -> None:
    desired = load_backrest_desired()
    plans = {plan.id: plan for plan in desired.plans}

    immich = plans["homeserver-immich-daily"]
    apple_originals = plans["homeserver-apple-originals-daily"]

    assert immich.paths == ("/source/immich",)
    assert immich.schedule.cron == "30 2 * * *"
    assert immich.retention.policy_time_bucketed.daily == 14
    assert apple_originals.paths == ("/source/apple-originals",)
    assert apple_originals.schedule.cron == "0 3 * * *"
    assert apple_originals.skip_if_unchanged is True


def test_backrest_repository_caps_uploads_below_half_the_wan_capacity() -> None:
    desired = load_backrest_desired()

    assert desired.repository.flags == ("--limit-upload=6000",)


def test_backrest_plan_reports_missing_upload_limit() -> None:
    current = current_config()
    current["repos"][0].pop("flags")

    plan = plan_backrest(load_backrest_desired(), current)
    repository = next(
        operation for operation in plan.operations if operation.resource_id == "homeserver-s3"
    )

    assert repository.kind is OperationKind.UPDATE
    assert repository.changed_fields == ("flags",)


def test_backrest_plan_reports_only_managed_fields_and_secret_aliases() -> None:
    current = current_config()
    current["repos"][0]["uri"] = "s3:wrong"

    plan = plan_backrest(load_backrest_desired(), current)
    repository = next(
        operation for operation in plan.operations if operation.resource_id == "homeserver-s3"
    )
    serialized = serialize_plan(plan)

    assert repository.kind is OperationKind.UPDATE
    assert repository.changed_fields == ("uri",)
    assert {ref.alias for ref in repository.secret_refs} == {
        "backrest_restic_repo_password",
        "backrest_aws_access_key_id",
        "backrest_aws_secret_access_key",
    }
    assert "runtime-guid" not in serialized


def test_backrest_only_deletes_explicitly_retired_plans() -> None:
    current = current_config()
    current["plans"].extend(
        [
            {"id": "homeserver-files-obsidian-weekly", "repo": "homeserver-s3"},
            {"id": "operator-plan", "repo": "homeserver-s3"},
        ]
    )

    plan = plan_backrest(load_backrest_desired(), current)

    assert (OperationKind.DELETE, "homeserver-files-obsidian-weekly") in [
        (operation.kind, operation.resource_id) for operation in plan.operations
    ]
    assert (OperationKind.UNCHANGED, "homeserver-immich-daily") in [
        (operation.kind, operation.resource_id) for operation in plan.operations
    ]
    assert (OperationKind.WARNING, "operator-plan") in [
        (operation.kind, operation.resource_id) for operation in plan.operations
    ]


def test_backrest_config_merge_preserves_runtime_and_unmanaged_objects() -> None:
    current = current_config()
    current["auth"] = {"users": ["runtime-owned"]}
    current["plans"].append({"id": "operator-plan", "repo": "homeserver-s3"})

    updated = build_backrest_config(load_backrest_desired(), current)

    assert updated["auth"] == {"users": ["runtime-owned"]}
    assert updated["repos"][0]["guid"] == current["repos"][0]["guid"]
    assert any(plan["id"] == "operator-plan" for plan in updated["plans"])


def test_backrest_apply_is_noop_when_managed_policy_is_current() -> None:
    current = current_config()
    client = FakeBackrestClient(current)

    apply_backrest(load_backrest_desired(), current, cast(BackrestClient, client))

    assert client.added == []
    assert client.updated == []
