from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from homeserver_iac.models.common import (
    EnvironmentName,
    OwnershipScope,
    SecretRef,
    StableId,
    StrictModel,
    VersionedDesiredState,
)


class SecretLifecycle(StrEnum):
    OPERATOR_CREATED = "operator-created"
    GENERATED = "generated"
    STACK_OUTPUT = "stack-output"


class SecretProject(StrictModel):
    name: StableId
    id: UUID


class SecretMetadata(StrictModel):
    key: str = Field(pattern=r"^homeserver/.+")
    id: UUID | None
    owner: OwnershipScope
    lifecycle: SecretLifecycle
    consumers: list[StableId] = Field(min_length=1)
    generation_method: str = Field(min_length=1)
    rotation_runbook: str = Field(pattern=r"^docs/runbooks/.+\.md(?:#.+)?$")
    purpose: str = Field(min_length=1)


class SecretTargetBinding(StrictModel):
    secret_ref: SecretRef


class SecretMetadataDesiredState(VersionedDesiredState):
    project: SecretProject
    secrets: dict[StableId, SecretMetadata] = Field(min_length=1)
    targets: dict[StableId, dict[EnvironmentName, SecretTargetBinding]] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_contract(self) -> SecretMetadataDesiredState:
        if self.ownership.scope != "secrets.bws_metadata":
            raise ValueError("ownership.scope must be 'secrets.bws_metadata'")
        known_aliases = set(self.secrets)
        missing_aliases = sorted(
            {
                binding.secret_ref.alias
                for target in self.targets.values()
                for binding in target.values()
                if binding.secret_ref.alias not in known_aliases
            }
        )
        if missing_aliases:
            raise ValueError(
                f"targets reference unknown secret aliases: {', '.join(missing_aliases)}"
            )
        secret_ids = [secret.id for secret in self.secrets.values() if secret.id is not None]
        if len(secret_ids) != len(set(secret_ids)):
            raise ValueError("non-empty BWS secret IDs must be unique")
        for alias, secret in self.secrets.items():
            bound_consumers = {
                target
                for target, bindings in self.targets.items()
                if any(binding.secret_ref.alias == alias for binding in bindings.values())
            }
            if set(secret.consumers) != bound_consumers:
                raise ValueError(
                    f"secret {alias!r} consumers must match its target bindings: "
                    f"{', '.join(sorted(bound_consumers))}"
                )
        return self
