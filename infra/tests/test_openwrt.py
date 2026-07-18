from __future__ import annotations

import hashlib
import io
import json
import struct
import tarfile
import zlib
from pathlib import Path
from typing import BinaryIO

import pytest

from homeserver_iac.models.common import ExitCode, OperationKind, serialize_plan
from homeserver_iac.models.openwrt import OpenWrtDesiredState
from homeserver_iac.openwrt import (
    REQUIRED_PACKAGES,
    ApplyAmbiguousError,
    CommandResult,
    LockContentionError,
    OpenWrtSafetyError,
    OpenWrtSshClient,
    apply_stage,
    effective_stage_policy,
    local_apply_lock,
    normalize_state,
    plan_openwrt,
    prove_timed_rollback,
    read_live_state,
    read_transaction_bundle,
    required_revert_health_stages,
    stream_encrypted_backup,
    validate_revert_bundle,
    validate_safety,
    write_transaction_bundle,
)
from homeserver_iac.openwrt_firmware import (
    BOARD,
    BOARD_ID,
    BUILDER_IMAGE,
    IMAGEBUILDER_SHA256,
    MODEL,
    PROFILE,
    REQUESTED_PACKAGES,
    TARGET,
    VERSION,
    FirmwareVerificationError,
    create_overlay,
    parse_sha256sums,
    verify_manifest,
)
from homeserver_iac.runtime import OperationalError
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.validation import load_model

FIXTURES = Path(__file__).parent / "fixtures/openwrt"
FAKE_SECRET = "fixture-secret-must-never-appear"


def fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text())


def test_timed_rollback_proof_observes_change_and_restoration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class RollbackClient:
        def __init__(self) -> None:
            self.snapshots = iter(("router", "homeserver-rollback-proof", "router"))
            self.methods: list[str] = []
            self.envelopes: list[dict[str, object]] = []

        def filtered_snapshot(self, configs: tuple[str, ...]) -> dict[str, str]:
            assert configs == ("system",)
            return {"system.cfg01.hostname": next(self.snapshots)}

        def helper_call(self, envelope: dict[str, object]) -> dict[str, object]:
            self.envelopes.append(envelope)
            method = str(envelope["method"])
            self.methods.append(method)
            if method == "lock-acquire":
                return {"ok": True, "acquired": True}
            if method == "create":
                return {"ok": True, "sid": "rollback-session"}
            if method == "lock-status":
                return {"ok": True, "present": False}
            return {"ok": True}

    ticks = iter((0.0, 0.0, 1.0, 2.0))
    monkeypatch.setattr("homeserver_iac.openwrt.time.monotonic", lambda: next(ticks))
    monkeypatch.setattr("homeserver_iac.openwrt.time.sleep", lambda seconds: None)
    client = RollbackClient()

    elapsed = prove_timed_rollback(
        client,  # type: ignore[arg-type]
        lock_path=tmp_path / "apply.lock",
        controller_id="rollback-proof-test",
    )

    assert elapsed == 2.0
    assert client.methods == [
        "lock-acquire",
        "create",
        "grant",
        "set",
        "apply",
        "destroy",
        "lock-release",
        "lock-status",
    ]
    apply = next(envelope for envelope in client.envelopes if envelope["method"] == "apply")
    assert apply["arguments"] == {
        "ubus_rpc_session": "rollback-session",
        "rollback": True,
        "timeout": 30,
    }


def test_timed_rollback_proof_cleans_up_when_apply_is_rejected(tmp_path: Path) -> None:
    class RejectedApplyClient:
        def __init__(self) -> None:
            self.methods: list[str] = []

        def filtered_snapshot(self, configs: tuple[str, ...]) -> dict[str, str]:
            assert configs == ("system",)
            return {"system.cfg01.hostname": "router"}

        def helper_call(self, envelope: dict[str, object]) -> dict[str, object]:
            method = str(envelope["method"])
            self.methods.append(method)
            if method == "lock-acquire":
                return {"ok": True, "acquired": True}
            if method == "create":
                return {"ok": True, "sid": "rollback-session"}
            if method == "apply":
                raise OperationalError("rejected")
            return {"ok": True}

    client = RejectedApplyClient()

    with pytest.raises(OperationalError, match="rejected"):
        prove_timed_rollback(
            client,  # type: ignore[arg-type]
            lock_path=tmp_path / "apply.lock",
            controller_id="rollback-proof-test",
        )

    assert client.methods == [
        "lock-acquire",
        "create",
        "grant",
        "set",
        "apply",
        "destroy",
        "lock-release",
    ]


DESIRED = {
    "system": {
        "hostname": "router",
        "timezone": "EET-2EEST,M3.5.0/3,M10.5.0/4",
        "zonename": "Europe/Athens",
    },
    "wan": {
        "protocol": "pppoe",
        "vlan_id": 835,
        "username": {"secret_ref": {"alias": "openwrt_pppoe_username"}},
        "password": {"secret_ref": {"alias": "openwrt_pppoe_password"}},
    },
    "security": {
        "upnp": False,
        "nat_pmp": False,
        "dmz": False,
        "wan_management": False,
        "port_forwards": [],
        "tailscale": False,
    },
}


def test_fixture_normalization_is_stable_and_drops_runtime_noise() -> None:
    raw = fixture("converged.json")
    raw["counters"] = {"bytes": 42}
    first = normalize_state(raw)
    second = normalize_state(json.loads(json.dumps(raw, sort_keys=True)))
    assert first == second
    assert "counters" not in first


def test_prebase_management_exception_is_explicit_and_narrow() -> None:
    state = fixture("factory.json")
    state["listeners"] = [{"network": "wan", "service": "dropbear"}]
    state["uci"]["dropbear.main._type"] = "dropbear"  # type: ignore[index]
    state["uci"]["dropbear.main.PasswordAuth"] = "on"  # type: ignore[index]
    state["uci"]["dropbear.main.RootPasswordAuth"] = "on"  # type: ignore[index]

    desired = load_model(INFRA_ROOT / "network/openwrt/router.yaml", OpenWrtDesiredState)
    with pytest.raises(OpenWrtSafetyError, match=r"management listener|password authentication"):
        validate_safety(desired, state)

    validate_safety(
        desired,
        state,
        allow_prebase_management=True,
    )

    state["firewall"]["wan_management"] = True  # type: ignore[index]
    with pytest.raises(OpenWrtSafetyError, match="WAN management"):
        validate_safety(
            desired,
            state,
            allow_prebase_management=True,
        )


def test_converged_and_drift_plans_are_deterministic_and_redacted() -> None:
    desired = load_model(INFRA_ROOT / "network/openwrt/router.yaml", OpenWrtDesiredState)
    converged = plan_openwrt(desired, fixture("converged.json"))
    assert all(operation.kind is OperationKind.UNCHANGED for operation in converged.operations)
    assert converged.exit_code == ExitCode.VALID

    drift = plan_openwrt(DESIRED, fixture("drift.json"))
    assert [(item.kind, item.resource_id) for item in drift.operations] == [
        (OperationKind.UPDATE, "system"),
        (OperationKind.STALE, "hs_retired"),
        (OperationKind.UNCHANGED, "security"),
        (OperationKind.UNCHANGED, "wan"),
    ]
    serialized = serialize_plan(drift)
    assert drift.exit_code == ExitCode.DRIFT
    assert FAKE_SECRET not in serialized
    assert "openwrt_pppoe_password" in serialized
    assert "password" not in next(
        item.changed_fields for item in drift.operations if item.resource_id == "system"
    )


def test_factory_fixture_is_clean_default_lan_with_disabled_radios() -> None:
    raw = fixture("factory.json")
    snapshot = raw["uci"]
    assert snapshot["network.lan.ipaddr"] == ["192.168.1.1/24"]
    assert snapshot["network.wan.proto"] == "dhcp"
    assert snapshot["network.wan6.proto"] == "dhcpv6"
    assert snapshot["wireless.default_radio0.disabled"] == "1"
    assert snapshot["wireless.default_radio1.disabled"] == "1"


def test_stage_plan_compares_only_owned_fields_and_preserves_later_state() -> None:
    desired = load_model(INFRA_ROOT / "network/openwrt/router.yaml", OpenWrtDesiredState)
    raw = fixture("converged.json")
    resources = raw["resources"]
    assert isinstance(resources, dict)
    resources["network-trusted"]["ipv6_hint"] = "f"
    resources["network-guest"]["address"] = "192.168.31.1/24"

    base = plan_openwrt(desired, raw, stage="base")

    assert all(operation.kind is OperationKind.UNCHANGED for operation in base.operations)
    assert {operation.resource_id for operation in base.operations} == {
        "management",
        "network-trusted",
        "reservation-atlas",
        "reservation-truenas",
        "system",
    }


def test_stage_plan_attaches_only_owned_secret_refs() -> None:
    desired = load_model(INFRA_ROOT / "network/openwrt/router.yaml", OpenWrtDesiredState)
    wan = plan_openwrt(desired, fixture("factory.json"), stage="wan")
    aliases = {secret.alias for operation in wan.operations for secret in operation.secret_refs}
    assert aliases == {"openwrt_pppoe_username", "openwrt_pppoe_password"}


def test_unmanaged_resource_is_a_non_mutating_warning() -> None:
    desired = load_model(INFRA_ROOT / "network/openwrt/router.yaml", OpenWrtDesiredState)
    raw = fixture("converged.json")
    raw["resources"]["operator-note"] = {"preserved": True}
    plan = plan_openwrt(desired, raw)
    warning = next(item for item in plan.operations if item.resource_id == "operator-note")
    assert warning.kind is OperationKind.WARNING
    assert plan.exit_code == 0


@pytest.mark.parametrize(
    "name, expected",
    [
        ("wrong-board.json", "identity.board_name"),
        ("wrong-packages.json", "forbidden packages"),
        ("rogue-forward.json", "redirects"),
    ],
)
def test_policy_violations_fail_before_planning(name: str, expected: str) -> None:
    with pytest.raises(OpenWrtSafetyError, match=expected):
        plan_openwrt(DESIRED, fixture(name))


class RecordingRunner:
    def __init__(self, responses: list[CommandResult] | None = None) -> None:
        self.calls: list[tuple[tuple[str, ...], bytes | None]] = []
        self.responses = responses or [CommandResult(0, b'{"ok":true}')]

    def __call__(
        self, argv: list[str] | tuple[str, ...], *, input_data: bytes | None, timeout: float
    ) -> CommandResult:
        self.calls.append((tuple(argv), input_data))
        return self.responses.pop(0) if self.responses else CommandResult(0, b'{"ok":true}')


def client(runner: RecordingRunner, *, proxy_jump: str | None = None) -> OpenWrtSshClient:
    return OpenWrtSshClient(
        host="root@192.0.2.1",
        known_hosts=Path("state/known_hosts"),
        identity=Path("keys/id_ed25519"),
        proxy_jump=proxy_jump,
        runner=runner,
    )


def test_ssh_argv_is_strict_and_helper_payload_is_stdin_only() -> None:
    runner = RecordingRunner()
    secret_envelope = {
        "object": "uci",
        "method": "set",
        "arguments": {"config": "network", "values": {"password": FAKE_SECRET}},
    }
    client(runner).helper_call(secret_envelope)
    argv, stdin = runner.calls[0]
    assert argv[:3] == ("ssh", "-F", "/dev/null")
    assert "StrictHostKeyChecking=yes" in argv
    assert argv[-1] == "/usr/libexec/homeserver-uci"
    assert FAKE_SECRET not in " ".join(argv)
    assert FAKE_SECRET.encode() in (stdin or b"")


def test_proxy_jump_is_read_only() -> None:
    runner = RecordingRunner([CommandResult(0, b'{"board_name":"test"}')])
    proxy_client = client(runner, proxy_jump="atlas")
    proxy_client.read_json("board")
    assert "-J" in runner.calls[0][0]
    with pytest.raises(OpenWrtSafetyError, match="direct wired"):
        proxy_client.helper_call({"object": "uci", "method": "confirm", "arguments": {}})


def test_proxy_jump_allows_default_deny_filtered_snapshot() -> None:
    runner = RecordingRunner(
        [CommandResult(0, b'{"ok":true,"values":{"system.system.hostname":"router"}}')]
    )
    values = client(runner, proxy_jump="atlas").filtered_snapshot({"system"})
    argv, payload = runner.calls[0]
    assert "-J" in argv
    assert values == {"system.system.hostname": "router"}
    assert json.loads(payload or b"{}")["arguments"] == {"configs": ["system"]}


def test_rollback_response_fixtures_fail_closed_without_diagnostics() -> None:
    responses = fixture("rollback-responses.json")
    success = responses["success"]
    success_stdout = json.dumps(success["stdout"]).encode()
    result = client(
        RecordingRunner([CommandResult(success["returncode"], success_stdout)])
    ).helper_call(
        {
            "object": "uci",
            "method": "rollback",
            "arguments": {"ubus_rpc_session": "fixture-sid"},
        }
    )
    assert result == {"ok": True}

    for name in ("timeout", "wrong_sid", "no_data", "ambiguous_ssh_termination"):
        response = responses[name]
        stdout = response["stdout"]
        encoded = json.dumps(stdout).encode() if stdout is not None else b""
        with pytest.raises(OperationalError) as error:
            client(RecordingRunner([CommandResult(response["returncode"], encoded)])).helper_call(
                {
                    "object": "uci",
                    "method": "rollback",
                    "arguments": {"ubus_rpc_session": "fixture-sid"},
                }
            )
        assert "fixture-sid" not in str(error.value)
        assert "error_code" not in str(error.value)


def test_helper_exposes_only_bounded_numeric_rejection_code() -> None:
    runner = RecordingRunner([CommandResult(1, b'{"ok":false,"error":22}')])

    with pytest.raises(
        OperationalError, match=r"uci.apply failed with exit 1 \(code 22\)"
    ) as error:
        client(runner).helper_call(
            {
                "object": "uci",
                "method": "apply",
                "arguments": {"password": FAKE_SECRET},
            }
        )

    assert FAKE_SECRET not in str(error.value)


class LiveReadRunner(RecordingRunner):
    def __init__(self, *, listener_output: bytes = b"") -> None:
        super().__init__()
        self.listener_output = listener_output

    def __call__(
        self, argv: list[str] | tuple[str, ...], *, input_data: bytes | None, timeout: float
    ) -> CommandResult:
        del timeout
        command = tuple(argv[tuple(argv).index("--") + 1 :])
        self.calls.append((tuple(argv), input_data))
        if command == ("ubus", "call", "system", "board"):
            return CommandResult(
                0,
                json.dumps(
                    {
                        "board_name": "cudy,wr3000e-v1",
                        "model": "Cudy WR3000E v1",
                        "release": {"version": "25.12.5", "target": "mediatek/filogic"},
                    }
                ).encode(),
            )
        if command == ("apk", "info"):
            return CommandResult(0, ("\n".join(sorted(REQUIRED_PACKAGES)) + "\n").encode())
        if command == ("/usr/libexec/homeserver-uci",):
            return CommandResult(
                0,
                json.dumps(
                    {
                        "ok": True,
                        "values": {
                            "firewall.rogue._type": "redirect",
                            "wireless.radio0.band": "2g",
                            "wireless.radio1.band": "5g",
                        },
                    }
                ).encode(),
            )
        if command in {
            ("ifstatus", "wan"),
            ("ifstatus", "wan6"),
            ("ubus", "call", "network.wireless", "status"),
        }:
            return CommandResult(0, b"{}")
        if command == ("tc", "-s", "qdisc", "show"):
            return CommandResult(0, b"")
        if command == ("netstat", "-lntp"):
            return CommandResult(0, self.listener_output)
        return CommandResult(0)


def test_live_reader_collects_filtered_surface_and_detects_rogue_redirect() -> None:
    runner = LiveReadRunner(
        listener_output=(b"tcp 0 0 192.168.1.1:443 0.0.0.0:* LISTEN 7404/uhttpd\n")
    )
    state = read_live_state(client(runner))
    assert state["identity"]["board_ids"] == ["R53"]
    assert set(state["packages"]) == REQUIRED_PACKAGES
    assert state["firewall"]["redirects"] == ["firewall.rogue"]
    commands = [call[0][call[0].index("--") + 1 :] for call in runner.calls]
    assert ("ifstatus", "wan") not in commands
    assert ("ifstatus", "wan6") not in commands
    assert state["listeners"] == []
    with pytest.raises(OpenWrtSafetyError, match="redirects"):
        plan_openwrt(DESIRED, state)


def test_live_reader_detects_only_local_wildcard_management_sockets() -> None:
    state = read_live_state(
        client(
            LiveReadRunner(
                listener_output=(b"tcp 0 0 " + b"0.0.0.0:443" + b" 0.0.0.0:* LISTEN 7404/uhttpd\n")
            )
        )
    )

    assert state["listeners"] == [{"network": "wan", "service": "uhttpd"}]


def test_unexpected_vlan_and_ssh_password_auth_fail_closed() -> None:
    raw = fixture("converged.json")
    raw["uci"] = {
        "network.rogue._type": "device",
        "network.rogue.type": "8021q",
        "network.rogue.vid": "7",
        "network.rogue.ifname": "lan1",
        "dropbear.dropbear.PasswordAuth": "on",
    }
    with pytest.raises(OpenWrtSafetyError, match="unexpected WAN VLAN"):
        plan_openwrt(DESIRED, raw)


def test_wan_zone_and_unrestricted_tcp_management_are_detected() -> None:
    raw = fixture("converged.json")
    raw["uci"] = {
        "firewall.cfg_zone._type": "zone",
        "firewall.cfg_zone.name": "wan",
        "firewall.cfg_zone.input": "ACCEPT",
        "firewall.cfg_rule._type": "rule",
        "firewall.cfg_rule.src": "wan",
        "firewall.cfg_rule.proto": "tcp",
        "firewall.cfg_rule.target": "ACCEPT",
    }
    raw["firewall"]["wan_management"] = True
    with pytest.raises(OpenWrtSafetyError, match="WAN management"):
        plan_openwrt(DESIRED, raw)


def test_stage_policy_runs_enabled_health_closure_and_extends_timeout() -> None:
    rollback, lifetime, health = effective_stage_policy(
        "base", {"network"}, {"base", "wan", "guest", "ipv6", "sqm"}
    )
    assert rollback == 300
    assert lifetime == 600
    assert health == ("base", "wan", "guest", "ipv6", "sqm")


def test_stage_policy_requires_dependencies() -> None:
    with pytest.raises(OpenWrtSafetyError, match="dependencies"):
        effective_stage_policy("guest", {"wireless"}, {"base", "wan"})


def test_revert_health_closure_excludes_newly_enabled_forward_stage() -> None:
    assert required_revert_health_stages({"network", "firewall"}, {"base"}) == ("base",)


def test_local_apply_lock_fails_closed_on_contention(tmp_path: Path) -> None:
    lock = tmp_path / "apply.lock"
    with (
        local_apply_lock(lock),
        pytest.raises(LockContentionError, match="controller lock"),
        local_apply_lock(lock),
    ):
        pytest.fail("contended lock must not be entered")


class ApplyRunner(RecordingRunner):
    def __init__(
        self,
        *,
        ambiguous_apply: bool = False,
        stale_lock: bool = False,
        mismatches: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.ambiguous_apply = ambiguous_apply
        self.stale_lock = stale_lock
        self.mismatches = mismatches
        self.apply_count = 0
        self.lock_count = 0

    def __call__(
        self, argv: list[str] | tuple[str, ...], *, input_data: bytes | None, timeout: float
    ) -> CommandResult:
        self.calls.append((tuple(argv), input_data))
        request = json.loads(input_data or b"{}")
        method = request.get("method")
        if method == "lock-acquire":
            self.lock_count += 1
            if self.stale_lock and self.lock_count == 1:
                return CommandResult(0, b'{"ok":true,"acquired":false}')
            return CommandResult(0, b'{"ok":true,"acquired":true}')
        if method == "lock-clear-stale":
            return CommandResult(0, b'{"ok":true,"cleared":true}')
        if method == "create":
            return CommandResult(0, b'{"ok":true,"sid":"fixture-sid"}')
        if method == "add":
            return CommandResult(0, b'{"ok":true,"section":"cfg99"}')
        if method == "compare":
            if self.mismatches is not None:
                return CommandResult(
                    0,
                    json.dumps(
                        {"ok": True, "match": False, "mismatches": self.mismatches}
                    ).encode(),
                )
            return CommandResult(0, b'{"ok":true,"match":true}')
        if method == "apply":
            self.apply_count += 1
            if self.ambiguous_apply:
                return CommandResult(255)
        return CommandResult(0, b'{"ok":true}')


def test_apply_uses_same_sid_exact_acl_health_then_confirm(tmp_path: Path) -> None:
    runner = ApplyRunner()
    health: list[str] = []
    backups: list[str] = []
    result = apply_stage(
        client=client(runner),
        stage="wan",
        packages={"network", "firewall"},
        mutations=[{"method": "set", "arguments": {"config": "network", "section": "wan"}}],
        expected_projection={"network.wan.proto": "pppoe"},
        enabled_stages={"base", "wan"},
        health_check=health.append,
        backup_before_apply=backups.append,
        lock_path=tmp_path / "apply.lock",
        controller_id="fixture-controller",
    )
    requests = [json.loads(data or b"{}") for _, data in runner.calls]
    assert [item["method"] for item in requests] == [
        "lock-acquire",
        "create",
        "grant",
        "set",
        "compare",
        "apply",
        "confirm",
        "destroy",
        "lock-release",
    ]
    assert requests[2]["arguments"]["objects"] == ["firewall", "network"]
    assert {item["arguments"].get("ubus_rpc_session") for item in requests[2:8]} == {"fixture-sid"}
    assert result.sid == "fixture-sid"
    assert health == ["base", "wan"]
    assert backups == ["wan"]


def test_apply_remaps_anonymous_restore_order_and_staged_projection(tmp_path: Path) -> None:
    runner = ApplyRunner()
    apply_stage(
        client=client(runner),
        stage="wan",
        packages={"firewall"},
        mutations=[
            {
                "method": "add",
                "arguments": {
                    "config": "firewall",
                    "type": "rule",
                    "values": {"name": "Allow-IPSec-ESP"},
                },
                "capture_section_as": "firewall.cfg02",
            },
            {
                "method": "order",
                "arguments": {
                    "config": "firewall",
                    "sections": ["defaults", "cfg02", "forwarding"],
                },
            },
        ],
        expected_projection={
            "firewall.cfg02._anonymous": True,
            "firewall.cfg02._index": 1,
            "firewall.cfg02._name": "cfg02",
            "firewall.cfg02._type": "rule",
            "firewall.cfg02.name": "Allow-IPSec-ESP",
        },
        enabled_stages={"base", "wan"},
        health_check=lambda _: None,
        backup_before_apply=lambda _: None,
        lock_path=tmp_path / "apply.lock",
        controller_id="fixture-controller",
    )

    requests = [json.loads(data or b"{}") for _, data in runner.calls]
    order = next(request for request in requests if request.get("method") == "order")
    compare = next(request for request in requests if request.get("method") == "compare")
    assert order["arguments"]["sections"] == ["defaults", "cfg99", "forwarding"]
    assert compare["arguments"]["expected"] == {
        "firewall.cfg99._anonymous": True,
        "firewall.cfg99._index": 1,
        "firewall.cfg99._name": "cfg99",
        "firewall.cfg99._type": "rule",
        "firewall.cfg99.name": "Allow-IPSec-ESP",
    }


def test_ambiguous_apply_is_never_retried_or_confirmed(tmp_path: Path) -> None:
    runner = ApplyRunner(ambiguous_apply=True)
    with pytest.raises(ApplyAmbiguousError, match="not retried"):
        apply_stage(
            client=client(runner),
            stage="sqm",
            packages={"sqm"},
            mutations=[],
            expected_projection={},
            enabled_stages={"base", "wan", "sqm"},
            health_check=lambda _: None,
            backup_before_apply=lambda _: None,
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )
    methods = [json.loads(data or b"{}").get("method") for _, data in runner.calls]
    assert runner.apply_count == 1
    assert "confirm" not in methods
    assert "lock-release" not in methods


def test_staged_mismatch_reports_only_bounded_paths(tmp_path: Path) -> None:
    runner = ApplyRunner(
        mismatches=["network.lan.ipaddr", "network.wan.password", "unsafe path=value"]
    )

    with pytest.raises(OpenWrtSafetyError) as error:
        apply_stage(
            client=client(runner),
            stage="base",
            packages={"network"},
            mutations=[],
            expected_projection={"network.lan.ipaddr": ["192.168.1.1/24"]},
            enabled_stages={"base"},
            health_check=lambda _: None,
            backup_before_apply=lambda _: None,
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )

    message = str(error.value)
    assert "base staged projection mismatch" in message
    assert "network.lan.ipaddr" in message
    assert "network.wan.password" in message
    assert "unsafe path=value" not in message


def test_expired_remote_lock_is_cleared_once_then_reacquired(tmp_path: Path) -> None:
    runner = ApplyRunner(stale_lock=True)
    apply_stage(
        client=client(runner),
        stage="base",
        packages={"system"},
        mutations=[],
        expected_projection={},
        enabled_stages={"base"},
        health_check=lambda _: None,
        backup_before_apply=lambda _: None,
        lock_path=tmp_path / "apply.lock",
        controller_id="fixture-controller",
    )
    methods = [json.loads(data or b"{}").get("method") for _, data in runner.calls]
    assert methods[:3] == ["lock-acquire", "lock-clear-stale", "lock-acquire"]


def test_failed_health_check_rolls_back_same_sid_without_confirm(tmp_path: Path) -> None:
    runner = ApplyRunner()

    with pytest.raises(RuntimeError, match="health failed"):
        apply_stage(
            client=client(runner),
            stage="wan",
            packages={"network"},
            mutations=[],
            expected_projection={},
            enabled_stages={"base", "wan"},
            health_check=lambda _: (_ for _ in ()).throw(RuntimeError("health failed")),
            backup_before_apply=lambda _: None,
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )
    requests = [json.loads(data or b"{}") for _, data in runner.calls]
    methods = [request.get("method") for request in requests]
    assert "confirm" not in methods
    assert methods[-3:] == ["rollback", "destroy", "lock-release"]
    assert requests[-3]["arguments"]["ubus_rpc_session"] == "fixture-sid"


def test_health_gate_polls_until_procd_config_triggers_converge(tmp_path: Path) -> None:
    runner = ApplyRunner()
    checks = 0

    def health(_: str) -> None:
        nonlocal checks
        checks += 1
        if checks == 1:
            raise OpenWrtSafetyError("management listener is exposed outside trusted LAN")

    result = apply_stage(
        client=client(runner),
        stage="base",
        packages={"dropbear", "uhttpd"},
        mutations=[],
        expected_projection={},
        enabled_stages={"base"},
        health_check=health,
        backup_before_apply=lambda _: None,
        lock_path=tmp_path / "apply.lock",
        controller_id="fixture-controller",
        health_poll_interval=0.001,
    )

    assert result.stage == "base"
    assert checks == 2
    methods = [json.loads(data or b"{}").get("method") for _, data in runner.calls]
    assert "confirm" in methods
    assert "rollback" not in methods


def test_bootstrap_sanitize_timeout_rolls_back_without_confirm(tmp_path: Path) -> None:
    runner = ApplyRunner()

    with pytest.raises(TimeoutError, match="bootstrap check timed out"):
        apply_stage(
            client=client(runner),
            stage="bootstrap-sanitize",
            packages={"network"},
            mutations=[],
            expected_projection={},
            enabled_stages=set(),
            health_check=lambda _: (_ for _ in ()).throw(TimeoutError("bootstrap check timed out")),
            backup_before_apply=lambda _: None,
            lock_path=tmp_path / "apply.lock",
            controller_id="fixture-controller",
        )
    methods = [json.loads(data or b"{}").get("method") for _, data in runner.calls]
    assert "confirm" not in methods
    assert methods[-3:] == ["rollback", "destroy", "lock-release"]


class FakeEncryptor:
    def encrypt(self, chunks: object, destination: BinaryIO) -> None:
        destination.write(b"AGE")
        for chunk in chunks:  # type: ignore[union-attr]
            destination.write(bytes(value ^ 0x55 for value in chunk))


class FakeDecryptor:
    def decrypt(self, chunks: object, destination: BinaryIO) -> None:
        encrypted = b"".join(chunks)  # type: ignore[arg-type]
        assert encrypted.startswith(b"AGE")
        destination.write(bytes(value ^ 0x55 for value in encrypted[3:]))


def test_backup_streams_to_encryptor_without_plaintext_file(tmp_path: Path) -> None:
    destination = tmp_path / "config.tar.age"
    plaintext = [b"fake-config-", b"archive"]
    with destination.open("wb") as output:
        metadata = stream_encrypted_backup(plaintext, FakeEncryptor(), output)
    assert metadata.plaintext_size == len(b"fake-config-archive")
    assert metadata.plaintext_sha256 == hashlib.sha256(b"fake-config-archive").hexdigest()
    assert destination.read_bytes().startswith(b"AGE")
    assert list(tmp_path.iterdir()) == [destination]


def test_transaction_bundle_keeps_authoritative_state_inside_ciphertext(tmp_path: Path) -> None:
    bundle = tmp_path / "transaction.age"
    index_path = tmp_path / "transaction.json"
    payload = {
        "transaction_id": "tx_fixture_001",
        "stage": "wan",
        "timestamp": "2026-07-16T12:00:00Z",
        "pre_projection": {"network.wan.password": FAKE_SECRET},
        "expected_post_projection": {"network.wan.password": "replacement-secret"},
        "owned_paths": ["network.wan.password"],
        "created_sections": [],
        "deleted_sections": [],
        "enabled_stages": ["base", "wan"],
        "parent_transaction_id": "tx_fixture_000",
    }

    index = write_transaction_bundle(
        payload=payload,
        encryptor=FakeEncryptor(),
        bundle_path=bundle,
        index_path=index_path,
    )

    public_index = index_path.read_text()
    assert index.ciphertext_sha256 == hashlib.sha256(bundle.read_bytes()).hexdigest()
    assert FAKE_SECRET not in public_index
    assert "network.wan.password" not in public_index
    assert set(path.name for path in tmp_path.iterdir()) == {bundle.name, index_path.name}

    restored = read_transaction_bundle(index_path=index_path, decryptor=FakeDecryptor())
    assert restored == payload
    validate_revert_bundle(
        restored,
        current_projection=payload["expected_post_projection"],
        current_parent_transaction_id="tx_fixture_000",
    )


def test_transaction_revert_rejects_tamper_stale_state_and_lineage(tmp_path: Path) -> None:
    bundle = tmp_path / "transaction.age"
    index_path = tmp_path / "transaction.json"
    payload = {
        "transaction_id": "tx_fixture_002",
        "stage": "sqm",
        "timestamp": "2026-07-16T12:01:00Z",
        "pre_projection": {"sqm.wan.download": "80000"},
        "expected_post_projection": {"sqm.wan.download": "87890"},
        "parent_transaction_id": "tx_fixture_001",
    }
    write_transaction_bundle(
        payload=payload,
        encryptor=FakeEncryptor(),
        bundle_path=bundle,
        index_path=index_path,
    )
    restored = read_transaction_bundle(index_path=index_path, decryptor=FakeDecryptor())
    with pytest.raises(OpenWrtSafetyError, match="stale"):
        validate_revert_bundle(
            restored,
            current_projection={"sqm.wan.download": "90000"},
            current_parent_transaction_id="tx_fixture_001",
        )
    with pytest.raises(OpenWrtSafetyError, match="lineage"):
        validate_revert_bundle(
            restored,
            current_projection=payload["expected_post_projection"],
            current_parent_transaction_id="tx_fixture_later",
        )

    bundle.write_bytes(bundle.read_bytes() + b"tampered")
    with pytest.raises(OpenWrtSafetyError, match="integrity"):
        read_transaction_bundle(index_path=index_path, decryptor=FakeDecryptor())


def test_overlay_and_offline_firmware_manifest_verification(tmp_path: Path) -> None:
    public_key = tmp_path / "id.pub"
    helper = tmp_path / "helper"
    artifact = tmp_path / f"openwrt-{VERSION}-mediatek-filogic-{PROFILE}-squashfs-sysupgrade.bin"
    public_key.write_text("ssh-ed25519 QUJD fake@example\n")
    helper.write_text("#!/usr/bin/ucode\nlet request = readfile('/dev/stdin');\n")
    embedded = {
        "supported_devices": [BOARD, BOARD_ID],
        "version": {"version": VERSION, "target": TARGET},
    }
    archive_bytes = io.BytesIO()
    root = f"sysupgrade-{PROFILE}"
    with tarfile.open(fileobj=archive_bytes, mode="w") as archive:
        directory = tarfile.TarInfo(root)
        directory.type = tarfile.DIRTYPE
        archive.addfile(directory)
        for name, content in (
            ("CONTROL", f"BOARD={PROFILE}\n".encode()),
            ("kernel", b"\xd0\r\xfe\xedfixture-fit"),
            ("root", b"hsqsfixture-root"),
        ):
            member = tarfile.TarInfo(f"{root}/{name}")
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    payload = b"\0" * 8 + json.dumps(embedded, separators=(",", ":")).encode()
    body = archive_bytes.getvalue() + payload
    trailer = struct.pack(
        ">IIB3xI",
        0x46577830,
        (zlib.crc32(body) ^ 0xFFFFFFFF) & 0xFFFFFFFF,
        1,
        len(payload) + 16,
    )
    artifact.write_bytes(body + trailer)
    overlay = create_overlay(public_key, helper, tmp_path / "overlay")
    manifest = {
        "artifact": artifact.name,
        "artifact_size": artifact.stat().st_size,
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "version": VERSION,
        "target": TARGET,
        "profile": PROFILE,
        "model": MODEL,
        "board": BOARD,
        "board_id": BOARD_ID,
        "imagebuilder_sha256": IMAGEBUILDER_SHA256,
        "builder_image": BUILDER_IMAGE,
        "requested_packages": list(REQUESTED_PACKAGES),
        "resolved_packages": {name: "fixture-version" for name in REQUIRED_PACKAGES},
        "feed_indexes": {"packages": "0" * 64},
        "overlay": overlay,
        "embedded_metadata": embedded,
    }
    verify_manifest(manifest, artifact, helper=helper, public_key=public_key)
    manifest["resolved_packages"]["miniupnpd"] = "fixture-version"
    with pytest.raises(FirmwareVerificationError, match="package policy"):
        verify_manifest(manifest, artifact, helper=helper, public_key=public_key)


def test_forbidden_firmware_layout_is_rejected(tmp_path: Path) -> None:
    artifact = tmp_path / f"openwrt-{VERSION}-{PROFILE}-ubootmod-squashfs-sysupgrade.bin"
    artifact.write_bytes(b"never-flash")
    with pytest.raises(FirmwareVerificationError, match="stock-layout"):
        verify_manifest({}, artifact, helper=artifact, public_key=artifact)


def test_official_checksum_parser_is_exact_and_path_safe() -> None:
    assert parse_sha256sums(f"{'0' * 64} *profiles.json\n{'1' * 64} *kmods/index.json\n") == {
        "profiles.json": "0" * 64,
        "kmods/index.json": "1" * 64,
    }
    with pytest.raises(FirmwareVerificationError, match="unsafe duplicate"):
        parse_sha256sums(f"{'0' * 64} *../profiles.json\n")
    with pytest.raises(FirmwareVerificationError, match="unsafe duplicate"):
        parse_sha256sums(f"{'0' * 64} *profiles.json\n{'1' * 64} *profiles.json\n")


def test_overlay_must_be_fresh(tmp_path: Path) -> None:
    public_key = tmp_path / "id.pub"
    helper = tmp_path / "helper"
    overlay = tmp_path / "overlay"
    public_key.write_text("ssh-ed25519 QUJD fake@example\n")
    helper.write_text("#!/usr/bin/ucode\nlet request = readfile('/dev/stdin');\n")
    overlay.mkdir()
    with pytest.raises(FirmwareVerificationError, match="must be new"):
        create_overlay(public_key, helper, overlay)


def test_tracked_helper_is_stdin_only_default_deny_and_has_no_shell_path() -> None:
    helper = (
        Path(__file__).parents[1] / "network/openwrt/files/usr/libexec/homeserver-uci"
    ).read_text()
    assert "'/dev/stdin'" in helper
    assert "withheld: true" in helper
    assert "const SENSITIVE" in helper
    assert "ubus.call" in helper
    assert "'rollback'" in helper
    assert "root-password-status" in helper
    assert "password_set" in helper
    assert "[]A-Za-z0-9_@[-]+" in helper
    assert r"^system\.[]A-Za-z0-9_@[-]+" in helper
    assert r"[A-Za-z0-9_@\[\]-]+" not in helper
    assert "[ config, 'read' ]" in helper
    assert "[ config, 'write' ]" in helper
    assert "[ 'uci', config ]" not in helper
    assert "equal_uci_value(actual, wanted)" in helper
    assert "valid_expected_value(path, wanted)" in helper
    assert "output.section = response.section" in helper
    assert "metadata = '.anonymous'" in helper
    assert "const UBUS_STATUS_NOT_FOUND = 4" in helper
    assert "error == UBUS_STATUS_NOT_FOUND" in helper
    assert "checked_ubus_call(ubus, 'uci', 'get', query, true)" in helper
    assert "/bin/sh" not in helper
    assert "system(" not in helper
    assert "popen(" not in helper
