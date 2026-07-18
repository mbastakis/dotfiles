from __future__ import annotations

import copy
import json
import os
import shlex
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from homeserver_iac.models.common import Operation, OperationKind, Plan, order_operations
from homeserver_iac.models.syncthing import SyncthingDesiredState, SyncthingFolder
from homeserver_iac.runtime import OperationalError, run_command
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.validation import load_model

SyncthingHost = Literal["mac", "truenas"]
DEFAULT_SYNCTHING_CONFIG = INFRA_ROOT / "sync/syncthing/config.yaml"
DEFAULT_STIGNORE = INFRA_ROOT / "sync/syncthing/stignore"
DEFAULT_TRUENAS_CONFIG_XML = "/mnt/pool_4tb/homeserver/apps/syncthing/config/config/config.xml"


def load_syncthing_desired(path: Path = DEFAULT_SYNCTHING_CONFIG) -> SyncthingDesiredState:
    return load_model(path, SyncthingDesiredState)


def _api_key_from_xml(content: str) -> str:
    try:
        root = ET.fromstring(content)
    except ET.ParseError as error:
        raise OperationalError("Syncthing config.xml is invalid") from error
    api_key = root.findtext(".//apikey", default="").strip()
    if not api_key:
        raise OperationalError("Syncthing config.xml contains no API key")
    return api_key


def read_syncthing_api_key(host: SyncthingHost, *, ssh_host: str = "truenas") -> str:
    if host == "truenas":
        remote_config_path = os.environ.get(
            "SYNCTHING_TRUENAS_CONFIG_XML", DEFAULT_TRUENAS_CONFIG_XML
        )
        content = run_command(
            (
                "ssh",
                "-n",
                "-o",
                "ConnectTimeout=10",
                ssh_host,
                f"sudo cat {shlex.quote(remote_config_path)}",
            ),
            timeout=20.0,
        )
        return _api_key_from_xml(content)

    candidates = (
        Path.home() / "Library/Application Support/Syncthing/config.xml",
        Path.home() / ".config/syncthing/config.xml",
    )
    local_config_path = next((path for path in candidates if path.is_file()), None)
    if local_config_path is None:
        raise OperationalError("Syncthing config.xml was not found for mac")
    return _api_key_from_xml(local_config_path.read_text())


class SyncthingClient:
    def __init__(self, base_url: str, api_key: str, *, timeout: float = 20.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def request(self, method: str, path: str, payload: Any = None) -> Any:
        data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json", "X-API-Key": self.api_key},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as error:
            raise OperationalError(
                f"Syncthing {method} {path} failed with HTTP {error.code}"
            ) from error
        except (TimeoutError, urllib.error.URLError) as error:
            raise OperationalError(f"Syncthing {method} {path} request failed") from error
        if not body:
            return None
        try:
            return json.loads(body)
        except json.JSONDecodeError as error:
            raise OperationalError(f"Syncthing {method} {path} returned invalid JSON") from error

    def get(self, path: str) -> Any:
        return self.request("GET", path)

    def post(self, path: str, payload: Mapping[str, Any]) -> None:
        self.request("POST", path, payload)

    def put(self, path: str, payload: Mapping[str, Any]) -> None:
        self.request("PUT", path, payload)


class SyncthingIgnoreFiles:
    def __init__(
        self,
        host: SyncthingHost,
        *,
        ssh_host: str = "truenas",
        source: Path = DEFAULT_STIGNORE,
    ) -> None:
        self.host = host
        self.ssh_host = ssh_host
        self.source = source

    def desired_content(self) -> str:
        try:
            return self.source.read_text()
        except OSError as error:
            raise OperationalError(
                f"Syncthing ignore source could not be read: {self.source}"
            ) from error

    def read(self, folder: SyncthingFolder) -> str:
        if self.host == "mac":
            local_path = Path(folder.mac_path) / ".stignore"
            return local_path.read_text() if local_path.is_file() else ""
        remote_path = str(Path(folder.truenas_host_path) / ".stignore")
        command = (
            f"if sudo test -f {shlex.quote(remote_path)}; "
            f"then sudo cat {shlex.quote(remote_path)}; fi"
        )
        return run_command(
            ("ssh", "-n", "-o", "ConnectTimeout=10", self.ssh_host, command),
            timeout=20.0,
        )

    def write(self, folder: SyncthingFolder, content: str) -> None:
        if self.host == "mac":
            local_path = Path(folder.mac_path) / ".stignore"
            local_path.write_text(content)
            return
        remote_path = str(Path(folder.truenas_host_path) / ".stignore")
        command = (
            f"sudo tee {shlex.quote(remote_path)} >/dev/null"
            f" && sudo chown apps:apps {shlex.quote(remote_path)}"
            f" && sudo chmod 0644 {shlex.quote(remote_path)}"
        )
        run_command(
            ("ssh", "-o", "ConnectTimeout=10", self.ssh_host, command),
            timeout=20.0,
            input_text=content,
        )


def read_syncthing_state(
    desired: SyncthingDesiredState,
    client: SyncthingClient,
    ignore_files: SyncthingIgnoreFiles,
) -> dict[str, Any]:
    options = client.get("/rest/config/options")
    devices = client.get("/rest/config/devices")
    folders = client.get("/rest/config/folders")
    if (
        not isinstance(options, dict)
        or not isinstance(devices, list)
        or not isinstance(folders, list)
    ):
        raise OperationalError("Syncthing config API returned an unexpected response")
    return {
        "options": options,
        "devices": devices,
        "folders": folders,
        "ignore_files": {folder.id: ignore_files.read(folder) for folder in desired.folders},
    }


def _host_devices(desired: SyncthingDesiredState, host: SyncthingHost) -> tuple[Any, Any]:
    local = desired.truenas if host == "truenas" else desired.mac
    remote = desired.mac if host == "truenas" else desired.truenas
    return local, remote


def desired_device(desired: SyncthingDesiredState, host: SyncthingHost) -> dict[str, Any]:
    _, remote = _host_devices(desired, host)
    return {
        "deviceID": remote.device_id,
        "name": remote.name,
        "addresses": list(remote.addresses),
        "compression": "metadata",
        "introducer": False,
    }


def desired_folder(
    desired: SyncthingDesiredState,
    folder: SyncthingFolder,
    host: SyncthingHost,
) -> dict[str, Any]:
    local, remote = _host_devices(desired, host)
    path = folder.truenas_path if host == "truenas" else folder.mac_path
    return {
        "id": folder.id,
        "label": folder.label,
        "path": path,
        "type": folder.type,
        "rescanIntervalS": 3600,
        "fsWatcherEnabled": True,
        "fsWatcherDelayS": 10,
        "devices": [
            {"deviceID": local.device_id, "introducedBy": "", "encryptionPassword": ""},
            {"deviceID": remote.device_id, "introducedBy": "", "encryptionPassword": ""},
        ],
        "versioning": folder.versioning.model_dump(mode="json"),
    }


def _changed_subset(desired: Mapping[str, Any], current: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(sorted(key for key, value in desired.items() if current.get(key) != value))


def _folder_changed_fields(
    desired: Mapping[str, Any], current: Mapping[str, Any]
) -> tuple[str, ...]:
    changed = list(
        _changed_subset(
            {key: value for key, value in desired.items() if key not in {"devices", "versioning"}},
            current,
        )
    )
    desired_versioning = desired["versioning"]
    current_versioning = current.get("versioning")
    if not isinstance(current_versioning, Mapping) or any(
        current_versioning.get(key) != value for key, value in desired_versioning.items()
    ):
        changed.append("versioning")

    current_devices_value = current.get("devices")
    current_devices = current_devices_value if isinstance(current_devices_value, list) else []
    current_device_by_id = {
        item.get("deviceID"): item for item in current_devices if isinstance(item, Mapping)
    }
    for device in desired["devices"]:
        current_device = current_device_by_id.get(device["deviceID"])
        if current_device is None or _changed_subset(device, current_device):
            changed.append(f"devices.{device['deviceID']}")
    return tuple(sorted(changed))


def plan_syncthing(
    desired: SyncthingDesiredState,
    host: SyncthingHost,
    current: Mapping[str, Any],
    desired_ignore: str,
) -> Plan:
    operations: list[Operation] = []
    options = desired.options.model_dump(mode="json", by_alias=True)
    current_options = current.get("options")
    if not isinstance(current_options, Mapping):
        raise OperationalError("Syncthing current options are missing")
    option_changes = _changed_subset(options, current_options)
    operations.append(
        Operation(
            kind=OperationKind.UPDATE if option_changes else OperationKind.UNCHANGED,
            scope=desired.ownership.scope,
            resource_id="options",
            summary=(
                "Syncthing options differ from desired state"
                if option_changes
                else "Syncthing options are current"
            ),
            changed_fields=option_changes,
        )
    )

    current_devices_value = current.get("devices")
    current_devices = current_devices_value if isinstance(current_devices_value, list) else []
    current_device_by_id = {
        item.get("deviceID"): item
        for item in current_devices
        if isinstance(item, Mapping) and isinstance(item.get("deviceID"), str)
    }
    local, remote = _host_devices(desired, host)
    device = desired_device(desired, host)
    current_device = current_device_by_id.get(remote.device_id)
    if current_device is None:
        device_kind = OperationKind.CREATE
        device_changes: tuple[str, ...] = ()
    else:
        device_changes = _changed_subset(device, current_device)
        device_kind = OperationKind.UPDATE if device_changes else OperationKind.UNCHANGED
    operations.append(
        Operation(
            kind=device_kind,
            scope=desired.ownership.scope,
            resource_id=f"device-{remote.name}",
            summary=(
                "Syncthing remote device is absent"
                if device_kind is OperationKind.CREATE
                else "Syncthing remote device differs from desired state"
                if device_kind is OperationKind.UPDATE
                else "Syncthing remote device is current"
            ),
            changed_fields=device_changes,
        )
    )

    managed_device_ids = {local.device_id, remote.device_id}
    for index, item in enumerate(current_devices):
        if isinstance(item, Mapping) and item.get("deviceID") not in managed_device_ids:
            operations.append(
                Operation(
                    kind=OperationKind.WARNING,
                    scope=desired.ownership.scope,
                    resource_id=f"unmanaged-device-{index}",
                    summary="Unmanaged Syncthing device is preserved",
                )
            )

    current_folders_value = current.get("folders")
    current_folders = current_folders_value if isinstance(current_folders_value, list) else []
    current_folder_by_id = {
        item.get("id"): item
        for item in current_folders
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    ignore_values = current.get("ignore_files")
    current_ignores = ignore_values if isinstance(ignore_values, Mapping) else {}
    desired_folder_ids = {folder.id for folder in desired.folders}
    for folder in desired.folders:
        folder_value = desired_folder(desired, folder, host)
        current_folder = current_folder_by_id.get(folder.id)
        if current_folder is None:
            folder_kind = OperationKind.CREATE
            folder_changes: tuple[str, ...] = ()
        else:
            folder_changes = _folder_changed_fields(folder_value, current_folder)
            folder_kind = OperationKind.UPDATE if folder_changes else OperationKind.UNCHANGED
        operations.append(
            Operation(
                kind=folder_kind,
                scope=desired.ownership.scope,
                resource_id=folder.id,
                summary=(
                    "Syncthing folder is absent"
                    if folder_kind is OperationKind.CREATE
                    else "Syncthing folder differs from desired state"
                    if folder_kind is OperationKind.UPDATE
                    else "Syncthing folder is current"
                ),
                changed_fields=folder_changes,
            )
        )
        ignore_changed = current_ignores.get(folder.id) != desired_ignore
        operations.append(
            Operation(
                kind=OperationKind.UPDATE if ignore_changed else OperationKind.UNCHANGED,
                scope=desired.ownership.scope,
                resource_id=f"ignore-{folder.id}",
                summary=(
                    "Syncthing ignore file differs from desired state"
                    if ignore_changed
                    else "Syncthing ignore file is current"
                ),
                changed_fields=("content",) if ignore_changed else (),
            )
        )

    for index, item in enumerate(current_folders):
        if isinstance(item, Mapping) and item.get("id") not in desired_folder_ids:
            operations.append(
                Operation(
                    kind=OperationKind.WARNING,
                    scope=desired.ownership.scope,
                    resource_id=f"unmanaged-folder-{index}",
                    summary="Unmanaged Syncthing folder is preserved",
                )
            )
    return Plan(operations=order_operations(operations))


def _merge_folder(current: Mapping[str, Any], desired: Mapping[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(dict(current))
    merged.update(
        {key: value for key, value in desired.items() if key not in {"devices", "versioning"}}
    )
    current_versioning = merged.get("versioning")
    versioning = dict(current_versioning) if isinstance(current_versioning, Mapping) else {}
    versioning.update(desired["versioning"])
    merged["versioning"] = versioning

    current_devices = merged.get("devices")
    devices = list(current_devices) if isinstance(current_devices, list) else []
    desired_by_id = {item["deviceID"]: item for item in desired["devices"]}
    seen: set[str] = set()
    merged_devices: list[Any] = []
    for item in devices:
        item_id = item.get("deviceID") if isinstance(item, Mapping) else None
        if isinstance(item_id, str) and item_id in desired_by_id:
            merged_devices.append({**item, **desired_by_id[item_id]})
            seen.add(item_id)
        else:
            merged_devices.append(item)
    merged_devices.extend(item for item_id, item in desired_by_id.items() if item_id not in seen)
    merged["devices"] = merged_devices
    return merged


def apply_syncthing(
    desired: SyncthingDesiredState,
    host: SyncthingHost,
    current: Mapping[str, Any],
    client: SyncthingClient,
    ignore_files: SyncthingIgnoreFiles,
) -> Plan:
    desired_ignore = ignore_files.desired_content()
    plan = plan_syncthing(desired, host, current, desired_ignore)
    operations = {operation.resource_id: operation for operation in plan.operations}
    current_options = current["options"]
    option_operation = operations["options"]
    if option_operation.kind is OperationKind.UPDATE:
        client.put(
            "/rest/config/options",
            {**current_options, **desired.options.model_dump(mode="json", by_alias=True)},
        )

    _, remote = _host_devices(desired, host)
    device_value = desired_device(desired, host)
    device_operation = operations[f"device-{remote.name}"]
    current_devices = current.get("devices", [])
    current_device = next(
        (
            item
            for item in current_devices
            if isinstance(item, Mapping) and item.get("deviceID") == remote.device_id
        ),
        None,
    )
    if device_operation.kind is OperationKind.CREATE:
        client.post("/rest/config/devices", device_value)
    elif device_operation.kind is OperationKind.UPDATE and current_device is not None:
        client.put(
            f"/rest/config/devices/{urllib.parse.quote(remote.device_id)}",
            {**current_device, **device_value},
        )

    current_folders = current.get("folders", [])
    for folder in desired.folders:
        folder_value = desired_folder(desired, folder, host)
        folder_operation = operations[folder.id]
        current_folder = next(
            (
                item
                for item in current_folders
                if isinstance(item, Mapping) and item.get("id") == folder.id
            ),
            None,
        )
        if folder_operation.kind is OperationKind.CREATE:
            client.post("/rest/config/folders", folder_value)
        elif folder_operation.kind is OperationKind.UPDATE and current_folder is not None:
            client.put(
                f"/rest/config/folders/{urllib.parse.quote(folder.id)}",
                _merge_folder(current_folder, folder_value),
            )
        if operations[f"ignore-{folder.id}"].kind is OperationKind.UPDATE:
            ignore_files.write(folder, desired_ignore)
    return plan
