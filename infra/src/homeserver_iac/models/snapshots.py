from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from homeserver_iac.models.common import StableId, StrictModel, VersionedDesiredState


class SnapshotSchedule(StrictModel):
    minute: str = Field(min_length=1)
    hour: str = Field(min_length=1)
    dom: str = Field(min_length=1)
    month: str = Field(min_length=1)
    dow: str = Field(min_length=1)


class SnapshotTask(StrictModel):
    id: StableId
    name: str = Field(min_length=1, max_length=100)
    lifetime_value: int = Field(gt=0)
    lifetime_unit: Literal["HOUR", "DAY", "WEEK", "MONTH", "YEAR"]
    naming_schema: str = Field(min_length=1)
    schedule: SnapshotSchedule

    @model_validator(mode="after")
    def require_hour_token(self) -> SnapshotTask:
        if "%H" not in self.naming_schema:
            raise ValueError("naming_schema must contain %H for TrueNAS")
        return self


class SnapshotDesiredState(VersionedDesiredState):
    dataset: str = Field(pattern=r"^[^/]+/.+$")
    recursive: bool
    tasks: tuple[SnapshotTask, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_contract(self) -> SnapshotDesiredState:
        if self.ownership.scope != "truenas.periodic_snapshots":
            raise ValueError("ownership.scope must be 'truenas.periodic_snapshots'")
        task_ids = [task.id for task in self.tasks]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("snapshot task IDs must be unique")
        naming_schemas = [task.naming_schema for task in self.tasks]
        if len(naming_schemas) != len(set(naming_schemas)):
            raise ValueError("snapshot naming schemas must be unique")
        return self
