from __future__ import annotations

import json
import os
import sqlite3
from hashlib import sha256
from pathlib import Path

import pytest

from homeserver_iac.apple_photos import (
    ExportValidationError,
    HiddenAssetPolicy,
    ImmichAssetBinding,
    ImmichMetadataOperationStatus,
    ImmichMetadataPlanError,
    MediaKind,
    _stack_actions,
    build_immich_metadata_plan,
    build_import_manifest,
    reconcile_immich_metadata,
    serialize_export_validation,
    validate_export,
    write_export_validation_report,
    write_import_manifest,
)
from homeserver_iac.runtime import OperationalError

FIXTURES = Path(__file__).parent / "fixtures/apple_photos"


def _stack_response(
    stack_id: str, primary_asset_id: str, asset_ids: tuple[str, ...]
) -> dict[str, object]:
    return {
        "id": stack_id,
        "primaryAssetId": primary_asset_id,
        "assets": [{"id": asset_id} for asset_id in asset_ids],
    }


class FakeImmichClient:
    def __init__(self) -> None:
        self.assets: dict[str, dict[str, object]] = {}
        self.albums: dict[str, dict[str, object]] = {}
        self.stacks_by_primary: dict[str, dict[str, object]] = {}
        self.mutations: list[tuple[str, str]] = []

    def get_asset(self, asset_id: str) -> dict[str, object]:
        return self.assets[asset_id]

    def update_assets(self, body: dict[str, object]) -> None:
        self.mutations.append(("PUT", "/api/assets"))
        asset_ids = body.get("ids")
        if not isinstance(asset_ids, list):
            raise AssertionError("asset update body must include IDs")
        for asset_id in asset_ids:
            if "isFavorite" in body:
                self.assets[str(asset_id)]["isFavorite"] = body["isFavorite"]
            if "visibility" in body:
                self.assets[str(asset_id)]["visibility"] = body["visibility"]

    def find_albums(self, lookup_endpoint: str) -> tuple[dict[str, object], ...]:
        if "name=" not in lookup_endpoint:
            raise AssertionError("album lookup endpoint must include a name")
        album_name = lookup_endpoint.split("name=", 1)[1].split("&", 1)[0]
        return tuple(
            album for album in self.albums.values() if album.get("albumName") == album_name
        )

    def create_album(self, body: dict[str, object]) -> dict[str, object]:
        self.mutations.append(("POST", "/api/albums"))
        album_name = body.get("albumName")
        if not isinstance(album_name, str):
            raise AssertionError("album create body must include albumName")
        album = {"id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "albumName": album_name}
        self.albums[album_name] = album
        return album

    def add_album_assets(self, album_id: str, body: dict[str, object]) -> list[dict[str, object]]:
        self.mutations.append(("PUT", f"/api/albums/{album_id}/assets"))
        asset_ids = body.get("ids")
        if not isinstance(asset_ids, list):
            raise AssertionError("album add body must include IDs")
        return [{"id": str(asset_id), "success": True} for asset_id in asset_ids]

    def get_stacks(self, lookup_endpoint: str) -> tuple[dict[str, object], ...]:
        primary_asset_id = lookup_endpoint.rsplit("=", 1)[1]
        stack = self.stacks_by_primary.get(primary_asset_id)
        return () if stack is None else (stack,)

    def create_stack(self, body: dict[str, object]) -> dict[str, object]:
        self.mutations.append(("POST", "/api/stacks"))
        asset_ids = body.get("assetIds")
        if not isinstance(asset_ids, list) or not all(isinstance(item, str) for item in asset_ids):
            raise AssertionError("stack create body must include assetIds")
        stack = _stack_response(
            "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            asset_ids[0],
            tuple(asset_ids),
        )
        self.stacks_by_primary[asset_ids[0]] = stack
        return stack


def _write_live_metadata_plan(
    tmp_path: Path,
    *,
    favorite_asset_ids: tuple[str, ...],
    album_asset_ids: tuple[str, ...],
    stack_asset_ids: tuple[str, ...],
    hidden_asset_ids: tuple[str, ...] = (),
) -> Path:
    source_uuid = "99999999-9999-4999-8999-999999999999"
    plan_path = tmp_path / "metadata-plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "export_root": str(tmp_path / "export"),
                "errors": [],
                "warnings": [],
                "unresolved_asset_paths": [],
                "favorite_actions": [
                    {
                        "action": "set_favorite_true",
                        "asset_ids": list(favorite_asset_ids),
                    }
                ],
                "hidden_visibility_actions": [
                    {
                        "action": "set_visibility_hidden",
                        "asset_ids": list(hidden_asset_ids),
                    }
                ]
                if hidden_asset_ids
                else [],
                "album_actions": [
                    {
                        "action": "ensure_album_assets",
                        "album_name": "Pilot",
                        "asset_ids": list(album_asset_ids),
                        "lookup_endpoint": "/api/albums?name=Pilot&isOwned=true&isShared=false",
                    }
                ],
                "stack_actions": [
                    {
                        "action": "ensure_stack_with_edited_primary",
                        "source_uuid": source_uuid,
                        "primary_asset_id": stack_asset_ids[0],
                        "asset_ids": list(stack_asset_ids),
                    }
                ],
            }
        )
    )
    return plan_path


def test_adjustment_plists_under_media_extensions_are_rejected() -> None:
    def unexpected_command(*args: object, **kwargs: object) -> str:
        raise AssertionError("plist content must be rejected before external commands run")

    report = validate_export(FIXTURES / "invalid-originals", runner=unexpected_command)

    assert report.valid is False
    assert report.candidate_media_files == 2
    assert report.valid_media_files == 0
    assert report.invalid_media_files == 2
    assert report.retry_source_uuids == (
        "11111111-1111-4111-8111-111111111111",
        "22222222-2222-4222-8222-222222222222",
    )
    assert [result.expected_kind for result in report.files] == [
        MediaKind.IMAGE,
        MediaKind.VIDEO,
    ]
    assert all(result.detected_mime == "text/xml" for result in report.files)
    assert all(result.errors == ("plist_or_xml_content",) for result in report.files)


def test_valid_media_requires_matching_mime_and_successful_full_decode(tmp_path: Path) -> None:
    source_uuid = "33333333-3333-4333-8333-333333333333"
    image = tmp_path / source_uuid / "IMG_0003.HEIC"
    image.parent.mkdir()
    image.write_bytes(b"synthetic media bytes")
    commands: list[tuple[str, ...]] = []

    def successful_command(command: tuple[str, ...], **kwargs: object) -> str:
        commands.append(command)
        return "image/heic\n" if command[0] == "/usr/bin/file" else ""

    report = validate_export(tmp_path, runner=successful_command)

    assert report.valid is True
    assert report.valid_media_files == 1
    assert report.files[0].sha256 == sha256(image.read_bytes()).hexdigest()
    assert commands[0][0] == "/usr/bin/file"
    assert commands[1][0] == "ffmpeg"
    assert "-xerror" in commands[1]
    assert commands[1][-3:] == ("-f", "null", "-")


def test_decode_failure_marks_source_uuid_for_retry(tmp_path: Path) -> None:
    source_uuid = "44444444-4444-4444-8444-444444444444"
    video = tmp_path / source_uuid / "IMG_0004.MOV"
    video.parent.mkdir()
    video.write_bytes(b"synthetic media bytes")

    def failing_decode(command: tuple[str, ...], **kwargs: object) -> str:
        if command[0] == "/usr/bin/file":
            return "video/quicktime\n"
        raise OperationalError("synthetic decode failure")

    report = validate_export(tmp_path, runner=failing_decode)

    assert report.valid is False
    assert report.retry_source_uuids == (source_uuid,)
    assert report.files[0].errors == ("decode_failed",)


def test_hardware_decode_failure_falls_back_to_software(tmp_path: Path) -> None:
    source_uuid = "44444444-4444-4444-8444-444444444444"
    video = tmp_path / source_uuid / "IMG_0004.MOV"
    video.parent.mkdir()
    video.write_bytes(b"synthetic media bytes")
    commands: list[tuple[str, ...]] = []

    def hardware_fails(command: tuple[str, ...], **kwargs: object) -> str:
        commands.append(command)
        if command[0] == "/usr/bin/file":
            return "video/quicktime\n"
        if "-hwaccel" in command:
            raise OperationalError("synthetic hardware decode failure")
        return ""

    report = validate_export(
        tmp_path,
        runner=hardware_fails,
        ffmpeg_hwaccel="videotoolbox",
    )

    assert report.valid is True
    assert "-hwaccel" in commands[1]
    assert "-hwaccel" not in commands[2]


def test_empty_export_fails_closed(tmp_path: Path) -> None:
    report = validate_export(tmp_path)

    assert report.valid is False
    assert report.errors == ("no_media_files",)


def test_report_is_deterministic_and_cannot_be_written_inside_export(
    tmp_path: Path,
) -> None:
    report = validate_export(FIXTURES / "invalid-originals", runner=lambda *args, **kwargs: "")
    serialized = serialize_export_validation(report)

    document = json.loads(serialized)
    assert document["schema_version"] == 2
    assert all(item["sha256"] for item in document["files"])
    with pytest.raises(ValueError, match="outside the export tree"):
        write_export_validation_report(
            report,
            FIXTURES / "invalid-originals/report.json",
        )

    destination = tmp_path / "report.json"
    write_export_validation_report(report, destination)
    assert destination.read_text() == serialized


def test_validation_checkpoint_resumes_results_in_deterministic_order(
    tmp_path: Path,
) -> None:
    export_root = tmp_path / "export"
    first = export_root / "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb" / "second.JPG"
    second = export_root / "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa" / "first.JPG"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    first.write_bytes(b"second")
    second.write_bytes(b"first")
    checkpoint = tmp_path / "validation.db"
    commands: list[tuple[str, ...]] = []

    def successful_command(command: tuple[str, ...], **kwargs: object) -> str:
        commands.append(command)
        return "image/jpeg\n" if command[0] == "/usr/bin/file" else ""

    initial = validate_export(
        export_root,
        runner=successful_command,
        workers=2,
        checkpoint_path=checkpoint,
    )

    assert initial.valid is True
    assert [result.path for result in initial.files] == sorted(
        result.path for result in initial.files
    )
    assert len(commands) == 4

    def unexpected_command(*args: object, **kwargs: object) -> str:
        raise AssertionError("unchanged checkpoint results must be reused")

    resumed = validate_export(
        export_root,
        runner=unexpected_command,
        workers=2,
        checkpoint_path=checkpoint,
    )

    assert resumed == initial


def test_validation_checkpoint_revalidates_changed_file(tmp_path: Path) -> None:
    export_root = tmp_path / "export"
    source_uuid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    image = export_root / source_uuid / "image.JPG"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"first")
    checkpoint = tmp_path / "validation.db"

    def successful_command(command: tuple[str, ...], **kwargs: object) -> str:
        return "image/jpeg\n" if command[0] == "/usr/bin/file" else ""

    validate_export(
        export_root,
        runner=successful_command,
        checkpoint_path=checkpoint,
    )
    image.write_bytes(b"changed content")
    commands: list[tuple[str, ...]] = []

    def record_command(command: tuple[str, ...], **kwargs: object) -> str:
        commands.append(command)
        return "image/jpeg\n" if command[0] == "/usr/bin/file" else ""

    report = validate_export(
        export_root,
        runner=record_command,
        checkpoint_path=checkpoint,
    )

    assert report.valid is True
    assert len(commands) == 2


def test_validation_checkpoint_revalidates_same_size_same_mtime_changed_bytes(
    tmp_path: Path,
) -> None:
    export_root = tmp_path / "export"
    image = export_root / "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa" / "image.JPG"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"first")
    original_mtime_ns = image.stat().st_mtime_ns
    checkpoint = tmp_path / "validation.db"

    def successful_command(command: tuple[str, ...], **kwargs: object) -> str:
        return "image/jpeg\n" if command[0] == "/usr/bin/file" else ""

    validate_export(export_root, runner=successful_command, checkpoint_path=checkpoint)
    image.write_bytes(b"other")
    os.utime(image, ns=(image.stat().st_atime_ns, original_mtime_ns))
    commands: list[tuple[str, ...]] = []

    def record_command(command: tuple[str, ...], **kwargs: object) -> str:
        commands.append(command)
        return "image/jpeg\n" if command[0] == "/usr/bin/file" else ""

    report = validate_export(export_root, runner=record_command, checkpoint_path=checkpoint)

    assert len(commands) == 2
    assert report.files[0].sha256 == sha256(b"other").hexdigest()


def test_validation_checkpoint_migrates_v1_without_reusing_unbound_rows(
    tmp_path: Path,
) -> None:
    export_root = (tmp_path / "export").resolve()
    relative_path = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/image.JPG"
    image = export_root / relative_path
    image.parent.mkdir(parents=True)
    image.write_bytes(b"image")
    stat = image.stat()
    checkpoint = tmp_path / "validation.db"
    connection = sqlite3.connect(checkpoint)
    connection.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute(
        "CREATE TABLE results ("
        "path TEXT PRIMARY KEY, size INTEGER NOT NULL, mtime_ns INTEGER NOT NULL, "
        "result_json TEXT NOT NULL)"
    )
    connection.executemany(
        "INSERT INTO metadata(key, value) VALUES (?, ?)",
        (("schema_version", "1"), ("export_root", str(export_root))),
    )
    connection.execute(
        "INSERT INTO results(path, size, mtime_ns, result_json) VALUES (?, ?, ?, ?)",
        (
            relative_path,
            stat.st_size,
            stat.st_mtime_ns,
            json.dumps(
                {
                    "path": relative_path,
                    "source_uuid": "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA",
                    "expected_kind": "image",
                    "detected_mime": "image/jpeg",
                    "valid": True,
                    "errors": [],
                }
            ),
        ),
    )
    connection.commit()
    connection.close()
    commands: list[tuple[str, ...]] = []

    def record_command(command: tuple[str, ...], **kwargs: object) -> str:
        commands.append(command)
        return "image/jpeg\n" if command[0] == "/usr/bin/file" else ""

    report = validate_export(export_root, runner=record_command, checkpoint_path=checkpoint)

    assert report.valid is True
    assert len(commands) == 2
    connection = sqlite3.connect(checkpoint)
    assert dict(connection.execute("SELECT key, value FROM metadata"))["schema_version"] == "2"
    columns = {row[1] for row in connection.execute("PRAGMA table_info(results)")}
    stored_sha256 = connection.execute("SELECT sha256 FROM results").fetchone()[0]
    connection.close()
    assert "sha256" in columns
    assert stored_sha256 == sha256(b"image").hexdigest()


def test_validation_checkpoint_rejects_root_mismatch(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    source_uuid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    first_file = first_root / source_uuid / "image.JPG"
    second_file = second_root / source_uuid / "image.JPG"
    first_file.parent.mkdir(parents=True)
    second_file.parent.mkdir(parents=True)
    first_file.write_bytes(b"first")
    second_file.write_bytes(b"second")
    checkpoint = tmp_path / "validation.db"

    def successful_command(command: tuple[str, ...], **kwargs: object) -> str:
        return "image/jpeg\n" if command[0] == "/usr/bin/file" else ""

    validate_export(
        first_root,
        runner=successful_command,
        checkpoint_path=checkpoint,
    )

    with pytest.raises(ExportValidationError, match="does not match"):
        validate_export(
            second_root,
            runner=successful_command,
            checkpoint_path=checkpoint,
        )


def test_validation_workers_must_be_positive(tmp_path: Path) -> None:
    with pytest.raises(ExportValidationError, match="at least 1"):
        validate_export(tmp_path, workers=0)


def test_import_manifest_selects_only_validated_media_and_preserves_renditions(
    tmp_path: Path,
) -> None:
    source_uuid = "55555555-5555-4555-8555-555555555555"
    source_dir = tmp_path / "export" / source_uuid
    source_dir.mkdir(parents=True)
    original = source_dir / "IMG_0005.HEIC"
    edited = source_dir / "IMG_0005_edited.jpeg"
    original.write_bytes(b"original image")
    edited.write_bytes(b"edited image")
    Path(f"{edited}.xmp").write_text("sidecar")
    (source_dir / "IMG_0005.AAE").write_text("adjustment")
    (source_dir / "IMG_0005.HEIC.json").write_text("{}")

    def successful_command(command: tuple[str, ...], **kwargs: object) -> str:
        if command[0] == "/usr/bin/file":
            return "image/jpeg\n" if command[-1].endswith("jpeg") else "image/heic\n"
        return ""

    validation = validate_export(tmp_path / "export", runner=successful_command)
    validation_path = tmp_path / "validation.json"
    write_export_validation_report(validation, validation_path)
    source_manifest = tmp_path / "source.json"
    source_manifest.write_text(
        json.dumps(
            [
                {
                    "uuid": source_uuid,
                    "live_photo": False,
                    "hasadjustments": True,
                }
            ]
        )
    )

    manifest = build_import_manifest(validation_path, (source_manifest,))

    assert manifest.valid is True
    assert len(manifest.entries) == 2
    assert [entry.rendition for entry in manifest.entries] == ["original", "edited"]
    assert manifest.entries[0].xmp_sidecar_path is None
    assert manifest.entries[1].xmp_sidecar_path == f"{edited}.xmp"
    assert manifest.entries[1].xmp_sidecar_size == len("sidecar")
    assert manifest.entries[1].xmp_sidecar_sha256
    assert all(entry.sha256 for entry in manifest.entries)
    assert not any(entry.path.endswith((".AAE", ".json", ".xmp")) for entry in manifest.entries)


def test_import_manifest_rejects_media_changed_after_validation(tmp_path: Path) -> None:
    source_uuid = "55555555-5555-4555-8555-555555555555"
    image = tmp_path / "export" / source_uuid / "IMG_0005.HEIC"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"validated bytes")

    def successful_command(command: tuple[str, ...], **kwargs: object) -> str:
        return "image/heic\n" if command[0] == "/usr/bin/file" else ""

    validation = validate_export(tmp_path / "export", runner=successful_command)
    validation_path = tmp_path / "validation.json"
    write_export_validation_report(validation, validation_path)
    source_manifest = tmp_path / "source.json"
    source_manifest.write_text(
        json.dumps([{"uuid": source_uuid, "live_photo": False, "hasadjustments": False}])
    )
    image.write_bytes(b"different bytes")

    manifest = build_import_manifest(validation_path, (source_manifest,))

    assert manifest.valid is False
    assert manifest.errors == ("validated_media_hash_mismatch",)
    assert manifest.entries == ()


def test_v1_validation_report_is_readable_but_cannot_build_authorizing_manifest(
    tmp_path: Path,
) -> None:
    source_uuid = "55555555-5555-4555-8555-555555555555"
    image = tmp_path / "export" / source_uuid / "IMG_0005.HEIC"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"image")

    def successful_command(command: tuple[str, ...], **kwargs: object) -> str:
        return "image/heic\n" if command[0] == "/usr/bin/file" else ""

    report = json.loads(
        serialize_export_validation(validate_export(image.parents[1], runner=successful_command))
    )
    report["schema_version"] = 1
    for item in report["files"]:
        item.pop("sha256")
    validation_path = tmp_path / "legacy-validation.json"
    validation_path.write_text(json.dumps(report))
    source_manifest = tmp_path / "source.json"
    source_manifest.write_text(
        json.dumps([{"uuid": source_uuid, "live_photo": False, "hasadjustments": False}])
    )

    manifest = build_import_manifest(validation_path, (source_manifest,))

    assert manifest.schema_version == 2
    assert manifest.valid is False
    assert manifest.errors == (
        "validation_content_binding_missing",
        "validation_report_content_unbound",
    )
    assert manifest.entries == ()


def test_import_manifest_fails_closed_for_uuid_missing_from_source_snapshot(
    tmp_path: Path,
) -> None:
    source_uuid = "66666666-6666-4666-8666-666666666666"
    image = tmp_path / "export" / source_uuid / "IMG_0006.HEIC"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"synthetic media bytes")

    def successful_command(command: tuple[str, ...], **kwargs: object) -> str:
        return "image/heic\n" if command[0] == "/usr/bin/file" else ""

    validation = validate_export(tmp_path / "export", runner=successful_command)
    validation_path = tmp_path / "validation.json"
    write_export_validation_report(validation, validation_path)
    source_manifest = tmp_path / "source.json"
    source_manifest.write_text("[]")

    manifest = build_import_manifest(validation_path, (source_manifest,))

    assert manifest.valid is False
    assert manifest.errors == ()
    assert manifest.unresolved_source_uuids == (source_uuid,)
    assert manifest.entries == ()


def test_immich_metadata_plan_binds_upload_ids_and_plans_metadata_actions(
    tmp_path: Path,
) -> None:
    adjusted_uuid = "77777777-7777-4777-8777-777777777777"
    album_uuid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    source_dir = tmp_path / "export" / adjusted_uuid
    source_dir.mkdir(parents=True)
    original = source_dir / "IMG_0007.HEIC"
    edited = source_dir / "IMG_0007_edited.jpeg"
    original.write_bytes(b"original image")
    edited.write_bytes(b"edited image")
    other_uuid = "88888888-8888-4888-8888-888888888888"
    other = tmp_path / "export" / other_uuid / "IMG_0008.JPG"
    other.parent.mkdir()
    other.write_bytes(b"other image")

    def successful_command(command: tuple[str, ...], **kwargs: object) -> str:
        if command[0] == "/usr/bin/file":
            return "image/heic\n" if command[-1].endswith("HEIC") else "image/jpeg\n"
        return ""

    validation = validate_export(tmp_path / "export", runner=successful_command)
    validation_path = tmp_path / "validation.json"
    write_export_validation_report(validation, validation_path)
    source_manifest = tmp_path / "source.json"
    source_manifest.write_text(
        json.dumps(
            [
                {
                    "uuid": adjusted_uuid,
                    "live_photo": False,
                    "hasadjustments": True,
                    "favorite": True,
                    "hidden": False,
                    "albums": ["Pilot", "Multi"],
                    "album_info": [
                        {"title": "Pilot", "uuid": album_uuid},
                        {"title": "Multi", "uuid": None},
                    ],
                },
                {
                    "uuid": other_uuid,
                    "live_photo": False,
                    "hasadjustments": False,
                    "favorite": False,
                    "hidden": False,
                    "albums": ["Pilot"],
                    "album_info": [{"title": "Pilot", "uuid": album_uuid}],
                },
            ]
        )
    )
    import_manifest = build_import_manifest(validation_path, (source_manifest,))
    import_manifest_path = tmp_path / "import-manifest.json"
    write_import_manifest(import_manifest, import_manifest_path)
    old_original_id = "11111111-1111-4111-8111-111111111111"
    new_original_id = "22222222-2222-4222-8222-222222222222"
    edited_id = "33333333-3333-4333-8333-333333333333"
    other_id = "44444444-4444-4444-8444-444444444444"
    upload_results = tmp_path / "upload.log"
    upload_results.write_text(
        "noise before JSON\n"
        + json.dumps(
            {
                "newAssets": [
                    {"id": old_original_id, "filepath": str(original)},
                    {"id": edited_id, "filepath": str(edited)},
                    {"id": other_id, "filepath": str(other)},
                ],
                "duplicates": [],
            }
        )
        + "\nretry replacement\n"
        + json.dumps({"newAssets": [{"id": new_original_id, "filepath": str(original)}]})
    )

    plan = build_immich_metadata_plan(import_manifest_path, upload_results)

    assert plan.valid is True
    assert plan.warnings == ("upload_results_contain_superseded_asset_ids",)
    assert plan.upload_asset_supersessions[0].previous_asset_id == old_original_id
    assert plan.upload_asset_supersessions[0].replacement_asset_id == new_original_id
    assert {binding.asset_id for binding in plan.asset_bindings} == {
        new_original_id,
        edited_id,
        other_id,
    }
    assert plan.favorite_actions[0].method == "PUT"
    assert plan.favorite_actions[0].endpoint == "/api/assets"
    assert set(plan.favorite_actions[0].asset_ids) == {new_original_id, edited_id}
    assert {action.album_name for action in plan.album_actions} == {"Multi", "Pilot"}
    pilot_album = next(action for action in plan.album_actions if action.album_name == "Pilot")
    assert pilot_album.source_album_uuid == album_uuid.upper()
    assert set(pilot_album.asset_ids) == {new_original_id, edited_id, other_id}
    assert plan.stack_actions[0].primary_asset_id == edited_id
    assert plan.stack_actions[0].create_body == {"assetIds": [edited_id, new_original_id]}


def test_immich_metadata_plan_skips_stack_for_deduplicated_renditions() -> None:
    source_uuid = "77777777-7777-4777-8777-777777777777"
    asset_id = "33333333-3333-4333-8333-333333333333"
    common = {
        "source_uuid": source_uuid,
        "asset_id": asset_id,
        "media_kind": MediaKind.IMAGE,
        "source_live_photo": False,
        "source_has_adjustments": True,
        "source_favorite": False,
        "source_hidden": False,
        "source_albums": (),
    }
    original = ImmichAssetBinding(
        **common,
        path="/export/IMG_0007.HEIC",
        relative_path="IMG_0007.HEIC",
        rendition="original",
    )
    edited = ImmichAssetBinding(
        **common,
        path="/export/IMG_0007_edited.jpeg",
        relative_path="IMG_0007_edited.jpeg",
        rendition="edited",
    )

    assert _stack_actions({source_uuid: (original, edited)}) == ()


def test_immich_metadata_plan_coalesces_stacks_with_shared_assets() -> None:
    first_uuid = "11111111-1111-4111-8111-111111111111"
    second_uuid = "22222222-2222-4222-8222-222222222222"
    shared_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"

    def binding(source_uuid: str, asset_id: str, rendition: str) -> ImmichAssetBinding:
        return ImmichAssetBinding(
            source_uuid=source_uuid,
            asset_id=asset_id,
            path=f"/export/{source_uuid}/{rendition}.jpeg",
            relative_path=f"{source_uuid}/{rendition}.jpeg",
            media_kind=MediaKind.IMAGE,
            rendition=rendition,
            source_live_photo=False,
            source_has_adjustments=True,
            source_favorite=False,
            source_hidden=False,
            source_albums=(),
        )

    actions = _stack_actions(
        {
            first_uuid: (
                binding(first_uuid, shared_id, "original"),
                binding(first_uuid, "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "edited"),
            ),
            second_uuid: (
                binding(second_uuid, shared_id, "original"),
                binding(second_uuid, "cccccccc-cccc-4ccc-8ccc-cccccccccccc", "edited"),
            ),
        }
    )

    assert len(actions) == 1
    assert actions[0].source_uuids == (first_uuid, second_uuid)
    assert actions[0].primary_asset_id == "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    assert set(actions[0].asset_ids) == {
        shared_id,
        "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    }


def test_immich_metadata_plan_fails_closed_for_unresolved_hidden_policy(
    tmp_path: Path,
) -> None:
    source_uuid = "99999999-9999-4999-8999-999999999999"
    image = tmp_path / "export" / source_uuid / "IMG_0009.HEIC"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"hidden image")

    def successful_command(command: tuple[str, ...], **kwargs: object) -> str:
        return "image/heic\n" if command[0] == "/usr/bin/file" else ""

    validation = validate_export(tmp_path / "export", runner=successful_command)
    validation_path = tmp_path / "validation.json"
    write_export_validation_report(validation, validation_path)
    source_manifest = tmp_path / "source.json"
    source_manifest.write_text(
        json.dumps(
            [
                {
                    "uuid": source_uuid,
                    "live_photo": False,
                    "hasadjustments": False,
                    "favorite": False,
                    "hidden": True,
                    "albums": [],
                    "album_info": [],
                }
            ]
        )
    )
    import_manifest = build_import_manifest(validation_path, (source_manifest,))
    import_manifest_path = tmp_path / "import-manifest.json"
    write_import_manifest(import_manifest, import_manifest_path)
    upload_results = tmp_path / "upload.json"
    upload_results.write_text(
        json.dumps(
            {"newAssets": [{"id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "filepath": str(image)}]}
        )
    )

    blocked = build_immich_metadata_plan(import_manifest_path, upload_results)
    included = build_immich_metadata_plan(
        import_manifest_path,
        upload_results,
        hidden_policy=HiddenAssetPolicy.INCLUDE,
    )

    assert blocked.valid is False
    assert blocked.errors == ("hidden_policy_unresolved",)
    assert blocked.hidden_source_uuids == (source_uuid,)
    assert included.valid is True
    assert included.hidden_source_uuids == (source_uuid,)
    assert included.hidden_visibility_actions[0].method == "PUT"
    assert included.hidden_visibility_actions[0].endpoint == "/api/assets"
    assert included.hidden_visibility_actions[0].body == {
        "ids": ["aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"],
        "visibility": "hidden",
    }


def test_immich_metadata_plan_requires_every_manifest_path_to_have_asset_id(
    tmp_path: Path,
) -> None:
    source_uuid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    image = tmp_path / "export" / source_uuid / "IMG_0010.HEIC"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"image")

    def successful_command(command: tuple[str, ...], **kwargs: object) -> str:
        return "image/heic\n" if command[0] == "/usr/bin/file" else ""

    validation = validate_export(tmp_path / "export", runner=successful_command)
    validation_path = tmp_path / "validation.json"
    write_export_validation_report(validation, validation_path)
    source_manifest = tmp_path / "source.json"
    source_manifest.write_text(
        json.dumps(
            [
                {
                    "uuid": source_uuid,
                    "live_photo": False,
                    "hasadjustments": False,
                    "favorite": False,
                    "hidden": False,
                    "albums": [],
                    "album_info": [],
                }
            ]
        )
    )
    import_manifest = build_import_manifest(validation_path, (source_manifest,))
    import_manifest_path = tmp_path / "import-manifest.json"
    write_import_manifest(import_manifest, import_manifest_path)
    upload_results = tmp_path / "upload.json"
    upload_results.write_text(json.dumps({"newAssets": []}))

    plan = build_immich_metadata_plan(import_manifest_path, upload_results)

    assert plan.valid is False
    assert plan.errors == ("uploaded_asset_id_unresolved",)
    assert plan.unresolved_asset_paths == (str(image.resolve()),)


def test_immich_metadata_reconcile_dry_run_compares_without_mutation(tmp_path: Path) -> None:
    needs_favorite_id = "11111111-1111-4111-8111-111111111111"
    already_favorite_id = "22222222-2222-4222-8222-222222222222"
    needs_hidden_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    already_hidden_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    original_id = "33333333-3333-4333-8333-333333333333"
    edited_id = "44444444-4444-4444-8444-444444444444"
    plan_path = _write_live_metadata_plan(
        tmp_path,
        favorite_asset_ids=(needs_favorite_id, already_favorite_id),
        hidden_asset_ids=(needs_hidden_id, already_hidden_id),
        album_asset_ids=(needs_favorite_id, original_id, edited_id),
        stack_asset_ids=(edited_id, original_id),
    )
    client = FakeImmichClient()
    client.assets = {
        needs_favorite_id: {"id": needs_favorite_id, "isFavorite": False},
        already_favorite_id: {"id": already_favorite_id, "isFavorite": True},
        needs_hidden_id: {"id": needs_hidden_id, "visibility": "timeline"},
        already_hidden_id: {"id": already_hidden_id, "visibility": "hidden"},
    }
    client.albums = {"Pilot": {"id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "albumName": "Pilot"}}

    report = reconcile_immich_metadata(
        plan_path,
        client,
        api_base_url="https://photos.example.test",
    )

    assert report.valid is True
    assert report.has_pending is True
    assert client.mutations == []
    assert "album_membership_state_not_readable_in_immich_v3_0_2" in report.warnings
    favorite = next(
        operation for operation in report.operations if operation.action == "set_favorite_true"
    )
    hidden_visibility = next(
        operation for operation in report.operations if operation.action == "set_visibility_hidden"
    )
    album = next(
        operation for operation in report.operations if operation.action == "ensure_album_assets"
    )
    stack = next(
        operation
        for operation in report.operations
        if operation.action == "ensure_stack_with_edited_primary"
    )
    assert favorite.status is ImmichMetadataOperationStatus.PENDING
    assert favorite.asset_ids == (needs_favorite_id,)
    assert hidden_visibility.status is ImmichMetadataOperationStatus.PENDING
    assert hidden_visibility.asset_ids == (needs_hidden_id,)
    assert hidden_visibility.changed_fields == ("visibility",)
    assert album.status is ImmichMetadataOperationStatus.PENDING
    assert album.changed_fields == ("assets",)
    assert stack.status is ImmichMetadataOperationStatus.PENDING


def test_immich_metadata_reconcile_apply_mutates_only_planned_actions(tmp_path: Path) -> None:
    favorite_id = "55555555-5555-4555-8555-555555555555"
    hidden_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    original_id = "66666666-6666-4666-8666-666666666666"
    edited_id = "77777777-7777-4777-8777-777777777777"
    plan_path = _write_live_metadata_plan(
        tmp_path,
        favorite_asset_ids=(favorite_id,),
        hidden_asset_ids=(hidden_id,),
        album_asset_ids=(favorite_id, original_id, edited_id),
        stack_asset_ids=(edited_id, original_id),
    )
    client = FakeImmichClient()
    client.assets = {
        favorite_id: {"id": favorite_id, "isFavorite": False},
        hidden_id: {"id": hidden_id, "visibility": "timeline"},
    }

    report = reconcile_immich_metadata(
        plan_path,
        client,
        api_base_url="https://photos.example.test",
        apply_changes=True,
    )

    assert report.valid is True
    assert report.has_pending is False
    assert client.assets[favorite_id]["isFavorite"] is True
    assert client.assets[hidden_id]["visibility"] == "hidden"
    assert "Pilot" in client.albums
    assert edited_id in client.stacks_by_primary
    assert {operation.status for operation in report.operations} == {
        ImmichMetadataOperationStatus.APPLIED
    }
    assert client.mutations == [
        ("PUT", "/api/assets"),
        ("PUT", "/api/assets"),
        ("POST", "/api/albums"),
        ("PUT", "/api/albums/bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb/assets"),
        ("POST", "/api/stacks"),
    ]


def test_v1_metadata_plan_cannot_authorize_mutation(tmp_path: Path) -> None:
    asset_id = "55555555-5555-4555-8555-555555555555"
    plan_path = _write_live_metadata_plan(
        tmp_path,
        favorite_asset_ids=(asset_id,),
        album_asset_ids=(asset_id,),
        stack_asset_ids=(asset_id,),
    )
    document = json.loads(plan_path.read_text())
    document["schema_version"] = 1
    plan_path.write_text(json.dumps(document))
    client = FakeImmichClient()

    with pytest.raises(ImmichMetadataPlanError, match="unsupported"):
        reconcile_immich_metadata(
            plan_path,
            client,
            api_base_url="https://photos.example.test",
            apply_changes=True,
        )

    assert client.mutations == []


def test_immich_metadata_reconcile_blocks_conflicting_stack(tmp_path: Path) -> None:
    favorite_id = "88888888-8888-4888-8888-888888888888"
    original_id = "99999999-9999-4999-8999-999999999999"
    edited_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    unrelated_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    plan_path = _write_live_metadata_plan(
        tmp_path,
        favorite_asset_ids=(favorite_id,),
        album_asset_ids=(favorite_id,),
        stack_asset_ids=(edited_id, original_id),
    )
    client = FakeImmichClient()
    client.assets = {favorite_id: {"id": favorite_id, "isFavorite": True}}
    client.stacks_by_primary[edited_id] = _stack_response(
        "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        edited_id,
        (edited_id, unrelated_id),
    )

    report = reconcile_immich_metadata(
        plan_path,
        client,
        api_base_url="https://photos.example.test",
    )

    assert report.valid is False
    assert report.errors == ("existing_stack_conflict",)
    stack = next(
        operation
        for operation in report.operations
        if operation.action == "ensure_stack_with_edited_primary"
    )
    assert stack.status is ImmichMetadataOperationStatus.BLOCKED
    assert client.mutations == []


def test_immich_metadata_reconcile_accepts_filtered_hidden_stack_assets(
    tmp_path: Path,
) -> None:
    favorite_id = "88888888-8888-4888-8888-888888888888"
    original_id = "99999999-9999-4999-8999-999999999999"
    edited_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    stack_id = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
    plan_path = _write_live_metadata_plan(
        tmp_path,
        favorite_asset_ids=(favorite_id,),
        album_asset_ids=(favorite_id,),
        stack_asset_ids=(edited_id, original_id),
        hidden_asset_ids=(edited_id, original_id),
    )
    client = FakeImmichClient()
    client.assets = {
        favorite_id: {"id": favorite_id, "isFavorite": True},
        edited_id: {"id": edited_id, "visibility": "hidden"},
        original_id: {"id": original_id, "visibility": "hidden"},
    }
    client.stacks_by_primary[edited_id] = {
        "id": stack_id,
        "primaryAssetId": edited_id,
        "assets": [],
    }

    report = reconcile_immich_metadata(
        plan_path,
        client,
        api_base_url="https://photos.example.test",
    )

    assert report.valid is True
    stack = next(
        operation
        for operation in report.operations
        if operation.action == "ensure_stack_with_edited_primary"
    )
    assert stack.status is ImmichMetadataOperationStatus.UNCHANGED
    assert "hidden_stack_membership_state_not_readable_in_immich_v3_0_2" in report.warnings
    assert client.mutations == []


def test_immich_metadata_reconcile_accepts_linked_live_photo_video(
    tmp_path: Path,
) -> None:
    favorite_id = "88888888-8888-4888-8888-888888888888"
    edited_image_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    edited_video_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    original_image_id = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
    original_video_id = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
    retained_pilot_id = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
    plan_path = _write_live_metadata_plan(
        tmp_path,
        favorite_asset_ids=(favorite_id,),
        album_asset_ids=(favorite_id,),
        stack_asset_ids=(
            edited_image_id,
            edited_video_id,
            original_image_id,
            original_video_id,
        ),
    )
    client = FakeImmichClient()
    client.assets = {favorite_id: {"id": favorite_id, "isFavorite": True}}
    client.stacks_by_primary[edited_image_id] = {
        "id": "ffffffff-ffff-4fff-8fff-ffffffffffff",
        "primaryAssetId": edited_image_id,
        "assets": [
            {"id": edited_image_id},
            {"id": original_image_id, "livePhotoVideoId": original_video_id},
            {"id": edited_video_id},
            {"id": retained_pilot_id},
        ],
    }

    report = reconcile_immich_metadata(
        plan_path,
        client,
        api_base_url="https://photos.example.test",
    )

    assert "existing_stack_conflict" not in report.errors
    stack = next(
        operation
        for operation in report.operations
        if operation.action == "ensure_stack_with_edited_primary"
    )
    assert stack.status is ImmichMetadataOperationStatus.UNCHANGED
