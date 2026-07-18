from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

from homeserver_iac.apps import (
    APP_ROOT,
    TrueNASAppFiles,
    apply_apps,
    load_app_declarations,
    plan_apps,
    sanitize_app_config,
)
from homeserver_iac.models.common import OperationKind, serialize_plan
from homeserver_iac.secrets import SecretResolver
from homeserver_iac.truenas import MidcltClient

FIXTURES = Path(__file__).parent / "fixtures/apps"


def synthetic_state() -> dict[str, Any]:
    declarations = load_app_declarations()
    permissions: dict[str, Any] = {}
    files: dict[str, str] = {}
    for declaration in declarations:
        for permission in declaration.path_permissions:
            permissions[permission.path] = {
                "owner": permission.owner,
                "group": permission.group,
                "mode": permission.mode,
            }
        for managed_file in declaration.managed_files:
            source = APP_ROOT / managed_file.source
            files[managed_file.destination] = {
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "content": source.read_text(),
            }
    return {
        "apps": [
            {
                "name": declaration.app_name,
                "state": "RUNNING",
                "version": declaration.version,
                "config": {**copy.deepcopy(declaration.values), "ix_context": {"runtime": True}},
            }
            for declaration in declarations
        ],
        "path_permissions": permissions,
        "managed_files": files,
    }


class FailingResolver:
    def resolve(self, alias: str, fallback_env: str) -> str:
        raise AssertionError(f"no-op apply resolved {alias} from {fallback_env}")


class FakeMidcltClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], bool]] = []

    def call(self, method: str, *arguments: Any, job: bool = False) -> None:
        self.calls.append((method, arguments, job))


class FakeAppFiles:
    def ensure_permission(self, path: str, owner: int, group: int, mode: str) -> None:
        raise AssertionError(f"unexpected permission write: {path} {owner}:{group} {mode}")

    def deploy_file(self, *arguments: Any) -> None:
        raise AssertionError(f"unexpected file deployment: {arguments}")


def test_app_plan_ignores_runtime_config_and_treats_version_as_warning() -> None:
    declaration = load_app_declarations(selected=("syncthing",))
    current = cast(dict[str, Any], json.loads((FIXTURES / "syncthing.json").read_text()))

    plan = plan_apps(declaration, current)

    assert (OperationKind.UNCHANGED, "syncthing") in [
        (operation.kind, operation.resource_id) for operation in plan.operations
    ]
    assert (OperationKind.WARNING, "syncthing-version") in [
        (operation.kind, operation.resource_id) for operation in plan.operations
    ]
    assert plan.exit_code == 0


def test_audiobookshelf_keeps_media_read_only_and_state_separate() -> None:
    declaration = load_app_declarations(selected=("audiobookshelf",))[0]
    storage = declaration.values["storage"]
    mounts = {item["mount_path"]: item for item in storage["additional_storage"]}

    assert declaration.train == "community"
    assert declaration.values["network"]["web_port"]["port_number"] == 30378
    assert storage["config"]["host_path_config"]["path"].endswith("/apps/audiobookshelf/config")
    assert storage["metadata"]["host_path_config"]["path"].endswith("/apps/audiobookshelf/metadata")
    assert mounts["/backups"]["read_only"] is False
    assert mounts["/books"]["read_only"] is True
    assert mounts["/books"]["host_path_config"]["path"].endswith("/data/books")


def test_app_config_sanitization_removes_every_secret_value() -> None:
    declaration = load_app_declarations(selected=("filebrowser-quantum",))[0]
    config = copy.deepcopy(declaration.values)
    config["filebrowser"]["admin_password"] = "literal-admin-secret"
    config["filebrowser"]["additional_envs"].extend(
        [
            {"name": "FILEBROWSER_OIDC_CLIENT_SECRET", "value": "literal-oidc-secret"},
            {"name": "FILEBROWSER_JWT_TOKEN_SECRET", "value": "literal-jwt-secret"},
        ]
    )

    sanitized = sanitize_app_config(declaration, config)
    serialized = serialize_plan(
        plan_apps(
            (declaration,),
            {
                "apps": [
                    {
                        "name": declaration.app_name,
                        "version": declaration.version,
                        "config": sanitized,
                    }
                ]
            },
        )
    )

    assert "literal-admin-secret" not in json.dumps(sanitized)
    assert "literal-oidc-secret" not in json.dumps(sanitized)
    assert "literal-jwt-secret" not in json.dumps(sanitized)
    assert "literal-admin-secret" not in serialized


def test_app_plan_reports_only_managed_value_path() -> None:
    current = synthetic_state()
    syncthing = next(app for app in current["apps"] if app["name"] == "syncthing")
    syncthing["config"]["resources"]["limits"]["memory"] = 512

    plan = plan_apps(load_app_declarations(), current)
    operation = next(item for item in plan.operations if item.resource_id == "syncthing")

    assert operation.kind is OperationKind.UPDATE
    assert operation.changed_fields == ("resources.limits.memory",)


def test_noop_app_apply_does_not_resolve_secrets_or_write() -> None:
    client = FakeMidcltClient()

    apply_apps(
        load_app_declarations(),
        synthetic_state(),
        cast(MidcltClient, client),
        cast(TrueNASAppFiles, FakeAppFiles()),
        cast(SecretResolver, FailingResolver()),
    )

    assert client.calls == []
