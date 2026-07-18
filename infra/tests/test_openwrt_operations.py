from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import BinaryIO

import pytest

from homeserver_iac.openwrt import CommandResult, OpenWrtSafetyError, OpenWrtSshClient
from homeserver_iac.openwrt_operations import (
    EXPECTED_MTD_PARTITIONS,
    CiphertextMetadata,
    SshImageUploader,
    SshRemoteRunner,
    backup_config,
    backup_intermediary_mtd,
    backup_mtd,
    clean_rebuild_firmware,
    parse_mtd_map,
    rotate_root_password,
    scan_and_pin_host_key,
    upgrade_firmware,
    verify_encrypted_backup,
    verify_luci_https_login,
    write_backup_manifest,
)


class FakeEncryptor:
    def encrypt(self, chunks: Iterable[bytes], destination: BinaryIO) -> None:
        destination.write(b"AGE")
        for chunk in chunks:
            destination.write(chunk)


class FakeRemote:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, ...], bytes | None]] = []
        self.outputs: dict[tuple[str, ...], CommandResult] = {}
        self.streams: dict[tuple[str, ...], list[bytes]] = {}

    def run(
        self, command: Sequence[str], *, input_data: bytes | None, timeout: float
    ) -> CommandResult:
        del timeout
        key = tuple(command)
        self.calls.append(("run", key, input_data))
        return self.outputs.get(key, CommandResult(0))

    def stream(self, command: Sequence[str], *, timeout: float) -> Iterable[bytes]:
        del timeout
        key = tuple(command)
        self.calls.append(("stream", key, None))
        yield from self.streams[key]


def mtd_map() -> bytes:
    lines = ["dev:    size   erasesize  name"]
    for partition in EXPECTED_MTD_PARTITIONS:
        index = partition.device.removeprefix("mtd")
        lines.append(f'mtd{index}: {partition.size:08x} 00020000 "{partition.label}"')
    return ("\n".join(lines) + "\n").encode()


def test_host_key_pin_requires_direct_confirmation_and_records_fingerprint(
    tmp_path: Path,
) -> None:
    key = base64.b64encode(b"fixture-ed25519-key").decode()
    calls: list[tuple[str, ...]] = []
    observed: list[str] = []

    def runner(argv: Sequence[str], *, input_data: bytes | None, timeout: float) -> CommandResult:
        del input_data, timeout
        calls.append(tuple(argv))
        return CommandResult(0, f"192.0.2.1 ssh-ed25519 {key}\n".encode())

    known_hosts = tmp_path / "state/known_hosts"
    pin = scan_and_pin_host_key(
        host="192.0.2.1",
        known_hosts=known_hosts,
        runner=runner,
        confirm=lambda candidate: observed.append(candidate.fingerprint) is None,
    )

    expected = base64.b64encode(hashlib.sha256(b"fixture-ed25519-key").digest()).decode()
    assert pin.fingerprint == f"SHA256:{expected.rstrip('=')}"
    assert observed == [pin.fingerprint]
    assert known_hosts.read_text() == f"192.0.2.1 ssh-ed25519 {key}\n"
    assert calls[0][:2] == ("ssh-keyscan", "-T")

    with pytest.raises(OpenWrtSafetyError, match="direct wired"):
        scan_and_pin_host_key(
            host="192.0.2.1",
            known_hosts=known_hosts,
            runner=runner,
            confirm=lambda _: True,
            proxy_jump="atlas",
        )


def test_host_key_is_not_written_without_explicit_confirmation(tmp_path: Path) -> None:
    key = base64.b64encode(b"fixture-ed25519-key").decode()

    def runner(argv: Sequence[str], *, input_data: bytes | None, timeout: float) -> CommandResult:
        del argv, input_data, timeout
        return CommandResult(0, f"router ssh-ed25519 {key}\n".encode())

    destination = tmp_path / "known_hosts"
    with pytest.raises(OpenWrtSafetyError, match="not explicitly confirmed"):
        scan_and_pin_host_key(
            host="router", known_hosts=destination, runner=runner, confirm=lambda _: False
        )
    assert not destination.exists()


def test_host_key_replacement_is_refused_by_default_and_requires_explicit_mode(
    tmp_path: Path,
) -> None:
    old_key = base64.b64encode(b"old-key").decode()
    new_key = base64.b64encode(b"new-key").decode()
    destination = tmp_path / "known_hosts"
    destination.write_text(f"router ssh-ed25519 {old_key}\n")

    def runner(argv: Sequence[str], *, input_data: bytes | None, timeout: float) -> CommandResult:
        del argv, input_data, timeout
        return CommandResult(0, f"router ssh-ed25519 {new_key}\n".encode())

    with pytest.raises(OpenWrtSafetyError, match="already contains a different key"):
        scan_and_pin_host_key(
            host="router", known_hosts=destination, runner=runner, confirm=lambda _: True
        )
    assert destination.read_text() == f"router ssh-ed25519 {old_key}\n"

    scan_and_pin_host_key(
        host="router",
        known_hosts=destination,
        runner=runner,
        confirm=lambda _: True,
        replace_existing=True,
    )
    assert destination.read_text() == f"router ssh-ed25519 {new_key}\n"


def test_config_backup_is_streamed_and_metadata_describes_only_ciphertext(
    tmp_path: Path,
) -> None:
    remote = FakeRemote()
    remote.streams[("sysupgrade", "-b", "-")] = [b"binary\0", b"config"]
    destination = tmp_path / "config.tar.age"

    metadata = backup_config(
        remote=remote,
        encryptor=FakeEncryptor(),
        destination=destination,
        proxy_jump="read-only-atlas",
    )

    ciphertext = b"AGEbinary\0config"
    assert destination.read_bytes() == ciphertext
    assert metadata == CiphertextMetadata(
        destination.name,
        len(b"binary\0config"),
        hashlib.sha256(b"binary\0config").hexdigest(),
        len(ciphertext),
        hashlib.sha256(ciphertext).hexdigest(),
    )
    verify_encrypted_backup(
        source=destination,
        decryptor=FakeDecryptor(),
        expected_size=metadata.plaintext_size,
        expected_sha256=metadata.plaintext_sha256,
    )


class FakeDecryptor:
    def decrypt(self, chunks: Iterable[bytes], destination: BinaryIO) -> None:
        content = b"".join(chunks)
        assert content.startswith(b"AGE")
        destination.write(content[3:])


def test_backup_manifest_records_required_non_secret_provenance(tmp_path: Path) -> None:
    record = CiphertextMetadata("config.age", 10, "0" * 64, 20, "1" * 64)
    manifest = tmp_path / "manifest.json"
    write_backup_manifest(
        path=manifest,
        board="cudy,wr3000e-v1",
        release="25.12.5",
        timestamp="2026-07-16T12:00:00Z",
        records=(record,),
    )
    content = manifest.read_text()
    assert "plaintext_sha256" in content
    assert "serial" not in content


def test_mtd_backup_validates_exact_map_before_streaming(tmp_path: Path) -> None:
    remote = FakeRemote()
    remote.outputs[("cat", "/proc/mtd")] = CommandResult(0, mtd_map())
    for partition in EXPECTED_MTD_PARTITIONS:
        remote.streams[("cat", f"/dev/{partition.device}")] = [b"x" * partition.size]

    records = backup_mtd(
        remote=remote,
        encryptor=FakeEncryptor(),
        destination_dir=tmp_path,
        recovery_workflow=True,
    )

    assert len(records) == 6
    assert remote.calls[0][1] == ("cat", "/proc/mtd")
    assert [call[1] for call in remote.calls[1:]] == [
        ("cat", f"/dev/{partition.device}") for partition in EXPECTED_MTD_PARTITIONS
    ]


def test_intermediary_mtd_backup_encrypts_metadata_and_validates_pinned_release(
    tmp_path: Path,
) -> None:
    remote = FakeRemote()
    board = {
        "model": "Cudy WR3000E v1",
        "board_name": "cudy,wr3000e-v1",
        "release": {
            "version": "23.05-SNAPSHOT-CUDY",
            "revision": "r23001+886-38c150612c",
            "target": "mediatek/filogic",
        },
    }
    remote.outputs[("ubus", "call", "system", "board")] = CommandResult(
        0, json.dumps(board).encode()
    )
    remote.outputs[("cat", "/proc/mtd")] = CommandResult(0, mtd_map())
    for partition in EXPECTED_MTD_PARTITIONS:
        remote.streams[("cat", f"/dev/{partition.device}")] = [b"x" * partition.size]

    result = backup_intermediary_mtd(
        remote=remote,
        encryptor=FakeEncryptor(),
        destination_dir=tmp_path,
        recovery_workflow=True,
    )

    assert result.board == "cudy,wr3000e-v1"
    assert result.release == "23.05-SNAPSHOT-CUDY"
    assert len(result.records) == 7
    metadata = (tmp_path / "intermediary-metadata.json.age").read_bytes()
    assert metadata.startswith(b"AGE")
    assert b'"proc_mtd"' in metadata

    board["release"]["revision"] = "unexpected"
    rejected = FakeRemote()
    rejected.outputs[("ubus", "call", "system", "board")] = CommandResult(
        0, json.dumps(board).encode()
    )
    with pytest.raises(OpenWrtSafetyError, match="pinned build"):
        backup_intermediary_mtd(
            remote=rejected,
            encryptor=FakeEncryptor(),
            destination_dir=tmp_path / "rejected",
            recovery_workflow=True,
        )


def test_intermediary_board_probe_is_allowlisted_by_ssh_transport(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []

    def runner(argv: Sequence[str], *, input_data: bytes | None, timeout: float) -> CommandResult:
        del input_data, timeout
        calls.append(tuple(argv))
        return CommandResult(0, b"{}")

    client = OpenWrtSshClient(
        host="root@192.168.1.1",
        known_hosts=tmp_path / "known_hosts",
        identity=tmp_path / "identity",
        runner=runner,
    )
    result = SshRemoteRunner(client).run(
        ("ubus", "call", "system", "board"), input_data=None, timeout=10
    )

    assert result.stdout == b"{}"
    assert calls[0][-4:] == ("ubus", "call", "system", "board")


def test_firmware_uploader_uses_strict_legacy_scp_without_a_shell(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []

    def runner(argv: Sequence[str], *, input_data: bytes | None, timeout: float) -> CommandResult:
        del input_data, timeout
        calls.append(tuple(argv))
        return CommandResult(0)

    image = tmp_path / "firmware.bin"
    image.write_bytes(b"firmware")
    client = OpenWrtSshClient(
        host="root@192.168.1.1",
        known_hosts=tmp_path / "known_hosts",
        identity=tmp_path / "identity",
        runner=runner,
    )

    SshImageUploader(client)(image, "/tmp/homeserver-sysupgrade.bin", timeout=60)

    assert calls == [
        (
            "scp",
            "-O",
            "-F",
            "/dev/null",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={tmp_path / 'known_hosts'}",
            "-o",
            "ConnectTimeout=10",
            "-i",
            str(tmp_path / "identity"),
            str(image),
            "root@192.168.1.1:/tmp/homeserver-sysupgrade.bin",
        )
    ]


def test_mtd_backup_rejects_map_or_byte_count_and_proxy_jump(tmp_path: Path) -> None:
    remote = FakeRemote()
    with pytest.raises(OpenWrtSafetyError, match="explicit recovery"):
        backup_mtd(remote=remote, encryptor=FakeEncryptor(), destination_dir=tmp_path)
    remote.outputs[("cat", "/proc/mtd")] = CommandResult(
        0, mtd_map().replace(b'"Factory"', b'"factory"')
    )
    with pytest.raises(OpenWrtSafetyError, match="exact stock layout"):
        backup_mtd(
            remote=remote,
            encryptor=FakeEncryptor(),
            destination_dir=tmp_path,
            recovery_workflow=True,
        )
    assert all(call[0] != "stream" for call in remote.calls)

    with pytest.raises(OpenWrtSafetyError, match="direct wired"):
        backup_mtd(
            remote=remote,
            encryptor=FakeEncryptor(),
            destination_dir=tmp_path,
            proxy_jump="atlas",
            recovery_workflow=True,
        )

    assert parse_mtd_map(mtd_map()) == EXPECTED_MTD_PARTITIONS
    short = FakeRemote()
    short.outputs[("cat", "/proc/mtd")] = CommandResult(0, mtd_map())
    short.streams[("cat", "/dev/mtd0")] = [b"short"]
    with pytest.raises(OpenWrtSafetyError, match="size differs"):
        backup_mtd(
            remote=short,
            encryptor=FakeEncryptor(),
            destination_dir=tmp_path,
            recovery_workflow=True,
        )
    assert not tuple(tmp_path.iterdir())


def test_password_rotation_uses_stdin_and_rejects_proxy_jump() -> None:
    remote = FakeRemote()
    secret = "fixture-secret"
    rotate_root_password(remote=remote, password=secret)
    _, argv, stdin = remote.calls[0]
    assert argv == ("passwd", "root")
    assert secret not in " ".join(argv)
    assert stdin == b"fixture-secret\nfixture-secret\n"

    with pytest.raises(OpenWrtSafetyError, match="direct wired"):
        rotate_root_password(remote=remote, password=secret, proxy_jump="atlas")


def test_luci_login_keeps_password_out_of_argv_and_requires_session_marker() -> None:
    calls: list[tuple[tuple[str, ...], bytes | None]] = []

    def runner(argv: Sequence[str], *, input_data: bytes | None, timeout: float) -> CommandResult:
        del timeout
        calls.append((tuple(argv), input_data))
        return CommandResult(0, b"Set-Cookie: sysauth_https=fixture; Secure\r\n")

    verify_luci_https_login(host="192.168.1.1", password="fixture secret", runner=runner)
    argv, stdin = calls[0]
    assert argv == ("curl", "--config", "-")
    assert "fixture secret" not in " ".join(argv)
    assert b"fixture+secret" in (stdin or b"")

    with pytest.raises(OpenWrtSafetyError, match="authenticated session"):
        verify_luci_https_login(
            host="192.168.1.1",
            password="fixture",
            runner=lambda argv, input_data, timeout: CommandResult(0, b"HTTP/2 200\r\n"),
        )


def test_upgrade_runs_all_preflight_and_post_boot_callbacks_in_order(tmp_path: Path) -> None:
    image = tmp_path / "firmware.bin"
    image.write_bytes(b"verified-firmware")
    checksum = hashlib.sha256(image.read_bytes()).hexdigest()
    remote_path = "/tmp/homeserver-sysupgrade.bin"
    remote = FakeRemote()
    remote.outputs[("sha256sum", remote_path)] = CommandResult(
        0, f"{checksum}  {remote_path}\n".encode()
    )
    events: list[str] = []

    def upload(source: Path, destination: str, *, timeout: float) -> None:
        del timeout
        assert source == image
        assert destination == remote_path
        events.append("upload")

    original_run = remote.run

    def recording_run(
        command: Sequence[str], *, input_data: bytes | None, timeout: float
    ) -> CommandResult:
        events.append("run:" + " ".join(command))
        return original_run(command, input_data=input_data, timeout=timeout)

    remote.run = recording_run  # type: ignore[method-assign]
    result = upgrade_firmware(
        remote=remote,
        upload=upload,
        image=image,
        expected_sha256=checksum,
        backup=lambda: events.append("backup"),
        reconnect=lambda: events.append("reconnect"),
        validate=lambda: events.append("validate"),
    )

    assert result.image_sha256 == checksum
    assert events == [
        "upload",
        f"run:sha256sum {remote_path}",
        f"run:sysupgrade -T {remote_path}",
        "backup",
        f"run:sysupgrade {remote_path}",
        "reconnect",
        "validate",
    ]
    assert "-F" not in remote.calls[-1][1]
    assert "-n" not in remote.calls[-1][1]


def test_upgrade_stops_before_install_on_mismatch_and_rejects_proxy_jump(
    tmp_path: Path,
) -> None:
    image = tmp_path / "firmware.bin"
    image.write_bytes(b"firmware")
    remote = FakeRemote()
    called: list[str] = []
    with pytest.raises(OpenWrtSafetyError, match="local firmware checksum"):
        upgrade_firmware(
            remote=remote,
            upload=lambda source, destination, timeout: called.append("upload"),
            image=image,
            expected_sha256="0" * 64,
            backup=lambda: called.append("backup"),
            reconnect=lambda: called.append("reconnect"),
            validate=lambda: called.append("validate"),
        )
    assert called == []

    with pytest.raises(OpenWrtSafetyError, match="direct wired"):
        upgrade_firmware(
            remote=remote,
            upload=lambda source, destination, timeout: None,
            image=image,
            expected_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
            backup=lambda: None,
            reconnect=lambda: None,
            validate=lambda: None,
            proxy_jump="atlas",
        )


def test_clean_rebuild_backs_up_then_uses_only_non_forced_clean_sysupgrade(
    tmp_path: Path,
) -> None:
    image = tmp_path / "firmware.bin"
    image.write_bytes(b"verified-clean-firmware")
    checksum = hashlib.sha256(image.read_bytes()).hexdigest()
    remote_path = "/tmp/homeserver-sysupgrade.bin"
    remote = FakeRemote()
    remote.outputs[("sha256sum", remote_path)] = CommandResult(
        0, f"{checksum}  {remote_path}\n".encode()
    )
    remote.outputs[("sysupgrade", "-n", remote_path)] = CommandResult(255)
    events: list[str] = []

    def upload(source: Path, destination: str, *, timeout: float) -> None:
        del timeout
        assert source == image
        assert destination == remote_path
        events.append("upload")

    original_run = remote.run

    def recording_run(
        command: Sequence[str], *, input_data: bytes | None, timeout: float
    ) -> CommandResult:
        events.append("run:" + " ".join(command))
        return original_run(command, input_data=input_data, timeout=timeout)

    remote.run = recording_run  # type: ignore[method-assign]
    result = clean_rebuild_firmware(
        remote=remote,
        upload=upload,
        image=image,
        expected_sha256=checksum,
        backup=lambda: events.append("backup"),
        confirmed=True,
    )

    assert result.image_sha256 == checksum
    assert events == [
        "backup",
        "upload",
        f"run:sha256sum {remote_path}",
        f"run:sysupgrade -T {remote_path}",
        f"run:sysupgrade -n {remote_path}",
    ]
    install = remote.calls[-1][1]
    assert install == ("sysupgrade", "-n", remote_path)
    assert "-F" not in install


def test_clean_rebuild_refuses_without_confirmation_or_direct_route(tmp_path: Path) -> None:
    image = tmp_path / "firmware.bin"
    image.write_bytes(b"firmware")
    checksum = hashlib.sha256(image.read_bytes()).hexdigest()
    remote = FakeRemote()

    with pytest.raises(OpenWrtSafetyError, match="confirmation token"):
        clean_rebuild_firmware(
            remote=remote,
            upload=lambda source, destination, timeout: None,
            image=image,
            expected_sha256=checksum,
            backup=lambda: None,
            confirmed=False,
        )
    with pytest.raises(OpenWrtSafetyError, match="direct wired"):
        clean_rebuild_firmware(
            remote=remote,
            upload=lambda source, destination, timeout: None,
            image=image,
            expected_sha256=checksum,
            backup=lambda: None,
            confirmed=True,
            proxy_jump="atlas",
        )
    assert remote.calls == []
