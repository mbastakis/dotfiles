from __future__ import annotations

import base64
import copy
import json
import os
import urllib.error
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from homeserver_iac.models.backrest import BackrestDesiredState
from homeserver_iac.models.common import (
    Operation,
    OperationKind,
    Plan,
    SecretRef,
    order_operations,
)
from homeserver_iac.runtime import OperationalError
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.validation import load_model

DEFAULT_BACKREST_CONFIG = INFRA_ROOT / "truenas/backrest/backrest-plans.yaml"
DEFAULT_BACKREST_URL = "http://192.168.1.74:30329"


def load_backrest_desired(path: Path = DEFAULT_BACKREST_CONFIG) -> BackrestDesiredState:
    return load_model(path, BackrestDesiredState)


class BackrestClient:
    def __init__(
        self,
        base_url: str,
        authorization: str,
        *,
        timeout: float = 20.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.authorization = authorization
        self.timeout = timeout

    @classmethod
    def from_environment(cls, base_url: str, *, timeout: float = 20.0) -> BackrestClient:
        token = os.environ.get("BACKREST_TOKEN", "")
        if token:
            return cls(base_url, f"Bearer {token}", timeout=timeout)
        password = os.environ.get("BACKREST_PASSWORD") or os.environ.get(
            "BACKREST_ADMIN_PASSWORD", ""
        )
        if not password:
            raise OperationalError(
                "set BACKREST_PASSWORD, BACKREST_ADMIN_PASSWORD, or BACKREST_TOKEN"
            )
        username = os.environ.get("BACKREST_USERNAME", "admin")
        encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
        return cls(base_url, f"Basic {encoded}", timeout=timeout)

    def call(self, method: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}/v1.Backrest/{method}",
            data=json.dumps(payload, separators=(",", ":")).encode(),
            headers={
                "Authorization": self.authorization,
                "Connect-Protocol-Version": "1",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as error:
            raise OperationalError(f"Backrest {method} failed with HTTP {error.code}") from error
        except (TimeoutError, urllib.error.URLError) as error:
            raise OperationalError(f"Backrest {method} request failed") from error
        if not body:
            return {}
        try:
            result = json.loads(body)
        except json.JSONDecodeError as error:
            raise OperationalError(f"Backrest {method} returned invalid JSON") from error
        if not isinstance(result, dict):
            raise OperationalError(f"Backrest {method} returned an unexpected response")
        return result

    def get_config(self) -> dict[str, Any]:
        return self.call("GetConfig", {})

    def set_config(self, config: Mapping[str, Any]) -> None:
        self.call("SetConfig", config)

    def add_repo(self, repository: Mapping[str, Any]) -> None:
        self.call("AddRepo", {"repo": repository})


def desired_repository(desired: BackrestDesiredState) -> dict[str, Any]:
    return desired.repository.model_dump(mode="json", by_alias=True)


def desired_plans(desired: BackrestDesiredState) -> list[dict[str, Any]]:
    return [plan.model_dump(mode="json", by_alias=True) for plan in desired.plans]


def _normalize_repository(repository: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(repository)
    if not normalized.get("password"):
        normalized.pop("password", None)
    env = normalized.get("env")
    if isinstance(env, list):
        normalized["env"] = sorted(env)
    return normalized


def _normalize_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(dict(plan))
    retention = normalized.get("retention")
    if not isinstance(retention, dict):
        return normalized
    buckets = retention.get("policyTimeBucketed")
    if not isinstance(buckets, dict):
        return normalized
    for bucket in ("daily", "weekly", "monthly", "yearly"):
        buckets.setdefault(bucket, 0)
    return normalized


def _repository_changed_fields(
    desired: Mapping[str, Any],
    current: Mapping[str, Any],
    clear_fields: tuple[str, ...],
) -> tuple[str, ...]:
    normalized_desired = _normalize_repository(desired)
    normalized_current = _normalize_repository(current)
    changed = [
        key for key, value in normalized_desired.items() if normalized_current.get(key) != value
    ]
    changed.extend(field for field in clear_fields if field in current)
    return tuple(sorted(set(changed)))


def plan_backrest(desired: BackrestDesiredState, current: Mapping[str, Any]) -> Plan:
    operations: list[Operation] = []
    repositories = current.get("repos")
    current_repositories = repositories if isinstance(repositories, list) else []
    plans = current.get("plans")
    current_plans = plans if isinstance(plans, list) else []
    repository = desired_repository(desired)
    repository_id = desired.repository.id
    current_repository = next(
        (
            item
            for item in current_repositories
            if isinstance(item, Mapping) and item.get("id") == repository_id
        ),
        None,
    )
    secret_refs = tuple(dict.fromkeys(binding.secret_ref.alias for binding in desired.secret_refs))
    if current_repository is None:
        operations.append(
            Operation(
                kind=OperationKind.CREATE,
                scope=desired.ownership.scope,
                resource_id=repository_id,
                summary="Backrest repository is absent",
                secret_refs=tuple(SecretRef(alias=alias) for alias in secret_refs),
            )
        )
    else:
        repository_changed_fields = _repository_changed_fields(
            repository, current_repository, desired.repository_clear_fields
        )
        operations.append(
            Operation(
                kind=(
                    OperationKind.UPDATE if repository_changed_fields else OperationKind.UNCHANGED
                ),
                scope=desired.ownership.scope,
                resource_id=repository_id,
                summary=(
                    "Backrest repository policy differs from desired state"
                    if repository_changed_fields
                    else "Backrest repository policy is current"
                ),
                changed_fields=repository_changed_fields,
                secret_refs=tuple(SecretRef(alias=alias) for alias in secret_refs),
            )
        )

    desired_plan_values = desired_plans(desired)
    current_plan_by_id = {
        str(item["id"]): item
        for item in current_plans
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    for plan in desired_plan_values:
        plan_id = str(plan["id"])
        current_plan = current_plan_by_id.get(plan_id)
        if current_plan is None:
            kind = OperationKind.CREATE
            plan_changed_fields: tuple[str, ...] = ()
            summary = "Backrest plan is absent"
        else:
            normalized_plan = _normalize_plan(plan)
            normalized_current = _normalize_plan(current_plan)
            plan_changed_fields = tuple(
                sorted(
                    key
                    for key in normalized_plan.keys() | normalized_current.keys()
                    if normalized_plan.get(key) != normalized_current.get(key)
                )
            )
            kind = OperationKind.UPDATE if plan_changed_fields else OperationKind.UNCHANGED
            summary = (
                "Backrest plan differs from desired state"
                if plan_changed_fields
                else "Backrest plan is current"
            )
        operations.append(
            Operation(
                kind=kind,
                scope=desired.ownership.scope,
                resource_id=plan_id,
                summary=summary,
                changed_fields=plan_changed_fields,
            )
        )

    for retired_id in desired.retire_plans:
        present = retired_id in current_plan_by_id
        operations.append(
            Operation(
                kind=OperationKind.DELETE if present else OperationKind.UNCHANGED,
                scope=desired.ownership.scope,
                resource_id=retired_id,
                summary=(
                    "Backrest plan is explicitly declared for retirement"
                    if present
                    else "Retired Backrest plan is absent"
                ),
            )
        )

    declared_ids = {plan.id for plan in desired.plans} | set(desired.retire_plans)
    for plan_id, current_plan_value in current_plan_by_id.items():
        if current_plan_value.get("repo") == repository_id and plan_id not in declared_ids:
            operations.append(
                Operation(
                    kind=OperationKind.WARNING,
                    scope=desired.ownership.scope,
                    resource_id=plan_id,
                    summary="Unmanaged Backrest plan is preserved",
                )
            )
    return Plan(operations=order_operations(operations))


def build_backrest_config(
    desired: BackrestDesiredState, current: Mapping[str, Any]
) -> dict[str, Any]:
    updated = copy.deepcopy(dict(current))
    repository = desired_repository(desired)
    repositories = updated.get("repos")
    current_repositories = repositories if isinstance(repositories, list) else []
    updated_repositories: list[Any] = []
    for item in current_repositories:
        if isinstance(item, dict) and item.get("id") == desired.repository.id:
            merged = {**item, **_normalize_repository(repository)}
            for field in desired.repository_clear_fields:
                merged.pop(field, None)
            updated_repositories.append(merged)
        else:
            updated_repositories.append(item)
    updated["repos"] = updated_repositories

    plans = updated.get("plans")
    current_plans = plans if isinstance(plans, list) else []
    desired_by_id = {str(plan["id"]): plan for plan in desired_plans(desired)}
    retired = set(desired.retire_plans)
    updated_plans: list[Any] = []
    seen: set[str] = set()
    for item in current_plans:
        item_id = item.get("id") if isinstance(item, Mapping) else None
        if isinstance(item_id, str) and item_id in retired:
            continue
        if isinstance(item_id, str) and item_id in desired_by_id:
            updated_plans.append(desired_by_id[item_id])
            seen.add(item_id)
        else:
            updated_plans.append(item)
    updated_plans.extend(plan for plan_id, plan in desired_by_id.items() if plan_id not in seen)
    updated["plans"] = updated_plans
    return updated


def apply_backrest(
    desired: BackrestDesiredState,
    current: Mapping[str, Any],
    client: BackrestClient,
) -> Plan:
    plan = plan_backrest(desired, current)
    repository_operation = next(
        operation for operation in plan.operations if operation.resource_id == desired.repository.id
    )
    working = dict(current)
    if repository_operation.kind is OperationKind.CREATE:
        client.add_repo(desired_repository(desired))
        working = client.get_config()
        repositories = working.get("repos", [])
        if not any(
            isinstance(item, Mapping) and item.get("id") == desired.repository.id
            for item in repositories
        ):
            raise OperationalError("Backrest did not return the newly added repository")

    mutating = {
        OperationKind.CREATE,
        OperationKind.UPDATE,
        OperationKind.DELETE,
    }
    updated = build_backrest_config(desired, working)
    if any(operation.kind in mutating for operation in plan.operations) and updated != working:
        client.set_config(updated)
        verification = plan_backrest(desired, client.get_config())
        if any(operation.kind in mutating for operation in verification.operations):
            raise OperationalError("Backrest accepted config but managed drift remains")
    return plan
