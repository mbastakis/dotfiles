from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from homeserver_iac.api_keys import (
    ApiKeyPublication,
    apply_api_key_publication,
    plan_api_key_publication,
)
from homeserver_iac.models.common import OperationKind, serialize_plan
from homeserver_iac.runtime import OperationalError
from homeserver_iac.secrets import BwsClient, load_secret_metadata
from homeserver_iac.truenas import MidcltClient

FIXTURE = Path(__file__).parent / "fixtures/api-keys/current.json"


def publication() -> ApiKeyPublication:
    return ApiKeyPublication(
        name="homepage-dashboard",
        username="mbastakis",
        secret_alias="truenas_api_key",
    )


class FakeMidcltClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def call(self, method: str, *arguments: Any, job: bool = False) -> Any:
        assert not job
        self.calls.append((method, arguments))
        if method == "api_key.create":
            return {"id": 9, "key": "new-api-key-secret"}
        return True


class FakeBwsClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.created: list[tuple[str, str, str]] = []

    def create_secret(self, key: str, value: str, project_id: str, *, note: str) -> str:
        assert note
        if self.fail:
            raise OperationalError("fixture failure")
        self.created.append((key, value, project_id))
        return "created-id"


def test_existing_api_key_and_bws_secret_are_noop_and_value_free() -> None:
    current = json.loads(FIXTURE.read_text())

    plan = plan_api_key_publication(
        publication(),
        load_secret_metadata(),
        current["api_keys"],
        current["bws_ids_by_key"],
    )

    assert all(operation.kind is OperationKind.UNCHANGED for operation in plan.operations)
    assert "35e303f1" not in serialize_plan(plan)


def test_publication_creates_both_sides_only_when_both_are_absent() -> None:
    truenas = FakeMidcltClient()
    bws = FakeBwsClient()

    apply_api_key_publication(
        publication(),
        load_secret_metadata(),
        [],
        {},
        cast(MidcltClient, truenas),
        cast(BwsClient, bws),
    )

    assert truenas.calls[0][0] == "api_key.create"
    assert bws.created[0][0] == "homeserver/truenas/api-keys/homepage"


def test_publication_rolls_back_just_created_key_when_bws_fails() -> None:
    truenas = FakeMidcltClient()

    with pytest.raises(OperationalError, match="was removed"):
        apply_api_key_publication(
            publication(),
            load_secret_metadata(),
            [],
            {},
            cast(MidcltClient, truenas),
            cast(BwsClient, FakeBwsClient(fail=True)),
        )

    assert [method for method, _ in truenas.calls] == ["api_key.create", "api_key.delete"]


def test_partial_publication_requires_operator_rotation() -> None:
    with pytest.raises(OperationalError, match="requires operator rotation"):
        apply_api_key_publication(
            publication(),
            load_secret_metadata(),
            [{"id": 1, "name": "homepage-dashboard", "username": "mbastakis"}],
            {},
            cast(MidcltClient, FakeMidcltClient()),
            cast(BwsClient, FakeBwsClient()),
        )
