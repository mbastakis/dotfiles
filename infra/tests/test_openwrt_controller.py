from __future__ import annotations

import base64
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, BinaryIO

import pytest

from homeserver_iac.models.openwrt import OpenWrtDesiredState
from homeserver_iac.openwrt import REQUIRED_PACKAGES, OpenWrtSafetyError
from homeserver_iac.openwrt_controller import (
    TransactionJournal,
    _restore_mutations,
    _verify_projection,
    apply_openwrt_all,
    apply_openwrt_stage,
    recover_pending_base,
    recover_pending_bootstrap_sanitize,
    recover_pending_stage_transaction,
    revert_openwrt_transaction,
    stage_changes_for_state,
)
from homeserver_iac.openwrt_reconcile import build_stage_changes
from homeserver_iac.runtime import OperationalError
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.validation import load_model


class FakeCrypto:
    def encrypt(self, chunks: Iterable[bytes], destination: BinaryIO) -> None:
        destination.write(b"AGE")
        for chunk in chunks:
            destination.write(bytes(value ^ 0x55 for value in chunk))

    def decrypt(self, chunks: Iterable[bytes], destination: BinaryIO) -> None:
        ciphertext = b"".join(chunks)
        assert ciphertext.startswith(b"AGE")
        destination.write(bytes(value ^ 0x55 for value in ciphertext[3:]))


class FakeHelper:
    def __init__(self) -> None:
        self.requests: list[Mapping[str, Any]] = []

    def helper_call(self, envelope: Mapping[str, Any]) -> Mapping[str, Any]:
        self.requests.append(envelope)
        method = envelope["method"]
        arguments = envelope.get("arguments", {})
        if method == "lock-acquire":
            return {"ok": True, "acquired": True}
        if method == "create":
            return {"ok": True, "sid": "fixture-sid"}
        if method == "lock-status":
            return {"ok": True, "present": False}
        if method == "compare":
            expected = arguments.get("expected", {})
            return {
                "ok": True,
                "match": True,
                "fields": {path: {"present": True, "match": True} for path in expected},
            }
        return {"ok": True}


class SequencedLockHelper(FakeHelper):
    def __init__(self, locks: Iterable[bool]) -> None:
        super().__init__()
        self.locks = iter(locks)

    def helper_call(self, envelope: Mapping[str, Any]) -> Mapping[str, Any]:
        if envelope["method"] == "lock-status":
            self.requests.append(envelope)
            return {"ok": True, "present": next(self.locks)}
        return super().helper_call(envelope)


class MismatchedSecretHelper(FakeHelper):
    def helper_call(self, envelope: Mapping[str, Any]) -> Mapping[str, Any]:
        response = super().helper_call(envelope)
        if envelope["method"] == "compare":
            expected = envelope.get("arguments", {}).get("expected", {})
            return {
                "ok": True,
                "match": False,
                "fields": {path: {"present": True, "match": False} for path in expected},
            }
        return response


class MissingSessionHelper(FakeHelper):
    def helper_call(self, envelope: Mapping[str, Any]) -> Mapping[str, Any]:
        response = super().helper_call(envelope)
        if envelope["method"] == "create":
            return {"ok": True}
        return response


def healthy_base_state(snapshot: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "identity": {
            "board_ids": ["R53"],
            "board_name": "cudy,wr3000e-v1",
            "model": "Cudy WR3000E v1",
            "profile": "cudy_wr3000e-v1",
            "release": "25.12.5",
            "target": "mediatek/filogic",
        },
        "packages": sorted(REQUIRED_PACKAGES),
        "uci": dict(snapshot or {}),
        "resources": {},
        "firewall": {"redirects": [], "includes": [], "dmz": False, "wan_management": False},
        "listeners": [],
        "services": {"upnp": False, "nat_pmp": False, "tailscale": False},
        "runtime": {
            "base": {
                "wired_ssh": True,
                "lan_address": "192.168.1.1/24",
                "dhcp": True,
                "dns": True,
                "firewall": True,
                "management_network": "trusted",
                "ssh_password_auth": False,
                "luci_https_only": True,
            },
            "sqm": {"enabled": False, "enabled_queues": 0},
            "radio_bands": [],
        },
    }


def converging_reader(
    desired: OpenWrtDesiredState,
) -> tuple[dict[str, Any], Any]:
    initial = healthy_base_state()
    post = healthy_base_state(build_stage_changes(desired, "base", snapshot={}).expected_projection)
    calls = 0

    def read() -> Mapping[str, Any]:
        nonlocal calls
        calls += 1
        return initial if calls <= 2 else post

    return post, read


@pytest.fixture
def desired() -> OpenWrtDesiredState:
    return load_model(INFRA_ROOT / "network/openwrt/router.yaml", OpenWrtDesiredState)


def test_apply_journals_before_rpcd_and_promotes_only_after_confirm(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    _, read_state = converging_reader(desired)
    helper = FakeHelper()
    crypto = FakeCrypto()
    journal = TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto)

    result = apply_openwrt_stage(
        desired=desired,
        client=helper,
        state_reader=read_state,
        resolve_secret=lambda alias: f"fixture-{alias}",
        config_archive=lambda: b"fixture-config-archive",
        journal=journal,
        stage="base",
        lock_path=tmp_path / "apply.lock",
        controller_id="fixture-controller",
    )

    assert result.transaction.transaction_id.startswith("tx_")
    assert result.transaction.index_path.exists()
    assert [request["method"] for request in helper.requests][-3:] == [
        "confirm",
        "destroy",
        "lock-release",
    ]
    public_index = result.transaction.index_path.read_text()
    assert "fixture-config-archive" not in public_index
    payload = journal.load(result.transaction.transaction_id)
    assert payload["config_archive_base64"]
    assert payload["created_sections"]


def test_converged_stage_is_a_true_noop(desired: OpenWrtDesiredState, tmp_path: Path) -> None:
    initial = build_stage_changes(desired, "base", snapshot={})
    snapshot = {
        path: value
        for path, value in initial.expected_projection.items()
        if value is not None and not path.endswith("._section_absent")
    }
    for section in initial.created_sections:
        snapshot[f"{section}._type"] = "fixture"
    state = healthy_base_state(snapshot)
    helper = FakeHelper()
    crypto = FakeCrypto()
    result = apply_openwrt_stage(
        desired=desired,
        client=helper,
        state_reader=lambda: state,
        resolve_secret=lambda alias: f"fixture-{alias}",
        config_archive=lambda: pytest.fail("converged stage must not create a backup"),
        journal=TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto),
        stage="base",
        lock_path=tmp_path / "apply.lock",
        controller_id="fixture-controller",
    )
    assert result.apply is None
    assert result.transaction is None
    assert helper.requests == []


def test_transaction_generation_archive_preserves_ciphertext_and_hides_lineage(
    tmp_path: Path,
) -> None:
    crypto = FakeCrypto()
    root = tmp_path / "transactions"
    journal = TransactionJournal(root, encryptor=crypto, decryptor=crypto)
    accepted = root / "tx_fixture_accepted"
    failed = root / ".tx_fixture.failed-health-rolled-back"
    accepted.mkdir(parents=True)
    failed.mkdir()
    (accepted / "bundle.age").write_bytes(b"AGEaccepted")
    (failed / "bundle.age").write_bytes(b"AGEfailed")

    generation = journal.archive_generation()

    assert generation is not None
    assert generation.name.startswith(".generation-pre-clean-")
    assert (generation / accepted.name / "bundle.age").read_bytes() == b"AGEaccepted"
    assert (generation / failed.name / "bundle.age").read_bytes() == b"AGEfailed"
    assert journal.accepted() == ()


def test_transaction_generation_archive_refuses_pending_state(tmp_path: Path) -> None:
    crypto = FakeCrypto()
    root = tmp_path / "transactions"
    pending = root / ".tx_fixture_pending.pending"
    pending.mkdir(parents=True)
    (pending / "index.json").write_text(
        json.dumps({"transaction_id": "tx_fixture_pending", "stage": "base"})
    )
    active = root / "tx_fixture_accepted"
    active.mkdir()

    journal = TransactionJournal(root, encryptor=crypto, decryptor=crypto)
    with pytest.raises(OpenWrtSafetyError, match="while one is pending"):
        journal.archive_generation()
    assert active.exists()


def test_apply_refuses_existing_pending_transaction(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    crypto = FakeCrypto()
    journal = TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto)
    journal.prepare(
        {
            "transaction_id": "tx_fixture_pending",
            "stage": "base",
            "timestamp": "2026-07-16T00:00:00+00:00",
        }
    )

    with pytest.raises(OpenWrtSafetyError, match="existing pending transaction"):
        apply_openwrt_stage(
            desired=desired,
            client=FakeHelper(),
            state_reader=lambda: pytest.fail("pending journal must block before reading state"),
            resolve_secret=lambda alias: alias,
            config_archive=lambda: b"archive",
            journal=journal,
            stage="base",
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )


def test_changed_preflight_state_archives_pending_transaction(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    initial = healthy_base_state()
    changed = healthy_base_state({"system.system.hostname": "changed"})
    calls = 0

    def read_state() -> Mapping[str, Any]:
        nonlocal calls
        calls += 1
        return initial if calls == 1 else changed

    crypto = FakeCrypto()
    journal = TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto)
    with pytest.raises(OpenWrtSafetyError, match="changed before staging"):
        apply_openwrt_stage(
            desired=desired,
            client=FakeHelper(),
            state_reader=read_state,
            resolve_secret=lambda alias: f"fixture-{alias}",
            config_archive=lambda: b"archive",
            journal=journal,
            stage="base",
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )

    assert journal.pending() == ()
    assert len(tuple((tmp_path / "transactions").glob("*.failed-preflight"))) == 1


def test_failed_apply_archives_journal_after_verified_pre_state(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    state = healthy_base_state()
    crypto = FakeCrypto()
    journal = TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto)

    with pytest.raises(OperationalError, match=r"transaction .* failed"):
        apply_openwrt_stage(
            desired=desired,
            client=MissingSessionHelper(),
            state_reader=lambda: state,
            resolve_secret=lambda alias: f"fixture-{alias}",
            config_archive=lambda: b"archive",
            journal=journal,
            stage="base",
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )

    assert journal.pending() == ()
    assert len(tuple((tmp_path / "transactions").glob("*.failed-rolled-back"))) == 1


def test_ansible_owned_hidden_base_fields_are_ignored_by_protected_convergence(
    desired: OpenWrtDesiredState,
) -> None:
    initial = build_stage_changes(desired, "base", snapshot={})
    snapshot = {
        path: value
        for path, value in initial.expected_projection.items()
        if value is not None and not path.endswith("._section_absent")
    }
    for section in initial.created_sections:
        snapshot[f"{section}._type"] = "fixture"
    hidden = {
        "dhcp.dnsmasq.rebind_domain": desired.security.dns_rebind_allow_domains,
        "dhcp.dnsmasq.server": desired.dns.upstreams,
        "dhcp.dnsmasq.strictorder": "1",
        "dhcp.dnsmasq.noresolv": "1",
        "dhcp.hs_base_host_atlas.dns": "1",
        "dhcp.hs_base_host_truenas.dns": "1",
    }
    for path in hidden:
        snapshot[path] = {"present": True, "withheld": True}
    helper = FakeHelper()

    changes = stage_changes_for_state(
        desired=desired,
        client=helper,
        state=healthy_base_state(snapshot),
        stage="base",
        resolve_secret=lambda alias: pytest.fail(f"unexpected secret lookup: {alias}"),
    )

    assert changes.mutations == ()
    assert helper.requests == []


def test_pending_stage_recovery_accepts_reused_anonymous_section_id(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    state = healthy_base_state(
        {
            "firewall.cfg05._anonymous": True,
            "firewall.cfg05._type": "rule",
            "firewall.cfg05.name": "Remaining-Rule",
        }
    )
    transaction_id = "tx_fixture_pending"
    crypto = FakeCrypto()
    journal = TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto)
    journal.prepare(
        {
            "transaction_id": transaction_id,
            "stage": "base",
            "timestamp": "2026-07-16T00:00:00+00:00",
            "board": state["identity"],
            "config_schema_version": desired.schema_version,
            "pre_projection": {
                "firewall.cfg05._anonymous": True,
                "firewall.cfg05._type": "rule",
                "firewall.cfg05.name": "Deleted-Rule",
            },
            "expected_post_projection": {"firewall.cfg05._section_absent": None},
            "owned_paths": [],
            "created_sections": [],
            "deleted_sections": ["firewall.cfg05"],
            "enabled_stages": ["base"],
            "parent_transaction_id": None,
            "config_archive_base64": base64.b64encode(b"archive").decode(),
        }
    )

    recovered = recover_pending_stage_transaction(
        desired=desired,
        client=FakeHelper(),
        state_reader=lambda: state,
        journal=journal,
        transaction_id=transaction_id,
    )

    assert recovered.transaction_id == transaction_id
    assert journal.pending() == ()


def prepare_pending_recovery(
    *,
    desired: OpenWrtDesiredState,
    root: Path,
    state: Mapping[str, Any],
    pre: Mapping[str, Any],
    post: Mapping[str, Any],
    revert: bool = False,
) -> tuple[TransactionJournal, str]:
    crypto = FakeCrypto()
    journal = TransactionJournal(root, encryptor=crypto, decryptor=crypto)
    parent_id: str | None = None
    if revert:
        parent_id = "tx_fixture_original"
        original = journal.prepare(
            {
                "transaction_id": parent_id,
                "stage": "base",
                "timestamp": "2026-07-16T00:00:00+00:00",
                "pre_projection": dict(post),
                "expected_post_projection": dict(pre),
                "created_sections": [],
                "deleted_sections": [],
                "enabled_stages": [],
            }
        )
        journal.accept(original, parent_id)
    transaction_id = "tx_fixture_pending"
    payload: dict[str, Any] = {
        "transaction_id": transaction_id,
        "stage": "base",
        "timestamp": "2026-07-16T00:01:00+00:00",
        "board": state["identity"],
        "config_schema_version": desired.schema_version,
        "pre_projection": dict(pre),
        "expected_post_projection": dict(post),
        "owned_paths": list(pre),
        "created_sections": [],
        "deleted_sections": [],
        "enabled_stages": [],
        "parent_transaction_id": parent_id,
        "config_archive_base64": base64.b64encode(b"archive").decode(),
    }
    if parent_id is not None:
        payload["reverts_transaction_id"] = parent_id
    journal.prepare(payload)
    return journal, transaction_id


@pytest.mark.parametrize(
    ("endpoint", "outcome"),
    [("post", "accepted"), ("pre", "rolled-back")],
)
def test_pending_stage_recovery_classifies_stable_normal_endpoints(
    desired: OpenWrtDesiredState, tmp_path: Path, endpoint: str, outcome: str
) -> None:
    pre = {"system.system.hostname": "before"}
    post = {"system.system.hostname": "after"}
    state = healthy_base_state(post if endpoint == "post" else pre)
    journal, transaction_id = prepare_pending_recovery(
        desired=desired,
        root=tmp_path / "transactions",
        state=state,
        pre=pre,
        post=post,
    )

    result = recover_pending_stage_transaction(
        desired=desired,
        client=SequencedLockHelper([False, False, False]),
        state_reader=lambda: state,
        journal=journal,
        transaction_id=transaction_id,
    )

    assert result.outcome == outcome
    assert journal.pending() == ()
    if outcome == "accepted":
        assert journal.latest("base").transaction_id == transaction_id
    else:
        assert result.path.name == f".{transaction_id}.failed-rolled-back"


def test_pending_stage_recovery_leaves_intermediate_state_pending(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    state = healthy_base_state({"system.system.hostname": "intermediate"})
    journal, transaction_id = prepare_pending_recovery(
        desired=desired,
        root=tmp_path / "transactions",
        state=state,
        pre={"system.system.hostname": "before"},
        post={"system.system.hostname": "after"},
    )

    with pytest.raises(OpenWrtSafetyError, match="no exact terminal endpoint"):
        recover_pending_stage_transaction(
            desired=desired,
            client=SequencedLockHelper([False, False, False]),
            state_reader=lambda: state,
            journal=journal,
            transaction_id=transaction_id,
        )
    assert journal.pending()[0].transaction_id == transaction_id


def test_pending_stage_recovery_leaves_locked_state_pending(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    state = healthy_base_state({"system.system.hostname": "after"})
    journal, transaction_id = prepare_pending_recovery(
        desired=desired,
        root=tmp_path / "transactions",
        state=state,
        pre={"system.system.hostname": "before"},
        post={"system.system.hostname": "after"},
    )

    with pytest.raises(OpenWrtSafetyError, match="lock appeared during"):
        recover_pending_stage_transaction(
            desired=desired,
            client=SequencedLockHelper([False, True]),
            state_reader=lambda: state,
            journal=journal,
            transaction_id=transaction_id,
        )
    assert journal.pending()[0].transaction_id == transaction_id


def test_pending_stage_recovery_leaves_changed_reads_pending(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    first = healthy_base_state({"system.system.hostname": "after"})
    second = healthy_base_state({"system.system.hostname": "after", "network.lan.proto": "changed"})
    states = iter((first, second))
    journal, transaction_id = prepare_pending_recovery(
        desired=desired,
        root=tmp_path / "transactions",
        state=first,
        pre={"system.system.hostname": "before"},
        post={"system.system.hostname": "after"},
    )

    with pytest.raises(OpenWrtSafetyError, match="state changed"):
        recover_pending_stage_transaction(
            desired=desired,
            client=SequencedLockHelper([False, False, False]),
            state_reader=lambda: next(states),
            journal=journal,
            transaction_id=transaction_id,
        )
    assert journal.pending()[0].transaction_id == transaction_id


@pytest.mark.parametrize(
    ("endpoint", "outcome"),
    [("post", "accepted"), ("pre", "rolled-back")],
)
def test_pending_revert_recovery_classifies_stable_endpoints(
    desired: OpenWrtDesiredState, tmp_path: Path, endpoint: str, outcome: str
) -> None:
    revert_pre = {"system.system.hostname": "applied"}
    revert_post = {"system.system.hostname": "restored"}
    state = healthy_base_state(revert_post if endpoint == "post" else revert_pre)
    journal, transaction_id = prepare_pending_recovery(
        desired=desired,
        root=tmp_path / "transactions",
        state=state,
        pre=revert_pre,
        post=revert_post,
        revert=True,
    )

    result = recover_pending_stage_transaction(
        desired=desired,
        client=SequencedLockHelper([False, False, False]),
        state_reader=lambda: state,
        journal=journal,
        transaction_id=transaction_id,
    )

    assert result.outcome == outcome
    assert journal.pending() == ()


def test_restore_skips_options_absent_before_and_after() -> None:
    assert (
        _restore_mutations(
            {
                "pre_projection": {"network.globals.ula_prefix": None},
                "expected_post_projection": {"network.globals.ula_prefix": None},
                "created_sections": [],
                "deleted_sections": [],
            },
            current_snapshot={},
        )
        == ()
    )


def test_restore_recreates_deleted_sections_with_anonymity_values_and_order() -> None:
    mutations = _restore_mutations(
        {
            "pre_projection": {
                "firewall.wan._anonymous": False,
                "firewall.wan._index": 1,
                "firewall.wan._name": "wan",
                "firewall.wan._type": "zone",
                "firewall.wan.input": "REJECT",
                "firewall.cfg02._anonymous": True,
                "firewall.cfg02._index": 2,
                "firewall.cfg02._name": "cfg02",
                "firewall.cfg02._type": "rule",
                "firewall.cfg02.name": "Allow-IPSec-ESP",
                "firewall.cfg02.proto": "esp",
            },
            "expected_post_projection": {
                "firewall.wan._section_absent": None,
                "firewall.cfg02._section_absent": None,
            },
            "created_sections": [],
            "deleted_sections": ["firewall.wan", "firewall.cfg02"],
        },
        current_snapshot={
            "firewall.defaults._anonymous": False,
            "firewall.defaults._index": 0,
            "firewall.defaults._name": "defaults",
            "firewall.defaults._type": "defaults",
            "firewall.forwarding._anonymous": False,
            "firewall.forwarding._index": 1,
            "firewall.forwarding._name": "forwarding",
            "firewall.forwarding._type": "forwarding",
        },
    )

    assert mutations == (
        {
            "method": "add",
            "arguments": {
                "config": "firewall",
                "type": "zone",
                "name": "wan",
                "values": {"input": "REJECT"},
            },
        },
        {
            "method": "add",
            "arguments": {
                "config": "firewall",
                "type": "rule",
                "values": {"name": "Allow-IPSec-ESP", "proto": "esp"},
            },
            "capture_section_as": "firewall.cfg02",
        },
        {
            "method": "order",
            "arguments": {
                "config": "firewall",
                "sections": ["defaults", "wan", "cfg02", "forwarding"],
            },
        },
    )


def test_projection_verification_rebinds_restored_anonymous_section_id() -> None:
    expected = {
        "firewall.cfg02._anonymous": True,
        "firewall.cfg02._index": 1,
        "firewall.cfg02._name": "cfg02",
        "firewall.cfg02._type": "rule",
        "firewall.cfg02.name": "Allow-IPSec-ESP",
        "firewall.cfg02.proto": "esp",
    }
    state = healthy_base_state(
        {
            "firewall.cfg99._anonymous": True,
            "firewall.cfg99._index": 1,
            "firewall.cfg99._name": "cfg99",
            "firewall.cfg99._type": "rule",
            "firewall.cfg99.name": "Allow-IPSec-ESP",
            "firewall.cfg99.proto": "esp",
        }
    )

    _verify_projection(FakeHelper(), state, expected)


def test_base_cannot_bypass_bootstrap_sanitize_on_clean_image(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    state = healthy_base_state({"network.wan.proto": "dhcp", "network.wan6.proto": "dhcpv6"})
    crypto = FakeCrypto()
    with pytest.raises(OpenWrtSafetyError, match="requires bootstrap-sanitize"):
        apply_openwrt_stage(
            desired=desired,
            client=FakeHelper(),
            state_reader=lambda: state,
            resolve_secret=lambda alias: f"fixture-{alias}",
            config_archive=lambda: b"archive",
            journal=TransactionJournal(
                tmp_path / "transactions", encryptor=crypto, decryptor=crypto
            ),
            stage="base",
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )


def test_bootstrap_sanitize_runs_as_a_protected_transaction(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    factory_snapshot = {
        "network.wan._type": "interface",
        "network.wan.device": "wan",
        "network.wan.proto": "dhcp",
        "network.wan6._type": "interface",
        "network.wan6.device": "wan",
        "network.wan6.proto": "dhcpv6",
        "network.lan._type": "interface",
        "network.lan.device": "br-lan",
        "network.lan.proto": "static",
        "network.lan.ipaddr": ["192.168.1.1/24"],
        "wireless.radio0._type": "wifi-device",
        "wireless.radio1._type": "wifi-device",
        "wireless.default_radio0._type": "wifi-iface",
        "wireless.default_radio0.disabled": "1",
        "wireless.default_radio1._type": "wifi-iface",
        "wireless.default_radio1.disabled": "1",
    }
    initial = healthy_base_state(factory_snapshot)
    initial["runtime"] = {
        "bootstrap-sanitize": {
            "default_wan": True,
            "default_wan6": True,
            "wireless": False,
        },
        "sqm": {"enabled": False, "enabled_queues": 0},
        "radio_bands": [],
    }
    post_snapshot = {
        path: value
        for path, value in factory_snapshot.items()
        if not path.startswith(("network.wan.", "network.wan6."))
    }
    post = healthy_base_state(post_snapshot)
    post["runtime"]["bootstrap-sanitize"] = {
        "default_wan": False,
        "default_wan6": False,
        "wireless": False,
    }
    calls = 0

    def read_state() -> Mapping[str, Any]:
        nonlocal calls
        calls += 1
        return initial if calls <= 2 else post

    helper = FakeHelper()
    crypto = FakeCrypto()
    result = apply_openwrt_stage(
        desired=desired,
        client=helper,
        state_reader=read_state,
        resolve_secret=lambda alias: f"fixture-{alias}",
        config_archive=lambda: b"factory-archive",
        journal=TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto),
        stage="bootstrap-sanitize",
        lock_path=tmp_path / "apply.lock",
        controller_id="fixture-controller",
    )
    methods = [request["method"] for request in helper.requests]
    assert result.apply is not None
    assert result.apply.stage == "bootstrap-sanitize"
    assert methods.count("apply") == 1
    assert methods.count("confirm") == 1


def test_pending_bootstrap_sanitize_recovery_requires_exact_live_post_state(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    snapshot = {
        "network.lan._type": "interface",
        "network.lan.device": "br-lan",
        "network.lan.proto": "static",
        "network.lan.ipaddr": ["192.168.1.1/24"],
        "wireless.radio0._type": "wifi-device",
        "wireless.radio1._type": "wifi-device",
        "wireless.default_radio0._type": "wifi-iface",
        "wireless.default_radio0.disabled": "1",
        "wireless.default_radio1._type": "wifi-iface",
        "wireless.default_radio1.disabled": "1",
    }
    state = healthy_base_state(snapshot)
    state["runtime"]["bootstrap-sanitize"] = {
        "default_wan": False,
        "default_wan6": False,
        "wireless": False,
    }
    transaction_id = "tx_20260716T164346Z_9da1e7637094"
    crypto = FakeCrypto()
    journal = TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto)
    pending = journal.prepare(
        {
            "transaction_id": transaction_id,
            "stage": "bootstrap-sanitize",
            "timestamp": "2026-07-16T16:43:46+00:00",
            "board": state["identity"],
            "config_schema_version": desired.schema_version,
            "pre_projection": {
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
            },
            "expected_post_projection": {
                "network.wan._section_absent": None,
                "network.wan6._section_absent": None,
            },
            "owned_paths": [],
            "created_sections": [],
            "deleted_sections": ["network.wan", "network.wan6"],
            "enabled_stages": [],
            "parent_transaction_id": None,
            "config_archive_base64": "YmFja3Vw",
        }
    )

    recovered = recover_pending_bootstrap_sanitize(
        desired=desired,
        client=FakeHelper(),
        state_reader=lambda: state,
        journal=journal,
    )

    assert recovered.transaction_id == transaction_id
    assert not pending.exists()
    assert journal.latest("bootstrap-sanitize") == recovered

    second_journal = TransactionJournal(
        tmp_path / "second-transactions", encryptor=crypto, decryptor=crypto
    )
    second_journal.prepare(journal.load(transaction_id))
    stale = {**state, "uci": {**snapshot, "network.wan.proto": "dhcp"}}
    with pytest.raises(OpenWrtSafetyError, match="exact clean-image"):
        recover_pending_bootstrap_sanitize(
            desired=desired,
            client=FakeHelper(),
            state_reader=lambda: stale,
            journal=second_journal,
        )


def test_pending_base_recovery_requires_converged_live_state_and_sanitize_lineage(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    crypto = FakeCrypto()
    journal = TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto)
    sanitize_id = "tx_20260716T170000Z_sanitize0001"
    sanitize = journal.prepare(
        {
            "transaction_id": sanitize_id,
            "stage": "bootstrap-sanitize",
            "timestamp": "2026-07-16T17:00:00+00:00",
            "expected_post_projection": {},
        }
    )
    journal.accept(sanitize, sanitize_id)

    initial_changes = build_stage_changes(desired, "base", snapshot={})
    state = healthy_base_state(
        {
            path: value
            for path, value in initial_changes.expected_projection.items()
            if value is not None
        }
    )
    converged = build_stage_changes(desired, "base", snapshot=state["uci"])
    assert converged.mutations == ()
    transaction_id = "tx_20260716T171003Z_ee77a79c3d93"
    pending = journal.prepare(
        {
            "transaction_id": transaction_id,
            "stage": "base",
            "timestamp": "2026-07-16T17:10:03+00:00",
            "board": state["identity"],
            "config_schema_version": desired.schema_version,
            "pre_projection": {},
            "expected_post_projection": dict(converged.expected_projection),
            "owned_paths": list(converged.owned_paths),
            "created_sections": [],
            "deleted_sections": [],
            "enabled_stages": [],
            "parent_transaction_id": None,
            "config_archive_base64": "YmFja3Vw",
        }
    )

    recovered = recover_pending_base(
        desired=desired,
        client=FakeHelper(),
        state_reader=lambda: state,
        journal=journal,
    )

    assert recovered.transaction_id == transaction_id
    assert not pending.exists()
    assert journal.latest("base") == recovered


def test_bootstrap_sanitize_is_refused_after_accepted_wan(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    crypto = FakeCrypto()
    journal = TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto)
    transaction_id = "tx_20260716T120000Z_fixturewan0001"
    pending = journal.prepare(
        {
            "transaction_id": transaction_id,
            "stage": "wan",
            "timestamp": "2026-07-16T12:00:00Z",
            "pre_projection": {},
            "expected_post_projection": {},
            "owned_paths": [],
            "created_sections": [],
            "deleted_sections": [],
            "enabled_stages": ["base", "wan"],
            "parent_transaction_id": None,
            "config_archive_base64": "",
        }
    )
    journal.accept(pending, transaction_id)
    with pytest.raises(OpenWrtSafetyError, match="one-time"):
        apply_openwrt_stage(
            desired=desired,
            client=FakeHelper(),
            state_reader=lambda: healthy_base_state(),
            resolve_secret=lambda alias: f"fixture-{alias}",
            config_archive=lambda: b"archive",
            journal=journal,
            stage="bootstrap-sanitize",
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )


def test_revert_requires_stage_head_and_matching_current_projection(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    mutable_state, read_state = converging_reader(desired)
    helper = FakeHelper()
    crypto = FakeCrypto()
    journal = TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto)
    applied = apply_openwrt_stage(
        desired=desired,
        client=helper,
        state_reader=read_state,
        resolve_secret=lambda alias: f"fixture-{alias}",
        config_archive=lambda: b"archive",
        journal=journal,
        stage="base",
        lock_path=tmp_path / "apply.lock",
        controller_id="fixture-controller",
    )
    payload = journal.load(applied.transaction.transaction_id)
    mutable_state["uci"] = dict(payload["expected_post_projection"])
    pre_state = healthy_base_state(
        {
            path: value
            for path, value in payload["pre_projection"].items()
            if value is not None and not path.endswith("._section_absent")
        }
    )
    revert_reads = 0

    def read_revert_state() -> Mapping[str, Any]:
        nonlocal revert_reads
        revert_reads += 1
        return mutable_state if revert_reads <= 3 else pre_state

    result = revert_openwrt_transaction(
        desired=desired,
        client=helper,
        state_reader=read_revert_state,
        config_archive=lambda: b"revert-archive",
        journal=journal,
        transaction_id=applied.transaction.transaction_id,
        lock_path=tmp_path / "apply.lock",
        controller_id="fixture-controller",
    )
    assert result.stage == "base"
    assert any(request["method"] == "delete" for request in helper.requests)
    latest = journal.latest("base")
    assert latest is not None
    assert latest.transaction_id != applied.transaction.transaction_id
    assert (
        journal.load(latest.transaction_id)["expected_post_projection"] == payload["pre_projection"]
    )

    mutable_state["uci"] = {"system.system.hostname": "unexpected"}
    with pytest.raises(OpenWrtSafetyError, match="stale"):
        revert_openwrt_transaction(
            desired=desired,
            client=helper,
            state_reader=lambda: mutable_state,
            config_archive=lambda: b"archive",
            journal=journal,
            transaction_id=applied.transaction.transaction_id,
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )


def test_public_transaction_index_has_only_ciphertext_metadata(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    _, read_state = converging_reader(desired)
    crypto = FakeCrypto()
    journal = TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto)
    applied = apply_openwrt_stage(
        desired=desired,
        client=FakeHelper(),
        state_reader=read_state,
        resolve_secret=lambda alias: f"fixture-{alias}",
        config_archive=lambda: b"secret-bearing-config",
        journal=journal,
        stage="base",
        lock_path=tmp_path / "apply.lock",
        controller_id="fixture-controller",
    )
    index = json.loads(applied.transaction.index_path.read_text())
    assert set(index) == {
        "bundle",
        "ciphertext_sha256",
        "ciphertext_size",
        "stage",
        "timestamp",
        "transaction_id",
    }


def test_failed_post_confirm_acceptance_runs_protected_pre_state_restore(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    initial = healthy_base_state()
    bad_post = healthy_base_state({"system.system.hostname": "wrong"})
    helper = FakeHelper()
    calls = 0

    def read_state() -> Mapping[str, Any]:
        nonlocal calls
        calls += 1
        if sum(request["method"] == "apply" for request in helper.requests) >= 2:
            return initial
        return initial if calls <= 2 else bad_post

    crypto = FakeCrypto()
    journal = TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto)
    with pytest.raises(OpenWrtSafetyError, match="differs"):
        apply_openwrt_stage(
            desired=desired,
            client=helper,
            state_reader=read_state,
            resolve_secret=lambda alias: f"fixture-{alias}",
            config_archive=lambda: b"archive",
            journal=journal,
            stage="base",
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )
    assert sum(request["method"] == "apply" for request in helper.requests) == 2
    assert journal.accepted() == ()
    assert journal.pending() == ()
    assert len(tuple((tmp_path / "transactions").glob("*.failed-rolled-back"))) == 1


def test_all_orchestrates_only_protected_stage_calls(monkeypatch: object, tmp_path: Path) -> None:
    import homeserver_iac.openwrt_controller as controller

    stages: list[str] = []
    monkeypatch.setattr(
        controller,
        "apply_openwrt_stage",
        lambda **kwargs: (
            stages.append(str(kwargs["stage"])) or controller.ControllerResult(None, None)
        ),
    )
    crypto = FakeCrypto()
    results = apply_openwrt_all(
        desired=object(),  # type: ignore[arg-type]
        client=FakeHelper(),
        state_reader=lambda: {},
        resolve_secret=lambda alias: alias,
        config_archive=lambda: b"",
        journal=TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto),
        lock_path=tmp_path / "apply.lock",
        controller_id="fixture-controller",
    )
    assert stages == ["base", "wan", "guest", "ipv6"]
    assert len(results) == 4


@pytest.mark.parametrize("stage", ["main-wifi", "sqm"])
def test_protected_controller_rejects_ansible_owned_stages(
    desired: OpenWrtDesiredState, tmp_path: Path, stage: str
) -> None:
    crypto = FakeCrypto()
    with pytest.raises(OpenWrtSafetyError, match="not a protected convergence stage"):
        apply_openwrt_stage(
            desired=desired,
            client=FakeHelper(),
            state_reader=lambda: pytest.fail("routine stage must fail before state read"),
            resolve_secret=lambda alias: alias,
            config_archive=lambda: b"",
            journal=TransactionJournal(
                tmp_path / "transactions", encryptor=crypto, decryptor=crypto
            ),
            stage=stage,
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )


def test_out_of_band_secret_change_blocks_prior_state_journaling(
    desired: OpenWrtDesiredState, tmp_path: Path
) -> None:
    crypto = FakeCrypto()
    journal = TransactionJournal(tmp_path / "transactions", encryptor=crypto, decryptor=crypto)
    transaction_id = "tx_20260716T120000Z_fixture000001"
    pending = journal.prepare(
        {
            "transaction_id": transaction_id,
            "stage": "wan",
            "timestamp": "2026-07-16T12:00:00Z",
            "pre_projection": {},
            "expected_post_projection": {"network.wan.password": "old-secret"},
            "owned_paths": ["network.wan.password"],
            "created_sections": [],
            "deleted_sections": [],
            "enabled_stages": ["base", "wan"],
            "parent_transaction_id": None,
            "config_archive_base64": "",
        }
    )
    journal.accept(pending, transaction_id)
    state = healthy_base_state({"network.wan.password": {"present": True}})
    with pytest.raises(OpenWrtSafetyError, match="accepted transaction lineage"):
        apply_openwrt_stage(
            desired=desired,
            client=MismatchedSecretHelper(),
            state_reader=lambda: state,
            resolve_secret=lambda alias: "old-secret",
            config_archive=lambda: b"archive",
            journal=journal,
            stage="wan",
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )
