from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from homeserver_iac.models import (
    AudiobookshelfDesiredState,
    BackrestDesiredState,
    MaintenanceDesiredState,
    NfsDesiredState,
    OpenWrtDesiredState,
    SecretMetadataDesiredState,
    SmbDesiredState,
    SnapshotDesiredState,
    SyncthingDesiredState,
    TrueNASAppDesiredState,
)

INFRA_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = INFRA_ROOT / "schemas"
SCHEMA_MODELS: dict[str, type[BaseModel]] = {
    "audiobookshelf.schema.json": AudiobookshelfDesiredState,
    "backrest.schema.json": BackrestDesiredState,
    "truenas-maintenance.schema.json": MaintenanceDesiredState,
    "truenas-nfs.schema.json": NfsDesiredState,
    "openwrt.schema.json": OpenWrtDesiredState,
    "secret-metadata.schema.json": SecretMetadataDesiredState,
    "truenas-smb.schema.json": SmbDesiredState,
    "syncthing.schema.json": SyncthingDesiredState,
    "truenas-app.schema.json": TrueNASAppDesiredState,
    "truenas-snapshots.schema.json": SnapshotDesiredState,
}


def schema_content(filename: str, model: type[BaseModel]) -> str:
    schema = model.model_json_schema(by_alias=True, mode="validation")
    schema["$id"] = f"urn:homeserver-iac:schema:{filename.removesuffix('.schema.json')}"
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return json.dumps(schema, indent=2, sort_keys=True) + "\n"


def generate_schemas(*, check: bool) -> list[Path]:
    changed: list[Path] = []
    if not check:
        SCHEMA_DIR.mkdir(parents=True, exist_ok=True)

    for filename, model in SCHEMA_MODELS.items():
        path = SCHEMA_DIR / filename
        expected = schema_content(filename, model)
        actual = path.read_text() if path.exists() else None
        if actual == expected:
            continue
        changed.append(path)
        if not check:
            path.write_text(expected)
    return changed
