from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from homeserver_iac.models.common import Operation, OperationKind, Plan, order_operations
from homeserver_iac.models.nfs import NfsDesiredState, NfsShare
from homeserver_iac.runtime import OperationalError
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.truenas import MidcltClient
from homeserver_iac.validation import load_model

DEFAULT_NFS_CONFIG = INFRA_ROOT / "truenas/shares/nfs-shares.yaml"


def load_nfs_desired(path: Path = DEFAULT_NFS_CONFIG) -> NfsDesiredState:
    return load_model(path, NfsDesiredState)


def desired_share_payload(share: NfsShare) -> dict[str, Any]:
    return {
        "path": share.path,
        "hosts": list(share.hosts),
        "networks": list(share.networks),
        "ro": share.read_only,
        "enabled": share.enabled,
        "mapall_user": share.mapall_user,
        "mapall_group": share.mapall_group,
    }


def _managed_share(current: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "path": current.get("path"),
        "hosts": current.get("hosts", []),
        "networks": current.get("networks", []),
        "ro": current.get("ro"),
        "enabled": current.get("enabled"),
        "mapall_user": current.get("mapall_user"),
        "mapall_group": current.get("mapall_group"),
    }


def _changed_fields(desired: Mapping[str, Any], current: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(key for key, value in desired.items() if current.get(key) != value))


def _current_by_managed_path(
    desired: NfsDesiredState, current_shares: Sequence[Mapping[str, Any]]
) -> dict[str, Mapping[str, Any]]:
    managed_paths = {share.path for share in desired.shares} | {
        share.path for share in desired.retire_shares
    }
    matches: dict[str, list[Mapping[str, Any]]] = {}
    for current in current_shares:
        path = current.get("path")
        if isinstance(path, str) and path in managed_paths:
            matches.setdefault(path, []).append(current)
    for path, shares in matches.items():
        if len(shares) > 1:
            raise OperationalError(f"multiple NFS shares match managed path {path!r}")
    return {path: shares[0] for path, shares in matches.items()}


def plan_nfs(
    desired: NfsDesiredState,
    current_service: Mapping[str, Any],
    current_shares: Sequence[Mapping[str, Any]],
) -> Plan:
    current_by_path = _current_by_managed_path(desired, current_shares)
    operations: list[Operation] = []
    service_fields = []
    if current_service.get("enable") != desired.service.enabled:
        service_fields.append("enabled")
    is_running = current_service.get("state") == "RUNNING"
    if is_running != desired.service.running:
        service_fields.append("running")
    operations.append(
        Operation(
            kind=OperationKind.UPDATE if service_fields else OperationKind.UNCHANGED,
            scope=desired.ownership.scope,
            resource_id="nfs-service",
            summary="NFS service differs from desired state"
            if service_fields
            else "NFS service is current",
            changed_fields=tuple(service_fields),
        )
    )

    for share in desired.shares:
        current = current_by_path.get(share.path)
        if current is None:
            operations.append(
                Operation(
                    kind=OperationKind.CREATE,
                    scope=desired.ownership.scope,
                    resource_id=share.id,
                    summary="NFS share is absent",
                )
            )
            continue
        changed_fields = _changed_fields(desired_share_payload(share), _managed_share(current))
        operations.append(
            Operation(
                kind=OperationKind.UPDATE if changed_fields else OperationKind.UNCHANGED,
                scope=desired.ownership.scope,
                resource_id=share.id,
                summary="NFS share differs from desired state"
                if changed_fields
                else "NFS share is current",
                changed_fields=changed_fields,
            )
        )
    for retired in desired.retire_shares:
        if current_by_path.get(retired.path):
            operations.append(
                Operation(
                    kind=OperationKind.DELETE,
                    scope=desired.ownership.scope,
                    resource_id=retired.id,
                    summary="NFS share is explicitly declared for retirement",
                )
            )
    return Plan(operations=order_operations(operations))


def apply_nfs(
    desired: NfsDesiredState,
    current_service: Mapping[str, Any],
    current_shares: Sequence[Mapping[str, Any]],
    client: MidcltClient,
) -> Plan:
    plan = plan_nfs(desired, current_service, current_shares)
    desired_by_id = {share.id: share for share in desired.shares}
    retired_by_id = {share.id: share for share in desired.retire_shares}
    current_by_path = _current_by_managed_path(desired, current_shares)

    if current_service.get("enable") != desired.service.enabled:
        client.call("service.update", "nfs", {"enable": desired.service.enabled})
    is_running = current_service.get("state") == "RUNNING"
    if desired.service.running and not is_running:
        client.call("service.start", "nfs", {"silent": False})
    elif not desired.service.running and is_running:
        client.call("service.stop", "nfs", {"silent": False})

    for operation in plan.operations:
        if operation.resource_id == "nfs-service":
            continue
        if operation.kind is OperationKind.CREATE:
            share = desired_by_id[operation.resource_id]
            client.call("sharing.nfs.create", desired_share_payload(share))
        elif operation.kind is OperationKind.UPDATE:
            share = desired_by_id[operation.resource_id]
            client.call(
                "sharing.nfs.update",
                current_by_path[share.path]["id"],
                desired_share_payload(share),
            )
        elif operation.kind is OperationKind.DELETE:
            retired = retired_by_id[operation.resource_id]
            client.call("sharing.nfs.delete", current_by_path[retired.path]["id"])
    return plan
