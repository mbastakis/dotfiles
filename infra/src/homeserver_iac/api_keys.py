from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import Field

from homeserver_iac.models.common import (
    Operation,
    OperationKind,
    Plan,
    SecretRef,
    StableId,
    StrictModel,
    order_operations,
)
from homeserver_iac.models.secrets import SecretMetadataDesiredState
from homeserver_iac.runtime import OperationalError
from homeserver_iac.secrets import BwsClient
from homeserver_iac.truenas import MidcltClient


class ApiKeyPublication(StrictModel):
    name: StableId
    username: str = Field(min_length=1)
    secret_alias: StableId


def plan_api_key_publication(
    publication: ApiKeyPublication,
    secret_metadata: SecretMetadataDesiredState,
    api_keys: Sequence[Mapping[str, Any]],
    bws_ids_by_key: Mapping[str, str],
) -> Plan:
    try:
        secret = secret_metadata.secrets[publication.secret_alias]
    except KeyError as error:
        raise OperationalError(
            f"unknown API-key publication secret alias: {publication.secret_alias}"
        ) from error
    api_key = next((item for item in api_keys if item.get("name") == publication.name), None)
    bws_secret_id = bws_ids_by_key.get(secret.key, "")
    operations: list[Operation] = []

    if api_key is None and not bws_secret_id:
        operations.extend(
            (
                Operation(
                    kind=OperationKind.CREATE,
                    scope="truenas.api_key_publication",
                    resource_id=f"truenas-{publication.name}",
                    summary="TrueNAS API key will be created",
                ),
                Operation(
                    kind=OperationKind.CREATE,
                    scope="truenas.api_key_publication",
                    resource_id=f"bws-{publication.secret_alias}",
                    summary="Created TrueNAS API key will be published to BWS",
                    secret_refs=(SecretRef(alias=publication.secret_alias),),
                ),
            )
        )
    elif api_key is None or not bws_secret_id:
        operations.append(
            Operation(
                kind=OperationKind.STALE,
                scope="truenas.api_key_publication",
                resource_id=publication.name,
                summary=(
                    "BWS secret exists but the named TrueNAS API key is absent"
                    if api_key is None
                    else "TrueNAS API key exists but its unrecoverable value is absent from BWS"
                ),
                secret_refs=(SecretRef(alias=publication.secret_alias),),
            )
        )
    else:
        operations.extend(
            (
                Operation(
                    kind=OperationKind.UNCHANGED,
                    scope="truenas.api_key_publication",
                    resource_id=f"truenas-{publication.name}",
                    summary="TrueNAS API key exists",
                ),
                Operation(
                    kind=OperationKind.UNCHANGED,
                    scope="truenas.api_key_publication",
                    resource_id=f"bws-{publication.secret_alias}",
                    summary="BWS API-key secret exists",
                    secret_refs=(SecretRef(alias=publication.secret_alias),),
                ),
            )
        )
        if api_key.get("username") != publication.username or api_key.get("revoked") is True:
            operations.append(
                Operation(
                    kind=OperationKind.STALE,
                    scope="truenas.api_key_publication",
                    resource_id=f"truenas-{publication.name}-metadata",
                    summary="TrueNAS API key metadata requires operator-managed rotation",
                )
            )
    return Plan(operations=order_operations(operations))


def apply_api_key_publication(
    publication: ApiKeyPublication,
    secret_metadata: SecretMetadataDesiredState,
    api_keys: Sequence[Mapping[str, Any]],
    bws_ids_by_key: Mapping[str, str],
    truenas: MidcltClient,
    bws: BwsClient,
) -> Plan:
    plan = plan_api_key_publication(publication, secret_metadata, api_keys, bws_ids_by_key)
    creates = [operation for operation in plan.operations if operation.kind is OperationKind.CREATE]
    stale = [operation for operation in plan.operations if operation.kind is OperationKind.STALE]
    if stale:
        raise OperationalError("API-key publication is inconsistent and requires operator rotation")
    if not creates:
        return plan

    secret = secret_metadata.secrets[publication.secret_alias]
    created = truenas.call(
        "api_key.create",
        {"name": publication.name, "username": publication.username},
    )
    if not isinstance(created, Mapping):
        raise OperationalError("TrueNAS api_key.create returned an unexpected response")
    key_value = created.get("key") or created.get("api_key")
    key_id = created.get("id")
    if not isinstance(key_value, str) or not key_value or not isinstance(key_id, int):
        raise OperationalError("TrueNAS api_key.create returned no usable key")
    try:
        bws.create_secret(
            secret.key,
            key_value,
            str(secret_metadata.project.id),
            note="Created by homeserver-iac TrueNAS API-key publication",
        )
    except OperationalError as publication_error:
        try:
            truenas.call("api_key.delete", key_id)
        except OperationalError as rollback_error:
            raise OperationalError(
                "BWS publication failed and the just-created TrueNAS API key could not be removed"
            ) from rollback_error
        raise OperationalError(
            "BWS publication failed; the just-created TrueNAS API key was removed"
        ) from publication_error
    return plan
