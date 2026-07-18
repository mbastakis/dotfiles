from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from homeserver_iac.models.audiobookshelf import AudiobookshelfDesiredState
from homeserver_iac.models.common import (
    Operation,
    OperationKind,
    Plan,
    order_operations,
)
from homeserver_iac.runtime import OperationalError
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.validation import load_model

DEFAULT_AUDIOBOOKSHELF_CONFIG = INFRA_ROOT / "truenas/audiobookshelf/audiobookshelf.yaml"
DEFAULT_AUDIOBOOKSHELF_URL = "http://192.168.1.74:30378"


def load_audiobookshelf_desired(
    path: Path = DEFAULT_AUDIOBOOKSHELF_CONFIG,
) -> AudiobookshelfDesiredState:
    return load_model(path, AudiobookshelfDesiredState)


class AudiobookshelfClient:
    def __init__(self, base_url: str, *, timeout: float = 20.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
        *,
        token: str | None = None,
    ) -> Any:
        headers = {"Accept": "application/json"}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload, separators=(",", ":")).encode()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(
            urllib.parse.urljoin(f"{self.base_url}/", path.lstrip("/")),
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as error:
            raise OperationalError(
                f"Audiobookshelf {method} {path} failed with HTTP {error.code}"
            ) from error
        except (TimeoutError, urllib.error.URLError) as error:
            raise OperationalError(f"Audiobookshelf {method} {path} request failed") from error
        if not body:
            return None
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return body.decode(errors="replace")

    def status(self) -> dict[str, Any]:
        result = self.request("GET", "/status")
        if not isinstance(result, dict):
            raise OperationalError("Audiobookshelf status returned an unexpected response")
        return result

    def initialize(self, username: str, password: str) -> None:
        self.request(
            "POST",
            "/init",
            {"newRoot": {"username": username, "password": password}},
        )

    def login(self, username: str, password: str) -> tuple[str, dict[str, Any]]:
        result = self.request("POST", "/login", {"username": username, "password": password})
        if not isinstance(result, dict):
            raise OperationalError("Audiobookshelf login returned an unexpected response")
        user = result.get("user")
        token = user.get("accessToken") if isinstance(user, dict) else None
        if not isinstance(token, str) or not token:
            raise OperationalError("Audiobookshelf login did not return an access token")
        return token, result

    def libraries(self, token: str) -> list[dict[str, Any]]:
        result = self.request("GET", "/api/libraries", token=token)
        libraries = result.get("libraries") if isinstance(result, dict) else None
        if not isinstance(libraries, list) or not all(isinstance(item, dict) for item in libraries):
            raise OperationalError("Audiobookshelf libraries returned an unexpected response")
        return libraries

    def auth_settings(self, token: str) -> dict[str, Any]:
        result = self.request("GET", "/api/auth-settings", token=token)
        if not isinstance(result, dict):
            raise OperationalError("Audiobookshelf auth settings returned an unexpected response")
        return result

    def create_library(self, payload: Mapping[str, Any], token: str) -> None:
        self.request("POST", "/api/libraries", payload, token=token)

    def update_library(self, library_id: str, payload: Mapping[str, Any], token: str) -> None:
        self.request("PATCH", f"/api/libraries/{library_id}", payload, token=token)

    def update_settings(self, payload: Mapping[str, Any], token: str) -> None:
        self.request("PATCH", "/api/settings", payload, token=token)

    def update_sorting_prefixes(self, prefixes: tuple[str, ...], token: str) -> None:
        self.request(
            "PATCH",
            "/api/sorting-prefixes",
            {"sortingPrefixes": list(prefixes)},
            token=token,
        )

    def update_auth_settings(self, payload: Mapping[str, Any], token: str) -> None:
        self.request("PATCH", "/api/auth-settings", payload, token=token)


def discover_openid(issuer_url: str, *, timeout: float = 20.0) -> dict[str, Any]:
    url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
        raise OperationalError("Audiobookshelf OpenID discovery request failed") from error
    try:
        result = json.loads(body)
    except json.JSONDecodeError as error:
        raise OperationalError("Audiobookshelf OpenID discovery returned invalid JSON") from error
    required = (
        "issuer",
        "authorization_endpoint",
        "token_endpoint",
        "userinfo_endpoint",
        "jwks_uri",
    )
    if not isinstance(result, dict) or any(
        not isinstance(result.get(key), str) for key in required
    ):
        raise OperationalError("Audiobookshelf OpenID discovery response is incomplete")
    return result


def _library_folders(library: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    folders = library.get("folders", library.get("libraryFolders", []))
    if not isinstance(folders, list):
        return []
    return [folder for folder in folders if isinstance(folder, Mapping)]


def _folder_path(folder: Mapping[str, Any]) -> str | None:
    path = folder.get("path", folder.get("fullPath"))
    return path if isinstance(path, str) else None


def find_managed_library(
    desired: AudiobookshelfDesiredState, libraries: list[dict[str, Any]]
) -> dict[str, Any] | None:
    path_matches = [
        library
        for library in libraries
        if any(
            _folder_path(folder) == desired.library.folder for folder in _library_folders(library)
        )
    ]
    if len(path_matches) > 1:
        raise OperationalError("multiple Audiobookshelf libraries use the managed folder")
    if path_matches:
        return path_matches[0]
    name_matches = [library for library in libraries if library.get("name") == desired.library.name]
    if len(name_matches) > 1:
        raise OperationalError("multiple Audiobookshelf libraries use the managed name")
    return name_matches[0] if name_matches else None


def desired_library_payload(desired: AudiobookshelfDesiredState) -> dict[str, Any]:
    return {
        "name": desired.library.name,
        "mediaType": desired.library.media_type,
        "folders": [{"fullPath": desired.library.folder}],
        "provider": desired.library.provider,
        "settings": desired.library.settings.model_dump(by_alias=True, mode="json"),
    }


def desired_server_settings_payload(desired: AudiobookshelfDesiredState) -> dict[str, Any]:
    return desired.server_settings.model_dump(by_alias=True, mode="json")


def desired_backup_payload(desired: AudiobookshelfDesiredState) -> dict[str, Any]:
    return {
        "backupSchedule": desired.backup.schedule,
        "backupsToKeep": desired.backup.backups_to_keep,
        "maxBackupSize": desired.backup.max_backup_size,
    }


def desired_openid_payload(
    desired: AudiobookshelfDesiredState,
    discovery: Mapping[str, Any],
    client_secret: str,
) -> dict[str, Any]:
    algorithms = discovery.get("id_token_signing_alg_values_supported", [])
    if not isinstance(algorithms, list) or desired.openid.signing_algorithm not in algorithms:
        raise OperationalError(
            f"OpenID provider does not advertise {desired.openid.signing_algorithm} signing"
        )
    return {
        "authActiveAuthMethods": list(desired.openid.active_auth_methods),
        "authOpenIDIssuerURL": discovery["issuer"],
        "authOpenIDAuthorizationURL": discovery["authorization_endpoint"],
        "authOpenIDTokenURL": discovery["token_endpoint"],
        "authOpenIDUserInfoURL": discovery["userinfo_endpoint"],
        "authOpenIDJwksURL": discovery["jwks_uri"],
        "authOpenIDLogoutURL": discovery.get("end_session_endpoint"),
        "authOpenIDClientID": desired.openid.client_id,
        "authOpenIDClientSecret": client_secret,
        "authOpenIDTokenSigningAlgorithm": desired.openid.signing_algorithm,
        "authOpenIDButtonText": desired.openid.button_text,
        "authOpenIDAutoLaunch": desired.openid.auto_launch,
        "authOpenIDAutoRegister": desired.openid.auto_register,
        "authOpenIDMatchExistingBy": desired.openid.match_existing_by,
        "authOpenIDMobileRedirectURIs": list(desired.openid.mobile_redirect_uris),
        "authOpenIDGroupClaim": desired.openid.group_claim,
        "authOpenIDAdvancedPermsClaim": "",
        "authOpenIDSubfolderForRedirectURLs": desired.openid.redirect_subfolder,
    }


def read_audiobookshelf_state(
    desired: AudiobookshelfDesiredState,
    client: AudiobookshelfClient,
    root_password: str,
) -> dict[str, Any]:
    status = client.status()
    if status.get("isInit") is not True:
        return {"initialized": False}
    token, login = client.login(desired.root_user.username, root_password)
    server_settings = login.get("serverSettings")
    if not isinstance(server_settings, dict):
        raise OperationalError("Audiobookshelf login omitted server settings")
    return {
        "initialized": True,
        "token": token,
        "libraries": client.libraries(token),
        "server_settings": server_settings,
        "auth_settings": client.auth_settings(token),
    }


def _changed_fields(desired: Mapping[str, Any], current: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(key for key, value in desired.items() if current.get(key) != value))


def plan_audiobookshelf(
    desired: AudiobookshelfDesiredState,
    current: Mapping[str, Any],
    discovery: Mapping[str, Any] | None,
    oidc_client_secret: str,
) -> Plan:
    root_ref = desired.root_user.password
    oidc_ref = desired.openid.client_secret
    if current.get("initialized") is not True:
        return Plan(
            operations=order_operations(
                [
                    Operation(
                        kind=OperationKind.CREATE,
                        scope=desired.ownership.scope,
                        resource_id="root-user",
                        summary="Audiobookshelf requires initial root bootstrap",
                        secret_refs=(root_ref,),
                    ),
                    Operation(
                        kind=OperationKind.CREATE,
                        scope=desired.ownership.scope,
                        resource_id="books-library",
                        summary="Books library will be created after bootstrap",
                    ),
                    Operation(
                        kind=OperationKind.CREATE,
                        scope=desired.ownership.scope,
                        resource_id="backup-policy",
                        summary="Built-in backup policy will be configured after bootstrap",
                    ),
                    Operation(
                        kind=OperationKind.CREATE,
                        scope=desired.ownership.scope,
                        resource_id="server-settings",
                        summary="Server and scanner settings will be configured after bootstrap",
                    ),
                    Operation(
                        kind=OperationKind.CREATE,
                        scope=desired.ownership.scope,
                        resource_id="openid",
                        summary="Native OpenID authentication will be configured after bootstrap",
                        secret_refs=(oidc_ref,),
                    ),
                ]
            )
        )

    if discovery is None:
        raise OperationalError("OpenID discovery is required for initialized Audiobookshelf")
    operations = [
        Operation(
            kind=OperationKind.UNCHANGED,
            scope=desired.ownership.scope,
            resource_id="root-user",
            summary="Audiobookshelf root bootstrap is complete",
            secret_refs=(root_ref,),
        )
    ]

    libraries = current.get("libraries")
    if not isinstance(libraries, list) or not all(isinstance(item, dict) for item in libraries):
        raise OperationalError("Audiobookshelf current library state is invalid")
    library = find_managed_library(desired, libraries)
    if library is None:
        library_kind = OperationKind.CREATE
        library_fields: tuple[str, ...] = ()
        library_summary = "Books library is absent"
    else:
        wanted_settings = desired.library.settings.model_dump(by_alias=True, mode="json")
        current_settings = library.get("settings")
        if not isinstance(current_settings, Mapping):
            current_settings = {}
        current_library = {
            "name": library.get("name"),
            "mediaType": library.get("mediaType"),
            "folders": sorted(
                path
                for folder in _library_folders(library)
                if (path := _folder_path(folder)) is not None
            ),
            "provider": library.get("provider"),
            "settings": {key: current_settings.get(key) for key in wanted_settings},
        }
        wanted_library = {
            "name": desired.library.name,
            "mediaType": desired.library.media_type,
            "folders": [desired.library.folder],
            "provider": desired.library.provider,
            "settings": wanted_settings,
        }
        library_fields = _changed_fields(wanted_library, current_library)
        library_kind = OperationKind.UPDATE if library_fields else OperationKind.UNCHANGED
        library_summary = (
            "Books library differs from desired state"
            if library_fields
            else "Books library is current"
        )
    operations.append(
        Operation(
            kind=library_kind,
            scope=desired.ownership.scope,
            resource_id="books-library",
            summary=library_summary,
            changed_fields=library_fields,
        )
    )

    server_settings = current.get("server_settings")
    auth_settings = current.get("auth_settings")
    if not isinstance(server_settings, Mapping) or not isinstance(auth_settings, Mapping):
        raise OperationalError("Audiobookshelf current settings state is invalid")
    server_settings_fields = _changed_fields(
        desired_server_settings_payload(desired), server_settings
    )
    operations.append(
        Operation(
            kind=OperationKind.UPDATE if server_settings_fields else OperationKind.UNCHANGED,
            scope=desired.ownership.scope,
            resource_id="server-settings",
            summary=(
                "Server or scanner settings differ from desired state"
                if server_settings_fields
                else "Server and scanner settings are current"
            ),
            changed_fields=server_settings_fields,
        )
    )
    backup_fields = _changed_fields(desired_backup_payload(desired), server_settings)
    operations.append(
        Operation(
            kind=OperationKind.UPDATE if backup_fields else OperationKind.UNCHANGED,
            scope=desired.ownership.scope,
            resource_id="backup-policy",
            summary=(
                "Built-in backup policy differs from desired state"
                if backup_fields
                else "Built-in backup policy is current"
            ),
            changed_fields=backup_fields,
        )
    )
    openid_fields = _changed_fields(
        desired_openid_payload(desired, discovery, oidc_client_secret), auth_settings
    )
    operations.append(
        Operation(
            kind=OperationKind.UPDATE if openid_fields else OperationKind.UNCHANGED,
            scope=desired.ownership.scope,
            resource_id="openid",
            summary=(
                "Native OpenID authentication differs from desired state"
                if openid_fields
                else "Native OpenID authentication is current"
            ),
            changed_fields=openid_fields,
            secret_refs=(oidc_ref,),
        )
    )
    return Plan(operations=order_operations(operations))


def apply_audiobookshelf(
    desired: AudiobookshelfDesiredState,
    current: Mapping[str, Any],
    client: AudiobookshelfClient,
    root_password: str,
    oidc_client_secret: str,
) -> Plan:
    initial_discovery = (
        discover_openid(desired.openid.issuer_url) if current.get("initialized") is True else None
    )
    initial_plan = plan_audiobookshelf(desired, current, initial_discovery, oidc_client_secret)
    if current.get("initialized") is not True:
        client.initialize(desired.root_user.username, root_password)
        current = read_audiobookshelf_state(desired, client, root_password)

    discovery = discover_openid(desired.openid.issuer_url)
    plan = plan_audiobookshelf(desired, current, discovery, oidc_client_secret)
    token = current.get("token")
    if not isinstance(token, str) or not token:
        raise OperationalError("Audiobookshelf apply has no access token")

    operations = {operation.resource_id: operation for operation in plan.operations}
    library_operation = operations["books-library"]
    if library_operation.kind is OperationKind.CREATE:
        client.create_library(desired_library_payload(desired), token)
    elif library_operation.kind is OperationKind.UPDATE:
        libraries = current.get("libraries")
        if not isinstance(libraries, list):
            raise OperationalError("Audiobookshelf apply has invalid library state")
        library = find_managed_library(desired, libraries)
        if library is None:
            raise OperationalError("Audiobookshelf managed library disappeared before update")
        library_id = library.get("id")
        if not isinstance(library_id, str):
            raise OperationalError("Audiobookshelf managed library has no stable ID")
        library_payload = desired_library_payload(desired)
        if "folders" not in library_operation.changed_fields:
            del library_payload["folders"]
        else:
            current_folders = _library_folders(library)
            if len(current_folders) == 1 and isinstance(current_folders[0].get("id"), str):
                library_payload["folders"][0]["id"] = current_folders[0]["id"]
        client.update_library(library_id, library_payload, token)
    if operations["server-settings"].kind is OperationKind.UPDATE:
        server_payload = desired_server_settings_payload(desired)
        prefixes = tuple(server_payload.pop("sortingPrefixes"))
        client.update_settings(server_payload, token)
        server_settings = current.get("server_settings")
        if not isinstance(server_settings, Mapping):
            raise OperationalError("Audiobookshelf apply has invalid server settings")
        if server_settings.get("sortingPrefixes") != list(prefixes):
            client.update_sorting_prefixes(prefixes, token)
    if operations["backup-policy"].kind is OperationKind.UPDATE:
        client.update_settings(desired_backup_payload(desired), token)
    if operations["openid"].kind is OperationKind.UPDATE:
        client.update_auth_settings(
            desired_openid_payload(desired, discovery, oidc_client_secret), token
        )

    verified = read_audiobookshelf_state(desired, client, root_password)
    verification = plan_audiobookshelf(desired, verified, discovery, oidc_client_secret)
    mutating = {OperationKind.CREATE, OperationKind.UPDATE, OperationKind.DELETE}
    if any(operation.kind in mutating for operation in verification.operations):
        raise OperationalError("Audiobookshelf accepted configuration but managed drift remains")
    return initial_plan
