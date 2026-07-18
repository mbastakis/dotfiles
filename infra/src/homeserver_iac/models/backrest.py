from __future__ import annotations

import re
from typing import Literal

from pydantic import Field, field_validator, model_validator

from homeserver_iac.models.common import (
    AbsolutePath,
    DottedPath,
    EnvironmentName,
    SecretRef,
    StableId,
    StrictModel,
    VersionedDesiredState,
)


class BackrestSchedule(StrictModel):
    cron: str = Field(min_length=1)
    clock: Literal["CLOCK_LOCAL", "CLOCK_UTC"]


class BackrestPrunePolicy(StrictModel):
    schedule: BackrestSchedule
    max_unused_percent: int = Field(alias="maxUnusedPercent", ge=0, le=100)


class BackrestCheckPolicy(StrictModel):
    schedule: BackrestSchedule
    structure_only: bool = Field(alias="structureOnly")


class BackrestRepository(StrictModel):
    id: StableId
    uri: str = Field(min_length=1)
    password: Literal[""]
    flags: tuple[str, ...] = Field(min_length=1, max_length=1)
    env: tuple[str, ...] = Field(min_length=1)
    auto_unlock: bool = Field(alias="autoUnlock")
    prune_policy: BackrestPrunePolicy = Field(alias="prunePolicy")
    check_policy: BackrestCheckPolicy = Field(alias="checkPolicy")

    @field_validator("flags")
    @classmethod
    def require_upload_limit(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not re.fullmatch(r"--limit-upload=[1-9][0-9]*", value[0]):
            raise ValueError("repository.flags must contain one positive --limit-upload value")
        return value

    @field_validator("env")
    @classmethod
    def require_environment_placeholders(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        pattern = re.compile(r"^[A-Z][A-Z0-9_]*=\$\{[A-Z][A-Z0-9_]*\}$")
        invalid = [entry for entry in value if not pattern.fullmatch(entry)]
        if invalid:
            raise ValueError("repository.env accepts only NAME=${NAME} placeholders")
        return value


class BackrestTimeBucketedRetention(StrictModel):
    daily: int = Field(ge=0)
    weekly: int = Field(ge=0)
    monthly: int = Field(ge=0)
    yearly: int = Field(ge=0)


class BackrestRetention(StrictModel):
    policy_time_bucketed: BackrestTimeBucketedRetention = Field(alias="policyTimeBucketed")


class BackrestPlan(StrictModel):
    id: StableId
    repo: StableId
    paths: tuple[AbsolutePath, ...] = Field(min_length=1)
    schedule: BackrestSchedule
    retention: BackrestRetention
    skip_if_unchanged: bool = Field(alias="skipIfUnchanged")


class BackrestSecretBinding(StrictModel):
    path: DottedPath
    env: EnvironmentName
    secret_ref: SecretRef


class BackrestDesiredState(VersionedDesiredState):
    repository: BackrestRepository
    secret_refs: tuple[BackrestSecretBinding, ...] = Field(min_length=1)
    repository_clear_fields: tuple[str, ...] = Field(alias="repositoryClearFields", default=())
    plans: tuple[BackrestPlan, ...] = Field(min_length=1)
    retire_plans: tuple[StableId, ...] = Field(alias="retirePlans", default=())

    @model_validator(mode="after")
    def validate_contract(self) -> BackrestDesiredState:
        if self.ownership.scope != "truenas.backrest_policy":
            raise ValueError("ownership.scope must be 'truenas.backrest_policy'")
        plan_ids = [plan.id for plan in self.plans]
        if len(plan_ids) != len(set(plan_ids)):
            raise ValueError("Backrest plan IDs must be unique")
        if any(plan.repo != self.repository.id for plan in self.plans):
            raise ValueError("every Backrest plan must reference repository.id")
        if set(plan_ids) & set(self.retire_plans):
            raise ValueError("active and retired Backrest plan IDs must not overlap")
        refs = {(binding.env, binding.secret_ref.alias) for binding in self.secret_refs}
        for entry in self.repository.env:
            env_name = entry.partition("=")[0]
            if not any(ref_env == env_name for ref_env, _ in refs):
                raise ValueError(f"repository placeholder {env_name} needs a typed secret_ref")
        return self
