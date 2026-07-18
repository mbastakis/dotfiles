from __future__ import annotations

import json
import re
import sqlite3
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import quote

from homeserver_iac.runtime import OperationalError, run_command

IMAGE_EXTENSIONS = frozenset(
    {
        ".avif",
        ".bmp",
        ".gif",
        ".heic",
        ".heif",
        ".jpeg",
        ".jpg",
        ".png",
        ".tif",
        ".tiff",
        ".webp",
    }
)
VIDEO_EXTENSIONS = frozenset(
    {
        ".3gp",
        ".avi",
        ".m2ts",
        ".m4v",
        ".mkv",
        ".mov",
        ".mp4",
        ".mpeg",
        ".mpg",
        ".mts",
        ".webm",
        ".wmv",
    }
)
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")

CommandRunner = Callable[..., str]
ValidationProgress = Callable[[int, int, int], None]


class ExportValidationError(ValueError):
    pass


class ImportManifestError(ValueError):
    pass


class ImmichMetadataPlanError(ValueError):
    pass


class MediaKind(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class HiddenAssetPolicy(StrEnum):
    BLOCK = "block"
    INCLUDE = "include"


class ImmichMetadataOperationStatus(StrEnum):
    UNCHANGED = "unchanged"
    PENDING = "pending"
    APPLIED = "applied"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class MediaValidation:
    path: str
    source_uuid: str | None
    expected_kind: MediaKind
    detected_mime: str | None
    sha256: str | None
    valid: bool
    errors: tuple[str, ...]


@dataclass(frozen=True)
class ExportValidationReport:
    schema_version: int
    export_root: str
    errors: tuple[str, ...]
    candidate_media_files: int
    valid_media_files: int
    invalid_media_files: int
    retry_source_uuids: tuple[str, ...]
    files: tuple[MediaValidation, ...]

    @property
    def valid(self) -> bool:
        return not self.errors and self.invalid_media_files == 0


@dataclass(frozen=True)
class EvidenceFile:
    path: str
    sha256: str


@dataclass(frozen=True)
class ImportManifestEntry:
    source_uuid: str
    path: str
    relative_path: str
    media_kind: MediaKind
    rendition: str
    xmp_sidecar_path: str | None
    xmp_sidecar_size: int | None
    xmp_sidecar_sha256: str | None
    size: int
    sha256: str
    source_live_photo: bool
    source_has_adjustments: bool


@dataclass(frozen=True)
class ImportManifest:
    schema_version: int
    export_root: str
    validation_report: EvidenceFile
    source_manifests: tuple[EvidenceFile, ...]
    errors: tuple[str, ...]
    unresolved_source_uuids: tuple[str, ...]
    entries: tuple[ImportManifestEntry, ...]

    @property
    def valid(self) -> bool:
        return not self.errors and not self.unresolved_source_uuids


@dataclass(frozen=True)
class UploadAssetSupersession:
    path: str
    previous_asset_id: str
    replacement_asset_id: str


@dataclass(frozen=True)
class ImmichAssetBinding:
    source_uuid: str
    asset_id: str
    path: str
    relative_path: str
    media_kind: MediaKind
    rendition: str
    source_live_photo: bool
    source_has_adjustments: bool
    source_favorite: bool
    source_hidden: bool
    source_albums: tuple[str, ...]


@dataclass(frozen=True)
class ImmichFavoriteAction:
    action: str
    method: str
    endpoint: str
    asset_ids: tuple[str, ...]
    body: dict[str, object]


@dataclass(frozen=True)
class ImmichHiddenVisibilityAction:
    action: str
    method: str
    endpoint: str
    asset_ids: tuple[str, ...]
    body: dict[str, object]


@dataclass(frozen=True)
class ImmichAlbumAction:
    action: str
    album_name: str
    source_album_uuid: str | None
    asset_ids: tuple[str, ...]
    lookup_method: str
    lookup_endpoint: str
    create_method: str
    create_endpoint: str
    create_body: dict[str, object]
    add_method: str
    add_endpoint_template: str
    add_body: dict[str, object]


@dataclass(frozen=True)
class ImmichStackAction:
    action: str
    source_uuid: str
    source_uuids: tuple[str, ...]
    primary_asset_id: str
    asset_ids: tuple[str, ...]
    lookup_method: str
    lookup_endpoint: str
    create_method: str
    create_endpoint: str
    create_body: dict[str, object]


@dataclass(frozen=True)
class ImmichMetadataPlan:
    schema_version: int
    export_root: str
    hidden_policy: HiddenAssetPolicy
    import_manifest: EvidenceFile
    upload_results: EvidenceFile
    source_manifests: tuple[EvidenceFile, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    unresolved_asset_paths: tuple[str, ...]
    upload_paths_not_in_manifest: tuple[str, ...]
    hidden_source_uuids: tuple[str, ...]
    upload_asset_supersessions: tuple[UploadAssetSupersession, ...]
    asset_bindings: tuple[ImmichAssetBinding, ...]
    favorite_actions: tuple[ImmichFavoriteAction, ...]
    hidden_visibility_actions: tuple[ImmichHiddenVisibilityAction, ...]
    album_actions: tuple[ImmichAlbumAction, ...]
    stack_actions: tuple[ImmichStackAction, ...]

    @property
    def valid(self) -> bool:
        return not self.errors and not self.unresolved_asset_paths


@dataclass(frozen=True)
class ImmichMetadataLiveOperation:
    action: str
    status: ImmichMetadataOperationStatus
    resource_id: str
    summary: str
    asset_ids: tuple[str, ...] = ()
    changed_fields: tuple[str, ...] = ()
    album_name: str | None = None
    source_uuid: str | None = None
    primary_asset_id: str | None = None
    endpoint: str | None = None


@dataclass(frozen=True)
class ImmichMetadataReconcileReport:
    schema_version: int
    export_root: str
    metadata_plan: EvidenceFile
    api_base_url: str
    apply: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    operations: tuple[ImmichMetadataLiveOperation, ...]

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def has_pending(self) -> bool:
        return any(
            operation.status is ImmichMetadataOperationStatus.PENDING
            for operation in self.operations
        )


class ImmichMetadataClient(Protocol):
    def get_asset(self, asset_id: str) -> Mapping[str, Any]: ...

    def update_assets(self, body: Mapping[str, object]) -> Any: ...

    def find_albums(self, lookup_endpoint: str) -> tuple[Mapping[str, Any], ...]: ...

    def create_album(self, body: Mapping[str, object]) -> Mapping[str, Any]: ...

    def add_album_assets(self, album_id: str, body: Mapping[str, object]) -> Any: ...

    def get_stacks(self, lookup_endpoint: str) -> tuple[Mapping[str, Any], ...]: ...

    def create_stack(self, body: Mapping[str, object]) -> Mapping[str, Any]: ...


def _source_uuid(path: Path) -> str | None:
    for part in reversed(path.parts):
        if UUID_PATTERN.fullmatch(part):
            return part.upper()
    return None


def _expected_kind(path: Path) -> MediaKind:
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        return MediaKind.IMAGE
    return MediaKind.VIDEO


def _plist_or_xml_mime(path: Path) -> str | None:
    with path.open("rb") as file:
        prefix = file.read(4096).lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    if prefix.startswith(b"bplist00"):
        return "application/x-apple-binary-plist"
    if prefix.startswith((b"<?xml", b"<plist", b"<!doctype plist")):
        return "text/xml"
    return None


def _mime_matches(kind: MediaKind, mime: str) -> bool:
    return mime.startswith(f"{kind.value}/")


def validate_media_file(
    path: Path,
    export_root: Path,
    *,
    runner: CommandRunner = run_command,
    file_command: str = "/usr/bin/file",
    ffmpeg_command: str = "ffmpeg",
    ffmpeg_hwaccel: str | None = None,
    command_timeout: float = 10800.0,
) -> MediaValidation:
    relative_path = path.relative_to(export_root).as_posix()
    source_uuid = _source_uuid(path.relative_to(export_root))
    expected_kind = _expected_kind(path)

    if not path.is_file() or path.is_symlink():
        return MediaValidation(
            path=relative_path,
            source_uuid=source_uuid,
            expected_kind=expected_kind,
            detected_mime=None,
            sha256=None,
            valid=False,
            errors=("not_regular_file",),
        )

    content_sha256 = _sha256_file(path)
    detected_mime = _plist_or_xml_mime(path)
    if detected_mime is not None:
        return MediaValidation(
            path=relative_path,
            source_uuid=source_uuid,
            expected_kind=expected_kind,
            detected_mime=detected_mime,
            sha256=content_sha256,
            valid=False,
            errors=("plist_or_xml_content",),
        )

    try:
        detected_mime = runner(
            (file_command, "--brief", "--mime-type", str(path)),
            timeout=command_timeout,
        ).strip()
    except OperationalError:
        return MediaValidation(
            path=relative_path,
            source_uuid=source_uuid,
            expected_kind=expected_kind,
            detected_mime=None,
            sha256=content_sha256,
            valid=False,
            errors=("content_type_check_failed",),
        )

    errors: list[str] = []
    if not _mime_matches(expected_kind, detected_mime):
        errors.append("content_type_mismatch")
    if source_uuid is None:
        errors.append("missing_source_uuid")
    if errors:
        return MediaValidation(
            path=relative_path,
            source_uuid=source_uuid,
            expected_kind=expected_kind,
            detected_mime=detected_mime,
            sha256=content_sha256,
            valid=False,
            errors=tuple(errors),
        )

    decode_command = (
        ffmpeg_command,
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-xerror",
        "-i",
        str(path),
        "-map",
        "0:v:0",
        "-f",
        "null",
        "-",
    )
    hardware_decode_command = (
        (*decode_command[:6], "-hwaccel", ffmpeg_hwaccel, *decode_command[6:])
        if ffmpeg_hwaccel is not None
        else decode_command
    )
    try:
        runner(hardware_decode_command, timeout=command_timeout)
    except OperationalError:
        if ffmpeg_hwaccel is None:
            errors.append("decode_failed")
        else:
            try:
                runner(decode_command, timeout=command_timeout)
            except OperationalError:
                errors.append("decode_failed")

    final_sha256 = _sha256_file(path)
    if final_sha256 != content_sha256:
        errors.append("content_changed_during_validation")

    return MediaValidation(
        path=relative_path,
        source_uuid=source_uuid,
        expected_kind=expected_kind,
        detected_mime=detected_mime,
        sha256=final_sha256,
        valid=not errors,
        errors=tuple(errors),
    )


def validate_export(
    export_root: Path,
    *,
    runner: CommandRunner = run_command,
    file_command: str = "/usr/bin/file",
    ffmpeg_command: str = "ffmpeg",
    ffmpeg_hwaccel: str | None = None,
    command_timeout: float = 10800.0,
    workers: int = 1,
    checkpoint_path: Path | None = None,
    progress: ValidationProgress | None = None,
) -> ExportValidationReport:
    root = export_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"export root is not a directory: {root}")
    if workers < 1:
        raise ExportValidationError("validation workers must be at least 1")

    candidates = tuple(
        sorted(
            (path for path in root.rglob("*") if path.suffix.lower() in MEDIA_EXTENSIONS),
            key=lambda path: path.relative_to(root).as_posix(),
        )
    )
    relative_paths = tuple(path.relative_to(root).as_posix() for path in candidates)
    candidate_stats = {
        relative_path: path.stat()
        for path, relative_path in zip(candidates, relative_paths, strict=True)
    }
    checkpoint = (
        _open_validation_checkpoint(checkpoint_path, root) if checkpoint_path is not None else None
    )
    try:
        results = (
            _load_validation_checkpoint(checkpoint, root, candidate_stats)
            if checkpoint is not None
            else {}
        )
        resumed = len(results)
        if progress is not None:
            progress(resumed, len(candidates), resumed)

        pending = tuple(
            path
            for path, relative_path in zip(candidates, relative_paths, strict=True)
            if relative_path not in results
        )

        def validate(path: Path) -> MediaValidation:
            return validate_media_file(
                path,
                root,
                runner=runner,
                file_command=file_command,
                ffmpeg_command=ffmpeg_command,
                ffmpeg_hwaccel=ffmpeg_hwaccel,
                command_timeout=command_timeout,
            )

        if workers == 1:
            completed_results = (validate(path) for path in pending)
            for result in completed_results:
                results[result.path] = result
                if checkpoint is not None:
                    _store_validation_checkpoint_result(
                        checkpoint,
                        candidate_stats[result.path],
                        result,
                    )
                if progress is not None:
                    progress(len(results), len(candidates), resumed)
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(validate, path): path for path in pending}
                for future in as_completed(futures):
                    result = future.result()
                    results[result.path] = result
                    if checkpoint is not None:
                        _store_validation_checkpoint_result(
                            checkpoint,
                            candidate_stats[result.path],
                            result,
                        )
                    if progress is not None:
                        progress(len(results), len(candidates), resumed)
    finally:
        if checkpoint is not None:
            checkpoint.close()

    files = tuple(results[relative_path] for relative_path in relative_paths)
    retry_source_uuids = tuple(
        sorted(
            {
                result.source_uuid
                for result in files
                if not result.valid and result.source_uuid is not None
            }
        )
    )
    valid_count = sum(result.valid for result in files)
    return ExportValidationReport(
        schema_version=2,
        export_root=str(root),
        errors=() if files else ("no_media_files",),
        candidate_media_files=len(files),
        valid_media_files=valid_count,
        invalid_media_files=len(files) - valid_count,
        retry_source_uuids=retry_source_uuids,
        files=files,
    )


def _open_validation_checkpoint(path: Path, export_root: Path) -> sqlite3.Connection:
    checkpoint_path = path.resolve()
    if checkpoint_path == export_root or checkpoint_path.is_relative_to(export_root):
        raise ExportValidationError("validation checkpoint must be outside the export tree")
    if not checkpoint_path.parent.is_dir():
        raise ExportValidationError("validation checkpoint parent directory does not exist")

    try:
        connection = sqlite3.connect(checkpoint_path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS results (
                path TEXT PRIMARY KEY,
                size INTEGER NOT NULL,
                mtime_ns INTEGER NOT NULL,
                sha256 TEXT,
                result_json TEXT NOT NULL
            )
            """
        )
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        expected = {"schema_version": "2", "export_root": str(export_root)}
        if metadata:
            legacy = {"schema_version": "1", "export_root": str(export_root)}
            if metadata == legacy:
                columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(results)").fetchall()
                }
                if "sha256" not in columns:
                    connection.execute("ALTER TABLE results ADD COLUMN sha256 TEXT")
                connection.execute("UPDATE metadata SET value = '2' WHERE key = 'schema_version'")
                connection.commit()
            elif metadata != expected:
                raise ExportValidationError(
                    "validation checkpoint schema or export root does not match"
                )
        else:
            connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                expected.items(),
            )
            connection.commit()
    except sqlite3.Error as error:
        raise ExportValidationError(f"invalid validation checkpoint: {error}") from error
    return connection


def _load_validation_checkpoint(
    connection: sqlite3.Connection,
    export_root: Path,
    candidate_stats: Mapping[str, Any],
) -> dict[str, MediaValidation]:
    results: dict[str, MediaValidation] = {}
    try:
        rows = connection.execute(
            "SELECT path, size, mtime_ns, sha256, result_json FROM results"
        ).fetchall()
        for relative_path, size, mtime_ns, content_sha256, result_json in rows:
            stat = candidate_stats.get(relative_path)
            if stat is None or stat.st_size != size or stat.st_mtime_ns != mtime_ns:
                continue
            if (
                not isinstance(content_sha256, str)
                or SHA256_PATTERN.fullmatch(content_sha256) is None
                or _sha256_file(export_root / relative_path) != content_sha256
            ):
                continue
            document = json.loads(result_json)
            if not isinstance(document, Mapping) or document.get("path") != relative_path:
                raise ExportValidationError("validation checkpoint contains malformed results")
            errors = document.get("errors")
            if not isinstance(errors, list) or not all(isinstance(item, str) for item in errors):
                raise ExportValidationError("validation checkpoint contains malformed results")
            source_uuid = document.get("source_uuid")
            detected_mime = document.get("detected_mime")
            document_sha256 = document.get("sha256")
            expected_kind = document.get("expected_kind")
            valid = document.get("valid")
            if (
                (source_uuid is not None and not isinstance(source_uuid, str))
                or (detected_mime is not None and not isinstance(detected_mime, str))
                or document_sha256 != content_sha256
                or not isinstance(expected_kind, str)
                or not isinstance(valid, bool)
            ):
                raise ExportValidationError("validation checkpoint contains malformed results")
            results[relative_path] = MediaValidation(
                path=relative_path,
                source_uuid=source_uuid,
                expected_kind=MediaKind(expected_kind),
                detected_mime=detected_mime,
                sha256=content_sha256,
                valid=valid,
                errors=tuple(errors),
            )
    except (json.JSONDecodeError, sqlite3.Error, ValueError) as error:
        if isinstance(error, ExportValidationError):
            raise
        raise ExportValidationError(f"invalid validation checkpoint: {error}") from error
    return results


def _store_validation_checkpoint_result(
    connection: sqlite3.Connection,
    stat: Any,
    result: MediaValidation,
) -> None:
    try:
        connection.execute(
            """
            INSERT INTO results(path, size, mtime_ns, sha256, result_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                size = excluded.size,
                mtime_ns = excluded.mtime_ns,
                sha256 = excluded.sha256,
                result_json = excluded.result_json
            """,
            (
                result.path,
                stat.st_size,
                stat.st_mtime_ns,
                result.sha256,
                json.dumps(asdict(result), sort_keys=True),
            ),
        )
        connection.commit()
    except sqlite3.Error as error:
        raise ExportValidationError(f"could not update validation checkpoint: {error}") from error


def serialize_export_validation(report: ExportValidationReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"


def write_export_validation_report(
    report: ExportValidationReport,
    destination: Path,
) -> None:
    export_root = Path(report.export_root).resolve()
    output = destination.resolve()
    if output == export_root or output.is_relative_to(export_root):
        raise ExportValidationError("validation report must be outside the export tree")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_export_validation(report))


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    try:
        with path.open() as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise ImportManifestError(f"invalid JSON: {path}") from error


def _load_source_records(
    paths: Sequence[Path],
) -> tuple[dict[str, dict[str, Any]], tuple[EvidenceFile, ...]]:
    records: dict[str, dict[str, Any]] = {}
    evidence: list[EvidenceFile] = []
    for path in paths:
        resolved = path.resolve()
        data = _load_json(resolved)
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ImportManifestError(f"source manifest must contain a JSON array: {resolved}")
        evidence.append(EvidenceFile(path=str(resolved), sha256=_sha256_file(resolved)))
        for item in data:
            source_uuid = item.get("uuid")
            if not isinstance(source_uuid, str) or UUID_PATTERN.fullmatch(source_uuid) is None:
                raise ImportManifestError(f"source manifest contains an invalid UUID: {resolved}")
            source_uuid = source_uuid.upper()
            if source_uuid in records:
                raise ImportManifestError(f"duplicate source UUID across manifests: {source_uuid}")
            records[source_uuid] = item
    return records, tuple(evidence)


def build_import_manifest(
    validation_report_path: Path,
    source_manifest_paths: Sequence[Path],
) -> ImportManifest:
    validation_path = validation_report_path.resolve()
    validation = _load_json(validation_path)
    if not isinstance(validation, dict) or validation.get("schema_version") not in (1, 2):
        raise ImportManifestError("unsupported export validation report")
    validation_schema_version = validation["schema_version"]

    export_root_value = validation.get("export_root")
    files = validation.get("files")
    if not isinstance(export_root_value, str) or not isinstance(files, list):
        raise ImportManifestError("malformed export validation report")
    export_root = Path(export_root_value).resolve()
    if not export_root.is_dir():
        raise ImportManifestError(f"validation export root is unavailable: {export_root}")
    if not source_manifest_paths:
        raise ImportManifestError("at least one source manifest is required")

    source_records, source_evidence = _load_source_records(source_manifest_paths)
    errors: list[str] = []
    if validation_schema_version == 1:
        errors.append("validation_report_content_unbound")
    if validation.get("errors") or validation.get("invalid_media_files") != 0:
        errors.append("export_validation_failed")
    if not files:
        errors.append("no_validated_media")

    valid_files: list[dict[str, Any]] = []
    source_uuids: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            raise ImportManifestError("malformed media entry in validation report")
        source_uuid = item.get("source_uuid")
        relative_path = item.get("path")
        media_kind = item.get("expected_kind")
        if (
            not isinstance(source_uuid, str)
            or UUID_PATTERN.fullmatch(source_uuid) is None
            or not isinstance(relative_path, str)
            or media_kind not in (MediaKind.IMAGE, MediaKind.VIDEO)
        ):
            raise ImportManifestError("malformed media entry in validation report")
        if item.get("valid") is not True or item.get("errors"):
            errors.append("export_validation_failed")
            continue
        expected_sha256 = item.get("sha256")
        if (
            validation_schema_version != 2
            or not isinstance(expected_sha256, str)
            or SHA256_PATTERN.fullmatch(expected_sha256) is None
        ):
            errors.append("validation_content_binding_missing")
            continue
        source_uuid = source_uuid.upper()
        source_uuids.add(source_uuid)
        valid_files.append(item)

    unresolved = tuple(sorted(source_uuids - source_records.keys()))
    entries: list[ImportManifestEntry] = []
    for item in valid_files:
        source_uuid = str(item["source_uuid"]).upper()
        if source_uuid not in source_records:
            continue
        relative_path = Path(str(item["path"]))
        media_path = (export_root / relative_path).resolve()
        if (
            not media_path.is_relative_to(export_root)
            or not media_path.is_file()
            or media_path.is_symlink()
        ):
            errors.append("validated_media_unavailable")
            continue
        media_stat = media_path.stat()
        current_sha256 = _sha256_file(media_path)
        if current_sha256 != item["sha256"]:
            errors.append("validated_media_hash_mismatch")
            continue

        source = source_records[source_uuid]
        live_photo = source.get("live_photo")
        has_adjustments = source.get("hasadjustments")
        if not isinstance(live_photo, bool) or not isinstance(has_adjustments, bool):
            errors.append("source_metadata_incomplete")
            continue
        rendition = "edited" if "_edited" in media_path.stem.lower() else "original"
        if rendition == "edited" and not has_adjustments:
            errors.append("unexpected_edited_rendition")
            continue

        sidecar = Path(f"{media_path}.xmp")
        has_sidecar = sidecar.is_file() and not sidecar.is_symlink()
        entries.append(
            ImportManifestEntry(
                source_uuid=source_uuid,
                path=str(media_path),
                relative_path=relative_path.as_posix(),
                media_kind=MediaKind(str(item["expected_kind"])),
                rendition=rendition,
                xmp_sidecar_path=str(sidecar) if has_sidecar else None,
                xmp_sidecar_size=sidecar.stat().st_size if has_sidecar else None,
                xmp_sidecar_sha256=_sha256_file(sidecar) if has_sidecar else None,
                size=media_stat.st_size,
                sha256=current_sha256,
                source_live_photo=live_photo,
                source_has_adjustments=has_adjustments,
            )
        )

    return ImportManifest(
        schema_version=2,
        export_root=str(export_root),
        validation_report=EvidenceFile(
            path=str(validation_path),
            sha256=_sha256_file(validation_path),
        ),
        source_manifests=source_evidence,
        errors=tuple(sorted(set(errors))),
        unresolved_source_uuids=unresolved,
        entries=tuple(entries),
    )


def serialize_import_manifest(manifest: ImportManifest) -> str:
    return json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n"


def write_import_manifest(manifest: ImportManifest, destination: Path) -> None:
    export_root = Path(manifest.export_root).resolve()
    output = destination.resolve()
    if output == export_root or output.is_relative_to(export_root):
        raise ImportManifestError("import manifest must be outside the export tree")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_import_manifest(manifest))


def _normalized_path(value: str) -> str:
    return str(Path(value).expanduser().resolve())


def _extract_json_values(text: str) -> tuple[Any, ...]:
    decoder = json.JSONDecoder()
    values: list[Any] = []
    index = 0
    while index < len(text):
        starts = [
            position for position in (text.find("{", index), text.find("[", index)) if position >= 0
        ]
        if not starts:
            break
        index = min(starts)
        try:
            value, end = decoder.raw_decode(text, index)
        except json.JSONDecodeError:
            index += 1
            continue
        values.append(value)
        index = end
    return tuple(values)


def _upload_result_objects(value: Any) -> tuple[dict[str, Any], ...]:
    if isinstance(value, dict):
        return (value,)
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, dict))
    return ()


def _load_immich_upload_asset_map(
    path: Path,
) -> tuple[dict[str, str], EvidenceFile, tuple[UploadAssetSupersession, ...]]:
    resolved = path.resolve()
    values = _extract_json_values(resolved.read_text())
    if not values:
        raise ImmichMetadataPlanError(f"upload results contain no JSON objects: {resolved}")

    asset_ids_by_path: dict[str, str] = {}
    supersessions: list[UploadAssetSupersession] = []
    for value in values:
        for result in _upload_result_objects(value):
            for key in ("duplicates", "newAssets"):
                assets = result.get(key)
                if not isinstance(assets, list):
                    continue
                for asset in assets:
                    if not isinstance(asset, dict):
                        raise ImmichMetadataPlanError("upload asset result must be an object")
                    asset_id = asset.get("id", asset.get("assetId"))
                    filepath = asset.get("filepath", asset.get("path"))
                    if not isinstance(asset_id, str) or UUID_PATTERN.fullmatch(asset_id) is None:
                        raise ImmichMetadataPlanError("upload asset result contains an invalid ID")
                    if not isinstance(filepath, str) or not filepath:
                        raise ImmichMetadataPlanError(
                            "upload asset result contains an invalid path"
                        )
                    normalized = _normalized_path(filepath)
                    asset_id = asset_id.lower()
                    previous = asset_ids_by_path.get(normalized)
                    if previous is not None and previous != asset_id:
                        supersessions.append(
                            UploadAssetSupersession(
                                path=normalized,
                                previous_asset_id=previous,
                                replacement_asset_id=asset_id,
                            )
                        )
                    asset_ids_by_path[normalized] = asset_id

    return (
        asset_ids_by_path,
        EvidenceFile(path=str(resolved), sha256=_sha256_file(resolved)),
        tuple(supersessions),
    )


def _source_manifest_paths_from_import_manifest(
    import_manifest: dict[str, Any],
) -> tuple[tuple[Path, str], ...]:
    source_manifest_values = import_manifest.get("source_manifests")
    if not isinstance(source_manifest_values, list) or not source_manifest_values:
        raise ImmichMetadataPlanError("import manifest has no source manifest evidence")

    source_manifests: list[tuple[Path, str]] = []
    for item in source_manifest_values:
        if not isinstance(item, dict):
            raise ImmichMetadataPlanError("source manifest evidence must be an object")
        path = item.get("path")
        checksum = item.get("sha256")
        if not isinstance(path, str) or not isinstance(checksum, str):
            raise ImmichMetadataPlanError("source manifest evidence is incomplete")
        source_manifests.append((Path(path).resolve(), checksum))
    return tuple(source_manifests)


def _load_source_records_from_import_manifest(
    import_manifest: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], tuple[EvidenceFile, ...], tuple[str, ...]]:
    source_manifest_values = _source_manifest_paths_from_import_manifest(import_manifest)
    source_paths = tuple(path for path, _checksum in source_manifest_values)
    source_records, evidence = _load_source_records(source_paths)
    expected_checksums = {str(path): checksum for path, checksum in source_manifest_values}
    errors = tuple(
        "source_manifest_hash_mismatch"
        for item in evidence
        if expected_checksums.get(item.path) != item.sha256
    )
    return source_records, evidence, errors


def _source_bool(record: dict[str, Any], key: str) -> bool | None:
    value = record.get(key)
    return value if isinstance(value, bool) else None


def _source_albums(record: dict[str, Any]) -> tuple[str, ...] | None:
    albums = record.get("albums")
    if not isinstance(albums, list):
        return None
    if not all(isinstance(album, str) and album for album in albums):
        return None
    return tuple(albums)


def _source_album_uuids(record: dict[str, Any]) -> dict[str, str | None]:
    album_uuids: dict[str, str | None] = {}
    album_info = record.get("album_info")
    if not isinstance(album_info, list):
        return album_uuids
    for item in album_info:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        album_uuid = item.get("uuid")
        if not isinstance(title, str) or not title:
            continue
        if isinstance(album_uuid, str) and UUID_PATTERN.fullmatch(album_uuid) is not None:
            album_uuids[title] = album_uuid.upper()
        else:
            album_uuids[title] = None
    return album_uuids


def _manifest_entry_path(entry: dict[str, Any]) -> str:
    value = entry.get("path")
    if not isinstance(value, str) or not value:
        raise ImmichMetadataPlanError("import manifest entry has an invalid path")
    return _normalized_path(value)


def _favorite_actions(bindings: Sequence[ImmichAssetBinding]) -> tuple[ImmichFavoriteAction, ...]:
    asset_ids = tuple(binding.asset_id for binding in bindings if binding.source_favorite)
    if not asset_ids:
        return ()
    return (
        ImmichFavoriteAction(
            action="set_favorite_true",
            method="PUT",
            endpoint="/api/assets",
            asset_ids=asset_ids,
            body={"ids": list(asset_ids), "isFavorite": True},
        ),
    )


def _hidden_visibility_actions(
    bindings: Sequence[ImmichAssetBinding],
    hidden_policy: HiddenAssetPolicy,
) -> tuple[ImmichHiddenVisibilityAction, ...]:
    if hidden_policy != HiddenAssetPolicy.INCLUDE:
        return ()
    asset_ids = tuple(binding.asset_id for binding in bindings if binding.source_hidden)
    if not asset_ids:
        return ()
    return (
        ImmichHiddenVisibilityAction(
            action="set_visibility_hidden",
            method="PUT",
            endpoint="/api/assets",
            asset_ids=asset_ids,
            body={"ids": list(asset_ids), "visibility": "hidden"},
        ),
    )


def _album_actions(
    bindings_by_source: dict[str, tuple[ImmichAssetBinding, ...]],
    source_album_uuids_by_name: dict[str, str | None],
) -> tuple[ImmichAlbumAction, ...]:
    asset_ids_by_album: dict[str, set[str]] = {}
    for source_bindings in bindings_by_source.values():
        if not source_bindings:
            continue
        source_asset_ids = {binding.asset_id for binding in source_bindings}
        for album_name in source_bindings[0].source_albums:
            asset_ids_by_album.setdefault(album_name, set()).update(source_asset_ids)

    actions: list[ImmichAlbumAction] = []
    for album_name in sorted(asset_ids_by_album):
        album_asset_ids = tuple(sorted(asset_ids_by_album[album_name]))
        encoded_name = quote(album_name, safe="")
        actions.append(
            ImmichAlbumAction(
                action="ensure_album_assets",
                album_name=album_name,
                source_album_uuid=source_album_uuids_by_name.get(album_name),
                asset_ids=album_asset_ids,
                lookup_method="GET",
                lookup_endpoint=(f"/api/albums?name={encoded_name}&isOwned=true&isShared=false"),
                create_method="POST",
                create_endpoint="/api/albums",
                create_body={"albumName": album_name},
                add_method="PUT",
                add_endpoint_template="/api/albums/{album_id}/assets",
                add_body={"ids": list(album_asset_ids)},
            )
        )
    return tuple(actions)


def _stack_sort_key(binding: ImmichAssetBinding) -> tuple[int, int, str]:
    rendition_rank = 0 if binding.rendition == "edited" else 1
    media_rank = 0 if binding.media_kind == MediaKind.IMAGE else 1
    return (rendition_rank, media_rank, binding.relative_path)


def _stack_actions(
    bindings_by_source: dict[str, tuple[ImmichAssetBinding, ...]],
) -> tuple[ImmichStackAction, ...]:
    candidates: list[tuple[str, str, tuple[str, ...]]] = []
    for source_uuid in sorted(bindings_by_source):
        source_bindings = bindings_by_source[source_uuid]
        if not source_bindings or not source_bindings[0].source_has_adjustments:
            continue
        edited = tuple(binding for binding in source_bindings if binding.rendition == "edited")
        original = tuple(binding for binding in source_bindings if binding.rendition == "original")
        if not edited or not original:
            continue
        primary = sorted(edited, key=_stack_sort_key)[0]
        ordered = (
            primary,
            *(
                binding
                for binding in sorted(source_bindings, key=_stack_sort_key)
                if binding.asset_id != primary.asset_id
            ),
        )
        asset_ids = tuple(dict.fromkeys(binding.asset_id for binding in ordered))
        if len(asset_ids) < 2:
            continue
        candidates.append((source_uuid, primary.asset_id, asset_ids))

    groups: list[tuple[tuple[str, ...], str, tuple[str, ...]]] = []
    for source_uuid, primary_asset_id, asset_ids in candidates:
        overlapping = [
            index
            for index, (_, _, grouped_asset_ids) in enumerate(groups)
            if set(asset_ids) & set(grouped_asset_ids)
        ]
        if not overlapping:
            groups.append(((source_uuid,), primary_asset_id, asset_ids))
            continue

        components = [(source_uuid, primary_asset_id, asset_ids)]
        for index in reversed(overlapping):
            source_uuids, grouped_primary, grouped_asset_ids = groups.pop(index)
            components.extend(
                (grouped_source_uuid, grouped_primary, grouped_asset_ids)
                for grouped_source_uuid in source_uuids
            )
        components.sort(key=lambda component: component[0])
        grouped_source_uuids = tuple(component[0] for component in components)
        grouped_primary = components[0][1]
        grouped_asset_ids = tuple(
            dict.fromkeys(
                [grouped_primary]
                + [
                    asset_id
                    for _, _, component_asset_ids in components
                    for asset_id in component_asset_ids
                    if asset_id != grouped_primary
                ]
            )
        )
        groups.append((grouped_source_uuids, grouped_primary, grouped_asset_ids))

    actions: list[ImmichStackAction] = []
    for source_uuids, primary_asset_id, asset_ids in sorted(groups):
        source_uuid = source_uuids[0]
        actions.append(
            ImmichStackAction(
                action="ensure_stack_with_edited_primary",
                source_uuid=source_uuid,
                source_uuids=source_uuids,
                primary_asset_id=primary_asset_id,
                asset_ids=asset_ids,
                lookup_method="GET",
                lookup_endpoint=f"/api/stacks?primaryAssetId={primary_asset_id}",
                create_method="POST",
                create_endpoint="/api/stacks",
                create_body={"assetIds": list(asset_ids)},
            )
        )
    return tuple(actions)


def build_immich_metadata_plan(
    import_manifest_path: Path,
    upload_results_path: Path,
    *,
    hidden_policy: HiddenAssetPolicy = HiddenAssetPolicy.BLOCK,
) -> ImmichMetadataPlan:
    manifest_path = import_manifest_path.resolve()
    import_manifest = _load_json(manifest_path)
    if not isinstance(import_manifest, dict) or import_manifest.get("schema_version") != 2:
        raise ImmichMetadataPlanError("unsupported import manifest")

    export_root_value = import_manifest.get("export_root")
    entries = import_manifest.get("entries")
    if not isinstance(export_root_value, str) or not isinstance(entries, list):
        raise ImmichMetadataPlanError("malformed import manifest")
    export_root = Path(export_root_value).resolve()

    errors: list[str] = []
    warnings: list[str] = []
    if import_manifest.get("errors") or import_manifest.get("unresolved_source_uuids"):
        errors.append("import_manifest_invalid")
    if not entries:
        errors.append("no_import_manifest_entries")

    source_records, source_evidence, source_errors = _load_source_records_from_import_manifest(
        import_manifest
    )
    errors.extend(source_errors)
    upload_asset_ids_by_path, upload_evidence, supersessions = _load_immich_upload_asset_map(
        upload_results_path
    )
    if supersessions:
        warnings.append("upload_results_contain_superseded_asset_ids")

    entries_by_path: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ImmichMetadataPlanError("import manifest entry must be an object")
        path = _manifest_entry_path(entry)
        if path in entries_by_path:
            raise ImmichMetadataPlanError(f"duplicate import manifest path: {path}")
        entries_by_path[path] = entry

    unresolved_asset_paths = tuple(sorted(entries_by_path.keys() - upload_asset_ids_by_path.keys()))
    upload_paths_not_in_manifest = tuple(
        sorted(upload_asset_ids_by_path.keys() - entries_by_path.keys())
    )
    if unresolved_asset_paths:
        errors.append("uploaded_asset_id_unresolved")
    if upload_paths_not_in_manifest:
        errors.append("upload_result_path_not_in_import_manifest")

    source_album_uuids_by_name: dict[str, str | None] = {}
    hidden_source_uuids: set[str] = set()
    bindings: list[ImmichAssetBinding] = []
    bindings_by_source: dict[str, list[ImmichAssetBinding]] = {}
    for path, entry in sorted(entries_by_path.items()):
        source_uuid = entry.get("source_uuid")
        relative_path = entry.get("relative_path")
        media_kind = entry.get("media_kind")
        rendition = entry.get("rendition")
        live_photo = entry.get("source_live_photo")
        has_adjustments = entry.get("source_has_adjustments")
        if (
            not isinstance(source_uuid, str)
            or UUID_PATTERN.fullmatch(source_uuid) is None
            or not isinstance(relative_path, str)
            or media_kind not in (MediaKind.IMAGE, MediaKind.VIDEO)
            or rendition not in ("original", "edited")
            or not isinstance(live_photo, bool)
            or not isinstance(has_adjustments, bool)
        ):
            raise ImmichMetadataPlanError("malformed import manifest entry")
        source_uuid = source_uuid.upper()
        source = source_records.get(source_uuid)
        if source is None:
            errors.append("source_metadata_unavailable")
            continue
        favorite = _source_bool(source, "favorite")
        hidden = _source_bool(source, "hidden")
        albums = _source_albums(source)
        if favorite is None or hidden is None or albums is None:
            errors.append("source_metadata_incomplete")
            continue
        if hidden:
            hidden_source_uuids.add(source_uuid)
        for album_name, album_uuid in _source_album_uuids(source).items():
            if album_name not in source_album_uuids_by_name:
                source_album_uuids_by_name[album_name] = album_uuid
                continue
            previous = source_album_uuids_by_name[album_name]
            if previous is None and album_uuid is not None:
                source_album_uuids_by_name[album_name] = album_uuid
            elif previous is not None and album_uuid is not None and previous != album_uuid:
                errors.append("ambiguous_source_album_name")
        asset_id = upload_asset_ids_by_path.get(path)
        if asset_id is None:
            continue
        binding = ImmichAssetBinding(
            source_uuid=source_uuid,
            asset_id=asset_id,
            path=path,
            relative_path=relative_path,
            media_kind=MediaKind(str(media_kind)),
            rendition=rendition,
            source_live_photo=live_photo,
            source_has_adjustments=has_adjustments,
            source_favorite=favorite,
            source_hidden=hidden,
            source_albums=albums,
        )
        bindings.append(binding)
        bindings_by_source.setdefault(source_uuid, []).append(binding)

    if hidden_source_uuids and hidden_policy == HiddenAssetPolicy.BLOCK:
        errors.append("hidden_policy_unresolved")
    adjusted_without_edited = tuple(
        source_uuid
        for source_uuid, source_bindings in bindings_by_source.items()
        if source_bindings[0].source_has_adjustments
        and not any(binding.rendition == "edited" for binding in source_bindings)
    )
    if adjusted_without_edited:
        warnings.append("adjusted_sources_without_edited_renditions")

    frozen_bindings_by_source = {
        source_uuid: tuple(sorted(source_bindings, key=lambda binding: binding.relative_path))
        for source_uuid, source_bindings in bindings_by_source.items()
    }
    sorted_bindings = tuple(sorted(bindings, key=lambda binding: binding.relative_path))
    stack_actions = _stack_actions(frozen_bindings_by_source)
    if any(len(action.source_uuids) > 1 for action in stack_actions):
        warnings.append("stack_actions_coalesced_for_deduplicated_assets")
    return ImmichMetadataPlan(
        schema_version=2,
        export_root=str(export_root),
        hidden_policy=hidden_policy,
        import_manifest=EvidenceFile(path=str(manifest_path), sha256=_sha256_file(manifest_path)),
        upload_results=upload_evidence,
        source_manifests=source_evidence,
        errors=tuple(sorted(set(errors))),
        warnings=tuple(sorted(set(warnings))),
        unresolved_asset_paths=unresolved_asset_paths,
        upload_paths_not_in_manifest=upload_paths_not_in_manifest,
        hidden_source_uuids=tuple(sorted(hidden_source_uuids)),
        upload_asset_supersessions=supersessions,
        asset_bindings=sorted_bindings,
        favorite_actions=_favorite_actions(sorted_bindings),
        hidden_visibility_actions=_hidden_visibility_actions(sorted_bindings, hidden_policy),
        album_actions=_album_actions(frozen_bindings_by_source, source_album_uuids_by_name),
        stack_actions=stack_actions,
    )


def serialize_immich_metadata_plan(plan: ImmichMetadataPlan) -> str:
    return json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n"


def write_immich_metadata_plan(plan: ImmichMetadataPlan, destination: Path) -> None:
    export_root = Path(plan.export_root).resolve()
    output = destination.resolve()
    if output == export_root or output.is_relative_to(export_root):
        raise ImmichMetadataPlanError("Immich metadata plan must be outside the export tree")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_immich_metadata_plan(plan))


def _expect_json_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise OperationalError(f"Immich {context} returned an unexpected response")
    result: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise OperationalError(f"Immich {context} returned a non-string field name")
        result[key] = item
    return result


def _expect_json_objects(value: Any, context: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise OperationalError(f"Immich {context} returned an unexpected response")
    return tuple(_expect_json_object(item, context) for item in value)


class ImmichApiClient:
    def __init__(self, base_url: str, api_key: str, *, timeout: float = 20.0) -> None:
        if not base_url:
            raise OperationalError("Immich API base URL is required")
        if not api_key:
            raise OperationalError("Immich API key is required")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def request(self, method: str, endpoint: str, body: Mapping[str, object] | None = None) -> Any:
        if not endpoint.startswith("/"):
            raise OperationalError("Immich API endpoint must be absolute")
        headers = {"Accept": "application/json", "x-api-key": self.api_key}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body, separators=(",", ":")).encode()
        request = urllib.request.Request(
            f"{self.base_url}{endpoint}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_body = response.read()
        except urllib.error.HTTPError as error:
            raise OperationalError(
                f"Immich {method} {endpoint} failed with HTTP {error.code}"
            ) from error
        except (TimeoutError, urllib.error.URLError) as error:
            raise OperationalError(f"Immich {method} {endpoint} request failed") from error
        if not response_body:
            return None
        try:
            return json.loads(response_body)
        except json.JSONDecodeError as error:
            raise OperationalError(f"Immich {method} {endpoint} returned invalid JSON") from error

    def get_asset(self, asset_id: str) -> Mapping[str, Any]:
        return _expect_json_object(
            self.request("GET", f"/api/assets/{quote(asset_id, safe='')}"),
            "asset lookup",
        )

    def update_assets(self, body: Mapping[str, object]) -> Any:
        return self.request("PUT", "/api/assets", body)

    def find_albums(self, lookup_endpoint: str) -> tuple[Mapping[str, Any], ...]:
        return _expect_json_objects(self.request("GET", lookup_endpoint), "album lookup")

    def create_album(self, body: Mapping[str, object]) -> Mapping[str, Any]:
        return _expect_json_object(self.request("POST", "/api/albums", body), "album create")

    def add_album_assets(self, album_id: str, body: Mapping[str, object]) -> Any:
        return self.request("PUT", f"/api/albums/{quote(album_id, safe='')}/assets", body)

    def get_stacks(self, lookup_endpoint: str) -> tuple[Mapping[str, Any], ...]:
        return _expect_json_objects(self.request("GET", lookup_endpoint), "stack lookup")

    def create_stack(self, body: Mapping[str, object]) -> Mapping[str, Any]:
        return _expect_json_object(self.request("POST", "/api/stacks", body), "stack create")


def _load_immich_metadata_plan_document(
    path: Path,
) -> tuple[dict[str, Any], EvidenceFile]:
    resolved = path.resolve()
    try:
        data = _load_json(resolved)
    except ImportManifestError as error:
        raise ImmichMetadataPlanError(f"invalid Immich metadata plan JSON: {resolved}") from error
    if not isinstance(data, dict) or data.get("schema_version") != 2:
        raise ImmichMetadataPlanError("unsupported Immich metadata plan")
    errors = data.get("errors")
    unresolved = data.get("unresolved_asset_paths")
    if not isinstance(errors, list) or not isinstance(unresolved, list):
        raise ImmichMetadataPlanError("malformed Immich metadata plan")
    if errors or unresolved:
        raise ImmichMetadataPlanError("Immich metadata plan is invalid")
    return data, EvidenceFile(path=str(resolved), sha256=_sha256_file(resolved))


def _plan_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise ImmichMetadataPlanError(f"Immich metadata plan has an invalid {context}")
    return value


def _plan_strings(value: Any, context: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ImmichMetadataPlanError(f"Immich metadata plan has invalid {context}")
    return tuple(value)


def _plan_actions(
    document: Mapping[str, Any],
    key: str,
    *,
    required: bool = True,
) -> tuple[dict[str, Any], ...]:
    value = document.get(key)
    if value is None and not required:
        return ()
    if not isinstance(value, list):
        raise ImmichMetadataPlanError(f"Immich metadata plan has invalid {key}")
    return tuple(_expect_plan_action(item, key) for item in value)


def _expect_plan_action(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ImmichMetadataPlanError(f"Immich metadata plan has invalid {context}")
    result: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ImmichMetadataPlanError(f"Immich metadata plan has invalid {context}")
        result[key] = item
    return result


def _plan_warnings(document: Mapping[str, Any]) -> tuple[str, ...]:
    value = document.get("warnings")
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ImmichMetadataPlanError("Immich metadata plan has invalid warnings")
    return tuple(value)


def _response_id(value: Mapping[str, Any], context: str) -> str:
    identifier = value.get("id")
    if not isinstance(identifier, str) or UUID_PATTERN.fullmatch(identifier) is None:
        raise OperationalError(f"Immich {context} response did not include a valid ID")
    return identifier.lower()


def _favorite_state(
    client: ImmichMetadataClient,
    asset_id: str,
    unreadable: list[str],
) -> bool | None:
    favorite = client.get_asset(asset_id).get("isFavorite")
    if not isinstance(favorite, bool):
        unreadable.append(asset_id)
        return None
    return favorite


def _visibility_state(
    client: ImmichMetadataClient,
    asset_id: str,
    unreadable: list[str],
) -> str | None:
    visibility = client.get_asset(asset_id).get("visibility")
    if not isinstance(visibility, str):
        unreadable.append(asset_id)
        return None
    return visibility


def _reconcile_favorite_action(
    action: Mapping[str, Any],
    client: ImmichMetadataClient,
    *,
    apply_changes: bool,
    errors: list[str],
) -> ImmichMetadataLiveOperation:
    asset_ids = _plan_strings(action.get("asset_ids"), "favorite asset IDs")
    unreadable: list[str] = []
    needs_update = tuple(
        asset_id for asset_id in asset_ids if _favorite_state(client, asset_id, unreadable) is False
    )
    if unreadable:
        errors.append("favorite_state_unreadable")
        return ImmichMetadataLiveOperation(
            action="set_favorite_true",
            status=ImmichMetadataOperationStatus.BLOCKED,
            resource_id="favorites",
            summary="One or more asset favorite states could not be read",
            asset_ids=tuple(unreadable),
            changed_fields=("isFavorite",),
            endpoint="/api/assets",
        )
    if not needs_update:
        return ImmichMetadataLiveOperation(
            action="set_favorite_true",
            status=ImmichMetadataOperationStatus.UNCHANGED,
            resource_id="favorites",
            summary="All planned favorite assets are already favorites",
            asset_ids=asset_ids,
            endpoint="/api/assets",
        )
    if not apply_changes:
        return ImmichMetadataLiveOperation(
            action="set_favorite_true",
            status=ImmichMetadataOperationStatus.PENDING,
            resource_id="favorites",
            summary="Favorite state would be set on planned assets",
            asset_ids=needs_update,
            changed_fields=("isFavorite",),
            endpoint="/api/assets",
        )

    client.update_assets({"ids": list(needs_update), "isFavorite": True})
    verify_unreadable: list[str] = []
    unverified = tuple(
        asset_id
        for asset_id in needs_update
        if _favorite_state(client, asset_id, verify_unreadable) is not True
    )
    if verify_unreadable or unverified:
        errors.append("favorite_update_unverified")
        return ImmichMetadataLiveOperation(
            action="set_favorite_true",
            status=ImmichMetadataOperationStatus.BLOCKED,
            resource_id="favorites",
            summary="Favorite update was accepted but could not be verified",
            asset_ids=tuple(sorted(set(verify_unreadable) | set(unverified))),
            changed_fields=("isFavorite",),
            endpoint="/api/assets",
        )
    return ImmichMetadataLiveOperation(
        action="set_favorite_true",
        status=ImmichMetadataOperationStatus.APPLIED,
        resource_id="favorites",
        summary="Favorite state was set on planned assets",
        asset_ids=needs_update,
        changed_fields=("isFavorite",),
        endpoint="/api/assets",
    )


def _reconcile_hidden_visibility_action(
    action: Mapping[str, Any],
    client: ImmichMetadataClient,
    *,
    apply_changes: bool,
    errors: list[str],
) -> ImmichMetadataLiveOperation:
    asset_ids = _plan_strings(action.get("asset_ids"), "hidden visibility asset IDs")
    unreadable: list[str] = []
    needs_update: list[str] = []
    for asset_id in asset_ids:
        visibility = _visibility_state(client, asset_id, unreadable)
        if visibility is not None and visibility != "hidden":
            needs_update.append(asset_id)

    if unreadable:
        errors.append("hidden_visibility_state_unreadable")
        return ImmichMetadataLiveOperation(
            action="set_visibility_hidden",
            status=ImmichMetadataOperationStatus.BLOCKED,
            resource_id="hidden_visibility",
            summary="One or more asset visibility states could not be read",
            asset_ids=tuple(unreadable),
            changed_fields=("visibility",),
            endpoint="/api/assets",
        )
    if not needs_update:
        return ImmichMetadataLiveOperation(
            action="set_visibility_hidden",
            status=ImmichMetadataOperationStatus.UNCHANGED,
            resource_id="hidden_visibility",
            summary="All planned hidden assets already have hidden visibility",
            asset_ids=asset_ids,
            endpoint="/api/assets",
        )
    if not apply_changes:
        return ImmichMetadataLiveOperation(
            action="set_visibility_hidden",
            status=ImmichMetadataOperationStatus.PENDING,
            resource_id="hidden_visibility",
            summary="Hidden visibility would be set on planned assets",
            asset_ids=tuple(needs_update),
            changed_fields=("visibility",),
            endpoint="/api/assets",
        )

    client.update_assets({"ids": needs_update, "visibility": "hidden"})
    verify_unreadable: list[str] = []
    unverified = tuple(
        asset_id
        for asset_id in needs_update
        if _visibility_state(client, asset_id, verify_unreadable) != "hidden"
    )
    if verify_unreadable or unverified:
        errors.append("hidden_visibility_update_unverified")
        return ImmichMetadataLiveOperation(
            action="set_visibility_hidden",
            status=ImmichMetadataOperationStatus.BLOCKED,
            resource_id="hidden_visibility",
            summary="Hidden visibility update was accepted but could not be verified",
            asset_ids=tuple(sorted(set(verify_unreadable) | set(unverified))),
            changed_fields=("visibility",),
            endpoint="/api/assets",
        )
    return ImmichMetadataLiveOperation(
        action="set_visibility_hidden",
        status=ImmichMetadataOperationStatus.APPLIED,
        resource_id="hidden_visibility",
        summary="Hidden visibility was set on planned assets",
        asset_ids=tuple(needs_update),
        changed_fields=("visibility",),
        endpoint="/api/assets",
    )


def _album_add_failures(response: Any) -> tuple[str, ...]:
    if response is None:
        return ()
    failures: list[str] = []
    for item in _expect_json_objects(response, "album asset add"):
        success = item.get("success")
        if success is True:
            continue
        identifier = item.get("id")
        asset_id = identifier if isinstance(identifier, str) else "unknown"
        message = item.get("errorMessage", item.get("error", ""))
        message_text = message if isinstance(message, str) else ""
        if success is False and re.search(r"already|duplicate", message_text, re.IGNORECASE):
            continue
        failures.append(asset_id)
    return tuple(failures)


def _reconcile_album_action(
    action: Mapping[str, Any],
    client: ImmichMetadataClient,
    *,
    apply_changes: bool,
    errors: list[str],
) -> ImmichMetadataLiveOperation:
    album_name = _plan_string(action.get("album_name"), "album name")
    asset_ids = _plan_strings(action.get("asset_ids"), "album asset IDs")
    lookup_endpoint = _plan_string(action.get("lookup_endpoint"), "album lookup endpoint")
    albums = tuple(
        album
        for album in client.find_albums(lookup_endpoint)
        if album.get("albumName") == album_name
    )
    if len(albums) > 1:
        errors.append("ambiguous_immich_album_name")
        return ImmichMetadataLiveOperation(
            action="ensure_album_assets",
            status=ImmichMetadataOperationStatus.BLOCKED,
            resource_id=f"album:{album_name}",
            summary="Multiple owned unshared Immich albums matched the source album name",
            asset_ids=asset_ids,
            album_name=album_name,
            changed_fields=("album", "assets"),
            endpoint=lookup_endpoint,
        )

    if not albums:
        if not apply_changes:
            return ImmichMetadataLiveOperation(
                action="ensure_album_assets",
                status=ImmichMetadataOperationStatus.PENDING,
                resource_id=f"album:{album_name}",
                summary="Album is absent and would be created before adding assets",
                asset_ids=asset_ids,
                album_name=album_name,
                changed_fields=("album", "assets"),
                endpoint="/api/albums",
            )
        album_id = _response_id(client.create_album({"albumName": album_name}), "album create")
        failures = _album_add_failures(client.add_album_assets(album_id, {"ids": list(asset_ids)}))
        if failures:
            errors.append("album_asset_add_failed")
            return ImmichMetadataLiveOperation(
                action="ensure_album_assets",
                status=ImmichMetadataOperationStatus.BLOCKED,
                resource_id=f"album:{album_name}",
                summary="Album was created but one or more asset additions failed",
                asset_ids=failures,
                album_name=album_name,
                changed_fields=("assets",),
                endpoint=f"/api/albums/{album_id}/assets",
            )
        return ImmichMetadataLiveOperation(
            action="ensure_album_assets",
            status=ImmichMetadataOperationStatus.APPLIED,
            resource_id=f"album:{album_name}",
            summary="Album was created and planned assets were added",
            asset_ids=asset_ids,
            album_name=album_name,
            changed_fields=("album", "assets"),
            endpoint=f"/api/albums/{album_id}/assets",
        )

    album_id = _response_id(albums[0], "album lookup")
    if not apply_changes:
        return ImmichMetadataLiveOperation(
            action="ensure_album_assets",
            status=ImmichMetadataOperationStatus.PENDING,
            resource_id=f"album:{album_name}",
            summary="Album exists; Immich v3.0.2 does not expose album asset membership",
            asset_ids=asset_ids,
            album_name=album_name,
            changed_fields=("assets",),
            endpoint=f"/api/albums/{album_id}/assets",
        )
    failures = _album_add_failures(client.add_album_assets(album_id, {"ids": list(asset_ids)}))
    if failures:
        errors.append("album_asset_add_failed")
        return ImmichMetadataLiveOperation(
            action="ensure_album_assets",
            status=ImmichMetadataOperationStatus.BLOCKED,
            resource_id=f"album:{album_name}",
            summary="One or more asset additions to the existing album failed",
            asset_ids=failures,
            album_name=album_name,
            changed_fields=("assets",),
            endpoint=f"/api/albums/{album_id}/assets",
        )
    return ImmichMetadataLiveOperation(
        action="ensure_album_assets",
        status=ImmichMetadataOperationStatus.APPLIED,
        resource_id=f"album:{album_name}",
        summary="Album exists and planned asset membership was re-applied",
        asset_ids=asset_ids,
        album_name=album_name,
        changed_fields=("assets",),
        endpoint=f"/api/albums/{album_id}/assets",
    )


def _stack_asset_ids(stack: Mapping[str, Any]) -> tuple[str, ...]:
    assets = stack.get("assets")
    if not isinstance(assets, list):
        raise OperationalError("Immich stack response did not include assets")
    asset_ids: list[str] = []
    for asset in assets:
        asset_value = _expect_json_object(asset, "stack asset")
        asset_id = asset_value.get("id")
        if not isinstance(asset_id, str) or UUID_PATTERN.fullmatch(asset_id) is None:
            raise OperationalError("Immich stack response included an invalid asset ID")
        asset_ids.append(asset_id.lower())
        live_photo_video_id = asset_value.get("livePhotoVideoId")
        if live_photo_video_id is None:
            continue
        if (
            not isinstance(live_photo_video_id, str)
            or UUID_PATTERN.fullmatch(live_photo_video_id) is None
        ):
            raise OperationalError("Immich stack response included an invalid Live Photo video ID")
        asset_ids.append(live_photo_video_id.lower())
    return tuple(asset_ids)


def _stack_matches(
    stack: Mapping[str, Any],
    primary_asset_id: str,
    asset_ids: Sequence[str],
    *,
    allow_filtered_assets: bool = False,
) -> bool:
    primary = stack.get("primaryAssetId")
    if not isinstance(primary, str) or UUID_PATTERN.fullmatch(primary) is None:
        raise OperationalError("Immich stack response did not include a valid primary asset ID")
    expected_asset_ids = {asset_id.lower() for asset_id in asset_ids}
    actual_asset_ids = set(_stack_asset_ids(stack))
    return primary.lower() == primary_asset_id.lower() and (
        expected_asset_ids.issubset(actual_asset_ids)
        or (allow_filtered_assets and not actual_asset_ids)
    )


def _stack_lookup_endpoint(primary_asset_id: str) -> str:
    return f"/api/stacks?primaryAssetId={quote(primary_asset_id, safe='')}"


def _existing_stacks_for_action(
    client: ImmichMetadataClient,
    asset_ids: Sequence[str],
) -> tuple[Mapping[str, Any], ...]:
    stacks_by_id: dict[str, Mapping[str, Any]] = {}
    for asset_id in asset_ids:
        for stack in client.get_stacks(_stack_lookup_endpoint(asset_id)):
            stacks_by_id[_response_id(stack, "stack lookup")] = stack
    return tuple(stacks_by_id.values())


def _reconcile_stack_action(
    action: Mapping[str, Any],
    client: ImmichMetadataClient,
    *,
    apply_changes: bool,
    errors: list[str],
    hidden_asset_ids: frozenset[str],
) -> ImmichMetadataLiveOperation:
    source_uuid = _plan_string(action.get("source_uuid"), "stack source UUID")
    primary_asset_id = _plan_string(action.get("primary_asset_id"), "stack primary asset ID")
    asset_ids = _plan_strings(action.get("asset_ids"), "stack asset IDs")
    if len(asset_ids) < 2 or asset_ids[0].lower() != primary_asset_id.lower():
        raise ImmichMetadataPlanError("Immich metadata stack action has invalid asset ordering")
    all_assets_hidden = all(asset_id.lower() in hidden_asset_ids for asset_id in asset_ids)

    existing_stacks = _existing_stacks_for_action(client, asset_ids)
    if len(existing_stacks) > 1:
        errors.append("existing_stack_conflict")
        return ImmichMetadataLiveOperation(
            action="ensure_stack_with_edited_primary",
            status=ImmichMetadataOperationStatus.BLOCKED,
            resource_id=source_uuid,
            summary="More than one existing stack matched the planned stack assets",
            asset_ids=asset_ids,
            source_uuid=source_uuid,
            primary_asset_id=primary_asset_id,
            changed_fields=("assets", "primaryAssetId"),
            endpoint=_stack_lookup_endpoint(primary_asset_id),
        )
    if existing_stacks:
        if _stack_matches(
            existing_stacks[0],
            primary_asset_id,
            asset_ids,
            allow_filtered_assets=all_assets_hidden,
        ):
            return ImmichMetadataLiveOperation(
                action="ensure_stack_with_edited_primary",
                status=ImmichMetadataOperationStatus.UNCHANGED,
                resource_id=source_uuid,
                summary="Stack already has the edited rendition as primary",
                asset_ids=asset_ids,
                source_uuid=source_uuid,
                primary_asset_id=primary_asset_id,
                endpoint=_stack_lookup_endpoint(primary_asset_id),
            )
        errors.append("existing_stack_conflict")
        return ImmichMetadataLiveOperation(
            action="ensure_stack_with_edited_primary",
            status=ImmichMetadataOperationStatus.BLOCKED,
            resource_id=source_uuid,
            summary="An existing stack differs from the planned edited-primary stack",
            asset_ids=asset_ids,
            source_uuid=source_uuid,
            primary_asset_id=primary_asset_id,
            changed_fields=("assets", "primaryAssetId"),
            endpoint=_stack_lookup_endpoint(primary_asset_id),
        )

    if not apply_changes:
        return ImmichMetadataLiveOperation(
            action="ensure_stack_with_edited_primary",
            status=ImmichMetadataOperationStatus.PENDING,
            resource_id=source_uuid,
            summary="Stack is absent and would be created with the edited rendition as primary",
            asset_ids=asset_ids,
            source_uuid=source_uuid,
            primary_asset_id=primary_asset_id,
            changed_fields=("stack",),
            endpoint="/api/stacks",
        )

    created = client.create_stack({"assetIds": list(asset_ids)})
    if not _stack_matches(
        created,
        primary_asset_id,
        asset_ids,
        allow_filtered_assets=all_assets_hidden,
    ):
        errors.append("stack_create_unverified")
        return ImmichMetadataLiveOperation(
            action="ensure_stack_with_edited_primary",
            status=ImmichMetadataOperationStatus.BLOCKED,
            resource_id=source_uuid,
            summary="Stack create returned a response that did not match the planned stack",
            asset_ids=asset_ids,
            source_uuid=source_uuid,
            primary_asset_id=primary_asset_id,
            changed_fields=("stack",),
            endpoint="/api/stacks",
        )
    return ImmichMetadataLiveOperation(
        action="ensure_stack_with_edited_primary",
        status=ImmichMetadataOperationStatus.APPLIED,
        resource_id=source_uuid,
        summary="Stack was created with the edited rendition as primary",
        asset_ids=asset_ids,
        source_uuid=source_uuid,
        primary_asset_id=primary_asset_id,
        changed_fields=("stack",),
        endpoint="/api/stacks",
    )


def reconcile_immich_metadata(
    metadata_plan_path: Path,
    client: ImmichMetadataClient,
    *,
    api_base_url: str,
    apply_changes: bool = False,
) -> ImmichMetadataReconcileReport:
    document, evidence = _load_immich_metadata_plan_document(metadata_plan_path)
    export_root = _plan_string(document.get("export_root"), "export root")
    warnings = list(_plan_warnings(document))
    errors: list[str] = []
    operations: list[ImmichMetadataLiveOperation] = []

    favorite_actions = _plan_actions(document, "favorite_actions")
    hidden_visibility_actions = _plan_actions(
        document,
        "hidden_visibility_actions",
        required=False,
    )
    album_actions = _plan_actions(document, "album_actions")
    stack_actions = _plan_actions(document, "stack_actions")
    hidden_asset_ids = frozenset(
        asset_id.lower()
        for action in hidden_visibility_actions
        for asset_id in _plan_strings(action.get("asset_ids"), "hidden visibility asset IDs")
    )
    if album_actions:
        warnings.append("album_membership_state_not_readable_in_immich_v3_0_2")
    if any(
        all(
            asset_id.lower() in hidden_asset_ids
            for asset_id in _plan_strings(action.get("asset_ids"), "stack asset IDs")
        )
        for action in stack_actions
    ):
        warnings.append("hidden_stack_membership_state_not_readable_in_immich_v3_0_2")

    operations.extend(
        _reconcile_favorite_action(
            action,
            client,
            apply_changes=apply_changes,
            errors=errors,
        )
        for action in favorite_actions
    )
    operations.extend(
        _reconcile_hidden_visibility_action(
            action,
            client,
            apply_changes=apply_changes,
            errors=errors,
        )
        for action in hidden_visibility_actions
    )
    operations.extend(
        _reconcile_album_action(
            action,
            client,
            apply_changes=apply_changes,
            errors=errors,
        )
        for action in album_actions
    )
    operations.extend(
        _reconcile_stack_action(
            action,
            client,
            apply_changes=apply_changes,
            errors=errors,
            hidden_asset_ids=hidden_asset_ids,
        )
        for action in stack_actions
    )

    return ImmichMetadataReconcileReport(
        schema_version=1,
        export_root=export_root,
        metadata_plan=evidence,
        api_base_url=api_base_url.rstrip("/"),
        apply=apply_changes,
        errors=tuple(sorted(set(errors))),
        warnings=tuple(sorted(set(warnings))),
        operations=tuple(operations),
    )


def serialize_immich_metadata_reconcile(report: ImmichMetadataReconcileReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"


def write_immich_metadata_reconcile_report(
    report: ImmichMetadataReconcileReport,
    destination: Path,
) -> None:
    export_root = Path(report.export_root).resolve()
    output = destination.resolve()
    if output == export_root or output.is_relative_to(export_root):
        raise ImmichMetadataPlanError(
            "Immich metadata reconcile report must be outside the export tree"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize_immich_metadata_reconcile(report))
