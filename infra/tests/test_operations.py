from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from homeserver_iac.models.common import (
    ExitCode,
    OperationKind,
    SecretRef,
    compare_resources,
    redact_secret_values,
    serialize_plan,
)

FIXTURES = Path(__file__).parent / "fixtures/comparison"


def test_comparison_uses_stable_ids_and_common_operation_order() -> None:
    desired = json.loads((FIXTURES / "desired.json").read_text())
    current = json.loads((FIXTURES / "current.json").read_text())

    plan = compare_resources(
        scope="truenas.catalog_apps",
        desired=desired,
        current=current,
        explicit_delete_ids=("delete-me",),
        warnings=(("warning-id", "Review runtime-owned fields"),),
    )

    assert [(operation.kind, operation.resource_id) for operation in plan.operations] == [
        (OperationKind.CREATE, "create-me"),
        (OperationKind.UPDATE, "update-me"),
        (OperationKind.DELETE, "delete-me"),
        (OperationKind.STALE, "stale-me"),
        (OperationKind.WARNING, "warning-id"),
        (OperationKind.UNCHANGED, "same"),
    ]
    assert plan.exit_code is ExitCode.DRIFT


def test_plan_serialization_never_contains_compared_secret_values() -> None:
    desired = json.loads((FIXTURES / "desired.json").read_text())
    current = json.loads((FIXTURES / "current.json").read_text())
    serialized = serialize_plan(
        compare_resources(scope="truenas.catalog_apps", desired=desired, current=current)
    )

    assert "desired-secret" not in serialized
    assert "current-secret" not in serialized
    assert '"changed_fields"' in serialized


def test_secret_ref_cannot_hold_secret_material() -> None:
    with pytest.raises(ValidationError):
        SecretRef.model_validate({"alias": "backrest_password", "value": "do-not-print"})


def test_redaction_covers_nested_runtime_credentials() -> None:
    redacted = redact_secret_values(
        {
            "username": "admin",
            "password": "secret-one",
            "nested": [{"AWS_SECRET_ACCESS_KEY": "secret-two"}],
        }
    )

    assert redacted == {
        "username": "admin",
        "password": "<redacted>",
        "nested": [{"AWS_SECRET_ACCESS_KEY": "<redacted>"}],
    }


def test_no_drift_uses_success_exit_code() -> None:
    plan = compare_resources(
        scope="sync.syncthing",
        desired={"folder": {"enabled": True}},
        current={"folder": {"enabled": True}},
    )
    assert plan.exit_code is ExitCode.VALID
