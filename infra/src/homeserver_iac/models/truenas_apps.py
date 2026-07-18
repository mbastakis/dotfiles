from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, StringConstraints, field_validator, model_validator

from homeserver_iac.models.common import (
    AbsolutePath,
    DottedPath,
    EnvironmentName,
    SecretRef,
    StableId,
    StrictModel,
    VersionedDesiredState,
    literal_secret_paths,
)

OctalMode = Annotated[str, StringConstraints(pattern=r"^0[0-7]{3}$")]


class ManagedFile(StrictModel):
    source: str = Field(min_length=1)
    destination: AbsolutePath
    owner: int = Field(ge=0)
    group: int = Field(ge=0)
    mode: OctalMode
    dir_mode: OctalMode
    content_mode: Literal["exact", "yaml-subset"] = "exact"


class PathPermission(StrictModel):
    path: AbsolutePath
    owner: int = Field(ge=0)
    group: int = Field(ge=0)
    mode: OctalMode
    enforce_existing: bool = True


class SecretValueBinding(StrictModel):
    path: DottedPath
    secret_ref: SecretRef
    env: EnvironmentName | None = None


class SecretEnvironmentBinding(StrictModel):
    path: DottedPath
    name: EnvironmentName
    secret_ref: SecretRef
    env: EnvironmentName | None = None


class TrueNASAppDesiredState(VersionedDesiredState):
    app_name: StableId
    catalog_app: StableId
    train: StableId
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    managed_files: tuple[ManagedFile, ...] = ()
    secret_values: tuple[SecretValueBinding, ...] = ()
    secret_envs: tuple[SecretEnvironmentBinding, ...] = ()
    path_permissions: tuple[PathPermission, ...] = ()
    values: dict[str, Any]

    @field_validator("values")
    @classmethod
    def reject_literal_secrets(cls, value: dict[str, Any]) -> dict[str, Any]:
        secret_paths = literal_secret_paths(value)
        if secret_paths:
            raise ValueError(f"literal secret values are forbidden at: {', '.join(secret_paths)}")
        return value

    @model_validator(mode="after")
    def validate_contract(self) -> TrueNASAppDesiredState:
        if self.ownership.scope != "truenas.catalog_apps":
            raise ValueError("ownership.scope must be 'truenas.catalog_apps'")
        binding_ids = [
            *(f"value:{binding.path}" for binding in self.secret_values),
            *(f"env:{binding.path}:{binding.name}" for binding in self.secret_envs),
        ]
        if len(binding_ids) != len(set(binding_ids)):
            raise ValueError("secret value paths and environment bindings must be unique")
        return self
