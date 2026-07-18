from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

StableId = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=128,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    ),
]
OwnershipScope = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=128,
        pattern=r"^[a-z][a-z0-9_-]*(?:\.[a-z0-9][a-z0-9_-]*)+$",
    ),
]
EnvironmentName = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z][A-Za-z0-9_]*$"),
]
DottedPath = Annotated[
    str,
    StringConstraints(pattern=r"^[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)*$"),
]
AbsolutePath = Annotated[str, StringConstraints(pattern=r"^/[^\x00]*$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)


class Ownership(StrictModel):
    scope: OwnershipScope
    mode: Literal["bounded"]


class SecretRef(StrictModel):
    """A logical reference only; secret material is deliberately not representable."""

    alias: StableId


class VersionedDesiredState(StrictModel):
    schema_version: Literal[1]
    ownership: Ownership


class VersionedDesiredStateV2(StrictModel):
    schema_version: Literal[2]
    ownership: Ownership


class ExitCode(IntEnum):
    VALID = 0
    DRIFT = 2
    VALIDATION_FAILURE = 3
    OPERATIONAL_FAILURE = 4


class OperationKind(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    UNCHANGED = "unchanged"
    STALE = "stale"
    WARNING = "warning"
    DELETE = "delete"


class Operation(StrictModel):
    kind: OperationKind
    scope: OwnershipScope
    resource_id: StableId
    summary: str = Field(min_length=1, max_length=500)
    changed_fields: tuple[str, ...] = ()
    secret_refs: tuple[SecretRef, ...] = ()


class Plan(StrictModel):
    operations: tuple[Operation, ...]

    @property
    def exit_code(self) -> ExitCode:
        drift_kinds = {
            OperationKind.CREATE,
            OperationKind.UPDATE,
            OperationKind.STALE,
            OperationKind.DELETE,
        }
        if any(operation.kind in drift_kinds for operation in self.operations):
            return ExitCode.DRIFT
        return ExitCode.VALID


_OPERATION_ORDER = {
    OperationKind.CREATE: 0,
    OperationKind.UPDATE: 1,
    OperationKind.DELETE: 2,
    OperationKind.STALE: 3,
    OperationKind.WARNING: 4,
    OperationKind.UNCHANGED: 5,
}


def order_operations(operations: Iterable[Operation]) -> tuple[Operation, ...]:
    return tuple(
        sorted(
            operations,
            key=lambda operation: (
                _OPERATION_ORDER[operation.kind],
                operation.scope,
                operation.resource_id,
            ),
        )
    )


def compare_resources(
    *,
    scope: OwnershipScope,
    desired: Mapping[str, Mapping[str, Any]],
    current: Mapping[str, Mapping[str, Any]],
    explicit_delete_ids: Iterable[str] = (),
    warnings: Iterable[tuple[str, str]] = (),
) -> Plan:
    """Compare stable IDs without ever carrying resource values into the plan."""

    operations: list[Operation] = []
    delete_ids = set(explicit_delete_ids)

    for resource_id in sorted(desired):
        if resource_id not in current:
            operations.append(
                Operation(
                    kind=OperationKind.CREATE,
                    scope=scope,
                    resource_id=resource_id,
                    summary="Resource is declared but absent",
                )
            )
            continue

        desired_value = desired[resource_id]
        current_value = current[resource_id]
        changed_fields = tuple(
            sorted(
                key
                for key in desired_value.keys() | current_value.keys()
                if desired_value.get(key) != current_value.get(key)
            )
        )
        kind = OperationKind.UPDATE if changed_fields else OperationKind.UNCHANGED
        summary = "Resource differs from desired state" if changed_fields else "Resource is current"
        operations.append(
            Operation(
                kind=kind,
                scope=scope,
                resource_id=resource_id,
                summary=summary,
                changed_fields=changed_fields,
            )
        )

    for resource_id in sorted(delete_ids & current.keys()):
        operations.append(
            Operation(
                kind=OperationKind.DELETE,
                scope=scope,
                resource_id=resource_id,
                summary="Resource is explicitly declared for deletion",
            )
        )

    stale_ids = current.keys() - desired.keys() - delete_ids
    for resource_id in sorted(stale_ids):
        operations.append(
            Operation(
                kind=OperationKind.STALE,
                scope=scope,
                resource_id=resource_id,
                summary="Resource is inside the ownership scope but is not declared",
            )
        )

    for resource_id, summary in warnings:
        operations.append(
            Operation(
                kind=OperationKind.WARNING,
                scope=scope,
                resource_id=resource_id,
                summary=summary,
            )
        )

    return Plan(operations=order_operations(operations))


_SENSITIVE_KEY_SUFFIXES = (
    "_access_key_id",
    "_api_key",
    "_auth_key",
    "_password",
    "_secret",
    "_secret_access_key",
    "_token",
)
_SENSITIVE_KEYS = {
    "access_key_id",
    "api_key",
    "apikey",
    "auth_key",
    "password",
    "secret",
    "secret_access_key",
    "token",
}


def is_sensitive_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
    return normalized in _SENSITIVE_KEYS or normalized.endswith(_SENSITIVE_KEY_SUFFIXES)


def literal_secret_paths(value: Any, prefix: tuple[str, ...] = ()) -> tuple[str, ...]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_prefix = (*prefix, key_text)
            if is_sensitive_key(key_text) and child not in (None, "", [], {}):
                paths.append(".".join(child_prefix))
            else:
                paths.extend(literal_secret_paths(child, child_prefix))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(literal_secret_paths(child, (*prefix, str(index))))
    return tuple(paths)


def redact_secret_values(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): "<redacted>" if is_sensitive_key(str(key)) else redact_secret_values(child)
            for key, child in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_secret_values(child) for child in value]
    return value


def serialize_plan(plan: Plan) -> str:
    redacted = redact_secret_values(plan.model_dump(mode="json"))
    return json.dumps(redacted, indent=2, sort_keys=True) + "\n"
