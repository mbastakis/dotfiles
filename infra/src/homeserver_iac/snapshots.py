from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from homeserver_iac.models.common import Operation, OperationKind, Plan, order_operations
from homeserver_iac.models.snapshots import SnapshotDesiredState, SnapshotTask
from homeserver_iac.runtime import OperationalError
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.truenas import MidcltClient
from homeserver_iac.validation import load_model

DEFAULT_SNAPSHOT_CONFIG = INFRA_ROOT / "truenas/snapshots/snapshot-tasks.yaml"


def load_snapshot_desired(path: Path = DEFAULT_SNAPSHOT_CONFIG) -> SnapshotDesiredState:
    return load_model(path, SnapshotDesiredState)


def desired_payload(desired: SnapshotDesiredState, task: SnapshotTask) -> dict[str, Any]:
    return {
        "dataset": desired.dataset,
        "recursive": desired.recursive,
        "lifetime_value": task.lifetime_value,
        "lifetime_unit": task.lifetime_unit,
        "naming_schema": task.naming_schema,
        "schedule": task.schedule.model_dump(mode="json"),
    }


def _managed_current(current: Mapping[str, Any]) -> dict[str, Any]:
    schedule = current.get("schedule")
    schedule_mapping = schedule if isinstance(schedule, Mapping) else {}
    return {
        "dataset": current.get("dataset"),
        "recursive": current.get("recursive"),
        "lifetime_value": current.get("lifetime_value"),
        "lifetime_unit": current.get("lifetime_unit"),
        "naming_schema": current.get("naming_schema"),
        "schedule": {
            key: schedule_mapping.get(key) for key in ("minute", "hour", "dom", "month", "dow")
        },
    }


def _changed_fields(desired: Mapping[str, Any], current: Mapping[str, Any]) -> tuple[str, ...]:
    changed: list[str] = []
    for key, value in desired.items():
        current_value = current.get(key)
        if isinstance(value, Mapping) and isinstance(current_value, Mapping):
            changed.extend(
                f"{key}.{child_key}"
                for child_key, child_value in value.items()
                if current_value.get(child_key) != child_value
            )
        elif current_value != value:
            changed.append(key)
    return tuple(sorted(changed))


def _current_by_managed_identity(
    desired: SnapshotDesiredState, current_tasks: Sequence[Mapping[str, Any]]
) -> dict[tuple[str, str], Mapping[str, Any]]:
    managed_identities = {(desired.dataset, task.naming_schema) for task in desired.tasks}
    matches: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for current in current_tasks:
        dataset = current.get("dataset")
        naming_schema = current.get("naming_schema")
        if isinstance(dataset, str) and isinstance(naming_schema, str):
            identity = (dataset, naming_schema)
            if identity in managed_identities:
                matches.setdefault(identity, []).append(current)
    for identity, tasks in matches.items():
        if len(tasks) > 1:
            raise OperationalError(
                "multiple periodic snapshot tasks match managed identity "
                f"dataset={identity[0]!r}, naming_schema={identity[1]!r}"
            )
    return {identity: tasks[0] for identity, tasks in matches.items()}


def plan_snapshots(
    desired: SnapshotDesiredState,
    current_tasks: Sequence[Mapping[str, Any]],
    *,
    prune: bool = False,
) -> Plan:
    current_by_schema = _current_by_managed_identity(desired, current_tasks)
    operations: list[Operation] = []

    desired_schemas = {task.naming_schema for task in desired.tasks}
    for task in desired.tasks:
        current = current_by_schema.get((desired.dataset, task.naming_schema))
        payload = desired_payload(desired, task)
        if current is None:
            operations.append(
                Operation(
                    kind=OperationKind.CREATE,
                    scope=desired.ownership.scope,
                    resource_id=task.id,
                    summary="Periodic snapshot task is absent",
                )
            )
            continue
        changed_fields = _changed_fields(payload, _managed_current(current))
        operations.append(
            Operation(
                kind=OperationKind.UPDATE if changed_fields else OperationKind.UNCHANGED,
                scope=desired.ownership.scope,
                resource_id=task.id,
                summary=(
                    "Periodic snapshot task differs from desired state"
                    if changed_fields
                    else "Periodic snapshot task is current"
                ),
                changed_fields=changed_fields,
            )
        )
    for current in current_tasks:
        if current.get("dataset") != desired.dataset:
            continue
        naming_schema = current.get("naming_schema")
        if naming_schema in desired_schemas:
            continue
        remote_id = str(current.get("id", "unknown"))
        operations.append(
            Operation(
                kind=OperationKind.DELETE if prune else OperationKind.STALE,
                scope=desired.ownership.scope,
                resource_id=f"snapshot-{remote_id}",
                summary=(
                    "Periodic snapshot task will be explicitly pruned"
                    if prune
                    else "Unmanaged periodic snapshot task shares the managed dataset"
                ),
            )
        )
    return Plan(operations=order_operations(operations))


def apply_snapshots(
    desired: SnapshotDesiredState,
    current_tasks: Sequence[Mapping[str, Any]],
    client: MidcltClient,
    *,
    prune: bool = False,
) -> Plan:
    plan = plan_snapshots(desired, current_tasks, prune=prune)
    task_by_id = {task.id: task for task in desired.tasks}
    current_by_schema = _current_by_managed_identity(desired, current_tasks)
    current_by_id = {f"snapshot-{current.get('id')}": current for current in current_tasks}

    for operation in plan.operations:
        if operation.kind is OperationKind.CREATE:
            task = task_by_id[operation.resource_id]
            client.call("pool.snapshottask.create", desired_payload(desired, task))
        elif operation.kind is OperationKind.UPDATE:
            task = task_by_id[operation.resource_id]
            current = current_by_schema[(desired.dataset, task.naming_schema)]
            client.call(
                "pool.snapshottask.update",
                current["id"],
                desired_payload(desired, task),
            )
        elif operation.kind is OperationKind.DELETE:
            client.call("pool.snapshottask.delete", current_by_id[operation.resource_id]["id"])
    return plan
