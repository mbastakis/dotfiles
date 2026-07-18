from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from homeserver_iac.models.common import Operation, OperationKind, Plan, order_operations
from homeserver_iac.models.smb import SmbDesiredState, SmbShare
from homeserver_iac.runtime import OperationalError
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.truenas import MidcltClient
from homeserver_iac.validation import load_model

DEFAULT_SMB_CONFIG = INFRA_ROOT / "truenas/shares/smb-shares.yaml"


def load_smb_desired(path: Path = DEFAULT_SMB_CONFIG) -> SmbDesiredState:
    return load_model(path, SmbDesiredState)


def _auxiliary_config(share: SmbShare) -> str:
    allowed_users = " ".join(share.allowed_users)
    return "\n".join(
        (
            f"valid users = {allowed_users}",
            f"force user = {share.force_user}",
            f"force group = {share.force_group}",
            "create mask = 0660",
            "directory mask = 0770",
        )
    )


def desired_share_payload(share: SmbShare) -> dict[str, Any]:
    return {
        "purpose": "NO_PRESET",
        "path": share.path,
        "name": share.name,
        "comment": share.comment,
        "ro": share.read_only,
        "browsable": share.browsable,
        "guestok": False,
        "acl": False,
        "shadowcopy": False,
        "streams": True,
        "auxsmbconf": _auxiliary_config(share),
        "enabled": share.enabled,
    }


def _managed_share(current: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "purpose": current.get("purpose"),
        "path": current.get("path"),
        "name": current.get("name"),
        "comment": current.get("comment", ""),
        "ro": current.get("ro"),
        "browsable": current.get("browsable"),
        "guestok": current.get("guestok"),
        "acl": current.get("acl"),
        "shadowcopy": current.get("shadowcopy"),
        "streams": current.get("streams"),
        "auxsmbconf": current.get("auxsmbconf", ""),
        "enabled": current.get("enabled"),
    }


def _changed_fields(desired: Mapping[str, Any], current: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(key for key, value in desired.items() if current.get(key) != value))


def _current_by_managed_name(
    desired: SmbDesiredState, current_shares: Sequence[Mapping[str, Any]]
) -> dict[str, Mapping[str, Any]]:
    managed_names = {share.name.casefold() for share in desired.shares} | {
        share.name.casefold() for share in desired.retire_shares
    }
    matches: dict[str, list[Mapping[str, Any]]] = {}
    for current in current_shares:
        name = current.get("name")
        if isinstance(name, str) and name.casefold() in managed_names:
            matches.setdefault(name.casefold(), []).append(current)
    for name, shares in matches.items():
        if len(shares) > 1:
            raise OperationalError(f"multiple SMB shares match managed name {name!r}")
    return {name: shares[0] for name, shares in matches.items()}


def plan_smb(
    desired: SmbDesiredState,
    current_service: Mapping[str, Any],
    current_shares: Sequence[Mapping[str, Any]],
) -> Plan:
    current_by_name = _current_by_managed_name(desired, current_shares)
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
            resource_id="smb-service",
            summary="SMB service differs from desired state"
            if service_fields
            else "SMB service is current",
            changed_fields=tuple(service_fields),
        )
    )

    for share in desired.shares:
        current = current_by_name.get(share.name.casefold())
        if current is None:
            operations.append(
                Operation(
                    kind=OperationKind.CREATE,
                    scope=desired.ownership.scope,
                    resource_id=share.id,
                    summary="SMB share is absent",
                )
            )
            continue
        changed_fields = _changed_fields(desired_share_payload(share), _managed_share(current))
        operations.append(
            Operation(
                kind=OperationKind.UPDATE if changed_fields else OperationKind.UNCHANGED,
                scope=desired.ownership.scope,
                resource_id=share.id,
                summary="SMB share differs from desired state"
                if changed_fields
                else "SMB share is current",
                changed_fields=changed_fields,
            )
        )
    for retired in desired.retire_shares:
        if current_by_name.get(retired.name.casefold()):
            operations.append(
                Operation(
                    kind=OperationKind.DELETE,
                    scope=desired.ownership.scope,
                    resource_id=retired.id,
                    summary="SMB share is explicitly declared for retirement",
                )
            )
    return Plan(operations=order_operations(operations))


def apply_smb(
    desired: SmbDesiredState,
    current_service: Mapping[str, Any],
    current_shares: Sequence[Mapping[str, Any]],
    client: MidcltClient,
) -> Plan:
    plan = plan_smb(desired, current_service, current_shares)
    desired_by_id = {share.id: share for share in desired.shares}
    retired_by_id = {share.id: share for share in desired.retire_shares}
    current_by_name = _current_by_managed_name(desired, current_shares)

    if current_service.get("enable") != desired.service.enabled:
        client.call("service.update", "cifs", {"enable": desired.service.enabled})
    is_running = current_service.get("state") == "RUNNING"
    if not desired.service.running and is_running:
        client.call("service.stop", "cifs", {"silent": False})

    for operation in plan.operations:
        if operation.resource_id == "smb-service":
            continue
        if operation.kind is OperationKind.CREATE:
            share = desired_by_id[operation.resource_id]
            client.call("sharing.smb.create", desired_share_payload(share))
        elif operation.kind is OperationKind.UPDATE:
            share = desired_by_id[operation.resource_id]
            client.call(
                "sharing.smb.update",
                current_by_name[share.name.casefold()]["id"],
                desired_share_payload(share),
            )
        elif operation.kind is OperationKind.DELETE:
            retired = retired_by_id[operation.resource_id]
            client.call(
                "sharing.smb.delete",
                current_by_name[retired.name.casefold()]["id"],
            )

    if desired.service.running and not is_running:
        client.call("service.start", "cifs", {"silent": False})
    return plan
