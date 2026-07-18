from __future__ import annotations

import base64
import binascii
import json
import os
import shutil
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol

from homeserver_iac.models.openwrt import OpenWrtDesiredState
from homeserver_iac.openwrt import (
    PROTECTED_STAGE_ORDER,
    STAGE_ORDER,
    STAGE_PACKAGES,
    ApplyResult,
    ChunkDecryptor,
    ChunkEncryptor,
    OpenWrtSafetyError,
    apply_stage,
    effective_stage_policy,
    read_transaction_bundle,
    required_revert_health_stages,
    validate_safety,
    write_transaction_bundle,
)
from homeserver_iac.openwrt_health import derive_health_observations, validate_stage_health
from homeserver_iac.openwrt_reconcile import (
    StageChanges,
    build_stage_changes,
    validate_clean_image_transition,
)
from homeserver_iac.runtime import OperationalError

StateReader = Callable[[], Mapping[str, Any]]
SecretResolver = Callable[[str], str]
ConfigArchive = Callable[[], bytes]


class HelperClient(Protocol):
    def helper_call(self, envelope: Mapping[str, Any]) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class AcceptedTransaction:
    transaction_id: str
    stage: str
    index_path: Path


@dataclass(frozen=True)
class PendingTransaction:
    transaction_id: str
    stage: str
    path: Path
    index_path: Path


@dataclass(frozen=True)
class PendingRecoveryResult:
    transaction_id: str
    stage: str
    outcome: Literal["accepted", "rolled-back"]
    path: Path


@dataclass(frozen=True)
class ControllerResult:
    apply: ApplyResult | None
    transaction: AcceptedTransaction | None


class TransactionJournal:
    def __init__(
        self,
        root: Path,
        *,
        encryptor: ChunkEncryptor,
        decryptor: ChunkDecryptor,
    ) -> None:
        self.root = root
        self.encryptor = encryptor
        self.decryptor = decryptor

    def accepted(self) -> tuple[AcceptedTransaction, ...]:
        if not self.root.exists():
            return ()
        records: list[AcceptedTransaction] = []
        for directory in self.root.iterdir():
            if not directory.is_dir() or directory.name.startswith("."):
                continue
            index_path = directory / "index.json"
            if not index_path.is_file():
                continue
            try:
                index = json.loads(index_path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if index.get("transaction_id") != directory.name or not isinstance(
                index.get("stage"), str
            ):
                continue
            records.append(AcceptedTransaction(directory.name, str(index["stage"]), index_path))
        return tuple(
            sorted(
                records,
                key=lambda item: (item.index_path.stat().st_mtime_ns, item.transaction_id),
            )
        )

    def latest(self, stage: str) -> AcceptedTransaction | None:
        matches = [item for item in self.accepted() if item.stage == stage]
        return matches[-1] if matches else None

    def pending(self) -> tuple[PendingTransaction, ...]:
        if not self.root.exists():
            return ()
        records: list[PendingTransaction] = []
        for directory in self.root.iterdir():
            if not directory.name.startswith(".") or not directory.name.endswith(".pending"):
                continue
            if directory.is_symlink() or not directory.is_dir():
                raise OpenWrtSafetyError("pending transaction path is invalid")
            transaction_id = directory.name[1 : -len(".pending")]
            index_path = directory / "index.json"
            try:
                index = json.loads(index_path.read_text())
            except (OSError, json.JSONDecodeError) as error:
                raise OpenWrtSafetyError("pending transaction index is invalid") from error
            if (
                not isinstance(index, Mapping)
                or index.get("transaction_id") != transaction_id
                or not isinstance(index.get("stage"), str)
            ):
                raise OpenWrtSafetyError("pending transaction index is invalid")
            records.append(
                PendingTransaction(transaction_id, str(index["stage"]), directory, index_path)
            )
        return tuple(sorted(records, key=lambda item: item.transaction_id))

    def load(self, transaction_id: str) -> Mapping[str, Any]:
        if not transaction_id or Path(transaction_id).name != transaction_id:
            raise OpenWrtSafetyError("transaction ID is invalid")
        return read_transaction_bundle(
            index_path=self.root / transaction_id / "index.json",
            decryptor=self.decryptor,
        )

    def load_pending(self, pending: PendingTransaction) -> Mapping[str, Any]:
        if pending.path != self.root / f".{pending.transaction_id}.pending":
            raise OpenWrtSafetyError("pending transaction path is invalid")
        return read_transaction_bundle(index_path=pending.index_path, decryptor=self.decryptor)

    def archive_generation(self) -> Path | None:
        """Hide the active lineage without reading, decrypting, or deleting it."""

        if self.pending():
            raise OpenWrtSafetyError("cannot archive a transaction generation while one is pending")
        if not self.root.exists():
            return None
        active = tuple(
            sorted(
                path
                for path in self.root.iterdir()
                if not path.name.startswith(".")
                or (path.name.startswith(".tx_") and ".failed-" in path.name)
            )
        )
        if not active:
            return None
        if any(path.is_symlink() or not path.is_dir() for path in active):
            raise OpenWrtSafetyError("active transaction path is invalid")
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        generation = self.root / f".generation-pre-clean-{timestamp}"
        if generation.exists():
            raise OpenWrtSafetyError("transaction generation archive already exists")
        generation.mkdir(mode=0o700)
        for path in active:
            os.replace(path, generation / path.name)
        return generation

    def prepare(self, payload: Mapping[str, Any]) -> Path:
        transaction_id = str(payload["transaction_id"])
        pending = self.root / f".{transaction_id}.pending"
        if pending.exists() or (self.root / transaction_id).exists():
            raise OpenWrtSafetyError("transaction ID already exists")
        pending.mkdir(parents=True, mode=0o700)
        try:
            write_transaction_bundle(
                payload=payload,
                encryptor=self.encryptor,
                bundle_path=pending / "bundle.age",
                index_path=pending / "index.json",
            )
        except Exception:
            shutil.rmtree(pending, ignore_errors=True)
            raise
        return pending

    def accept(self, pending: Path, transaction_id: str) -> AcceptedTransaction:
        if pending != self.root / f".{transaction_id}.pending":
            raise OpenWrtSafetyError("pending transaction path is invalid")
        accepted = self.root / transaction_id
        os.replace(pending, accepted)
        payload = self.load(transaction_id)
        return AcceptedTransaction(transaction_id, str(payload["stage"]), accepted / "index.json")

    def fail(self, pending: Path, transaction_id: str, reason: str) -> Path:
        if pending != self.root / f".{transaction_id}.pending":
            raise OpenWrtSafetyError("pending transaction path is invalid")
        if reason not in {"preflight", "rolled-back"}:
            raise OpenWrtSafetyError("failed transaction reason is invalid")
        failed = self.root / f".{transaction_id}.failed-{reason}"
        if failed.exists():
            raise OpenWrtSafetyError("failed transaction archive already exists")
        os.replace(pending, failed)
        return failed


def _transaction_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"tx_{timestamp}_{uuid.uuid4().hex[:12]}"


def _hidden_expected(expected: Mapping[str, Any], snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        path: value
        for path, value in expected.items()
        if str(path).endswith((".username", ".password", ".ssid", ".key"))
        or (isinstance(snapshot.get(path), Mapping) and snapshot[path].get("present") is True)
    }


def _hidden_matches(client: HelperClient, expected: Mapping[str, Any]) -> dict[str, bool]:
    if not expected:
        return {}
    response = client.helper_call(
        {"object": "homeserver", "method": "compare", "arguments": {"expected": expected}}
    )
    fields = response.get("fields")
    if not isinstance(fields, Mapping):
        raise OpenWrtSafetyError("hidden-field comparison returned no field metadata")
    result: dict[str, bool] = {}
    for path in expected:
        metadata = fields.get(path)
        if not isinstance(metadata, Mapping) or not isinstance(metadata.get("match"), bool):
            raise OpenWrtSafetyError("hidden-field comparison metadata is invalid")
        result[path] = bool(metadata["match"])
    return result


def _projection_from_snapshot(
    changes: StageChanges,
    snapshot: Mapping[str, Any],
    previous_expected: Mapping[str, Any],
) -> dict[str, Any]:
    projection: dict[str, Any] = {}
    for path in changes.owned_paths:
        value = snapshot.get(path)
        if isinstance(value, Mapping) and value.get("present") is True:
            if path not in previous_expected:
                raise OpenWrtSafetyError(
                    "cannot journal an existing hidden field without accepted lineage"
                )
            value = previous_expected[path]
        projection[path] = value
    for section in changes.created_sections:
        projection[f"{section}._section_absent"] = None
    for section in changes.deleted_sections:
        prefix = section + "."
        for path, value in snapshot.items():
            if str(path).startswith(prefix):
                if isinstance(value, Mapping) and value.get("present") is True:
                    if path not in previous_expected:
                        raise OpenWrtSafetyError(
                            "cannot journal a stale hidden field without accepted lineage"
                        )
                    value = previous_expected[path]
                projection[str(path)] = value
    return projection


def _verify_projection(
    client: HelperClient,
    state: Mapping[str, Any],
    expected: Mapping[str, Any],
    *,
    prior_projection: Mapping[str, Any] | None = None,
) -> None:
    snapshot = state.get("uci")
    if not isinstance(snapshot, Mapping):
        raise OpenWrtSafetyError("OpenWrt state has no filtered UCI snapshot")
    section_aliases: dict[str, str] = {}
    for path, anonymous in expected.items():
        parts = str(path).split(".", 2)
        if len(parts) != 3 or parts[2] != "_anonymous" or anonymous is not True:
            continue
        config, section, _ = parts
        section_id = f"{config}.{section}"
        expected_index = expected.get(f"{section_id}._index")
        expected_type = expected.get(f"{section_id}._type")
        if (
            not isinstance(expected_index, int)
            or isinstance(expected_index, bool)
            or not isinstance(expected_type, str)
        ):
            continue
        candidates: list[str] = []
        for current_path, current_index in snapshot.items():
            current_parts = str(current_path).split(".", 2)
            if (
                len(current_parts) != 3
                or current_parts[0] != config
                or current_parts[2] != "_index"
                or current_index != expected_index
            ):
                continue
            current_id = f"{config}.{current_parts[1]}"
            if (
                snapshot.get(f"{current_id}._anonymous") is True
                and snapshot.get(f"{current_id}._type") == expected_type
            ):
                candidates.append(current_id)
        if len(candidates) != 1:
            raise OpenWrtSafetyError("accepted OpenWrt stage differs from expected structure")
        section_aliases[section_id] = candidates[0]

    resolved_expected: dict[str, Any] = {}
    for path, wanted in expected.items():
        parts = str(path).split(".", 2)
        if len(parts) != 3:
            raise OpenWrtSafetyError("accepted OpenWrt projection path is invalid")
        config, section, option = parts
        section_id = f"{config}.{section}"
        actual_id = section_aliases.get(section_id, section_id)
        actual_section = actual_id.split(".", 1)[1]
        actual_path = f"{config}.{actual_section}.{option}"
        if actual_path in resolved_expected:
            raise OpenWrtSafetyError("accepted OpenWrt projection aliases collide")
        if actual_id != section_id and option == "_name":
            wanted = actual_section
        resolved_expected[actual_path] = wanted

    hidden = _hidden_expected(resolved_expected, snapshot)
    matches = _hidden_matches(client, hidden)
    for path, wanted in resolved_expected.items():
        path_text = str(path)
        if path_text in hidden:
            if matches.get(path_text) is not True:
                raise OpenWrtSafetyError("accepted OpenWrt stage differs from expected state")
        elif path_text.endswith("._section_absent"):
            prefix = path_text.removesuffix("._section_absent") + "."
            current_paths = [item for item in snapshot if str(item).startswith(prefix)]
            prior = prior_projection or {}
            anonymous_reused = (
                bool(current_paths)
                and prior.get(prefix + "_anonymous") is True
                and isinstance(prior.get(prefix + "name"), str)
                and snapshot.get(prefix + "name") != prior.get(prefix + "name")
            )
            if current_paths and not anonymous_reused:
                raise OpenWrtSafetyError("accepted OpenWrt stage retained a deleted section")
        elif _canonical_projection_value(snapshot.get(path)) != _canonical_projection_value(wanted):
            raise OpenWrtSafetyError("accepted OpenWrt stage differs from expected state")


def _canonical_projection_value(value: Any) -> Any:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(value)
    return value


def _canonical_projection(projection: Mapping[str, Any]) -> dict[str, Any]:
    return {str(path): _canonical_projection_value(value) for path, value in projection.items()}


def _archive_pending_after_rollback(
    *,
    desired: OpenWrtDesiredState,
    client: HelperClient,
    state_reader: StateReader,
    journal: TransactionJournal,
    pending: Path,
    transaction_id: str,
    payload: Mapping[str, Any],
    allow_prebase_management: bool,
) -> bool:
    pre = payload.get("pre_projection")
    post = payload.get("expected_post_projection")
    if not isinstance(pre, Mapping) or not isinstance(post, Mapping):
        return False

    def verify() -> Mapping[str, Any]:
        state = state_reader()
        validate_safety(desired, state, allow_prebase_management=allow_prebase_management)
        if state.get("identity") != payload.get("board"):
            raise OpenWrtSafetyError("rolled-back router identity differs")
        _verify_projection(client, state, pre, prior_projection=post)
        snapshot = state.get("uci")
        if not isinstance(snapshot, Mapping):
            raise OpenWrtSafetyError("rolled-back state has no UCI snapshot")
        return snapshot

    try:
        snapshot = verify()
        lock = client.helper_call(
            {"object": "homeserver", "method": "lock-status", "arguments": {}}
        )
        if lock.get("present") is not False:
            return False
        immediate_snapshot = verify()
        if dict(immediate_snapshot) != dict(snapshot):
            return False
        lock = client.helper_call(
            {"object": "homeserver", "method": "lock-status", "arguments": {}}
        )
        if lock.get("present") is not False:
            return False
    except (OpenWrtSafetyError, OperationalError):
        return False
    journal.fail(pending, transaction_id, "rolled-back")
    return True


def _enabled_stages(
    journal: TransactionJournal, state: Mapping[str, Any] | None = None
) -> frozenset[str]:
    enabled = {item.stage for item in journal.accepted() if item.stage in STAGE_ORDER}
    if state is not None:
        for stage in STAGE_ORDER:
            try:
                validate_stage_health(stage, _health_state(state, stage))
            except OpenWrtSafetyError:
                continue
            enabled.add(stage)
    return frozenset(enabled)


def _health_state(state: Mapping[str, Any], stage: str) -> Mapping[str, Any]:
    runtime = state.get("runtime")
    markers = {
        "bootstrap-sanitize": "default_wan",
        "base": "lan_address",
        "wan": "protocol",
        "main-wifi": "radios",
        "guest": "same_bss_isolation",
        "ipv6": "delegated_prefix_length",
        "sqm": "runtime_rates",
    }
    if isinstance(runtime, Mapping):
        observed = runtime.get(stage)
        if isinstance(observed, Mapping) and markers[stage] in observed:
            return state
    return derive_health_observations(state)


def stage_changes_for_state(
    *,
    desired: OpenWrtDesiredState,
    client: HelperClient,
    state: Mapping[str, Any],
    stage: str,
    resolve_secret: SecretResolver,
    accepted_stages: Sequence[str] = (),
) -> StageChanges:
    snapshot = state.get("uci")
    if not isinstance(snapshot, Mapping):
        raise OpenWrtSafetyError("OpenWrt state has no filtered UCI snapshot")
    preliminary = build_stage_changes(
        desired,
        stage,
        snapshot=snapshot,
        resolve_secret=resolve_secret,
        accepted_stages=accepted_stages,
    )
    matches = _hidden_matches(
        client,
        _hidden_expected(preliminary.expected_projection, snapshot),
    )
    return build_stage_changes(
        desired,
        stage,
        snapshot=snapshot,
        resolve_secret=resolve_secret,
        secret_matches=matches,
        accepted_stages=accepted_stages,
    )


def apply_openwrt_stage(
    *,
    desired: OpenWrtDesiredState,
    client: HelperClient,
    state_reader: StateReader,
    resolve_secret: SecretResolver,
    config_archive: ConfigArchive,
    journal: TransactionJournal,
    stage: str,
    lock_path: Path,
    controller_id: str,
) -> ControllerResult:
    if stage not in (*PROTECTED_STAGE_ORDER, "bootstrap-sanitize"):
        raise OpenWrtSafetyError(f"OpenWrt {stage} is not a protected convergence stage")
    if journal.pending():
        raise OpenWrtSafetyError("OpenWrt apply refuses an existing pending transaction")
    state = state_reader()
    prebase_transition = stage in {"bootstrap-sanitize", "base"} and journal.latest("base") is None
    validate_safety(desired, state, allow_prebase_management=prebase_transition)
    if stage == "bootstrap-sanitize" and (
        journal.latest("bootstrap-sanitize") is not None or journal.latest("wan") is not None
    ):
        raise OpenWrtSafetyError(
            "bootstrap-sanitize is one-time and cannot follow an accepted WAN stage"
        )
    snapshot = state.get("uci")
    if not isinstance(snapshot, Mapping):
        raise OpenWrtSafetyError("OpenWrt state has no filtered UCI snapshot")
    if (
        stage == "base"
        and snapshot.get("network.wan.proto") == "dhcp"
        and snapshot.get("network.wan6.proto") == "dhcpv6"
        and journal.latest("bootstrap-sanitize") is None
    ):
        raise OpenWrtSafetyError("base requires bootstrap-sanitize on the clean image")
    changes = stage_changes_for_state(
        desired=desired,
        client=client,
        state=state,
        stage=stage,
        resolve_secret=resolve_secret,
        accepted_stages=tuple(item.stage for item in journal.accepted()),
    )
    if not changes.mutations:
        return ControllerResult(None, None)
    parent = journal.latest(stage)
    previous_expected: Mapping[str, Any] = {}
    if parent is not None:
        prior_payload = journal.load(parent.transaction_id)
        value = prior_payload.get("expected_post_projection")
        if isinstance(value, Mapping):
            previous_expected = {
                key: item for key, item in value.items() if key in changes.expected_projection
            }
            previous_hidden = _hidden_expected(previous_expected, snapshot)
            if previous_hidden and not all(_hidden_matches(client, previous_hidden).values()):
                raise OpenWrtSafetyError(
                    "current hidden state differs from accepted transaction lineage"
                )
    transaction_id = _transaction_id()
    payload = {
        "transaction_id": transaction_id,
        "stage": stage,
        "timestamp": datetime.now(UTC).isoformat(),
        "board": state.get("identity"),
        "config_schema_version": desired.schema_version,
        "pre_projection": _projection_from_snapshot(changes, snapshot, previous_expected),
        "expected_post_projection": dict(changes.expected_projection),
        "owned_paths": list(changes.owned_paths),
        "created_sections": list(changes.created_sections),
        "deleted_sections": list(changes.deleted_sections),
        "enabled_stages": sorted(_enabled_stages(journal, state)),
        "parent_transaction_id": parent.transaction_id if parent else None,
        "config_archive_base64": base64.b64encode(config_archive()).decode(),
    }
    pre_projection = payload.get("pre_projection")
    if not isinstance(pre_projection, Mapping):
        raise OpenWrtSafetyError("OpenWrt transaction prior projection is invalid")
    pending = journal.prepare(payload)

    try:
        immediate = state_reader()
        validate_safety(desired, immediate, allow_prebase_management=prebase_transition)
        immediate_snapshot = immediate.get("uci")
        if not isinstance(immediate_snapshot, Mapping) or dict(immediate_snapshot) != dict(
            snapshot
        ):
            raise OpenWrtSafetyError("OpenWrt UCI state changed before staging")
    except (OpenWrtSafetyError, OperationalError):
        journal.fail(pending, transaction_id, "preflight")
        raise

    def health_check(health_stage: str) -> None:
        observed = state_reader()
        validate_safety(
            desired,
            observed,
            allow_prebase_management=stage == "bootstrap-sanitize" and prebase_transition,
        )
        validate_stage_health(health_stage, _health_state(observed, health_stage))

    def reread(_: str) -> None:
        current = state_reader()
        validate_safety(
            desired,
            current,
            allow_prebase_management=stage == "bootstrap-sanitize" and prebase_transition,
        )

    try:
        result = apply_stage(
            client=client,  # type: ignore[arg-type]
            stage=stage,
            packages=changes.packages,
            mutations=changes.mutations,
            expected_projection=changes.expected_projection,
            enabled_stages=_enabled_stages(journal, immediate),
            health_check=health_check,
            backup_before_apply=lambda _: None,
            lock_path=lock_path,
            controller_id=controller_id,
            read_after_apply=reread,
        )
    except (OpenWrtSafetyError, OperationalError) as error:
        _archive_pending_after_rollback(
            desired=desired,
            client=client,
            state_reader=state_reader,
            journal=journal,
            pending=pending,
            transaction_id=transaction_id,
            payload=payload,
            allow_prebase_management=prebase_transition,
        )
        raise type(error)(
            f"OpenWrt {stage} transaction {transaction_id} failed: {error}"
        ) from error
    accepted_state: Mapping[str, Any] | None = None
    try:
        accepted_state = state_reader()
        _verify_projection(
            client,
            accepted_state,
            changes.expected_projection,
            prior_projection=pre_projection,
        )
    except OpenWrtSafetyError:
        if accepted_state is None:
            raise
        pre = payload["pre_projection"]
        if not isinstance(pre, Mapping):
            raise
        previously_enabled = payload["enabled_stages"]
        if not isinstance(previously_enabled, Sequence) or isinstance(previously_enabled, str):
            raise OpenWrtSafetyError("transaction enabled-stage metadata is invalid") from None
        restore_snapshot = accepted_state.get("uci")
        if not isinstance(restore_snapshot, Mapping):
            raise OpenWrtSafetyError("OpenWrt restore state has no filtered UCI snapshot") from None
        apply_stage(
            client=client,  # type: ignore[arg-type]
            stage=stage,
            packages=changes.packages,
            mutations=_restore_mutations(payload, current_snapshot=restore_snapshot),
            expected_projection=pre,
            enabled_stages=_enabled_stages(journal, state_reader()) | {stage},
            health_check=health_check,
            backup_before_apply=lambda _: None,
            lock_path=lock_path,
            controller_id=f"{controller_id}-acceptance-revert",
            read_after_apply=reread,
            health_stages_override=required_revert_health_stages(
                changes.packages, (str(item) for item in previously_enabled)
            ),
        )
        _archive_pending_after_rollback(
            desired=desired,
            client=client,
            state_reader=state_reader,
            journal=journal,
            pending=pending,
            transaction_id=transaction_id,
            payload=payload,
            allow_prebase_management=prebase_transition,
        )
        raise
    accepted = journal.accept(pending, transaction_id)
    return ControllerResult(result, accepted)


def recover_pending_bootstrap_sanitize(
    *,
    desired: OpenWrtDesiredState,
    client: HelperClient,
    state_reader: StateReader,
    journal: TransactionJournal,
) -> AcceptedTransaction:
    if journal.accepted():
        raise OpenWrtSafetyError("pending sanitize recovery requires no accepted transaction")
    candidates = journal.pending()
    if len(candidates) != 1 or candidates[0].stage != "bootstrap-sanitize":
        raise OpenWrtSafetyError("pending sanitize recovery requires exactly one matching journal")
    pending = candidates[0]
    payload = journal.load_pending(pending)
    expected_post = {
        "network.wan._section_absent": None,
        "network.wan6._section_absent": None,
    }
    expected_pre = {
        "network.wan._anonymous": False,
        "network.wan._index": 4,
        "network.wan._name": "wan",
        "network.wan._type": "interface",
        "network.wan.device": "wan",
        "network.wan.proto": "dhcp",
        "network.wan6._anonymous": False,
        "network.wan6._index": 5,
        "network.wan6._name": "wan6",
        "network.wan6._type": "interface",
        "network.wan6.device": "wan",
        "network.wan6.proto": "dhcpv6",
    }
    archive = payload.get("config_archive_base64")
    try:
        archive_bytes = (
            base64.b64decode(archive, validate=True) if isinstance(archive, str) else b""
        )
    except (binascii.Error, ValueError) as error:
        raise OpenWrtSafetyError("pending sanitize config archive is invalid") from error
    if (
        payload.get("transaction_id") != pending.transaction_id
        or payload.get("stage") != "bootstrap-sanitize"
        or payload.get("config_schema_version") != desired.schema_version
        or payload.get("parent_transaction_id") is not None
        or payload.get("expected_post_projection") != expected_post
        or payload.get("pre_projection") != expected_pre
        or payload.get("owned_paths") != []
        or payload.get("created_sections") != []
        or payload.get("deleted_sections") != ["network.wan", "network.wan6"]
        or payload.get("enabled_stages") != []
        or not archive_bytes
    ):
        raise OpenWrtSafetyError("pending sanitize journal does not match the clean transition")

    state = state_reader()
    validate_safety(desired, state, allow_prebase_management=True)
    if payload.get("board") != state.get("identity"):
        raise OpenWrtSafetyError("pending sanitize board identity differs from the router")
    snapshot = state.get("uci")
    if not isinstance(snapshot, Mapping):
        raise OpenWrtSafetyError("OpenWrt state has no filtered UCI snapshot")
    validate_clean_image_transition(snapshot, sanitized=True)
    validate_stage_health("bootstrap-sanitize", _health_state(state, "bootstrap-sanitize"))
    _verify_projection(client, state, expected_post)
    lock = client.helper_call({"object": "homeserver", "method": "lock-status", "arguments": {}})
    if lock.get("present") is not False:
        raise OpenWrtSafetyError("router lock remains during pending sanitize recovery")

    immediate = state_reader()
    validate_safety(desired, immediate, allow_prebase_management=True)
    immediate_snapshot = immediate.get("uci")
    if not isinstance(immediate_snapshot, Mapping) or dict(immediate_snapshot) != dict(snapshot):
        raise OpenWrtSafetyError("OpenWrt UCI state changed during pending sanitize recovery")
    _verify_projection(client, immediate, expected_post)
    lock = client.helper_call({"object": "homeserver", "method": "lock-status", "arguments": {}})
    if lock.get("present") is not False:
        raise OpenWrtSafetyError("router lock appeared during pending sanitize recovery")
    return journal.accept(pending.path, pending.transaction_id)


def recover_pending_base(
    *,
    desired: OpenWrtDesiredState,
    client: HelperClient,
    state_reader: StateReader,
    journal: TransactionJournal,
) -> AcceptedTransaction:
    accepted = journal.accepted()
    if len(accepted) != 1 or accepted[0].stage != "bootstrap-sanitize":
        raise OpenWrtSafetyError("pending base recovery requires accepted sanitize lineage")
    candidates = journal.pending()
    if len(candidates) != 1 or candidates[0].stage != "base":
        raise OpenWrtSafetyError("pending base recovery requires exactly one matching journal")
    pending = candidates[0]
    payload = journal.load_pending(pending)
    archive = payload.get("config_archive_base64")
    try:
        archive_bytes = (
            base64.b64decode(archive, validate=True) if isinstance(archive, str) else b""
        )
    except (binascii.Error, ValueError) as error:
        raise OpenWrtSafetyError("pending base config archive is invalid") from error

    state = state_reader()
    validate_safety(desired, state)
    snapshot = state.get("uci")
    if not isinstance(snapshot, Mapping):
        raise OpenWrtSafetyError("OpenWrt state has no filtered UCI snapshot")
    expected_changes = build_stage_changes(desired, "base", snapshot=snapshot)
    matches = _hidden_matches(
        client,
        _hidden_expected(expected_changes.expected_projection, snapshot),
    )
    expected_changes = build_stage_changes(
        desired,
        "base",
        snapshot=snapshot,
        secret_matches=matches,
    )
    expected_post = dict(expected_changes.expected_projection)
    recorded_post = payload.get("expected_post_projection")
    if (
        payload.get("transaction_id") != pending.transaction_id
        or payload.get("stage") != "base"
        or payload.get("config_schema_version") != desired.schema_version
        or payload.get("parent_transaction_id") is not None
        or payload.get("board") != state.get("identity")
        or not isinstance(recorded_post, Mapping)
        or _canonical_projection(recorded_post) != _canonical_projection(expected_post)
        or payload.get("enabled_stages") != []
        or expected_changes.mutations
        or any(
            str(path).endswith((".username", ".password", ".ssid", ".key"))
            for path in expected_post
        )
        or not archive_bytes
    ):
        raise OpenWrtSafetyError("pending base journal does not match converged live state")
    validate_stage_health("base", _health_state(state, "base"))
    _verify_projection(client, state, expected_post)
    lock = client.helper_call({"object": "homeserver", "method": "lock-status", "arguments": {}})
    if lock.get("present") is not False:
        raise OpenWrtSafetyError("router lock remains during pending base recovery")

    immediate = state_reader()
    validate_safety(desired, immediate)
    immediate_snapshot = immediate.get("uci")
    if not isinstance(immediate_snapshot, Mapping) or dict(immediate_snapshot) != dict(snapshot):
        raise OpenWrtSafetyError("OpenWrt UCI state changed during pending base recovery")
    validate_stage_health("base", _health_state(immediate, "base"))
    _verify_projection(client, immediate, expected_post)
    lock = client.helper_call({"object": "homeserver", "method": "lock-status", "arguments": {}})
    if lock.get("present") is not False:
        raise OpenWrtSafetyError("router lock appeared during pending base recovery")
    return journal.accept(pending.path, pending.transaction_id)


def apply_openwrt_all(
    *,
    desired: OpenWrtDesiredState,
    client: HelperClient,
    state_reader: StateReader,
    resolve_secret: SecretResolver,
    config_archive: ConfigArchive,
    journal: TransactionJournal,
    lock_path: Path,
    controller_id: str,
) -> tuple[ControllerResult, ...]:
    results: list[ControllerResult] = []
    for stage in PROTECTED_STAGE_ORDER:
        results.append(
            apply_openwrt_stage(
                desired=desired,
                client=client,
                state_reader=state_reader,
                resolve_secret=resolve_secret,
                config_archive=config_archive,
                journal=journal,
                stage=stage,
                lock_path=lock_path,
                controller_id=controller_id,
            )
        )
    return tuple(results)


def _restore_mutations(
    payload: Mapping[str, Any], *, current_snapshot: Mapping[str, Any]
) -> tuple[Mapping[str, Any], ...]:
    pre = payload.get("pre_projection")
    if not isinstance(pre, Mapping):
        raise OpenWrtSafetyError("transaction has no prior projection")
    post = payload.get("expected_post_projection")
    if not isinstance(post, Mapping):
        raise OpenWrtSafetyError("transaction has no expected post projection")
    mutations: list[Mapping[str, Any]] = []
    created = payload.get("created_sections", [])
    if not isinstance(created, Sequence) or isinstance(created, str):
        raise OpenWrtSafetyError("transaction created-section metadata is invalid")
    for section_id in created:
        config, section = str(section_id).split(".", 1)
        mutations.append({"method": "delete", "arguments": {"config": config, "section": section}})
    deleted = payload.get("deleted_sections", [])
    if not isinstance(deleted, Sequence) or isinstance(deleted, str):
        raise OpenWrtSafetyError("transaction deleted-section metadata is invalid")
    restored: dict[str, tuple[str, int, str]] = {}
    for section_id in deleted:
        section_text = str(section_id)
        config, section = section_text.split(".", 1)
        section_type = pre.get(f"{section_text}._type")
        anonymous = pre.get(f"{section_text}._anonymous")
        section_name = pre.get(f"{section_text}._name")
        section_index = pre.get(f"{section_text}._index")
        if (
            not isinstance(section_type, str)
            or not isinstance(anonymous, bool)
            or not isinstance(section_name, str)
            or not isinstance(section_index, int)
            or isinstance(section_index, bool)
            or section_index < 0
            or (not anonymous and section_name != section)
        ):
            raise OpenWrtSafetyError("deleted section structural metadata is invalid")
        values = {
            str(path).split(".", 2)[2]: value
            for path, value in pre.items()
            if str(path).startswith(f"{section_text}.")
            and len(str(path).split(".", 2)) == 3
            and not str(path).split(".", 2)[2].startswith("_")
            and value is not None
        }
        arguments: dict[str, Any] = {"config": config, "type": section_type}
        if not anonymous:
            arguments["name"] = section_name
        if values:
            arguments["values"] = values
        mutation: dict[str, Any] = {"method": "add", "arguments": arguments}
        if anonymous:
            mutation["capture_section_as"] = section_text
        mutations.append(mutation)
        restored[section_text] = (section_name, section_index, section_type)
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for path, value in pre.items():
        config, section, option = str(path).split(".", 2)
        if option.startswith("_"):
            continue
        if f"{config}.{section}" in restored:
            continue
        if value is None:
            if path in post and post[path] is None:
                continue
            mutations.append(
                {
                    "method": "delete",
                    "arguments": {"config": config, "section": section, "option": option},
                }
            )
        else:
            grouped.setdefault((config, section), {})[option] = value
    for (config, section), values in sorted(grouped.items()):
        mutations.append(
            {
                "method": "set",
                "arguments": {"config": config, "section": section, "values": values},
            }
        )
    for config in sorted({section_id.split(".", 1)[0] for section_id in restored}):
        current_order = sorted(
            (
                (value, str(path).split(".", 2)[1])
                for path, value in current_snapshot.items()
                if len(str(path).split(".", 2)) == 3
                and str(path).split(".", 2)[0] == config
                and str(path).split(".", 2)[2] == "_index"
                and isinstance(value, int)
                and not isinstance(value, bool)
            ),
            key=lambda item: item[0],
        )
        sections = [section for _, section in current_order]
        for section_id, (section_name, section_index, _) in sorted(
            (
                (section_id, metadata)
                for section_id, metadata in restored.items()
                if section_id.startswith(f"{config}.")
            ),
            key=lambda item: item[1][1],
        ):
            marker = (
                section_id.split(".", 1)[1] if pre[f"{section_id}._anonymous"] else section_name
            )
            if marker in sections or section_index > len(sections):
                raise OpenWrtSafetyError("deleted section order metadata is invalid")
            sections.insert(section_index, marker)
        mutations.append({"method": "order", "arguments": {"config": config, "sections": sections}})
    return tuple(mutations)


def recover_pending_stage_transaction(
    *,
    desired: OpenWrtDesiredState,
    client: HelperClient,
    state_reader: StateReader,
    journal: TransactionJournal,
    transaction_id: str,
) -> PendingRecoveryResult:
    candidates = journal.pending()
    if len(candidates) != 1 or candidates[0].transaction_id != transaction_id:
        raise OpenWrtSafetyError("pending stage recovery requires one exact transaction")
    pending = candidates[0]
    if pending.stage not in PROTECTED_STAGE_ORDER:
        raise OpenWrtSafetyError("pending stage recovery is not protected")
    payload = journal.load_pending(pending)
    pre = payload.get("pre_projection")
    expected_post = payload.get("expected_post_projection")
    enabled = payload.get("enabled_stages")
    archive = payload.get("config_archive_base64")
    try:
        archive_bytes = (
            base64.b64decode(archive, validate=True) if isinstance(archive, str) else b""
        )
    except (binascii.Error, ValueError) as error:
        raise OpenWrtSafetyError("pending stage config archive is invalid") from error
    reverts_transaction_id = payload.get("reverts_transaction_id")
    if (
        payload.get("transaction_id") != transaction_id
        or payload.get("stage") != pending.stage
        or payload.get("config_schema_version") != desired.schema_version
        or (reverts_transaction_id is not None and not isinstance(reverts_transaction_id, str))
        or not isinstance(pre, Mapping)
        or not isinstance(expected_post, Mapping)
        or not isinstance(enabled, Sequence)
        or isinstance(enabled, str)
        or not archive_bytes
    ):
        raise OpenWrtSafetyError("pending stage transaction metadata is invalid")
    parent = journal.latest(pending.stage)
    parent_id = parent.transaction_id if parent is not None else None
    if payload.get("parent_transaction_id") != parent_id:
        raise OpenWrtSafetyError("pending stage transaction lineage is stale")

    enabled_stages = tuple(str(item) for item in enabled)
    if reverts_transaction_id is None:
        _, _, health_stages = effective_stage_policy(
            pending.stage,
            STAGE_PACKAGES[pending.stage],
            enabled_stages,
        )
    else:
        if parent is None or reverts_transaction_id != parent.transaction_id:
            raise OpenWrtSafetyError("pending revert transaction lineage is stale")
        reverted = journal.load(reverts_transaction_id)
        if (
            reverted.get("transaction_id") != reverts_transaction_id
            or reverted.get("stage") != pending.stage
            or payload.get("pre_projection") != reverted.get("expected_post_projection")
            or payload.get("expected_post_projection") != reverted.get("pre_projection")
            or payload.get("created_sections") != reverted.get("deleted_sections")
            or payload.get("deleted_sections") != reverted.get("created_sections")
            or payload.get("owned_paths") != list(pre.keys())
            or payload.get("enabled_stages") != reverted.get("enabled_stages")
        ):
            raise OpenWrtSafetyError("pending revert transaction lineage is invalid")
        health_stages = required_revert_health_stages(STAGE_PACKAGES[pending.stage], enabled_stages)

    def classify(state: Mapping[str, Any]) -> tuple[str, Mapping[str, Any]]:
        validate_safety(desired, state)
        if state.get("identity") != payload.get("board"):
            raise OpenWrtSafetyError("pending stage router identity differs")
        snapshot = state.get("uci")
        if not isinstance(snapshot, Mapping):
            raise OpenWrtSafetyError("pending stage state has no UCI snapshot")

        post_matches = True
        try:
            _verify_projection(client, state, expected_post, prior_projection=pre)
        except OpenWrtSafetyError:
            post_matches = False

        pre_matches = True
        try:
            _verify_projection(client, state, pre, prior_projection=expected_post)
        except OpenWrtSafetyError:
            pre_matches = False

        if post_matches == pre_matches:
            return "ambiguous", snapshot
        if pre_matches:
            return "pre", snapshot
        try:
            for health_stage in health_stages:
                validate_stage_health(health_stage, _health_state(state, health_stage))
        except OpenWrtSafetyError:
            return "ambiguous", snapshot
        return "post", snapshot

    def require_unlocked(position: str) -> None:
        lock = client.helper_call(
            {"object": "homeserver", "method": "lock-status", "arguments": {}}
        )
        if lock.get("present") is not False:
            raise OpenWrtSafetyError(f"router lock {position} pending stage recovery")

    require_unlocked("remains before")
    endpoint, snapshot = classify(state_reader())
    require_unlocked("appeared during")
    immediate_endpoint, immediate_snapshot = classify(state_reader())
    require_unlocked("appeared after")
    if endpoint != immediate_endpoint or dict(immediate_snapshot) != dict(snapshot):
        raise OpenWrtSafetyError("OpenWrt state changed during pending stage recovery")
    if endpoint == "ambiguous":
        raise OpenWrtSafetyError("OpenWrt pending stage has no exact terminal endpoint")
    if endpoint == "pre":
        failed = journal.fail(pending.path, transaction_id, "rolled-back")
        return PendingRecoveryResult(transaction_id, pending.stage, "rolled-back", failed)
    accepted = journal.accept(pending.path, transaction_id)
    return PendingRecoveryResult(
        accepted.transaction_id, accepted.stage, "accepted", accepted.index_path.parent
    )


def revert_openwrt_transaction(
    *,
    desired: OpenWrtDesiredState,
    client: HelperClient,
    state_reader: StateReader,
    config_archive: ConfigArchive,
    journal: TransactionJournal,
    transaction_id: str,
    lock_path: Path,
    controller_id: str,
) -> ApplyResult:
    payload = journal.load(transaction_id)
    stage = payload.get("stage")
    if not isinstance(stage, str) or stage not in PROTECTED_STAGE_ORDER:
        raise OpenWrtSafetyError("only protected transaction IDs can be reverted here")
    latest = journal.latest(stage)
    if latest is None or latest.transaction_id != transaction_id:
        raise OpenWrtSafetyError("transaction revert lineage is stale")
    state = state_reader()
    validate_safety(desired, state)
    snapshot = state.get("uci")
    expected = payload.get("expected_post_projection")
    if not isinstance(snapshot, Mapping) or not isinstance(expected, Mapping):
        raise OpenWrtSafetyError("transaction state projection is invalid")
    hidden = _hidden_expected(expected, snapshot)
    matches = _hidden_matches(client, hidden)
    for path, wanted in expected.items():
        if path in hidden:
            if matches.get(str(path)) is not True:
                raise OpenWrtSafetyError("transaction revert is stale for current owned fields")
        elif str(path).endswith("._section_absent"):
            prefix = str(path).removesuffix("._section_absent") + "."
            if any(str(item).startswith(prefix) for item in snapshot):
                raise OpenWrtSafetyError("transaction revert is stale for current owned fields")
        elif _canonical_projection_value(snapshot.get(path)) != _canonical_projection_value(wanted):
            raise OpenWrtSafetyError("transaction revert is stale for current owned fields")
    pre = payload.get("pre_projection")
    if not isinstance(pre, Mapping):
        raise OpenWrtSafetyError("transaction prior projection is invalid")
    enabled = payload.get("enabled_stages", [])
    if not isinstance(enabled, Sequence) or isinstance(enabled, str):
        raise OpenWrtSafetyError("transaction enabled-stage metadata is invalid")
    revert_transaction_id = _transaction_id()
    revert_payload = {
        "transaction_id": revert_transaction_id,
        "stage": stage,
        "timestamp": datetime.now(UTC).isoformat(),
        "board": state.get("identity"),
        "config_schema_version": desired.schema_version,
        "pre_projection": dict(expected),
        "expected_post_projection": dict(pre),
        "owned_paths": list(pre.keys()),
        "created_sections": list(payload.get("deleted_sections", [])),
        "deleted_sections": list(payload.get("created_sections", [])),
        "enabled_stages": [str(item) for item in enabled],
        "parent_transaction_id": transaction_id,
        "config_archive_base64": base64.b64encode(config_archive()).decode(),
        "reverts_transaction_id": transaction_id,
    }
    pending = journal.prepare(revert_payload)
    result = apply_stage(
        client=client,  # type: ignore[arg-type]
        stage=stage,
        packages=STAGE_PACKAGES[stage],
        mutations=_restore_mutations(payload, current_snapshot=snapshot),
        expected_projection=pre,
        enabled_stages={str(item) for item in enabled} | {stage},
        health_check=lambda health_stage: validate_stage_health(
            health_stage, _health_state(state_reader(), health_stage)
        ),
        backup_before_apply=lambda _: None,
        lock_path=lock_path,
        controller_id=controller_id,
        read_after_apply=lambda _: validate_safety(desired, state_reader()),
        health_stages_override=required_revert_health_stages(
            STAGE_PACKAGES[stage], {str(item) for item in enabled}
        ),
    )
    _verify_projection(client, state_reader(), pre)
    journal.accept(pending, revert_transaction_id)
    return result
