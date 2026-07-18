from __future__ import annotations

import os
import stat
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from homeserver_iac.models.secrets import SecretMetadataDesiredState
from homeserver_iac.runtime import OperationalError, run_json_command
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.validation import load_model

DEFAULT_SECRET_MAP = INFRA_ROOT / "secrets/homeserver.bws.yaml"
DEFAULT_TIMEOUT = 30.0


def load_secret_metadata(path: Path = DEFAULT_SECRET_MAP) -> SecretMetadataDesiredState:
    return load_model(path, SecretMetadataDesiredState)


def default_bws_command() -> tuple[str, ...]:
    helper = INFRA_ROOT.parent / "bin/chezmoi-bws"
    if helper.is_file() and os.access(helper, os.X_OK):
        return (str(helper),)
    return ("bws",)


class BwsClient:
    def __init__(
        self,
        command: Sequence[str] | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.command = tuple(command or default_bws_command())
        self.timeout = timeout
        self._ids_by_project: dict[str, dict[str, str]] = {}

    def _run(self, *arguments: str) -> Any:
        return run_json_command(
            (*self.command, *arguments, "-o", "json"),
            timeout=self.timeout,
        )

    def secret_ids_by_key(self, project_id: str) -> Mapping[str, str]:
        if project_id not in self._ids_by_project:
            payload = self._run("secret", "list", project_id)
            if not isinstance(payload, list):
                raise OperationalError("BWS secret list returned an unexpected response")
            ids: dict[str, str] = {}
            for item in payload:
                if not isinstance(item, dict):
                    continue
                key = item.get("key")
                secret_id = item.get("id")
                if isinstance(key, str) and isinstance(secret_id, str):
                    ids[key] = secret_id
            self._ids_by_project[project_id] = ids
        return self._ids_by_project[project_id]

    def secret_value(self, secret_id: str) -> str:
        payload = self._run("secret", "get", secret_id)
        if not isinstance(payload, dict):
            raise OperationalError("BWS secret get returned an unexpected response")
        value = payload.get("value")
        if not isinstance(value, str) or not value:
            raise OperationalError("BWS secret resolved to an empty value")
        return value

    def create_secret(self, key: str, value: str, project_id: str, *, note: str) -> str:
        payload = self._run("secret", "create", key, value, project_id, "--note", note)
        if not isinstance(payload, dict) or not isinstance(payload.get("id"), str):
            raise OperationalError("BWS secret create returned an unexpected response")
        return payload["id"]


class SecretResolver:
    def __init__(
        self,
        desired: SecretMetadataDesiredState,
        client: BwsClient,
        *,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self.desired = desired
        self.client = client
        self.environment = environment if environment is not None else os.environ

    def resolve(self, alias: str, fallback_env: str) -> str:
        try:
            metadata = self.desired.secrets[alias]
        except KeyError as error:
            raise OperationalError(f"unknown secret alias: {alias}") from error

        secret_id = str(metadata.id) if metadata.id is not None else ""
        if not secret_id:
            fallback = self.environment.get(fallback_env, "")
            if fallback:
                return fallback
            secret_id = self.client.secret_ids_by_key(str(self.desired.project.id)).get(
                metadata.key, ""
            )
        if not secret_id:
            raise OperationalError(
                f"secret alias '{alias}' has no BWS id and key '{metadata.key}' was not found"
            )
        return self.client.secret_value(secret_id)

    def target_environment(self, target: str) -> dict[str, str]:
        try:
            bindings = self.desired.targets[target]
        except KeyError as error:
            raise OperationalError(f"unknown secret target: {target}") from error
        return {
            env_name: self.resolve(binding.secret_ref.alias, env_name)
            for env_name, binding in bindings.items()
        }


def list_targets(desired: SecretMetadataDesiredState) -> tuple[str, ...]:
    return tuple(desired.targets)


def list_secrets(desired: SecretMetadataDesiredState) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (alias, metadata.key, str(metadata.id) if metadata.id is not None else "")
        for alias, metadata in desired.secrets.items()
    )


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def render_env_file(target: str, values: Mapping[str, str], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=output.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(descriptor, "w") as stream:
            stream.write("# Generated by homeserver-iac. Do not commit.\n")
            stream.write(f"# Target: {target}\n")
            for name, value in sorted(values.items()):
                stream.write(f"export {name}={shell_quote(value)}\n")
        os.replace(temporary, output)
        output.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
