from __future__ import annotations

from ipaddress import ip_address, ip_network

from pydantic import Field, model_validator

from homeserver_iac.models.common import AbsolutePath, StableId, StrictModel, VersionedDesiredState


class NfsService(StrictModel):
    enabled: bool
    running: bool


class NfsShare(StrictModel):
    id: StableId
    path: AbsolutePath
    hosts: tuple[str, ...] = ()
    networks: tuple[str, ...] = ()
    read_only: bool
    enabled: bool
    mapall_user: str = Field(min_length=1)
    mapall_group: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_clients(self) -> NfsShare:
        if not self.hosts and not self.networks:
            raise ValueError("hosts or networks must restrict the NFS export")
        for host in self.hosts:
            ip_address(host)
        for network in self.networks:
            ip_network(network)
        return self


class RetiredNfsShare(StrictModel):
    id: StableId
    path: AbsolutePath


class NfsDesiredState(VersionedDesiredState):
    service: NfsService
    shares: tuple[NfsShare, ...] = Field(min_length=1)
    retire_shares: tuple[RetiredNfsShare, ...] = ()

    @model_validator(mode="after")
    def validate_contract(self) -> NfsDesiredState:
        if self.ownership.scope != "truenas.nfs_shares":
            raise ValueError("ownership.scope must be 'truenas.nfs_shares'")
        ids = [share.id for share in self.shares]
        paths = [share.path for share in self.shares]
        retired_ids = [share.id for share in self.retire_shares]
        retired_paths = [share.path for share in self.retire_shares]
        if len(ids) != len(set(ids)) or len(paths) != len(set(paths)):
            raise ValueError("NFS share IDs and paths must be unique")
        if len(retired_ids) != len(set(retired_ids)) or len(retired_paths) != len(
            set(retired_paths)
        ):
            raise ValueError("retired NFS share IDs and paths must be unique")
        if set(ids) & set(retired_ids) or set(paths) & set(retired_paths):
            raise ValueError("active and retired NFS shares must be disjoint")
        return self
