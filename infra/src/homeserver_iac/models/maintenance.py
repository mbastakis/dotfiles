from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from homeserver_iac.models.common import StableId, StrictModel, VersionedDesiredState


class ScrubSchedule(StrictModel):
    minute: str = Field(min_length=1)
    hour: str = Field(min_length=1)
    dom: str = Field(min_length=1)
    month: str = Field(min_length=1)
    dow: str = Field(min_length=1)


class SmartTestSchedule(StrictModel):
    hour: str = Field(min_length=1)
    dom: str = Field(min_length=1)
    month: str = Field(min_length=1)
    dow: str = Field(min_length=1)


class ScrubPolicy(StrictModel):
    id: StableId
    threshold: int = Field(ge=1)
    description: str = Field(max_length=200)
    enabled: bool
    schedule: ScrubSchedule


class SmartSelfTest(StrictModel):
    id: StableId
    type: Literal["SHORT", "LONG"]
    desc: str = Field(min_length=1, max_length=200)
    all_disks: Literal[True]
    disks: tuple[str, ...] = Field(max_length=0)
    schedule: SmartTestSchedule


class SmartdService(StrictModel):
    enabled: Literal[True]
    running: Literal[True]


class MaintenanceDesiredState(VersionedDesiredState):
    pool: StableId
    scrub: ScrubPolicy
    smartd: SmartdService
    smart_tests: tuple[SmartSelfTest, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_contract(self) -> MaintenanceDesiredState:
        if self.ownership.scope != "truenas.disk_maintenance":
            raise ValueError("ownership.scope must be 'truenas.disk_maintenance'")
        test_ids = [test.id for test in self.smart_tests]
        if len(test_ids) != len(set(test_ids)):
            raise ValueError("SMART test IDs must be unique")
        test_types = [test.type for test in self.smart_tests]
        if len(test_types) != len(set(test_types)):
            raise ValueError("all-disk SMART test types must be unique")
        return self
