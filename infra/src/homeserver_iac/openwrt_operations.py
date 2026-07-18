from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import tempfile
import threading
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Protocol, cast
from urllib.parse import quote_plus

from homeserver_iac.openwrt import (
    ChunkEncryptor,
    CommandResult,
    CommandRunner,
    OpenWrtSafetyError,
    OpenWrtSshClient,
    subprocess_runner,
)
from homeserver_iac.runtime import OperationalError

_HOST = re.compile(r"^[A-Za-z0-9_.:-]+$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MTD_LINE = re.compile(
    r"^mtd(?P<index>[0-9]+): (?P<size>[0-9a-fA-F]{8}) "
    r'(?P<erase>[0-9a-fA-F]{8}) "(?P<label>[^"]+)"$'
)
_REMOTE_IMAGE = "/tmp/homeserver-sysupgrade.bin"


@dataclass(frozen=True)
class MtdPartition:
    device: str
    label: str
    size: int


EXPECTED_MTD_PARTITIONS = (
    MtdPartition("mtd0", "BL2", 1_048_576),
    MtdPartition("mtd1", "u-boot-env", 524_288),
    MtdPartition("mtd2", "Factory", 2_097_152),
    MtdPartition("mtd3", "bdinfo", 262_144),
    MtdPartition("mtd4", "FIP", 2_097_152),
    MtdPartition("mtd5", "ubi", 67_108_864),
)


@dataclass(frozen=True)
class HostKeyPin:
    host: str
    key_type: str
    fingerprint: str
    known_hosts_line: str


ConfirmHostKey = Callable[[HostKeyPin], bool]


class RemoteRunner(Protocol):
    """Execute fixed remote argv without invoking a caller-controlled shell."""

    def run(
        self, command: Sequence[str], *, input_data: bytes | None, timeout: float
    ) -> CommandResult: ...

    def stream(self, command: Sequence[str], *, timeout: float) -> Iterable[bytes]: ...


class ImageUploader(Protocol):
    def __call__(self, source: Path, destination: str, *, timeout: float) -> None: ...


@dataclass(frozen=True)
class CiphertextMetadata:
    filename: str
    plaintext_size: int
    plaintext_sha256: str
    ciphertext_size: int
    ciphertext_sha256: str


@dataclass(frozen=True)
class MtdBackupResult:
    board: str
    release: str
    records: tuple[CiphertextMetadata, ...]


@dataclass(frozen=True)
class UpgradeResult:
    image_sha256: str
    remote_image: str


class ChezmoiCrypto:
    """Stream configured chezmoi age encryption/decryption through pipes."""

    def _pipe(self, action: str, chunks: Iterable[bytes], destination: BinaryIO) -> None:
        try:
            process = subprocess.Popen(
                ("chezmoi", action, "--no-tty"),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as error:
            raise OperationalError("chezmoi is required for OpenWrt encryption") from error
        if process.stdin is None or process.stdout is None:
            process.kill()
            raise OperationalError("chezmoi encryption pipes are unavailable")
        process_stdin = process.stdin
        process_stdout = process.stdout
        failures: list[BaseException] = []

        def write_input() -> None:
            try:
                for chunk in chunks:
                    process_stdin.write(chunk)
                process_stdin.close()
            except BaseException as error:
                failures.append(error)
                with suppress(OSError):
                    process_stdin.close()

        writer = threading.Thread(target=write_input, daemon=True)
        writer.start()
        for chunk in iter(lambda: process_stdout.read(1024 * 1024), b""):
            destination.write(chunk)
        returncode = process.wait()
        writer.join()
        if failures or returncode:
            raise OperationalError(f"chezmoi {action} failed")

    def encrypt(self, chunks: Iterable[bytes], destination: BinaryIO) -> None:
        self._pipe("encrypt", chunks, destination)

    def decrypt(self, chunks: Iterable[bytes], destination: BinaryIO) -> None:
        self._pipe("decrypt", chunks, destination)


class SshRemoteRunner:
    def __init__(self, client: OpenWrtSshClient) -> None:
        self.client = client

    def run(
        self, command: Sequence[str], *, input_data: bytes | None, timeout: float
    ) -> CommandResult:
        mutating = tuple(command) not in {
            ("ubus", "call", "system", "board"),
            ("sysupgrade", "-b", "-"),
            ("cat", "/proc/mtd"),
            *(("cat", f"/dev/mtd{index}") for index in range(6)),
            ("sha256sum", _REMOTE_IMAGE),
            ("sysupgrade", "-T", _REMOTE_IMAGE),
        }
        return self.client.run_operation(
            command, input_data=input_data, timeout=timeout, mutating=mutating
        )

    def stream(self, command: Sequence[str], *, timeout: float) -> Iterable[bytes]:
        result = self.run(command, input_data=None, timeout=timeout)
        yield _command_ok(result, "stream read")


class SshImageUploader:
    def __init__(self, client: OpenWrtSshClient) -> None:
        self.client = client

    def __call__(self, source: Path, destination: str, *, timeout: float) -> None:
        if destination != _REMOTE_IMAGE:
            raise OpenWrtSafetyError("remote firmware path is not allowlisted")
        if self.client.proxy_jump is not None:
            raise OpenWrtSafetyError("firmware upload requires a direct wired SSH route")
        argv = (
            "scp",
            "-O",
            "-F",
            "/dev/null",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={self.client.known_hosts}",
            "-o",
            f"ConnectTimeout={self.client.connect_timeout}",
            "-i",
            str(self.client.identity),
            str(source),
            f"{self.client.host}:{destination}",
        )
        result = self.client.runner(argv, input_data=None, timeout=timeout)
        _command_ok(result, "firmware upload")


def _require_direct(proxy_jump: str | None, operation: str) -> None:
    if proxy_jump is not None:
        raise OpenWrtSafetyError(f"{operation} requires a direct wired SSH route")


def _command_ok(result: CommandResult, operation: str) -> bytes:
    if result.returncode:
        raise OperationalError(f"OpenWrt {operation} failed with exit {result.returncode}")
    return result.stdout


def scan_and_pin_host_key(
    *,
    host: str,
    known_hosts: Path,
    confirm: ConfirmHostKey,
    replace_existing: bool = False,
    proxy_jump: str | None = None,
    timeout: float = 10,
    runner: CommandRunner = subprocess_runner,
) -> HostKeyPin:
    """Scan and pin one directly observed ED25519 key after explicit confirmation."""

    _require_direct(proxy_jump, "host-key pinning")
    if not _HOST.fullmatch(host) or host.startswith("-"):
        raise ValueError("invalid host-key scan host")
    if timeout <= 0:
        raise ValueError("host-key scan timeout must be positive")
    result = runner(
        ("ssh-keyscan", "-T", str(max(1, int(timeout))), "-t", "ed25519", host),
        input_data=None,
        timeout=timeout,
    )
    output = _command_ok(result, "host-key scan")
    try:
        lines = [line for line in output.decode().splitlines() if line and not line.startswith("#")]
    except UnicodeDecodeError as error:
        raise OpenWrtSafetyError("host-key scan returned invalid text") from error
    if len(lines) != 1:
        raise OpenWrtSafetyError("host-key scan must return exactly one key")
    fields = lines[0].split()
    if len(fields) != 3 or fields[0] != host or fields[1] != "ssh-ed25519":
        raise OpenWrtSafetyError("host-key scan returned an unexpected key")
    try:
        key_blob = base64.b64decode(fields[2], validate=True)
    except ValueError as error:
        raise OpenWrtSafetyError("host-key scan returned an invalid key") from error
    fingerprint = base64.b64encode(hashlib.sha256(key_blob).digest()).decode().rstrip("=")
    pin = HostKeyPin(host, fields[1], f"SHA256:{fingerprint}", lines[0])
    if confirm(pin) is not True:
        raise OpenWrtSafetyError("host-key pinning was not explicitly confirmed")

    content = (pin.known_hosts_line + "\n").encode()
    if known_hosts.exists() and known_hosts.read_bytes() == content:
        return pin
    if known_hosts.exists() and known_hosts.stat().st_size and not replace_existing:
        raise OpenWrtSafetyError("known-host file already contains a different key")
    known_hosts.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=known_hosts.parent, prefix=f".{known_hosts.name}."
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as destination:
            destination.write(content)
            destination.flush()
            os.fsync(destination.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, known_hosts)
    except Exception:
        with suppress(FileNotFoundError):
            temporary.unlink()
        raise
    return pin


def parse_mtd_map(content: bytes) -> tuple[MtdPartition, ...]:
    try:
        lines = content.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise OpenWrtSafetyError("MTD partition map is not ASCII") from error
    if not lines or lines[0] != "dev:    size   erasesize  name":
        raise OpenWrtSafetyError("MTD partition map header differs")
    partitions: list[MtdPartition] = []
    for line in lines[1:]:
        match = _MTD_LINE.fullmatch(line)
        if match is None:
            raise OpenWrtSafetyError("MTD partition map is malformed")
        partitions.append(
            MtdPartition(
                device=f"mtd{match.group('index')}",
                label=match.group("label"),
                size=int(match.group("size"), 16),
            )
        )
    observed = tuple(partitions)
    if observed != EXPECTED_MTD_PARTITIONS:
        raise OpenWrtSafetyError("MTD partition map differs from the exact stock layout")
    return observed


class _ExactSizeChunks:
    def __init__(self, chunks: Iterable[bytes], expected_size: int | None) -> None:
        self._chunks = chunks
        self.expected_size = expected_size
        self.size = 0
        self.digest = hashlib.sha256()

    def __iter__(self) -> Iterator[bytes]:
        for chunk in self._chunks:
            if not isinstance(chunk, bytes):
                raise TypeError("backup stream must yield bytes")
            self.size += len(chunk)
            self.digest.update(chunk)
            if self.expected_size is not None and self.size > self.expected_size:
                raise OpenWrtSafetyError("backup stream exceeds the expected size")
            yield chunk


class _CiphertextWriter:
    def __init__(self, destination: BinaryIO) -> None:
        self.destination = destination
        self.size = 0
        self.digest = hashlib.sha256()

    def write(self, data: bytes) -> int:
        self.size += len(data)
        self.digest.update(data)
        return self.destination.write(data)

    def flush(self) -> None:
        self.destination.flush()


def _encrypt_backup(
    *,
    chunks: Iterable[bytes],
    encryptor: ChunkEncryptor,
    destination: Path,
    expected_size: int | None = None,
) -> CiphertextMetadata:
    if destination.exists():
        raise FileExistsError("backup ciphertext already exists")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent, prefix=f".{destination.name}."
    )
    temporary = Path(temporary_name)
    source = _ExactSizeChunks(chunks, expected_size)
    try:
        with os.fdopen(descriptor, "wb") as output:
            ciphertext = _CiphertextWriter(output)
            encryptor.encrypt(source, cast(BinaryIO, ciphertext))
            ciphertext.flush()
            os.fsync(output.fileno())
        if expected_size is not None and source.size != expected_size:
            raise OpenWrtSafetyError("backup stream size differs from the partition map")
        os.replace(temporary, destination)
    except Exception:
        with suppress(FileNotFoundError):
            temporary.unlink()
        raise
    return CiphertextMetadata(
        filename=destination.name,
        plaintext_size=source.size,
        plaintext_sha256=source.digest.hexdigest(),
        ciphertext_size=ciphertext.size,
        ciphertext_sha256=ciphertext.digest.hexdigest(),
    )


class _PlaintextVerifier:
    def __init__(self) -> None:
        self.size = 0
        self.digest = hashlib.sha256()

    def write(self, data: bytes) -> int:
        self.size += len(data)
        self.digest.update(data)
        return len(data)

    def flush(self) -> None:
        return None


def verify_encrypted_backup(
    *,
    source: Path,
    decryptor: object,
    expected_size: int,
    expected_sha256: str,
) -> None:
    """Verify ciphertext by decrypting into a hashing sink, never a plaintext file."""

    if not _SHA256.fullmatch(expected_sha256) or expected_size < 0:
        raise ValueError("backup verification metadata is invalid")
    decrypt = getattr(decryptor, "decrypt", None)
    if not callable(decrypt):
        raise TypeError("backup decryptor has no decrypt method")
    verifier = _PlaintextVerifier()
    try:
        with source.open("rb") as encrypted:
            decrypt(iter(lambda: encrypted.read(1024 * 1024), b""), cast(BinaryIO, verifier))
    except OSError as error:
        raise OperationalError("backup ciphertext is unreadable") from error
    if verifier.size != expected_size or verifier.digest.hexdigest() != expected_sha256:
        raise OpenWrtSafetyError("decrypted backup integrity check failed")


def write_backup_manifest(
    *,
    path: Path,
    board: str,
    release: str,
    timestamp: str,
    records: Sequence[CiphertextMetadata],
) -> None:
    if path.exists():
        raise FileExistsError("backup manifest already exists")
    if not board or not release or not timestamp or not records:
        raise ValueError("backup manifest metadata is incomplete")
    payload = {
        "board": board,
        "release": release,
        "timestamp": timestamp,
        "files": [record.__dict__ for record in records],
    }
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w") as destination:
            json.dump(payload, destination, indent=2, sort_keys=True)
            destination.write("\n")
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary, path)
    except Exception:
        with suppress(FileNotFoundError):
            temporary.unlink()
        raise


def backup_config(
    *,
    remote: RemoteRunner,
    encryptor: ChunkEncryptor,
    destination: Path,
    proxy_jump: str | None = None,
    timeout: float = 300,
) -> CiphertextMetadata:
    """Stream a sysupgrade config archive directly into ciphertext."""

    del proxy_jump  # Configuration capture is the sole backup allowed over a read-only jump.
    return _encrypt_backup(
        chunks=remote.stream(("sysupgrade", "-b", "-"), timeout=timeout),
        encryptor=encryptor,
        destination=destination,
    )


def backup_mtd(
    *,
    remote: RemoteRunner,
    encryptor: ChunkEncryptor,
    destination_dir: Path,
    proxy_jump: str | None = None,
    recovery_workflow: bool = False,
    timeout: float = 600,
) -> tuple[CiphertextMetadata, ...]:
    """Validate the complete map, then read and encrypt every partition exactly once."""

    _require_direct(proxy_jump, "MTD backup")
    if recovery_workflow is not True:
        raise OpenWrtSafetyError("MTD backup requires an explicit recovery workflow")
    map_result = remote.run(("cat", "/proc/mtd"), input_data=None, timeout=timeout)
    partitions = parse_mtd_map(_command_ok(map_result, "MTD map read"))
    records: list[CiphertextMetadata] = []
    for partition in partitions:
        records.append(
            _encrypt_backup(
                chunks=remote.stream(("cat", f"/dev/{partition.device}"), timeout=timeout),
                encryptor=encryptor,
                destination=destination_dir / f"{partition.device}-{partition.label}.bin.age",
                expected_size=partition.size,
            )
        )
    return tuple(records)


def backup_intermediary_mtd(
    *,
    remote: RemoteRunner,
    encryptor: ChunkEncryptor,
    destination_dir: Path,
    proxy_jump: str | None = None,
    recovery_workflow: bool = False,
    timeout: float = 600,
) -> MtdBackupResult:
    """Validate the signed intermediary and encrypt its recovery metadata and MTD."""

    _require_direct(proxy_jump, "MTD backup")
    if recovery_workflow is not True:
        raise OpenWrtSafetyError("MTD backup requires an explicit recovery workflow")
    board_content = _command_ok(
        remote.run(("ubus", "call", "system", "board"), input_data=None, timeout=timeout),
        "intermediary board read",
    )
    try:
        board = json.loads(board_content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OpenWrtSafetyError("intermediary board metadata is invalid") from error
    release = board.get("release", {}) if isinstance(board, dict) else {}
    expected = {
        "model": "Cudy WR3000E v1",
        "board_name": "cudy,wr3000e-v1",
    }
    if not isinstance(board, dict) or any(
        board.get(key) != value for key, value in expected.items()
    ):
        raise OpenWrtSafetyError("intermediary board identity is incompatible")
    if not isinstance(release, dict) or {
        "version": release.get("version"),
        "revision": release.get("revision"),
        "target": release.get("target"),
    } != {
        "version": "23.05-SNAPSHOT-CUDY",
        "revision": "r23001+886-38c150612c",
        "target": "mediatek/filogic",
    }:
        raise OpenWrtSafetyError("signed intermediary release differs from the pinned build")

    map_content = _command_ok(
        remote.run(("cat", "/proc/mtd"), input_data=None, timeout=timeout),
        "MTD map read",
    )
    partitions = parse_mtd_map(map_content)
    metadata = (
        json.dumps(
            {"system_board": board, "proc_mtd": map_content.decode("ascii")},
            indent=2,
            sort_keys=True,
        ).encode()
        + b"\n"
    )
    records = [
        _encrypt_backup(
            chunks=(metadata,),
            encryptor=encryptor,
            destination=destination_dir / "intermediary-metadata.json.age",
        )
    ]
    for partition in partitions:
        records.append(
            _encrypt_backup(
                chunks=remote.stream(("cat", f"/dev/{partition.device}"), timeout=timeout),
                encryptor=encryptor,
                destination=destination_dir / f"{partition.device}-{partition.label}.bin.age",
                expected_size=partition.size,
            )
        )
    return MtdBackupResult(
        board=str(board["board_name"]),
        release=str(release["version"]),
        records=tuple(records),
    )


def rotate_root_password(
    *,
    remote: RemoteRunner,
    password: str,
    proxy_jump: str | None = None,
    timeout: float = 60,
) -> None:
    """Perform an explicit password rotation with the secret only on stdin."""

    _require_direct(proxy_jump, "root password rotation")
    if not password or "\n" in password or "\r" in password or "\0" in password:
        raise ValueError("root password contains an unsupported character")
    result = remote.run(
        ("passwd", "root"),
        input_data=(password + "\n" + password + "\n").encode(),
        timeout=timeout,
    )
    _command_ok(result, "root password rotation")


def verify_luci_https_login(
    *,
    host: str,
    password: str,
    timeout: float = 30,
    runner: CommandRunner = subprocess_runner,
) -> None:
    """Verify LuCI authentication with credentials supplied only through curl stdin."""

    if not _HOST.fullmatch(host) or host.startswith("-"):
        raise ValueError("invalid LuCI host")
    if not password or "\0" in password or "\n" in password or "\r" in password:
        raise ValueError("root password contains an unsupported character")
    form = f"luci_username=root&luci_password={quote_plus(password)}"
    config = (
        f'url = "https://{host}/cgi-bin/luci/"\n'
        f'data = "{form}"\n'
        'header = "Content-Type: application/x-www-form-urlencoded"\n'
        "insecure\n"
        "silent\n"
        "show-error\n"
        "dump-header = -\n"
        "output = /dev/null\n"
    ).encode()
    result = runner(
        ("curl", "--config", "-"),
        input_data=config,
        timeout=timeout,
    )
    headers = _command_ok(result, "LuCI HTTPS login")
    lowered = headers.lower()
    if b"sysauth" not in lowered and b"stok=" not in lowered:
        raise OpenWrtSafetyError("LuCI HTTPS login did not establish an authenticated session")


def upgrade_firmware(
    *,
    remote: RemoteRunner,
    upload: ImageUploader,
    image: Path,
    expected_sha256: str,
    backup: Callable[[], object],
    reconnect: Callable[[], None],
    validate: Callable[[], None],
    proxy_jump: str | None = None,
    timeout: float = 600,
    remote_image: str = _REMOTE_IMAGE,
) -> UpgradeResult:
    """Run the checksum-bound, config-preserving point-upgrade sequence."""

    _require_direct(proxy_jump, "firmware upgrade")
    if not _SHA256.fullmatch(expected_sha256):
        raise ValueError("expected firmware checksum is invalid")
    if remote_image != _REMOTE_IMAGE:
        raise ValueError("remote firmware path is not allowlisted")
    digest = hashlib.sha256()
    try:
        with image.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise OperationalError("firmware image is unreadable") from error
    local_sha256 = digest.hexdigest()
    if local_sha256 != expected_sha256:
        raise OpenWrtSafetyError("local firmware checksum mismatch")

    upload(image, remote_image, timeout=timeout)
    checksum_result = remote.run(("sha256sum", remote_image), input_data=None, timeout=timeout)
    checksum_output = _command_ok(checksum_result, "remote firmware checksum")
    try:
        checksum_fields = checksum_output.decode("ascii").strip().split()
    except UnicodeDecodeError as error:
        raise OpenWrtSafetyError("remote firmware checksum is invalid") from error
    if checksum_fields != [expected_sha256, remote_image]:
        raise OpenWrtSafetyError("remote firmware checksum mismatch")

    test_result = remote.run(("sysupgrade", "-T", remote_image), input_data=None, timeout=timeout)
    _command_ok(test_result, "sysupgrade image test")
    backup()
    install_result = remote.run(("sysupgrade", remote_image), input_data=None, timeout=timeout)
    if install_result.returncode not in {0, 255}:
        raise OperationalError(
            f"OpenWrt sysupgrade install failed with exit {install_result.returncode}"
        )
    reconnect()
    validate()
    return UpgradeResult(local_sha256, remote_image)


def clean_rebuild_firmware(
    *,
    remote: RemoteRunner,
    upload: ImageUploader,
    image: Path,
    expected_sha256: str,
    backup: Callable[[], object],
    confirmed: bool,
    proxy_jump: str | None = None,
    timeout: float = 600,
    remote_image: str = _REMOTE_IMAGE,
) -> UpgradeResult:
    """Back up, verify, and clean-flash one checksum-bound firmware image."""

    _require_direct(proxy_jump, "clean rebuild")
    if confirmed is not True:
        raise OpenWrtSafetyError("clean rebuild requires the explicit confirmation token")
    if not _SHA256.fullmatch(expected_sha256):
        raise ValueError("expected firmware checksum is invalid")
    if remote_image != _REMOTE_IMAGE:
        raise ValueError("remote firmware path is not allowlisted")
    try:
        with image.open("rb") as source:
            local_sha256 = hashlib.file_digest(source, "sha256").hexdigest()
    except OSError as error:
        raise OperationalError("firmware image is unreadable") from error
    if local_sha256 != expected_sha256:
        raise OpenWrtSafetyError("local firmware checksum mismatch")

    backup()
    upload(image, remote_image, timeout=timeout)
    checksum_result = remote.run(("sha256sum", remote_image), input_data=None, timeout=timeout)
    checksum_output = _command_ok(checksum_result, "remote firmware checksum")
    try:
        checksum_fields = checksum_output.decode("ascii").strip().split()
    except UnicodeDecodeError as error:
        raise OpenWrtSafetyError("remote firmware checksum is invalid") from error
    if checksum_fields != [expected_sha256, remote_image]:
        raise OpenWrtSafetyError("remote firmware checksum mismatch")

    test_result = remote.run(("sysupgrade", "-T", remote_image), input_data=None, timeout=timeout)
    _command_ok(test_result, "sysupgrade image test")
    install_result = remote.run(
        ("sysupgrade", "-n", remote_image), input_data=None, timeout=timeout
    )
    if install_result.returncode not in {0, 255}:
        raise OperationalError(
            f"OpenWrt clean sysupgrade install failed with exit {install_result.returncode}"
        )
    return UpgradeResult(local_sha256, remote_image)
