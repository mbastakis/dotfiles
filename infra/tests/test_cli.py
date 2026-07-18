from pathlib import Path
from types import SimpleNamespace

import pytest

from homeserver_iac import cli
from homeserver_iac.models.common import ExitCode
from homeserver_iac.openwrt_operations import CiphertextMetadata
from homeserver_iac.runtime import OperationalError

OPENWRT_FIXTURES = Path("infra/tests/fixtures/openwrt")


def test_exit_code_contract_is_stable() -> None:
    assert ExitCode.VALID == 0
    assert ExitCode.DRIFT == 2
    assert ExitCode.VALIDATION_FAILURE == 3
    assert ExitCode.OPERATIONAL_FAILURE == 4


def test_cli_returns_validation_failure_for_unregistered_contract(capsys: object) -> None:
    result = cli.main(["desired", "validate", str(Path("unknown.yaml"))])

    assert result == ExitCode.VALIDATION_FAILURE


def test_cli_returns_operational_failure_for_io_error(monkeypatch: object) -> None:
    def fail(*, check: bool) -> list[Path]:
        raise OSError("fixture failure")

    monkeypatch.setattr(cli, "generate_schemas", fail)

    assert cli.main(["schema", "check"]) == ExitCode.OPERATIONAL_FAILURE


def test_photos_validator_accepts_checkpoint_and_workers() -> None:
    args = cli.parser().parse_args(
        [
            "photos",
            "validate-export",
            "/tmp/export",
            "--checkpoint",
            "/tmp/validation.db",
            "--workers",
            "4",
            "--ffmpeg-hwaccel",
            "videotoolbox",
        ]
    )

    assert args.checkpoint == Path("/tmp/validation.db")
    assert args.workers == 4
    assert args.ffmpeg_hwaccel == "videotoolbox"


def test_openwrt_parser_enforces_mutating_command_contract() -> None:
    args = cli.parser().parse_args(["openwrt", "apply", "--stage", "wan"])
    assert args.stage == "wan"
    assert not hasattr(args, "proxy_jump")
    clean = cli.parser().parse_args(
        [
            "openwrt",
            "clean-rebuild",
            "--image",
            "firmware.bin",
            "--confirm",
            "CLEAN-REBUILD",
        ]
    )
    assert clean.confirm == "CLEAN-REBUILD"
    assert not hasattr(clean, "proxy_jump")


def test_openwrt_plan_accepts_read_only_proxy_and_fixture() -> None:
    args = cli.parser().parse_args(
        ["openwrt", "plan", "--proxy-jump", "atlas", "--state-fixture", "state.json"]
    )
    assert args.proxy_jump == "atlas"
    assert args.state_fixture == Path("state.json")


def test_openwrt_firmware_commands_have_local_bundle_defaults() -> None:
    build = cli.parser().parse_args(["openwrt", "firmware", "build"])
    verify = cli.parser().parse_args(["openwrt", "firmware", "verify"])
    assert build.work_dir.name == "openwrt"
    assert build.archive_to is None
    assert verify.bundle.parts[-2:] == ("25.12.5", "homeserver")


def test_openwrt_fixture_plan_dispatches_without_live_clients(monkeypatch: object) -> None:
    def fail_live(*args: object, **kwargs: object) -> object:
        raise AssertionError("fixture plan must not construct or use live clients")

    monkeypatch.setattr(cli, "read_live_state", fail_live)
    monkeypatch.setattr(cli, "OpenWrtSshClient", fail_live)
    monkeypatch.setattr(cli, "ChezmoiCrypto", fail_live)
    fixture = OPENWRT_FIXTURES / "converged.json"
    assert cli.main(["openwrt", "plan", "--state-fixture", str(fixture), "--stage", "base"]) == 0


def test_openwrt_fixture_plan_exit_codes() -> None:
    assert (
        cli.main(["openwrt", "plan", "--state-fixture", str(OPENWRT_FIXTURES / "drift.json")])
        == ExitCode.DRIFT
    )
    for name in ("rogue-forward.json", "wrong-board.json", "wrong-packages.json"):
        assert (
            cli.main(["openwrt", "plan", "--state-fixture", str(OPENWRT_FIXTURES / name)])
            == ExitCode.VALIDATION_FAILURE
        )


def test_openwrt_fixture_task_bypasses_bws_wrapper() -> None:
    taskfile = Path("infra/network/Taskfile.yml").read_text()
    plan_task = taskfile.split("  openwrt:plan:", 1)[1].split("\n  openwrt:apply:", 1)[0]
    assert 'contains "--state-fixture"' in plan_task
    fixture_branch = plan_task.split("{{else}}", 1)[0]
    assert "infra/secrets/homeserver-secrets" not in fixture_branch
    assert '[ "$protected_status" -ne 0 ] && [ "$protected_status" -ne 2 ]' in plan_task
    assert 'exit "$protected_status"' in plan_task


def test_openwrt_upgrade_and_validation_tasks_are_self_contained() -> None:
    taskfile = Path("infra/network/Taskfile.yml").read_text()
    validate_task = taskfile.split("  openwrt:validate:", 1)[1].split("\n  openwrt:bootstrap:", 1)[
        0
    ]
    upgrade_task = taskfile.split("  openwrt:upgrade:", 1)[1].split(
        "\n  openwrt:clean-rebuild:", 1
    )[0]
    aggregate = Path("infra/Taskfile.yml").read_text().split("  validate:", 1)[1]

    assert "deps: [openwrt:ansible:sync]" in validate_task
    assert "infra/secrets/homeserver-secrets exec openwrt-router --" in upgrade_task
    assert 'task: ":network:openwrt:validate"' in aggregate


def test_openwrt_ansible_contract_matches_hostapd_secret_constraints() -> None:
    contract = Path("infra/ansible/roles/openwrt_contract/tasks/main.yml").read_text()

    assert ".main_ssid.encode('utf-8') | length" in contract
    assert "^[^\\x00\\r\\n]+$" in contract
    assert "^[ -~]{8,63}$" in contract
    assert "^[0-9A-Fa-f]{64}$" in contract


def test_opencode_remote_secrets_are_inside_designated_host_template_guards() -> None:
    notifier = Path("private_dot_config/opencode/private_clickable-notifier.json.tmpl").read_text()
    notifier_guard = notifier.split("{{- if eq .chezmoi.hostname .opencode.remote.host }}", 1)[
        1
    ].split("{{- end }}", 1)[0]
    assert "bitwardenSecrets .opencode.remote.ntfy_token_id" in notifier_guard

    reload_script = Path(
        ".chezmoiscripts/run_onchange_after_10-opencode-remote.sh.tmpl"
    ).read_text()
    secret_guard = reload_script.split(
        '{{- if and (eq .chezmoi.os "darwin") (eq .chezmoi.hostname .opencode.remote.host) }}',
        1,
    )[1].split("{{- end }}", 1)[0]
    assert secret_guard.count("bitwardenSecrets") == 3


def test_openwrt_apply_and_revert_dispatch_to_controller(monkeypatch: object) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        cli,
        "apply_openwrt_stage",
        lambda **kwargs: (
            calls.append(str(kwargs["stage"]))
            or SimpleNamespace(apply=SimpleNamespace(stage=kwargs["stage"]))
        ),
    )
    monkeypatch.setattr(
        cli,
        "revert_openwrt_transaction",
        lambda **kwargs: (
            calls.append(str(kwargs["transaction_id"])) or SimpleNamespace(stage="wan")
        ),
    )
    assert cli.main(["openwrt", "apply", "--stage", "wan"]) == 0
    assert cli.main(["openwrt", "apply", "--revert", "tx_fixture_001"]) == 0
    assert calls == ["wan", "tx_fixture_001"]


def test_openwrt_bootstrap_dispatches_two_stages_and_password_gate(
    monkeypatch: object,
) -> None:
    calls: list[str] = []
    monkeypatch.setenv("OPENWRT_ROOT_PASSWORD", "fixture-password")
    monkeypatch.setattr(cli, "input", lambda: "yes", raising=False)
    monkeypatch.setattr(cli, "scan_and_pin_host_key", lambda **kwargs: calls.append("pin"))
    monkeypatch.setattr(cli, "read_live_state", lambda client: {})
    monkeypatch.setattr(cli, "validate_safety", lambda desired, current, **kwargs: None)
    monkeypatch.setattr(
        cli, "_openwrt_journal", lambda crypto: SimpleNamespace(latest=lambda stage: None)
    )
    monkeypatch.setattr(
        cli,
        "apply_openwrt_stage",
        lambda **kwargs: calls.append(str(kwargs["stage"])) or SimpleNamespace(),
    )
    monkeypatch.setattr(cli, "rotate_root_password", lambda **kwargs: calls.append("password"))
    monkeypatch.setattr(cli, "verify_luci_https_login", lambda **kwargs: calls.append("luci"))
    assert cli.main(["openwrt", "bootstrap"]) == 0
    assert calls == ["pin", "bootstrap-sanitize", "base", "password", "luci"]


def test_openwrt_bootstrap_resumes_base_after_accepted_sanitize(monkeypatch: object) -> None:
    calls: list[str] = []
    monkeypatch.setenv("OPENWRT_ROOT_PASSWORD", "fixture-password")
    monkeypatch.setattr(cli, "input", lambda: "yes", raising=False)
    monkeypatch.setattr(cli, "scan_and_pin_host_key", lambda **kwargs: calls.append("pin"))
    monkeypatch.setattr(cli, "read_live_state", lambda client: {})
    monkeypatch.setattr(cli, "validate_safety", lambda desired, current, **kwargs: None)
    monkeypatch.setattr(
        cli,
        "_openwrt_journal",
        lambda crypto: SimpleNamespace(
            latest=lambda stage: SimpleNamespace() if stage == "bootstrap-sanitize" else None
        ),
    )
    monkeypatch.setattr(
        cli,
        "apply_openwrt_stage",
        lambda **kwargs: calls.append(str(kwargs["stage"])) or SimpleNamespace(),
    )
    monkeypatch.setattr(cli, "rotate_root_password", lambda **kwargs: calls.append("password"))
    monkeypatch.setattr(cli, "verify_luci_https_login", lambda **kwargs: calls.append("luci"))

    assert cli.main(["openwrt", "bootstrap"]) == 0
    assert calls == ["pin", "base", "password", "luci"]


def test_openwrt_bootstrap_supports_trust_and_rollback_only_modes(monkeypatch: object) -> None:
    calls: list[str] = []
    monkeypatch.setattr(cli, "input", lambda: "yes", raising=False)
    monkeypatch.setattr(cli, "scan_and_pin_host_key", lambda **kwargs: calls.append("pin"))
    monkeypatch.setattr(cli, "read_live_state", lambda client: {})
    monkeypatch.setattr(
        cli, "validate_safety", lambda desired, current, **kwargs: calls.append("safe")
    )
    monkeypatch.setattr(
        cli,
        "prove_timed_rollback",
        lambda *args, **kwargs: calls.append("rollback") or 10.0,
    )
    monkeypatch.setattr(
        cli,
        "recover_pending_bootstrap_sanitize",
        lambda **kwargs: (
            calls.append("recover") or SimpleNamespace(transaction_id="tx_fixture_recovered")
        ),
    )
    monkeypatch.setattr(
        cli,
        "recover_pending_base",
        lambda **kwargs: (
            calls.append("recover-base") or SimpleNamespace(transaction_id="tx_fixture_base")
        ),
    )

    assert cli.main(["openwrt", "bootstrap", "--pin-host-key-only"]) == 0
    assert cli.main(["openwrt", "bootstrap", "--test-rollback-only"]) == 0
    assert cli.main(["openwrt", "bootstrap", "--recover-pending-sanitize-only"]) == 0
    assert cli.main(["openwrt", "bootstrap", "--recover-pending-base-only"]) == 0
    assert calls == [
        "pin",
        "safe",
        "pin",
        "safe",
        "rollback",
        "pin",
        "safe",
        "recover",
        "pin",
        "safe",
        "recover-base",
    ]


def test_openwrt_clean_image_inspection_is_redacted_and_skips_safety_gate(
    monkeypatch: object, capsys: object
) -> None:
    monkeypatch.setattr(cli, "input", lambda: "yes", raising=False)
    monkeypatch.setattr(cli, "scan_and_pin_host_key", lambda **kwargs: None)
    monkeypatch.setattr(
        cli,
        "read_live_state",
        lambda client: {
            "identity": {"board_name": "cudy,wr3000e-v1"},
            "firewall": {"wan_management": False},
            "listeners": [{"network": "wan", "service": "uhttpd"}],
            "runtime": {"radio_bands": []},
            "uci": {
                "wireless.radio0._type": "wifi-device",
                "wireless.radio0.channel": "auto",
                "wireless.radio0.key": {"present": True},
                "uhttpd.main.listen_https": ["0.0.0.0:443"],
            },
        },
    )
    monkeypatch.setattr(
        cli,
        "validate_safety",
        lambda desired, current: (_ for _ in ()).throw(AssertionError("must not validate")),
    )

    assert cli.main(["openwrt", "bootstrap", "--inspect-clean-image-only"]) == 0
    output = capsys.readouterr().out  # type: ignore[attr-defined]
    assert "wireless.radio0.channel" in output
    assert "uhttpd.main.listen_https" in output
    assert "wireless.radio0.key" not in output


def test_openwrt_status_and_backup_dispatch_with_fake_state(
    monkeypatch: object, tmp_path: Path
) -> None:
    state = {
        "identity": {
            "board_ids": ["R53"],
            "board_name": "cudy,wr3000e-v1",
            "model": "Cudy WR3000E v1",
            "profile": "cudy_wr3000e-v1",
            "release": "25.12.5",
            "target": "mediatek/filogic",
        },
        "packages": list(cli.REQUIRED_PACKAGES) if hasattr(cli, "REQUIRED_PACKAGES") else [],
        "resources": {},
        "firewall": {"redirects": [], "includes": [], "dmz": False, "wan_management": False},
        "listeners": [],
        "services": {},
        "runtime": {},
        "uci": {},
    }
    monkeypatch.setattr(cli, "read_live_state", lambda client: state)
    monkeypatch.setattr(cli, "validate_safety", lambda desired, current: None)
    monkeypatch.setattr(cli, "status_summary", lambda current: {"stages": {}})
    metadata = CiphertextMetadata("config.age", 1, "0" * 64, 2, "1" * 64)
    monkeypatch.setattr(cli, "backup_config", lambda **kwargs: metadata)
    monkeypatch.setattr(cli, "verify_encrypted_backup", lambda **kwargs: None)
    monkeypatch.setattr(cli, "write_backup_manifest", lambda **kwargs: None)
    assert cli.main(["openwrt", "status"]) == 0
    state["runtime"] = {"wan": {"up": True}, "wan6": {"up": False}}
    assert cli.main(["openwrt", "status", "--expect-wan-down"]) == 3
    state["runtime"] = {}
    assert cli.main(["openwrt", "backup", "--kind", "config", "--output-dir", str(tmp_path)]) == 0


def test_openwrt_upgrade_requires_verified_bundle_and_dispatches(
    monkeypatch: object, tmp_path: Path
) -> None:
    image = tmp_path / "firmware.bin"
    image.write_bytes(b"verified")
    called: list[Path] = []
    monkeypatch.setattr(cli, "verify_firmware_bundle", lambda *args, **kwargs: image)
    monkeypatch.setattr(
        cli,
        "upgrade_firmware",
        lambda **kwargs: called.append(kwargs["image"]) or SimpleNamespace(image_sha256="0" * 64),
    )
    assert cli.main(["openwrt", "upgrade", "--image", str(image)]) == 0
    assert called == [image]


def test_openwrt_upgrade_reconnect_retries_until_board_is_available(
    monkeypatch: object,
) -> None:
    attempts = 0
    sleeps: list[float] = []

    def read_json(name: str) -> dict[str, str]:
        nonlocal attempts
        assert name == "board"
        attempts += 1
        if attempts < 3:
            raise OperationalError("router is rebooting")
        return {"board_name": "cudy,wr3000e-v1"}

    monkeypatch.setattr(cli.time, "monotonic", iter([0.0, 1.0, 2.0]).__next__)
    monkeypatch.setattr(cli.time, "sleep", sleeps.append)

    cli._wait_for_openwrt_reconnect(
        SimpleNamespace(read_json=read_json),  # type: ignore[arg-type]
        timeout=10,
        poll_interval=2,
    )

    assert attempts == 3
    assert sleeps == [2, 2]


def test_openwrt_upgrade_reconnect_has_a_bounded_timeout(monkeypatch: object) -> None:
    def read_json(name: str) -> dict[str, str]:
        raise OperationalError(f"unavailable: {name}")

    monkeypatch.setattr(cli.time, "monotonic", iter([0.0, 10.0]).__next__)
    monkeypatch.setattr(cli.time, "sleep", lambda _: None)

    with pytest.raises(OperationalError, match="did not reconnect within 10s"):
        cli._wait_for_openwrt_reconnect(
            SimpleNamespace(read_json=read_json),  # type: ignore[arg-type]
            timeout=10,
            poll_interval=2,
        )


def test_openwrt_clean_rebuild_requires_verified_bundle_and_dispatches(
    monkeypatch: object, tmp_path: Path
) -> None:
    image = tmp_path / "firmware.bin"
    image.write_bytes(b"verified")
    calls: list[tuple[Path, bool]] = []
    monkeypatch.setattr(cli, "verify_firmware_bundle", lambda *args, **kwargs: image)
    monkeypatch.setattr(cli, "read_live_state", lambda client: {"identity": {}})
    monkeypatch.setattr(cli, "validate_safety", lambda desired, current: None)
    monkeypatch.setattr(
        cli,
        "clean_rebuild_firmware",
        lambda **kwargs: (
            calls.append((kwargs["image"], kwargs["confirmed"]))
            or SimpleNamespace(image_sha256="0" * 64)
        ),
    )

    assert (
        cli.main(
            [
                "openwrt",
                "clean-rebuild",
                "--image",
                str(image),
                "--confirm",
                "CLEAN-REBUILD",
            ]
        )
        == 0
    )
    assert calls == [(image, True)]


def test_openwrt_prepare_clean_rebuild_replaces_pin_after_confirmation_and_archives(
    monkeypatch: object,
) -> None:
    calls: list[str] = []
    journal = SimpleNamespace(
        pending=lambda: (),
        archive_generation=lambda: calls.append("archive") or Path(".generation-pre-clean-test"),
    )
    monkeypatch.setattr(cli, "input", lambda: "yes", raising=False)
    monkeypatch.setattr(
        cli,
        "scan_and_pin_host_key",
        lambda **kwargs: calls.append(f"replace={kwargs['replace_existing']}"),
    )
    monkeypatch.setattr(cli, "read_live_state", lambda client: {"uci": {}})
    monkeypatch.setattr(cli, "validate_safety", lambda *args, **kwargs: calls.append("safe"))
    monkeypatch.setattr(
        cli, "validate_clean_image_transition", lambda *args, **kwargs: calls.append("clean")
    )
    monkeypatch.setattr(cli, "_openwrt_journal", lambda crypto: journal)

    assert cli.main(["openwrt", "bootstrap", "--prepare-clean-rebuild"]) == 0
    assert calls == ["replace=True", "safe", "clean", "archive"]
