from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from homeserver_iac.models.common import (
    AbsolutePath,
    StableId,
    StrictModel,
    VersionedDesiredStateV2,
)

DeviceId = Annotated[
    str,
    StringConstraints(pattern=r"^(?:[A-Z0-9]{7}-){7}[A-Z0-9]{7}$"),
]


class SyncthingDevice(StrictModel):
    device_id: DeviceId
    name: StableId
    addresses: tuple[str, ...] = Field(min_length=1)
    api_url: str = Field(pattern=r"^https?://")


class SyncthingVersioning(StrictModel):
    type: Literal["", "simple", "staggered", "trashcan", "external"]
    params: dict[str, str] = Field(default_factory=dict)


class SyncthingFolder(StrictModel):
    id: StableId
    label: str = Field(min_length=1, max_length=100)
    truenas_path: AbsolutePath
    truenas_host_path: AbsolutePath
    mac_path: AbsolutePath
    type: Literal["sendreceive", "sendonly", "receiveonly"]
    versioning: SyncthingVersioning


class SyncthingOptions(StrictModel):
    global_announce_enabled: bool = Field(alias="globalAnnounceEnabled")
    local_announce_enabled: bool = Field(alias="localAnnounceEnabled")
    nat_enabled: bool = Field(alias="natEnabled")
    relays_enabled: bool = Field(alias="relaysEnabled")


class SyncthingDesiredState(VersionedDesiredStateV2):
    truenas: SyncthingDevice
    mac: SyncthingDevice
    folders: tuple[SyncthingFolder, ...] = Field(min_length=1)
    options: SyncthingOptions

    @model_validator(mode="after")
    def validate_contract(self) -> SyncthingDesiredState:
        if self.ownership.scope != "sync.syncthing":
            raise ValueError("ownership.scope must be 'sync.syncthing'")
        if self.truenas.device_id == self.mac.device_id:
            raise ValueError("Syncthing device IDs must be unique")
        folder_ids = [folder.id for folder in self.folders]
        if len(folder_ids) != len(set(folder_ids)):
            raise ValueError("Syncthing folder IDs must be unique")
        return self
