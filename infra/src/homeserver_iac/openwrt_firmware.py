from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zlib import crc32

from homeserver_iac.openwrt import FORBIDDEN_PACKAGES, REQUIRED_PACKAGES
from homeserver_iac.runtime import OperationalError

VERSION = "25.12.5"
TARGET = "mediatek/filogic"
PROFILE = "cudy_wr3000e-v1"
MODEL = "Cudy WR3000E v1"
BOARD = "cudy,wr3000e-v1"
BOARD_ID = "R53"
IMAGEBUILDER_FILENAME = "openwrt-imagebuilder-25.12.5-mediatek-filogic.Linux-x86_64.tar.zst"
IMAGEBUILDER_URL = (
    "https://downloads.openwrt.org/releases/25.12.5/targets/mediatek/filogic/"
    + IMAGEBUILDER_FILENAME
)
IMAGEBUILDER_SHA256 = "7fb6cf626582ebcbfb46974da48c1eae577213f38879eaf6b1d982041e843461"
BASE_URL = f"https://downloads.openwrt.org/releases/{VERSION}/targets/{TARGET}/"
PROFILES_FILENAME = "profiles.json"
SHA256SUMS_FILENAME = "sha256sums"
BUILDER_IMAGE = (
    "docker.io/library/debian:bookworm-slim@"
    "sha256:63a496b5d3b99214b39f5ed70eb71a61e590a77979c79cbee4faf991f8c0783e"
)
REQUESTED_PACKAGES = (
    "luci-ssl",
    "luci-app-sqm",
    "sqm-scripts",
    "rpcd",
    "ucode",
    "ucode-mod-ubus",
)
_PUBLIC_KEY = re.compile(r"^ssh-(?:ed25519|rsa) [A-Za-z0-9+/]+={0,3}(?: [^\r\n]+)?$")
_PEM_BEGIN = b"BEGIN "
_SECRET_MARKERS = (
    _PEM_BEGIN + b"OPENSSH PRIVATE KEY",
    _PEM_BEGIN + b"PRIVATE KEY",
    b"BWS_ACCESS_TOKEN",
    b"OPENWRT_PPPOE_PASSWORD",
    b"OPENWRT_MAIN_WIFI_PSK",
    b"OPENWRT_GUEST_WIFI_PSK",
    b"fixture-secret-must-never-appear",
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FWTOOL_MAGIC = 0x46577830
_FWTOOL_INFO = 1
_FWTOOL_TRAILER_SIZE = 16
_OFFICIAL_SYSUPGRADE = f"openwrt-{VERSION}-mediatek-filogic-{PROFILE}-squashfs-sysupgrade.bin"


class FirmwareVerificationError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def _fetch_exact(
    url: str,
    destination: Path,
    *,
    expected_sha256: str | None = None,
    timeout: float = 60,
) -> Path:
    """Fetch one exact URL without redirects or partial published files."""

    if Path(urllib.parse.urlparse(url).path).name != destination.name:
        raise FirmwareVerificationError("download destination filename is not pinned")
    if destination.exists() and expected_sha256 == sha256_file(destination):
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.unlink(missing_ok=True)
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with (
            opener.open(url, timeout=timeout) as response,
            temporary.open("xb") as out,
        ):
            if response.geturl() != url:
                raise FirmwareVerificationError("download redirected")
            shutil.copyfileobj(response, out)
        if expected_sha256 is not None and sha256_file(temporary) != expected_sha256:
            raise FirmwareVerificationError("download checksum mismatch")
        os.replace(temporary, destination)
    except (OSError, urllib.error.URLError) as error:
        temporary.unlink(missing_ok=True)
        raise OperationalError(f"pinned download failed: {destination.name}") from error
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def fetch_imagebuilder(destination: Path, *, timeout: float = 600) -> Path:
    if destination.name != IMAGEBUILDER_FILENAME:
        raise FirmwareVerificationError("Image Builder destination filename is not pinned")
    return _fetch_exact(
        IMAGEBUILDER_URL,
        destination,
        expected_sha256=IMAGEBUILDER_SHA256,
        timeout=timeout,
    )


def parse_sha256sums(content: str) -> dict[str, str]:
    records: dict[str, str] = {}
    for line in content.splitlines():
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not _SHA256.fullmatch(parts[0]):
            raise FirmwareVerificationError("official sha256sums contains a malformed record")
        filename = parts[1].removeprefix("*")
        path = Path(filename)
        if not filename or path.is_absolute() or ".." in path.parts or filename in records:
            raise FirmwareVerificationError("official sha256sums contains an unsafe duplicate")
        records[filename] = parts[0]
    return records


def verify_profiles(profiles: Mapping[str, Any], checksums: Mapping[str, str]) -> Mapping[str, Any]:
    if profiles.get("version_number") != VERSION or profiles.get("target") != TARGET:
        raise FirmwareVerificationError("release profile metadata mismatch")
    profile = profiles.get("profiles", {}).get(PROFILE, {})
    if not isinstance(profile, Mapping):
        raise FirmwareVerificationError("pinned profile is absent")
    supported = profile.get("supported_devices", [])
    titles = profile.get("titles", [])
    expected_title = {"vendor": "Cudy", "model": "WR3000E", "variant": "v1"}
    if BOARD not in supported or BOARD_ID not in supported or expected_title not in titles:
        raise FirmwareVerificationError("profile board/model metadata mismatch")
    device_packages = set(profile.get("device_packages", []))
    required_device = {"kmod-mt7915e", "kmod-mt7981-firmware", "mt7981-wo-firmware"}
    if not required_device <= device_packages:
        raise FirmwareVerificationError("profile device packages are incomplete")
    images = profile.get("images", [])
    matches = [
        image
        for image in images
        if isinstance(image, Mapping)
        and image.get("name") == _OFFICIAL_SYSUPGRADE
        and image.get("filesystem") == "squashfs"
        and image.get("type") == "sysupgrade"
    ]
    if len(matches) != 1 or checksums.get(_OFFICIAL_SYSUPGRADE) != matches[0].get("sha256"):
        raise FirmwareVerificationError("official sysupgrade is absent from sha256sums")
    if matches[0].get("size") != 9_390_356:
        raise FirmwareVerificationError("official sysupgrade size metadata mismatch")
    return profile


def create_overlay(public_key: Path, helper: Path, destination: Path) -> dict[str, str]:
    if destination.exists():
        raise FirmwareVerificationError("firmware overlay destination must be new")
    key = public_key.read_text().strip()
    if not _PUBLIC_KEY.fullmatch(key) or len(key.splitlines()) != 1:
        raise FirmwareVerificationError("managed public key must contain one supported key")
    helper_data = helper.read_bytes()
    if not helper_data.startswith(b"#!/usr/bin/ucode\n"):
        raise FirmwareVerificationError("helper is not an auditable ucode program")
    if b"/bin/sh" in helper_data or b"system(" in helper_data or b"popen(" in helper_data:
        raise FirmwareVerificationError("helper contains a shell execution path")
    for marker in _SECRET_MARKERS:
        if marker in key.encode() or marker in helper_data:
            raise FirmwareVerificationError("firmware overlay contains a secret marker")

    authorized = destination / "etc/dropbear/authorized_keys"
    installed_helper = destination / "usr/libexec/homeserver-uci"
    authorized.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    installed_helper.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    authorized.write_text(key + "\n")
    installed_helper.write_bytes(helper_data)
    authorized.chmod(0o600)
    installed_helper.chmod(0o755)
    inventory = {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    }
    expected_inventory = {
        "etc/dropbear/authorized_keys",
        "usr/libexec/homeserver-uci",
    }
    if inventory != expected_inventory or any(path.is_symlink() for path in destination.rglob("*")):
        raise FirmwareVerificationError("firmware overlay contains an unexpected path")
    return {
        "etc/dropbear/authorized_keys": sha256_file(authorized),
        "usr/libexec/homeserver-uci": sha256_file(installed_helper),
    }


def docker_build_argv(*, repository: Path, work: Path, tag: str) -> tuple[str, ...]:
    """Return the constrained builder-image command; it does not run Docker."""

    return (
        "docker",
        "build",
        "--platform=linux/amd64",
        "--pull=false",
        "--tag",
        tag,
        "--file",
        str(repository / "infra/network/openwrt/Containerfile"),
        str(repository / "infra/network/openwrt"),
    )


def imagebuilder_make_argv(overlay: Path) -> tuple[str, ...]:
    return (
        "make",
        "image",
        f"PROFILE={PROFILE}",
        f"PACKAGES={' '.join(REQUESTED_PACKAGES)}",
        f"FILES={overlay}",
        "EXTRA_IMAGE_NAME=homeserver",
    )


@dataclass(frozen=True)
class FirmwareManifest:
    artifact: str
    artifact_size: int
    artifact_sha256: str
    version: str
    target: str
    profile: str
    model: str
    board: str
    board_id: str
    imagebuilder_sha256: str
    builder_image: str
    builder_image_id: str
    containerfile_sha256: str
    requested_packages: tuple[str, ...]
    resolved_packages: Mapping[str, str]
    feed_indexes: Mapping[str, str]
    overlay: Mapping[str, str]
    source_metadata: Mapping[str, str]
    embedded_metadata: Mapping[str, Any]

    def as_json(self) -> str:
        return json.dumps(self.__dict__, indent=2, sort_keys=True) + "\n"


def build_manifest(
    artifact: Path,
    *,
    resolved_packages: Mapping[str, str],
    feed_indexes: Mapping[str, str],
    overlay: Mapping[str, str],
    builder_image_id: str = "",
    containerfile_sha256: str = "",
    source_metadata: Mapping[str, str] | None = None,
    embedded_metadata: Mapping[str, Any] | None = None,
) -> FirmwareManifest:
    verify_artifact_name(artifact.name)
    return FirmwareManifest(
        artifact=artifact.name,
        artifact_size=artifact.stat().st_size,
        artifact_sha256=sha256_file(artifact),
        version=VERSION,
        target=TARGET,
        profile=PROFILE,
        model=MODEL,
        board=BOARD,
        board_id=BOARD_ID,
        imagebuilder_sha256=IMAGEBUILDER_SHA256,
        builder_image=BUILDER_IMAGE,
        builder_image_id=builder_image_id,
        containerfile_sha256=containerfile_sha256,
        requested_packages=REQUESTED_PACKAGES,
        resolved_packages=dict(sorted(resolved_packages.items())),
        feed_indexes=dict(sorted(feed_indexes.items())),
        overlay=dict(sorted(overlay.items())),
        source_metadata=dict(sorted((source_metadata or {}).items())),
        embedded_metadata=dict(embedded_metadata or {}),
    )


def verify_artifact_name(name: str) -> None:
    if "ubootmod" in name or not name.endswith("-squashfs-sysupgrade.bin"):
        raise FirmwareVerificationError("artifact is not a stock-layout squashfs sysupgrade image")
    if PROFILE not in name or VERSION not in name:
        raise FirmwareVerificationError("artifact filename does not match release/profile lock")


def read_fwtool_metadata(artifact: Path) -> Mapping[str, Any]:
    data = artifact.read_bytes()
    end = len(data)
    while end >= _FWTOOL_TRAILER_SIZE:
        trailer_offset = end - _FWTOOL_TRAILER_SIZE
        magic, expected_crc, chunk_type, chunk_size = struct.unpack(
            ">IIB3xI", data[trailer_offset:end]
        )
        if magic != _FWTOOL_MAGIC:
            raise FirmwareVerificationError("artifact has no valid fwtool trailer")
        if chunk_size < _FWTOOL_TRAILER_SIZE or chunk_size > end:
            raise FirmwareVerificationError("artifact has an invalid fwtool chunk size")
        if (crc32(data[:trailer_offset]) ^ 0xFFFFFFFF) & 0xFFFFFFFF != expected_crc:
            raise FirmwareVerificationError("artifact fwtool checksum mismatch")
        chunk_start = end - chunk_size
        payload = data[chunk_start:trailer_offset]
        if chunk_type == _FWTOOL_INFO:
            if len(payload) < 8 or payload[:8] != b"\0" * 8:
                raise FirmwareVerificationError("artifact metadata header is unsupported")
            try:
                metadata = json.loads(payload[8:])
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise FirmwareVerificationError("artifact metadata JSON is invalid") from error
            if not isinstance(metadata, Mapping):
                raise FirmwareVerificationError("artifact metadata is not an object")
            return metadata
        end = chunk_start
    raise FirmwareVerificationError("artifact contains no sysupgrade metadata")


def verify_embedded_metadata(metadata: Mapping[str, Any]) -> None:
    supported = metadata.get("supported_devices", [])
    version = metadata.get("version", {})
    if not isinstance(version, Mapping):
        raise FirmwareVerificationError("artifact version metadata is absent")
    if BOARD not in supported or BOARD_ID not in supported:
        raise FirmwareVerificationError("artifact supported-device metadata mismatch")
    if version.get("version") != VERSION or version.get("target") != TARGET:
        raise FirmwareVerificationError("artifact embedded release/target mismatch")


def verify_sysupgrade_archive(artifact: Path) -> None:
    root = f"sysupgrade-{PROFILE}"
    expected = {f"{root}/", f"{root}/CONTROL", f"{root}/kernel", f"{root}/root"}
    try:
        with tarfile.open(artifact, "r:") as archive:
            members = archive.getmembers()
            names = {member.name + ("/" if member.isdir() else "") for member in members}
            if names != expected or len(members) != len(expected):
                raise FirmwareVerificationError("sysupgrade archive layout is unexpected")
            if any(not (member.isdir() or member.isfile()) for member in members):
                raise FirmwareVerificationError("sysupgrade archive contains an unsafe member")
            control_file = archive.extractfile(f"{root}/CONTROL")
            kernel_file = archive.extractfile(f"{root}/kernel")
            root_file = archive.extractfile(f"{root}/root")
            if control_file is None or control_file.read() != f"BOARD={PROFILE}\n".encode():
                raise FirmwareVerificationError("sysupgrade CONTROL board mismatch")
            if kernel_file is None or kernel_file.read(4) != b"\xd0\r\xfe\xed":
                raise FirmwareVerificationError("sysupgrade kernel is not a FIT image")
            if root_file is None or root_file.read(4) != b"hsqs":
                raise FirmwareVerificationError("sysupgrade root is not squashfs")
    except (OSError, tarfile.TarError) as error:
        raise FirmwareVerificationError("artifact is not a readable sysupgrade archive") from error


def _parse_package_manifest(content: str) -> dict[str, str]:
    packages: dict[str, str] = {}
    for line in content.splitlines():
        if not line:
            continue
        try:
            name, version = line.rsplit(" - ", 1)
        except ValueError as error:
            raise FirmwareVerificationError("resolved package manifest is malformed") from error
        if not name or not version or name in packages:
            raise FirmwareVerificationError("resolved package manifest contains a duplicate")
        packages[name] = version
    return packages


def _run(argv: tuple[str, ...], *, capture: bool = False) -> str:
    try:
        result = subprocess.run(
            argv,
            check=False,
            text=True,
            capture_output=capture,
        )
    except FileNotFoundError as error:
        raise OperationalError(f"command not found: {argv[0]}") from error
    if result.returncode:
        detail = result.stderr.strip() if capture else ""
        suffix = f": {detail}" if detail else ""
        raise OperationalError(
            f"firmware command failed ({argv[0]}, exit {result.returncode}){suffix}"
        )
    return result.stdout.strip() if capture else ""


def _run_bytes(argv: tuple[str, ...]) -> bytes:
    try:
        result = subprocess.run(argv, check=False, capture_output=True)
    except FileNotFoundError as error:
        raise OperationalError(f"command not found: {argv[0]}") from error
    if result.returncode:
        detail = result.stderr.decode(errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise OperationalError(
            f"firmware inspection failed ({argv[0]}, exit {result.returncode}){suffix}"
        )
    return result.stdout


def _docker_run_argv(
    *,
    image: str,
    work: Path,
    command: tuple[str, ...],
    workdir: str = "/work",
    network: bool = True,
) -> tuple[str, ...]:
    argv = [
        "docker",
        "run",
        "--rm",
        "--platform=linux/amd64",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
    ]
    if not network:
        argv.append("--network=none")
    argv.extend(
        (
            "--mount",
            f"type=bind,src={work},dst=/work",
            "--workdir",
            workdir,
            image,
            *command,
        )
    )
    return tuple(argv)


def _require_private_work_root(repository: Path, work_root: Path) -> None:
    expected = (repository / ".local/openwrt").resolve()
    resolved = work_root.resolve()
    if resolved != expected:
        raise FirmwareVerificationError("firmware work root must be repository .local/openwrt")
    work_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    work_root.chmod(0o700)


def archive_firmware_bundle(
    bundle: Path,
    destination: Path,
    *,
    work_root: Path,
    helper: Path,
    public_key: Path,
) -> Path:
    destination = destination.expanduser().resolve()
    try:
        destination.relative_to(work_root.resolve())
    except ValueError:
        pass
    else:
        raise FirmwareVerificationError("second artifact copy must be outside .local/openwrt")
    if destination.exists() or not destination.parent.is_dir():
        raise FirmwareVerificationError(
            "archive destination must be a new path under an existing directory"
        )
    verify_firmware_bundle(bundle, helper=helper, public_key=public_key)
    temporary = destination.with_name(destination.name + ".tmp")
    if temporary.exists():
        raise FirmwareVerificationError("temporary archive destination already exists")
    shutil.copytree(bundle, temporary)
    os.replace(temporary, destination)
    verify_firmware_bundle(destination, helper=helper, public_key=public_key)
    return destination


def build_firmware(repository: Path, work_root: Path, *, archive_to: Path | None = None) -> Path:
    """Build and publish one checksum-bound custom firmware bundle."""

    repository = repository.resolve()
    _require_private_work_root(repository, work_root)
    build_root = work_root / "build"
    downloads = build_root / "downloads"
    artifacts = work_root / f"artifacts/{VERSION}/homeserver"
    if artifacts.exists():
        if archive_to is not None:
            return archive_firmware_bundle(
                artifacts,
                archive_to,
                work_root=work_root,
                helper=repository / "infra/network/openwrt/files/usr/libexec/homeserver-uci",
                public_key=repository / "private_dot_ssh/id_ed25519.pub",
            )
        raise FirmwareVerificationError(
            "custom artifact bundle already exists; preserve or remove it after review"
        )
    build_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    downloads.mkdir(parents=True, exist_ok=True, mode=0o700)

    sums_path = _fetch_exact(BASE_URL + SHA256SUMS_FILENAME, downloads / SHA256SUMS_FILENAME)
    checksums = parse_sha256sums(sums_path.read_text())
    if checksums.get(IMAGEBUILDER_FILENAME) != IMAGEBUILDER_SHA256:
        raise FirmwareVerificationError("official Image Builder checksum differs from lock")
    profiles_path = _fetch_exact(
        BASE_URL + PROFILES_FILENAME,
        downloads / PROFILES_FILENAME,
        expected_sha256=checksums.get(PROFILES_FILENAME),
    )
    profiles = json.loads(profiles_path.read_text())
    if not isinstance(profiles, Mapping):
        raise FirmwareVerificationError("profiles.json must contain an object")
    verify_profiles(profiles, checksums)
    archive = fetch_imagebuilder(downloads / IMAGEBUILDER_FILENAME)

    run_root = Path(tempfile.mkdtemp(prefix="run-", dir=build_root))
    overlay = run_root / "files"
    overlay_manifest = create_overlay(
        repository / "private_dot_ssh/id_ed25519.pub",
        repository / "infra/network/openwrt/files/usr/libexec/homeserver-uci",
        overlay,
    )
    containerfile = repository / "infra/network/openwrt/Containerfile"
    tag = f"homeserver-openwrt-builder:{VERSION}"
    _run(docker_build_argv(repository=repository, work=work_root, tag=tag))
    image_id = _run(("docker", "image", "inspect", tag, "--format", "{{.Id}}"), capture=True)
    if not image_id.startswith("sha256:"):
        raise OperationalError("Docker did not return an immutable builder image ID")
    architecture = _run(
        _docker_run_argv(image=image_id, work=build_root, command=("uname", "-m"), network=False),
        capture=True,
    )
    if architecture != "x86_64":
        raise FirmwareVerificationError("pinned builder container did not report x86_64")

    output = run_root / "output"
    output.mkdir(mode=0o700)
    extracted_name = IMAGEBUILDER_FILENAME.removesuffix(".tar.zst")
    build_script = "\n".join(
        (
            "set -euo pipefail",
            "tar --zstd -xf /input/imagebuilder.tar.zst",
            f"cd {extracted_name}",
            "make image "
            f"PROFILE={PROFILE} "
            f"PACKAGES='{' '.join(REQUESTED_PACKAGES)}' "
            "FILES=/input/files EXTRA_IMAGE_NAME=homeserver",
            "mkdir -p /output/target /output/feed-indexes",
            "cp bin/targets/mediatek/filogic/* /output/target/",
            "cp repositories /output/repositories",
            "cp dl/APKINDEX.* /output/feed-indexes/",
        )
    )
    _run(
        (
            "docker",
            "run",
            "--rm",
            "--platform=linux/amd64",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--mount",
            f"type=bind,src={archive},dst=/input/imagebuilder.tar.zst,readonly",
            "--mount",
            f"type=bind,src={overlay},dst=/input/files,readonly",
            "--mount",
            f"type=bind,src={output},dst=/output",
            image_id,
            "bash",
            "-euc",
            build_script,
        )
    )

    target_output = output / "target"
    candidates = tuple(target_output.glob(f"*homeserver*{PROFILE}*squashfs-sysupgrade.bin"))
    if len(candidates) != 1:
        raise FirmwareVerificationError(
            "Image Builder did not produce exactly one custom sysupgrade"
        )
    artifact = candidates[0]
    verify_artifact_name(artifact.name)
    embedded = read_fwtool_metadata(artifact)
    verify_embedded_metadata(embedded)
    verify_sysupgrade_archive(artifact)
    package_manifests = tuple(target_output.glob(f"*{PROFILE}*.manifest"))
    if len(package_manifests) != 1:
        raise FirmwareVerificationError(
            "Image Builder did not produce one resolved package manifest"
        )
    resolved = _parse_package_manifest(package_manifests[0].read_text())
    missing = REQUIRED_PACKAGES - set(resolved)
    forbidden = FORBIDDEN_PACKAGES & set(resolved)
    if missing or forbidden:
        raise FirmwareVerificationError("built package manifest violates package policy")
    feed_indexes = {
        path.name: sha256_file(path)
        for path in sorted((output / "feed-indexes").glob("APKINDEX.*"))
        if path.is_file()
    }
    if not feed_indexes:
        raise FirmwareVerificationError("Image Builder recorded no downloaded feed indexes")
    source_metadata = {
        IMAGEBUILDER_FILENAME: sha256_file(archive),
        PROFILES_FILENAME: sha256_file(profiles_path),
        SHA256SUMS_FILENAME: sha256_file(sums_path),
        "resolved-package-manifest": sha256_file(package_manifests[0]),
        "repositories": sha256_file(output / "repositories"),
    }
    manifest = build_manifest(
        artifact,
        resolved_packages=resolved,
        feed_indexes=feed_indexes,
        overlay=overlay_manifest,
        builder_image_id=image_id,
        containerfile_sha256=sha256_file(containerfile),
        source_metadata=source_metadata,
        embedded_metadata=embedded,
    )
    temporary_bundle = artifacts.with_name(artifacts.name + ".tmp")
    temporary_bundle.mkdir(parents=True, mode=0o700)
    published_artifact = temporary_bundle / artifact.name
    shutil.copy2(artifact, published_artifact)
    shutil.copy2(package_manifests[0], temporary_bundle / package_manifests[0].name)
    (temporary_bundle / "manifest.json").write_text(manifest.as_json())
    (temporary_bundle / f"{artifact.name}.sha256").write_text(
        f"{manifest.artifact_sha256}  {artifact.name}\n"
    )
    os.replace(temporary_bundle, artifacts)
    verify_firmware_bundle(
        artifacts,
        helper=repository / "infra/network/openwrt/files/usr/libexec/homeserver-uci",
        public_key=repository / "private_dot_ssh/id_ed25519.pub",
    )
    if archive_to is not None:
        return archive_firmware_bundle(
            artifacts,
            archive_to,
            work_root=work_root,
            helper=repository / "infra/network/openwrt/files/usr/libexec/homeserver-uci",
            public_key=repository / "private_dot_ssh/id_ed25519.pub",
        )
    return artifacts


def verify_manifest(
    manifest: Mapping[str, Any], artifact: Path, *, helper: Path, public_key: Path
) -> None:
    verify_artifact_name(artifact.name)
    expected = {
        "artifact": artifact.name,
        "artifact_size": artifact.stat().st_size,
        "artifact_sha256": sha256_file(artifact),
        "version": VERSION,
        "target": TARGET,
        "profile": PROFILE,
        "model": MODEL,
        "board": BOARD,
        "board_id": BOARD_ID,
        "imagebuilder_sha256": IMAGEBUILDER_SHA256,
        "builder_image": BUILDER_IMAGE,
        "requested_packages": list(REQUESTED_PACKAGES),
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise FirmwareVerificationError(f"manifest field mismatch: {key}")
    resolved = manifest.get("resolved_packages", {})
    if not isinstance(resolved, Mapping):
        raise FirmwareVerificationError("resolved package manifest is absent")
    package_names = set(resolved)
    missing = sorted(REQUIRED_PACKAGES - package_names)
    forbidden = sorted(FORBIDDEN_PACKAGES & package_names)
    if missing or forbidden:
        raise FirmwareVerificationError(
            f"package policy failed (missing={','.join(missing)} forbidden={','.join(forbidden)})"
        )
    feed_indexes = manifest.get("feed_indexes")
    if (
        not isinstance(feed_indexes, Mapping)
        or not feed_indexes
        or any(
            not isinstance(value, str) or not _SHA256.fullmatch(value)
            for value in feed_indexes.values()
        )
    ):
        raise FirmwareVerificationError("feed-index checksums are absent")
    overlay = manifest.get("overlay", {})
    if not isinstance(overlay, Mapping):
        raise FirmwareVerificationError("overlay manifest is absent")
    if overlay.get("usr/libexec/homeserver-uci") != sha256_file(helper):
        raise FirmwareVerificationError("tracked helper checksum differs from artifact manifest")
    key_digest = hashlib.sha256((public_key.read_text().strip() + "\n").encode()).hexdigest()
    if overlay.get("etc/dropbear/authorized_keys") != key_digest:
        raise FirmwareVerificationError(
            "managed public key checksum differs from artifact manifest"
        )
    embedded = read_fwtool_metadata(artifact)
    verify_embedded_metadata(embedded)
    if manifest.get("embedded_metadata") != embedded:
        raise FirmwareVerificationError("embedded artifact metadata differs from manifest")


def _verify_rootfs_overlay(
    artifact: Path,
    *,
    builder_image_id: str,
    helper: Path,
    public_key: Path,
) -> None:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", builder_image_id):
        raise FirmwareVerificationError("builder image ID is invalid")
    expected = {
        "etc/dropbear/authorized_keys": (public_key.read_text().strip() + "\n").encode(),
        "usr/libexec/homeserver-uci": helper.read_bytes(),
    }
    with tempfile.TemporaryDirectory(prefix=".verify-", dir=artifact.parent) as temporary:
        inspection = Path(temporary)
        root_image = inspection / "root.squashfs"
        root_name = f"sysupgrade-{PROFILE}/root"
        try:
            with tarfile.open(artifact, "r:") as archive:
                source = archive.extractfile(root_name)
                if source is None:
                    raise FirmwareVerificationError("sysupgrade rootfs is absent")
                with root_image.open("wb") as destination:
                    shutil.copyfileobj(source, destination)
        except (OSError, tarfile.TarError) as error:
            raise FirmwareVerificationError("cannot read sysupgrade rootfs") from error

        _run_bytes(
            (
                "docker",
                "run",
                "--rm",
                "--platform=linux/amd64",
                "--network=none",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--mount",
                f"type=bind,src={inspection},dst=/inspect",
                builder_image_id,
                "unsquashfs",
                "-no-progress",
                "-no-exit-code",
                "-d",
                "/inspect/rootfs",
                "/inspect/root.squashfs",
            )
        )
        rootfs = inspection / "rootfs"
        for relative, content in expected.items():
            installed = rootfs / relative
            if installed.read_bytes() != content:
                raise FirmwareVerificationError(f"artifact overlay content mismatch: {relative}")
        if stat.S_IMODE((rootfs / "etc/dropbear/authorized_keys").stat().st_mode) != 0o600:
            raise FirmwareVerificationError("artifact authorized_keys mode is not 0600")
        if stat.S_IMODE((rootfs / "usr/libexec/homeserver-uci").stat().st_mode) != 0o755:
            raise FirmwareVerificationError("artifact helper mode is not 0755")
        for path in rootfs.rglob("*"):
            if not stat.S_ISREG(path.lstat().st_mode):
                continue
            data = path.read_bytes()
            if b"\0" not in data[:4096] and any(marker in data for marker in _SECRET_MARKERS):
                relative = path.relative_to(rootfs).as_posix()
                raise FirmwareVerificationError(
                    f"artifact rootfs contains a secret marker: {relative}"
                )


def verify_firmware_bundle(bundle: Path, *, helper: Path, public_key: Path) -> Path:
    manifest_path = bundle / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise FirmwareVerificationError("firmware bundle manifest is unreadable") from error
    if not isinstance(manifest, Mapping) or not isinstance(manifest.get("artifact"), str):
        raise FirmwareVerificationError("firmware bundle manifest is invalid")
    artifact_name = str(manifest["artifact"])
    if Path(artifact_name).name != artifact_name:
        raise FirmwareVerificationError("firmware bundle artifact path is unsafe")
    artifact = bundle / artifact_name
    sidecar = bundle / f"{artifact_name}.sha256"
    expected_sidecar = f"{manifest.get('artifact_sha256')}  {artifact_name}\n"
    if sidecar.read_text() != expected_sidecar:
        raise FirmwareVerificationError("firmware checksum sidecar differs from manifest")
    verify_manifest(manifest, artifact, helper=helper, public_key=public_key)
    containerfile = helper.parents[3] / "Containerfile"
    if manifest.get("containerfile_sha256") != sha256_file(containerfile):
        raise FirmwareVerificationError("builder Containerfile differs from manifest")
    package_manifests = tuple(bundle.glob(f"*{PROFILE}.manifest"))
    if len(package_manifests) != 1:
        raise FirmwareVerificationError("resolved package sidecar is absent")
    source_metadata = manifest.get("source_metadata", {})
    if not isinstance(source_metadata, Mapping) or source_metadata.get(
        "resolved-package-manifest"
    ) != sha256_file(package_manifests[0]):
        raise FirmwareVerificationError("resolved package sidecar checksum mismatch")
    if _parse_package_manifest(package_manifests[0].read_text()) != manifest.get(
        "resolved_packages"
    ):
        raise FirmwareVerificationError("resolved package sidecar differs from manifest")
    builder_image_id = manifest.get("builder_image_id")
    if not isinstance(builder_image_id, str):
        raise FirmwareVerificationError("builder image ID is absent")
    _verify_rootfs_overlay(
        artifact,
        builder_image_id=builder_image_id,
        helper=helper,
        public_key=public_key,
    )
    return artifact
