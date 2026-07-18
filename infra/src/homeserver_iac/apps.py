from __future__ import annotations

import copy
import hashlib
import shlex
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from homeserver_iac.models.common import (
    Operation,
    OperationKind,
    Plan,
    SecretRef,
    order_operations,
)
from homeserver_iac.models.truenas_apps import TrueNASAppDesiredState
from homeserver_iac.runtime import OperationalError, run_command
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.secrets import SecretResolver
from homeserver_iac.truenas import MidcltClient
from homeserver_iac.validation import load_model

DEFAULT_APP_DECLARATIONS = INFRA_ROOT / "truenas/apps/declarations"
APP_ROOT = INFRA_ROOT / "truenas/apps"


def load_app_declarations(
    directory: Path = DEFAULT_APP_DECLARATIONS,
    selected: Sequence[str] = (),
) -> tuple[TrueNASAppDesiredState, ...]:
    declarations = tuple(
        load_model(path, TrueNASAppDesiredState) for path in sorted(directory.glob("*.yaml"))
    )
    if not selected:
        return declarations
    wanted = set(selected)
    matched = tuple(
        declaration
        for declaration in declarations
        if declaration.app_name in wanted or declaration.catalog_app in wanted
    )
    missing = wanted - {
        value
        for declaration in matched
        for value in (declaration.app_name, declaration.catalog_app)
    }
    if missing:
        raise OperationalError(f"no app declarations matched: {', '.join(sorted(missing))}")
    return matched


def _dotted_parent(value: dict[str, Any], path: str) -> tuple[dict[str, Any], str] | None:
    parts = path.split(".")
    current = value
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            return None
        current = child
    return current, parts[-1]


def _get_dotted(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _set_dotted(value: dict[str, Any], path: str, child: Any) -> None:
    parts = path.split(".")
    current = value
    for part in parts[:-1]:
        existing = current.get(part)
        if not isinstance(existing, dict):
            existing = {}
            current[part] = existing
        current = existing
    current[parts[-1]] = child


def sanitize_app_config(
    declaration: TrueNASAppDesiredState, config: Mapping[str, Any]
) -> dict[str, Any]:
    sanitized = copy.deepcopy(dict(config))
    for value_binding in declaration.secret_values:
        parent = _dotted_parent(sanitized, value_binding.path)
        if parent is not None:
            parent[0].pop(parent[1], None)
    for env_binding in declaration.secret_envs:
        environment = _get_dotted(sanitized, env_binding.path)
        if isinstance(environment, list):
            _set_dotted(
                sanitized,
                env_binding.path,
                [
                    entry
                    for entry in environment
                    if not isinstance(entry, Mapping) or entry.get("name") != env_binding.name
                ],
            )
    return sanitized


def render_app_values(
    declaration: TrueNASAppDesiredState, resolver: SecretResolver
) -> dict[str, Any]:
    values = copy.deepcopy(declaration.values)
    for value_binding in declaration.secret_values:
        secret = resolver.resolve(value_binding.secret_ref.alias, value_binding.env or "")
        _set_dotted(values, value_binding.path, secret)
    for env_binding in declaration.secret_envs:
        secret = resolver.resolve(env_binding.secret_ref.alias, env_binding.env or env_binding.name)
        environment = _get_dotted(values, env_binding.path)
        entries = list(environment) if isinstance(environment, list) else []
        entries = [
            entry
            for entry in entries
            if not isinstance(entry, Mapping) or entry.get("name") != env_binding.name
        ]
        entries.append({"name": env_binding.name, "value": secret})
        _set_dotted(values, env_binding.path, entries)
    return values


def _changed_subset(desired: Any, current: Any, prefix: str = "") -> tuple[str, ...]:
    if isinstance(desired, Mapping):
        if not isinstance(current, Mapping):
            return (prefix or "values",)
        changed: list[str] = []
        for key, value in desired.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            changed.extend(_changed_subset(value, current.get(key), child_prefix))
        return tuple(changed)
    return () if desired == current else (prefix or "values",)


class TrueNASAppFiles:
    def __init__(self, host: str = "truenas", *, timeout: float = 30.0) -> None:
        self.host = host
        self.timeout = timeout

    def _run(self, command: str, *, input_text: str | None = None) -> str:
        ssh = ["ssh"]
        if input_text is None:
            ssh.append("-n")
        ssh.extend(("-o", "ConnectTimeout=10", self.host, command))
        return run_command(tuple(ssh), timeout=self.timeout, input_text=input_text)

    def permission_state(self, path: str) -> dict[str, Any] | None:
        quoted = shlex.quote(path)
        output = self._run(
            f"if sudo test -d {quoted}; then sudo stat -c '%u:%g:%a' {quoted}; fi"
        ).strip()
        if not output:
            return None
        try:
            owner, group, mode = output.split(":", maxsplit=2)
        except ValueError as error:
            raise OperationalError(f"unexpected permission state for {path}") from error
        return {"owner": int(owner), "group": int(group), "mode": mode.zfill(4)}

    def file_hash(self, path: str) -> str:
        quoted = shlex.quote(path)
        output = self._run(
            f"if sudo test -f {quoted}; then sudo sha256sum {quoted} | cut -d' ' -f1; fi"
        ).strip()
        return output

    def file_content(self, path: str) -> str:
        quoted = shlex.quote(path)
        return self._run(f"if sudo test -f {quoted}; then sudo cat {quoted}; fi")

    def ensure_permission(self, path: str, owner: int, group: int, mode: str) -> None:
        self._run(
            "sudo install -d"
            f" -o {shlex.quote(str(owner))}"
            f" -g {shlex.quote(str(group))}"
            f" -m {shlex.quote(mode)}"
            f" {shlex.quote(path)}"
        )

    def deploy_file(
        self,
        source: Path,
        destination: str,
        owner: int,
        group: int,
        mode: str,
        dir_mode: str,
        content: str | None = None,
    ) -> None:
        if content is None:
            try:
                content = source.read_text()
            except OSError as error:
                raise OperationalError(
                    f"managed file source could not be read: {source}"
                ) from error
        destination_path = Path(destination)
        self._run(
            "sudo install -d"
            f" -o {shlex.quote(str(owner))}"
            f" -g {shlex.quote(str(group))}"
            f" -m {shlex.quote(dir_mode)}"
            f" {shlex.quote(str(destination_path.parent))}"
        )
        command = (
            "tmp=$(mktemp) && trap 'rm -f \"$tmp\"' EXIT"
            ' && cat > "$tmp"'
            f" && sudo install -o {shlex.quote(str(owner))}"
            f" -g {shlex.quote(str(group))}"
            f' -m {shlex.quote(mode)} "$tmp" {shlex.quote(destination)}'
        )
        self._run(command, input_text=content)


def read_apps_state(
    declarations: Sequence[TrueNASAppDesiredState],
    client: MidcltClient,
    files: TrueNASAppFiles,
) -> dict[str, Any]:
    query = client.call(
        "app.query",
        [],
        {"select": ["name", "state", "version"]},
    )
    if not isinstance(query, list):
        raise OperationalError("TrueNAS app query returned an unexpected response")
    declarations_by_name = {declaration.app_name: declaration for declaration in declarations}
    apps: list[dict[str, Any]] = []
    for app in query:
        if not isinstance(app, dict) or not isinstance(app.get("name"), str):
            continue
        app_state = dict(app)
        declaration = declarations_by_name.get(app["name"])
        if declaration is not None:
            config = client.call("app.config", declaration.app_name)
            if not isinstance(config, dict):
                raise OperationalError(
                    f"TrueNAS app config returned an unexpected response: {declaration.app_name}"
                )
            app_state["config"] = sanitize_app_config(declaration, config)
        apps.append(app_state)

    permission_state: dict[str, Any] = {}
    managed_files: dict[str, Any] = {}
    for declaration in declarations:
        for permission in declaration.path_permissions:
            permission_state[permission.path] = files.permission_state(permission.path)
        for managed_file in declaration.managed_files:
            managed_files[managed_file.destination] = {
                "sha256": files.file_hash(managed_file.destination),
                "content": (
                    files.file_content(managed_file.destination)
                    if managed_file.content_mode == "yaml-subset"
                    else None
                ),
            }
    return {
        "apps": apps,
        "path_permissions": permission_state,
        "managed_files": managed_files,
    }


def _source_hash(source: str) -> str:
    path = APP_ROOT / source
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise OperationalError(f"managed file source could not be read: {path}") from error


def _managed_file_changed(managed_file: Any, current: Any) -> bool:
    if not isinstance(current, Mapping):
        return True
    if managed_file.content_mode == "exact":
        return current.get("sha256") != _source_hash(managed_file.source)
    source_path = APP_ROOT / managed_file.source
    try:
        desired_yaml = yaml.safe_load(source_path.read_text())
        current_yaml = yaml.safe_load(current.get("content") or "")
    except (OSError, yaml.YAMLError) as error:
        raise OperationalError(
            f"managed YAML file could not be compared: {managed_file.destination}"
        ) from error
    return bool(_changed_subset(desired_yaml, current_yaml))


def _merge_yaml_content(managed_file: Any, current: Any) -> str | None:
    if managed_file.content_mode != "yaml-subset" or not isinstance(current, Mapping):
        return None
    source_path = APP_ROOT / managed_file.source
    try:
        desired_yaml = yaml.safe_load(source_path.read_text())
        current_yaml = yaml.safe_load(current.get("content") or "")
    except (OSError, yaml.YAMLError) as error:
        raise OperationalError(
            f"managed YAML file could not be merged: {managed_file.destination}"
        ) from error

    def merge(desired: Any, live: Any) -> Any:
        if isinstance(desired, Mapping) and isinstance(live, Mapping):
            result = dict(live)
            for key, value in desired.items():
                result[key] = merge(value, live.get(key))
            return result
        return copy.deepcopy(desired)

    return yaml.safe_dump(merge(desired_yaml, current_yaml), sort_keys=False)


def plan_apps(
    declarations: Sequence[TrueNASAppDesiredState],
    current: Mapping[str, Any],
) -> Plan:
    operations: list[Operation] = []
    app_values = current.get("apps")
    apps = app_values if isinstance(app_values, list) else []
    apps_by_name = {
        app.get("name"): app
        for app in apps
        if isinstance(app, Mapping) and isinstance(app.get("name"), str)
    }
    permission_values = current.get("path_permissions")
    permissions = permission_values if isinstance(permission_values, Mapping) else {}
    file_values = current.get("managed_files")
    managed_files = file_values if isinstance(file_values, Mapping) else {}
    declared_names = {declaration.app_name for declaration in declarations}

    for declaration in declarations:
        app = apps_by_name.get(declaration.app_name)
        secret_aliases = tuple(
            dict.fromkeys(
                [binding.secret_ref.alias for binding in declaration.secret_values]
                + [binding.secret_ref.alias for binding in declaration.secret_envs]
            )
        )
        if app is None:
            app_kind = OperationKind.CREATE
            app_changes: tuple[str, ...] = ()
            summary = "TrueNAS catalog app is absent"
        else:
            config = app.get("config")
            app_changes = _changed_subset(
                declaration.values,
                config if isinstance(config, Mapping) else {},
            )
            app_kind = OperationKind.UPDATE if app_changes else OperationKind.UNCHANGED
            summary = (
                "TrueNAS catalog app values differ from desired state"
                if app_changes
                else "TrueNAS catalog app values are current"
            )
        operations.append(
            Operation(
                kind=app_kind,
                scope=declaration.ownership.scope,
                resource_id=declaration.app_name,
                summary=summary,
                changed_fields=app_changes,
                secret_refs=tuple(SecretRef(alias=alias) for alias in secret_aliases),
            )
        )
        if app is not None and app.get("version") != declaration.version:
            operations.append(
                Operation(
                    kind=OperationKind.WARNING,
                    scope=declaration.ownership.scope,
                    resource_id=f"{declaration.app_name}-version",
                    summary=(
                        f"Live catalog version {app.get('version')} differs from install pin "
                        f"{declaration.version}; version lifecycle is not changed by values apply"
                    ),
                )
            )

        permission_changes = tuple(
            permission.path
            for permission in declaration.path_permissions
            if permissions.get(permission.path) is None
            or (
                permission.enforce_existing
                and permissions.get(permission.path)
                != {
                    "owner": permission.owner,
                    "group": permission.group,
                    "mode": permission.mode,
                }
            )
        )
        runtime_permission_paths = tuple(
            permission.path
            for permission in declaration.path_permissions
            if not permission.enforce_existing
            and permissions.get(permission.path) is not None
            and permissions.get(permission.path)
            != {
                "owner": permission.owner,
                "group": permission.group,
                "mode": permission.mode,
            }
        )
        if declaration.path_permissions:
            operations.append(
                Operation(
                    kind=(OperationKind.UPDATE if permission_changes else OperationKind.UNCHANGED),
                    scope=declaration.ownership.scope,
                    resource_id=f"{declaration.app_name}-permissions",
                    summary=(
                        "TrueNAS app path permissions differ from desired state"
                        if permission_changes
                        else "TrueNAS app path permissions are current"
                    ),
                    changed_fields=permission_changes,
                )
            )
        if runtime_permission_paths:
            operations.append(
                Operation(
                    kind=OperationKind.WARNING,
                    scope=declaration.ownership.scope,
                    resource_id=f"{declaration.app_name}-runtime-permissions",
                    summary="Runtime-owned app path permissions are preserved",
                    changed_fields=runtime_permission_paths,
                )
            )

        file_changes = tuple(
            managed_file.destination
            for managed_file in declaration.managed_files
            if _managed_file_changed(managed_file, managed_files.get(managed_file.destination))
        )
        if declaration.managed_files:
            operations.append(
                Operation(
                    kind=OperationKind.UPDATE if file_changes else OperationKind.UNCHANGED,
                    scope=declaration.ownership.scope,
                    resource_id=f"{declaration.app_name}-managed-files",
                    summary=(
                        "TrueNAS app managed files differ from desired state"
                        if file_changes
                        else "TrueNAS app managed files are current"
                    ),
                    changed_fields=file_changes,
                )
            )

    for index, app in enumerate(apps):
        if isinstance(app, Mapping) and app.get("name") not in declared_names:
            operations.append(
                Operation(
                    kind=OperationKind.WARNING,
                    scope="truenas.catalog_apps",
                    resource_id=f"unmanaged-app-{index}",
                    summary="Unmanaged TrueNAS catalog app is preserved",
                )
            )
    return Plan(operations=order_operations(operations))


def apply_apps(
    declarations: Sequence[TrueNASAppDesiredState],
    current: Mapping[str, Any],
    client: MidcltClient,
    files: TrueNASAppFiles,
    resolver: SecretResolver,
) -> Plan:
    plan = plan_apps(declarations, current)
    operations = {operation.resource_id: operation for operation in plan.operations}
    for declaration in declarations:
        permission_operation = operations.get(f"{declaration.app_name}-permissions")
        if permission_operation is not None and permission_operation.kind is OperationKind.UPDATE:
            changed_permissions = set(permission_operation.changed_fields)
            for permission in declaration.path_permissions:
                if permission.path in changed_permissions:
                    files.ensure_permission(
                        permission.path, permission.owner, permission.group, permission.mode
                    )

        file_operation = operations.get(f"{declaration.app_name}-managed-files")
        if file_operation is not None and file_operation.kind is OperationKind.UPDATE:
            changed = set(file_operation.changed_fields)
            for managed_file in declaration.managed_files:
                if managed_file.destination in changed:
                    files.deploy_file(
                        APP_ROOT / managed_file.source,
                        managed_file.destination,
                        managed_file.owner,
                        managed_file.group,
                        managed_file.mode,
                        managed_file.dir_mode,
                        _merge_yaml_content(
                            managed_file,
                            current.get("managed_files", {}).get(managed_file.destination),
                        ),
                    )

        app_operation = operations[declaration.app_name]
        if app_operation.kind not in {OperationKind.CREATE, OperationKind.UPDATE}:
            continue
        values = render_app_values(declaration, resolver)
        if app_operation.kind is OperationKind.CREATE:
            client.call(
                "app.create",
                {
                    "custom_app": False,
                    "app_name": declaration.app_name,
                    "catalog_app": declaration.catalog_app,
                    "train": declaration.train,
                    "version": declaration.version,
                    "values": values,
                },
                job=True,
            )
        else:
            client.call(
                "app.update",
                declaration.app_name,
                {"values": values},
                job=True,
            )
    return plan
