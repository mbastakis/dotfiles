from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from homeserver_iac.models import (
    AudiobookshelfDesiredState,
    BackrestDesiredState,
    MaintenanceDesiredState,
    NfsDesiredState,
    OpenWrtDesiredState,
    SecretMetadataDesiredState,
    SmbDesiredState,
    SnapshotDesiredState,
    SyncthingDesiredState,
    TrueNASAppDesiredState,
)
from homeserver_iac.models.common import SecretRef
from homeserver_iac.schema import INFRA_ROOT


class DesiredStateValidationError(Exception):
    pass


def desired_state_files() -> tuple[Path, ...]:
    app_files = tuple(sorted((INFRA_ROOT / "truenas/apps/declarations").glob("*.yaml")))
    return (
        *app_files,
        INFRA_ROOT / "truenas/snapshots/snapshot-tasks.yaml",
        INFRA_ROOT / "truenas/snapshots/photo-snapshot-tasks.yaml",
        INFRA_ROOT / "truenas/snapshots/audiobookshelf-snapshot-tasks.yaml",
        INFRA_ROOT / "truenas/snapshots/books-snapshot-tasks.yaml",
        INFRA_ROOT / "truenas/shares/nfs-shares.yaml",
        INFRA_ROOT / "truenas/shares/smb-shares.yaml",
        INFRA_ROOT / "truenas/backrest/backrest-plans.yaml",
        INFRA_ROOT / "truenas/maintenance/maintenance.yaml",
        INFRA_ROOT / "truenas/audiobookshelf/audiobookshelf.yaml",
        INFRA_ROOT / "sync/syncthing/config.yaml",
        INFRA_ROOT / "network/openwrt/router.yaml",
        INFRA_ROOT / "secrets/homeserver.bws.yaml",
    )


def model_for_path(path: Path) -> type[BaseModel]:
    resolved = path.resolve()
    if resolved.parent == (INFRA_ROOT / "truenas/apps/declarations").resolve():
        return TrueNASAppDesiredState
    models: dict[Path, type[BaseModel]] = {
        (INFRA_ROOT / "truenas/snapshots/snapshot-tasks.yaml").resolve(): SnapshotDesiredState,
        (
            INFRA_ROOT / "truenas/snapshots/photo-snapshot-tasks.yaml"
        ).resolve(): SnapshotDesiredState,
        (
            INFRA_ROOT / "truenas/snapshots/audiobookshelf-snapshot-tasks.yaml"
        ).resolve(): SnapshotDesiredState,
        (
            INFRA_ROOT / "truenas/snapshots/books-snapshot-tasks.yaml"
        ).resolve(): SnapshotDesiredState,
        (INFRA_ROOT / "truenas/shares/nfs-shares.yaml").resolve(): NfsDesiredState,
        (INFRA_ROOT / "truenas/shares/smb-shares.yaml").resolve(): SmbDesiredState,
        (INFRA_ROOT / "truenas/backrest/backrest-plans.yaml").resolve(): BackrestDesiredState,
        (INFRA_ROOT / "truenas/maintenance/maintenance.yaml").resolve(): MaintenanceDesiredState,
        (
            INFRA_ROOT / "truenas/audiobookshelf/audiobookshelf.yaml"
        ).resolve(): AudiobookshelfDesiredState,
        (INFRA_ROOT / "sync/syncthing/config.yaml").resolve(): SyncthingDesiredState,
        (INFRA_ROOT / "network/openwrt/router.yaml").resolve(): OpenWrtDesiredState,
        (INFRA_ROOT / "secrets/homeserver.bws.yaml").resolve(): SecretMetadataDesiredState,
    }
    try:
        return models[resolved]
    except KeyError as error:
        raise DesiredStateValidationError(
            f"no desired-state model registered for {path}"
        ) from error


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as error:
        raise DesiredStateValidationError(f"{path}: could not load YAML: {error}") from error


def format_validation_error(path: Path, error: ValidationError) -> DesiredStateValidationError:
    messages = []
    for detail in error.errors(include_input=False, include_url=False):
        location = ".".join(str(part) for part in detail["loc"]) or "document"
        messages.append(f"{path}: {location}: {detail['msg']}")
    return DesiredStateValidationError("\n".join(messages))


def load_model[ModelT: BaseModel](path: Path, model: type[ModelT]) -> ModelT:
    try:
        return model.model_validate(load_yaml(path))
    except ValidationError as error:
        raise format_validation_error(path, error) from None


def validate_path(path: Path) -> BaseModel:
    return load_model(path, model_for_path(path))


def iter_secret_refs(model: BaseModel) -> tuple[SecretRef, ...]:
    refs: list[SecretRef] = []

    def visit(value: Any) -> None:
        if isinstance(value, SecretRef):
            refs.append(value)
        elif isinstance(value, BaseModel):
            for field_name in type(value).model_fields:
                visit(getattr(value, field_name))
        elif isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)

    visit(model)
    return tuple(refs)


def validate_desired_state(paths: tuple[Path, ...] | None = None) -> tuple[Path, ...]:
    selected_paths = paths or desired_state_files()
    documents = {path: validate_path(path) for path in selected_paths}

    secret_path = INFRA_ROOT / "secrets/homeserver.bws.yaml"
    secret_document = documents.get(secret_path)
    if secret_document is None:
        secret_document = validate_path(secret_path)
    if not isinstance(secret_document, SecretMetadataDesiredState):
        raise DesiredStateValidationError("secret metadata model registration is invalid")

    known_aliases = set(secret_document.secrets)
    for path, document in documents.items():
        if isinstance(document, SecretMetadataDesiredState):
            continue
        missing = sorted({ref.alias for ref in iter_secret_refs(document)} - known_aliases)
        if missing:
            raise DesiredStateValidationError(
                f"{path}: secret_ref: unknown aliases: {', '.join(missing)}"
            )

    return tuple(documents)
