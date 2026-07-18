from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from homeserver_iac.models.common import Operation, OperationKind, Plan, order_operations
from homeserver_iac.models.maintenance import MaintenanceDesiredState, SmartSelfTest
from homeserver_iac.runtime import OperationalError
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.truenas import MidcltClient
from homeserver_iac.validation import load_model

DEFAULT_MAINTENANCE_CONFIG = INFRA_ROOT / "truenas/maintenance/maintenance.yaml"


def load_maintenance_desired(
    path: Path = DEFAULT_MAINTENANCE_CONFIG,
) -> MaintenanceDesiredState:
    return load_model(path, MaintenanceDesiredState)


def read_maintenance_state(
    desired: MaintenanceDesiredState, client: MidcltClient
) -> dict[str, Any]:
    return {
        "pools": client.call("pool.query", [["name", "=", desired.pool]]),
        "scrubs": client.call("pool.scrub.query"),
        "services": client.call("service.query", [["service", "=", "smartd"]]),
        "smart_tests": client.call("smart.test.query"),
    }


def scrub_payload(desired: MaintenanceDesiredState, pool_id: int) -> dict[str, Any]:
    return {
        "pool": pool_id,
        "threshold": desired.scrub.threshold,
        "description": desired.scrub.description,
        "schedule": desired.scrub.schedule.model_dump(mode="json"),
        "enabled": desired.scrub.enabled,
    }


def smart_test_payload(test: SmartSelfTest) -> dict[str, Any]:
    return {
        "type": test.type,
        "desc": test.desc,
        "all_disks": test.all_disks,
        "disks": list(test.disks),
        "schedule": test.schedule.model_dump(mode="json"),
    }


def _pool(
    desired: MaintenanceDesiredState, pools: Sequence[Mapping[str, Any]]
) -> Mapping[str, Any]:
    matches = [pool for pool in pools if pool.get("name") == desired.pool]
    if len(matches) != 1 or not isinstance(matches[0].get("id"), int):
        raise OperationalError(f"expected exactly one TrueNAS pool named {desired.pool}")
    return matches[0]


def _smartd_service(services: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    matches = [service for service in services if service.get("service") == "smartd"]
    if len(matches) != 1:
        raise OperationalError("expected exactly one TrueNAS smartd service")
    return matches[0]


def _managed_scrub(current: Mapping[str, Any]) -> dict[str, Any]:
    schedule = current.get("schedule")
    schedule_mapping = schedule if isinstance(schedule, Mapping) else {}
    return {
        "pool": current.get("pool"),
        "threshold": current.get("threshold"),
        "description": current.get("description"),
        "schedule": {
            key: schedule_mapping.get(key) for key in ("minute", "hour", "dom", "month", "dow")
        },
        "enabled": current.get("enabled"),
    }


def _managed_smart_test(current: Mapping[str, Any]) -> dict[str, Any]:
    schedule = current.get("schedule")
    schedule_mapping = schedule if isinstance(schedule, Mapping) else {}
    disks = current.get("disks")
    return {
        "type": current.get("type"),
        "desc": current.get("desc"),
        "all_disks": current.get("all_disks"),
        "disks": sorted(disks) if isinstance(disks, list) else [],
        "schedule": {key: schedule_mapping.get(key) for key in ("hour", "dom", "month", "dow")},
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


def _smart_matches(
    test: SmartSelfTest, current_tests: Sequence[Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    return [
        current
        for current in current_tests
        if current.get("type") == test.type and current.get("all_disks") is True
    ]


def plan_maintenance(
    desired: MaintenanceDesiredState,
    pools: Sequence[Mapping[str, Any]],
    scrubs: Sequence[Mapping[str, Any]],
    services: Sequence[Mapping[str, Any]],
    smart_tests: Sequence[Mapping[str, Any]],
) -> Plan:
    operations: list[Operation] = []
    current_pool = _pool(desired, pools)
    pool_id = int(current_pool["id"])
    if current_pool.get("status") != "ONLINE":
        operations.append(
            Operation(
                kind=OperationKind.WARNING,
                scope=desired.ownership.scope,
                resource_id="pool-health",
                summary="Disk-maintenance apply is blocked until the pool is ONLINE",
            )
        )

    smartd = _smartd_service(services)
    service_fields: list[str] = []
    if smartd.get("enable") is not desired.smartd.enabled:
        service_fields.append("enabled")
    if (smartd.get("state") == "RUNNING") is not desired.smartd.running:
        service_fields.append("running")
    operations.append(
        Operation(
            kind=OperationKind.UPDATE if service_fields else OperationKind.UNCHANGED,
            scope=desired.ownership.scope,
            resource_id="smartd-service",
            summary=(
                "SMART daemon differs from desired state"
                if service_fields
                else "SMART daemon is current"
            ),
            changed_fields=tuple(service_fields),
        )
    )

    scrub_matches = [scrub for scrub in scrubs if scrub.get("pool") == pool_id]
    desired_scrub = scrub_payload(desired, pool_id)
    if not scrub_matches:
        operations.append(
            Operation(
                kind=OperationKind.CREATE,
                scope=desired.ownership.scope,
                resource_id=desired.scrub.id,
                summary="Pool scrub task is absent",
            )
        )
    else:
        changed_fields = _changed_fields(desired_scrub, _managed_scrub(scrub_matches[0]))
        operations.append(
            Operation(
                kind=OperationKind.UPDATE if changed_fields else OperationKind.UNCHANGED,
                scope=desired.ownership.scope,
                resource_id=desired.scrub.id,
                summary=(
                    "Pool scrub task differs from desired state"
                    if changed_fields
                    else "Pool scrub task is current"
                ),
                changed_fields=changed_fields,
            )
        )
    for duplicate in scrub_matches[1:]:
        operations.append(
            Operation(
                kind=OperationKind.WARNING,
                scope=desired.ownership.scope,
                resource_id=f"duplicate-scrub-{duplicate.get('id', 'unknown')}",
                summary="Duplicate pool scrub task is preserved",
            )
        )

    desired_types = {test.type for test in desired.smart_tests}
    for test in desired.smart_tests:
        matches = _smart_matches(test, smart_tests)
        payload = smart_test_payload(test)
        if not matches:
            operations.append(
                Operation(
                    kind=OperationKind.CREATE,
                    scope=desired.ownership.scope,
                    resource_id=test.id,
                    summary=f"All-disk SMART {test.type.lower()} test is absent",
                )
            )
        else:
            changed_fields = _changed_fields(payload, _managed_smart_test(matches[0]))
            operations.append(
                Operation(
                    kind=OperationKind.UPDATE if changed_fields else OperationKind.UNCHANGED,
                    scope=desired.ownership.scope,
                    resource_id=test.id,
                    summary=(
                        f"SMART {test.type.lower()} test differs from desired state"
                        if changed_fields
                        else f"SMART {test.type.lower()} test is current"
                    ),
                    changed_fields=changed_fields,
                )
            )
        for duplicate in matches[1:]:
            operations.append(
                Operation(
                    kind=OperationKind.WARNING,
                    scope=desired.ownership.scope,
                    resource_id=f"duplicate-smart-{duplicate.get('id', 'unknown')}",
                    summary=f"Duplicate all-disk SMART {test.type.lower()} test is preserved",
                )
            )

    for current in smart_tests:
        if current.get("type") not in desired_types or current.get("all_disks") is True:
            continue
        operations.append(
            Operation(
                kind=OperationKind.WARNING,
                scope=desired.ownership.scope,
                resource_id=f"smart-{current.get('id', 'unknown')}",
                summary="Unmanaged SMART test is preserved and may conflict with all-disk policy",
            )
        )
    return Plan(operations=order_operations(operations))


def apply_maintenance(
    desired: MaintenanceDesiredState,
    pools: Sequence[Mapping[str, Any]],
    scrubs: Sequence[Mapping[str, Any]],
    services: Sequence[Mapping[str, Any]],
    smart_tests: Sequence[Mapping[str, Any]],
    client: MidcltClient,
) -> Plan:
    current_pool = _pool(desired, pools)
    if current_pool.get("status") != "ONLINE":
        raise OperationalError("refusing disk-maintenance apply while the pool is not ONLINE")

    plan = plan_maintenance(desired, pools, scrubs, services, smart_tests)
    pool_id = int(current_pool["id"])
    scrub_matches = [scrub for scrub in scrubs if scrub.get("pool") == pool_id]
    smart_by_id = {test.id: test for test in desired.smart_tests}
    smartd = _smartd_service(services)

    if smartd.get("enable") is not desired.smartd.enabled:
        client.call("service.update", "smartd", {"enable": desired.smartd.enabled})
    if (smartd.get("state") == "RUNNING") is not desired.smartd.running:
        client.call("service.start", "smartd", {"silent": False})

    for operation in plan.operations:
        if operation.resource_id == desired.scrub.id:
            if operation.kind is OperationKind.CREATE:
                client.call("pool.scrub.create", scrub_payload(desired, pool_id))
            elif operation.kind is OperationKind.UPDATE:
                client.call(
                    "pool.scrub.update",
                    scrub_matches[0]["id"],
                    scrub_payload(desired, pool_id),
                )
            continue
        test = smart_by_id.get(operation.resource_id)
        if test is None:
            continue
        matches = _smart_matches(test, smart_tests)
        if operation.kind is OperationKind.CREATE:
            conflicting = [current for current in smart_tests if current.get("type") == test.type]
            if conflicting:
                raise OperationalError(
                    f"existing SMART {test.type.lower()} task conflicts with all-disk policy"
                )
            client.call("smart.test.create", smart_test_payload(test))
        elif operation.kind is OperationKind.UPDATE:
            client.call("smart.test.update", matches[0]["id"], smart_test_payload(test))
    return plan
