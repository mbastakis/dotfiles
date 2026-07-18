from __future__ import annotations

import re

from pydantic import Field, model_validator

from homeserver_iac.models.common import AbsolutePath, StableId, StrictModel, VersionedDesiredState

_SMB_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SMB_ACCOUNT = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*\$?$")


class SmbService(StrictModel):
    enabled: bool
    running: bool


class SmbShare(StrictModel):
    id: StableId
    name: str = Field(min_length=1, max_length=80)
    path: AbsolutePath
    comment: str = Field(max_length=120)
    read_only: bool
    browsable: bool
    enabled: bool
    allowed_users: tuple[str, ...] = Field(min_length=1)
    force_user: str = Field(min_length=1)
    force_group: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_share(self) -> SmbShare:
        if not _SMB_NAME.fullmatch(self.name):
            raise ValueError("name must contain only SMB-safe characters")
        accounts = (*self.allowed_users, self.force_user, self.force_group)
        if any(not _SMB_ACCOUNT.fullmatch(account) for account in accounts):
            raise ValueError("SMB account names contain unsupported characters")
        if len(self.allowed_users) != len(set(self.allowed_users)):
            raise ValueError("allowed_users must be unique")
        return self


class RetiredSmbShare(StrictModel):
    id: StableId
    name: str = Field(min_length=1, max_length=80)


class SmbDesiredState(VersionedDesiredState):
    service: SmbService
    shares: tuple[SmbShare, ...] = Field(min_length=1)
    retire_shares: tuple[RetiredSmbShare, ...] = ()

    @model_validator(mode="after")
    def validate_contract(self) -> SmbDesiredState:
        if self.ownership.scope != "truenas.smb_shares":
            raise ValueError("ownership.scope must be 'truenas.smb_shares'")
        ids = [share.id for share in self.shares]
        names = [share.name.casefold() for share in self.shares]
        retired_ids = [share.id for share in self.retire_shares]
        retired_names = [share.name.casefold() for share in self.retire_shares]
        if len(ids) != len(set(ids)) or len(names) != len(set(names)):
            raise ValueError("SMB share IDs and names must be unique")
        if len(retired_ids) != len(set(retired_ids)) or len(retired_names) != len(
            set(retired_names)
        ):
            raise ValueError("retired SMB share IDs and names must be unique")
        if set(ids) & set(retired_ids) or set(names) & set(retired_names):
            raise ValueError("active and retired SMB shares must be disjoint")
        return self
