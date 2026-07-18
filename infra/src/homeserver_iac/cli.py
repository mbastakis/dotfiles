from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from homeserver_iac.api_keys import (
    ApiKeyPublication,
    apply_api_key_publication,
    plan_api_key_publication,
)
from homeserver_iac.apple_photos import (
    ExportValidationError,
    HiddenAssetPolicy,
    ImmichApiClient,
    ImmichMetadataPlanError,
    ImportManifestError,
    build_immich_metadata_plan,
    build_import_manifest,
    reconcile_immich_metadata,
    serialize_export_validation,
    serialize_immich_metadata_plan,
    serialize_immich_metadata_reconcile,
    validate_export,
    write_export_validation_report,
    write_immich_metadata_plan,
    write_immich_metadata_reconcile_report,
    write_import_manifest,
)
from homeserver_iac.apps import (
    TrueNASAppFiles,
    apply_apps,
    load_app_declarations,
    plan_apps,
    read_apps_state,
)
from homeserver_iac.audiobookshelf import (
    DEFAULT_AUDIOBOOKSHELF_CONFIG,
    AudiobookshelfClient,
    apply_audiobookshelf,
    discover_openid,
    load_audiobookshelf_desired,
    plan_audiobookshelf,
    read_audiobookshelf_state,
)
from homeserver_iac.backrest import (
    DEFAULT_BACKREST_CONFIG,
    DEFAULT_BACKREST_URL,
    BackrestClient,
    apply_backrest,
    load_backrest_desired,
    plan_backrest,
)
from homeserver_iac.maintenance import (
    DEFAULT_MAINTENANCE_CONFIG,
    apply_maintenance,
    load_maintenance_desired,
    plan_maintenance,
    read_maintenance_state,
)
from homeserver_iac.models.common import ExitCode, Plan, order_operations, serialize_plan
from homeserver_iac.models.openwrt import OpenWrtDesiredState
from homeserver_iac.nfs import apply_nfs, load_nfs_desired, plan_nfs
from homeserver_iac.openwrt import (
    PROTECTED_STAGE_ORDER,
    OpenWrtSafetyError,
    OpenWrtSshClient,
    plan_openwrt,
    prove_timed_rollback,
    read_live_state,
    validate_safety,
)
from homeserver_iac.openwrt_controller import (
    TransactionJournal,
    apply_openwrt_all,
    apply_openwrt_stage,
    recover_pending_base,
    recover_pending_bootstrap_sanitize,
    recover_pending_stage_transaction,
    revert_openwrt_transaction,
    stage_changes_for_state,
)
from homeserver_iac.openwrt_firmware import (
    VERSION as OPENWRT_VERSION,
)
from homeserver_iac.openwrt_firmware import (
    FirmwareVerificationError,
    build_firmware,
    verify_firmware_bundle,
)
from homeserver_iac.openwrt_health import status_summary
from homeserver_iac.openwrt_operations import (
    ChezmoiCrypto,
    SshImageUploader,
    SshRemoteRunner,
    backup_config,
    backup_intermediary_mtd,
    clean_rebuild_firmware,
    rotate_root_password,
    scan_and_pin_host_key,
    upgrade_firmware,
    verify_encrypted_backup,
    verify_luci_https_login,
    write_backup_manifest,
)
from homeserver_iac.openwrt_reconcile import plan_stage_changes, validate_clean_image_transition
from homeserver_iac.runtime import OperationalError
from homeserver_iac.schema import INFRA_ROOT, SCHEMA_MODELS, generate_schemas
from homeserver_iac.secrets import (
    DEFAULT_SECRET_MAP,
    BwsClient,
    SecretResolver,
    list_secrets,
    list_targets,
    load_secret_metadata,
    render_env_file,
)
from homeserver_iac.smb import apply_smb, load_smb_desired, plan_smb
from homeserver_iac.snapshots import apply_snapshots, load_snapshot_desired, plan_snapshots
from homeserver_iac.syncthing import (
    SyncthingClient,
    SyncthingHost,
    SyncthingIgnoreFiles,
    apply_syncthing,
    load_syncthing_desired,
    plan_syncthing,
    read_syncthing_api_key,
    read_syncthing_state,
)
from homeserver_iac.truenas import MidcltClient
from homeserver_iac.validation import (
    DesiredStateValidationError,
    load_model,
    validate_desired_state,
)

DEFAULT_OPENWRT_CONFIG = INFRA_ROOT / "network/openwrt/router.yaml"
DEFAULT_OPENWRT_KNOWN_HOSTS = INFRA_ROOT.parent / ".local/openwrt/known_hosts"


def _wait_for_openwrt_reconnect(
    client: OpenWrtSshClient,
    *,
    timeout: float = 300,
    poll_interval: float = 5,
) -> None:
    if timeout <= 0 or poll_interval <= 0:
        raise ValueError("OpenWrt reconnect timing is invalid")
    deadline = time.monotonic() + timeout
    while True:
        try:
            client.read_json("board")
            return
        except OperationalError as error:
            if time.monotonic() >= deadline:
                raise OperationalError(
                    f"OpenWrt did not reconnect within {timeout:g}s after sysupgrade"
                ) from error
            time.sleep(poll_interval)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="homeserver-iac")
    commands = root.add_subparsers(dest="command", required=True)

    schema = commands.add_parser("schema")
    schema_commands = schema.add_subparsers(dest="schema_command", required=True)
    schema_commands.add_parser("generate")
    schema_commands.add_parser("check")

    desired = commands.add_parser("desired")
    desired_commands = desired.add_subparsers(dest="desired_command", required=True)
    validate = desired_commands.add_parser("validate")
    validate.add_argument("paths", nargs="*", type=Path)

    secrets = commands.add_parser("secrets")
    secrets.add_argument(
        "--config",
        type=Path,
        default=Path(os.environ.get("HOMESERVER_BWS_FILE", DEFAULT_SECRET_MAP)),
    )
    secret_commands = secrets.add_subparsers(dest="secrets_command", required=True)
    secret_commands.add_parser("list-targets")
    secret_commands.add_parser("list-secrets")
    render = secret_commands.add_parser("render-env")
    render.add_argument("target")
    render.add_argument("--output", required=True, type=Path)
    execute = secret_commands.add_parser("exec")
    execute.add_argument("target")
    execute.add_argument("exec_command", nargs=argparse.REMAINDER)

    snapshots = commands.add_parser("snapshots")
    snapshots.add_argument(
        "--config",
        type=Path,
        default=(
            Path(os.environ["SNAPSHOT_TASKS_CONFIG"])
            if os.environ.get("SNAPSHOT_TASKS_CONFIG")
            else None
        ),
    )
    snapshot_commands = snapshots.add_subparsers(dest="snapshots_command", required=True)
    for command_name in ("plan", "apply"):
        snapshot_command = snapshot_commands.add_parser(command_name)
        snapshot_command.add_argument(
            "--host", default=os.environ.get("TRUENAS_SSH_HOST", "truenas")
        )
        snapshot_command.add_argument("--prune", action="store_true")
        if command_name == "plan":
            snapshot_command.add_argument("--state-fixture", type=Path)

    nfs = commands.add_parser("nfs")
    nfs.add_argument(
        "--config",
        type=Path,
        default=(
            Path(os.environ["NFS_SHARES_CONFIG"]) if os.environ.get("NFS_SHARES_CONFIG") else None
        ),
    )
    nfs_commands = nfs.add_subparsers(dest="nfs_command", required=True)
    for command_name in ("plan", "apply"):
        nfs_command = nfs_commands.add_parser(command_name)
        nfs_command.add_argument("--host", default=os.environ.get("TRUENAS_SSH_HOST", "truenas"))
        if command_name == "plan":
            nfs_command.add_argument("--state-fixture", type=Path)

    smb = commands.add_parser("smb")
    smb.add_argument(
        "--config",
        type=Path,
        default=(
            Path(os.environ["SMB_SHARES_CONFIG"]) if os.environ.get("SMB_SHARES_CONFIG") else None
        ),
    )
    smb_commands = smb.add_subparsers(dest="smb_command", required=True)
    for command_name in ("plan", "apply"):
        smb_command = smb_commands.add_parser(command_name)
        smb_command.add_argument("--host", default=os.environ.get("TRUENAS_SSH_HOST", "truenas"))
        if command_name == "plan":
            smb_command.add_argument("--state-fixture", type=Path)

    backrest = commands.add_parser("backrest")
    backrest_commands = backrest.add_subparsers(dest="backrest_command", required=True)
    for command_name in ("validate", "plan", "apply"):
        backrest_command = backrest_commands.add_parser(command_name)
        backrest_command.add_argument(
            "--config",
            type=Path,
            default=(
                Path(os.environ["BACKREST_POLICY_CONFIG"])
                if os.environ.get("BACKREST_POLICY_CONFIG")
                else None
            ),
        )
        if command_name != "validate":
            backrest_command.add_argument(
                "--url", default=os.environ.get("BACKREST_URL", DEFAULT_BACKREST_URL)
            )
        if command_name == "plan":
            backrest_command.add_argument("--state-fixture", type=Path)

    maintenance = commands.add_parser("maintenance")
    maintenance.add_argument(
        "--config",
        type=Path,
        default=Path(os.environ.get("TRUENAS_MAINTENANCE_CONFIG", DEFAULT_MAINTENANCE_CONFIG)),
    )
    maintenance_commands = maintenance.add_subparsers(dest="maintenance_command", required=True)
    for command_name in ("plan", "apply"):
        maintenance_command = maintenance_commands.add_parser(command_name)
        maintenance_command.add_argument(
            "--host", default=os.environ.get("TRUENAS_SSH_HOST", "truenas")
        )
        if command_name == "plan":
            maintenance_command.add_argument("--state-fixture", type=Path)

    audiobookshelf = commands.add_parser("audiobookshelf")
    audiobookshelf.add_argument(
        "--config",
        type=Path,
        default=Path(os.environ.get("AUDIOBOOKSHELF_CONFIG", DEFAULT_AUDIOBOOKSHELF_CONFIG)),
    )
    audiobookshelf_commands = audiobookshelf.add_subparsers(
        dest="audiobookshelf_command", required=True
    )
    for command_name in ("validate", "plan", "apply"):
        audiobookshelf_command = audiobookshelf_commands.add_parser(command_name)
        if command_name != "validate":
            audiobookshelf_command.add_argument("--url")

    syncthing = commands.add_parser("syncthing")
    syncthing.add_argument(
        "--config",
        type=Path,
        default=(
            Path(os.environ["SYNCTHING_CONFIG"]) if os.environ.get("SYNCTHING_CONFIG") else None
        ),
    )
    syncthing_commands = syncthing.add_subparsers(dest="syncthing_command", required=True)
    for command_name in ("plan", "apply"):
        syncthing_command = syncthing_commands.add_parser(command_name)
        syncthing_command.add_argument("--host", choices=("mac", "truenas"), required=True)
        syncthing_command.add_argument(
            "--ssh-host", default=os.environ.get("TRUENAS_SSH_HOST", "truenas")
        )
        if command_name == "plan":
            syncthing_command.add_argument("--state-fixture", type=Path)

    apps = commands.add_parser("apps")
    apps.add_argument("--declarations", type=Path)
    app_commands = apps.add_subparsers(dest="apps_command", required=True)
    for command_name in ("plan", "apply"):
        app_command = app_commands.add_parser(command_name)
        app_command.add_argument("--host", default=os.environ.get("TRUENAS_SSH_HOST", "truenas"))
        if command_name == "plan":
            app_command.add_argument("--state-fixture", type=Path)
        app_command.add_argument("apps", nargs="*")

    api_key = commands.add_parser("api-key")
    api_key_commands = api_key.add_subparsers(dest="api_key_command", required=True)
    for command_name in ("plan", "apply"):
        api_key_command = api_key_commands.add_parser(command_name)
        api_key_command.add_argument("--name", default="homepage-dashboard")
        api_key_command.add_argument("--username", default="mbastakis")
        api_key_command.add_argument("--secret-alias", default="truenas_api_key")
        api_key_command.add_argument("--secret-key")
        api_key_command.add_argument("--project-id")
        api_key_command.add_argument(
            "--host", default=os.environ.get("TRUENAS_SSH_HOST", "truenas")
        )
        api_key_command.add_argument("--port", type=int)
        if command_name == "plan":
            api_key_command.add_argument("--state-fixture", type=Path)

    openwrt = commands.add_parser("openwrt")
    openwrt_commands = openwrt.add_subparsers(dest="openwrt_command", required=True)
    firmware = openwrt_commands.add_parser("firmware")
    firmware_commands = firmware.add_subparsers(dest="firmware_command", required=True)
    firmware_build = firmware_commands.add_parser("build")
    firmware_build.add_argument(
        "--work-dir", type=Path, default=INFRA_ROOT.parent / ".local/openwrt"
    )
    firmware_build.add_argument(
        "--archive-to",
        type=Path,
        help="new bundle path on a second private storage location",
    )
    firmware_verify = firmware_commands.add_parser("verify")
    firmware_verify.add_argument(
        "--bundle",
        type=Path,
        default=INFRA_ROOT.parent / f".local/openwrt/artifacts/{OPENWRT_VERSION}/homeserver",
    )

    def add_openwrt_connection(command: argparse.ArgumentParser, *, proxy: bool = False) -> None:
        command.add_argument("--config", type=Path, default=DEFAULT_OPENWRT_CONFIG)
        command.add_argument("--host", default="root@192.168.1.1")
        command.add_argument("--known-hosts", type=Path, default=DEFAULT_OPENWRT_KNOWN_HOSTS)
        command.add_argument("--identity", type=Path, default=Path.home() / ".ssh/id_ed25519")
        command.add_argument("--connect-timeout", type=int, default=10)
        command.add_argument("--command-timeout", type=int, default=60)
        if proxy:
            command.add_argument("--proxy-jump")

    bootstrap = openwrt_commands.add_parser("bootstrap")
    add_openwrt_connection(bootstrap)
    bootstrap_mode = bootstrap.add_mutually_exclusive_group()
    bootstrap_mode.add_argument("--inspect-clean-image-only", action="store_true")
    bootstrap_mode.add_argument("--pin-host-key-only", action="store_true")
    bootstrap_mode.add_argument("--prepare-clean-rebuild", action="store_true")
    bootstrap_mode.add_argument("--test-rollback-only", action="store_true")
    bootstrap_mode.add_argument("--recover-pending-sanitize-only", action="store_true")
    bootstrap_mode.add_argument("--recover-pending-base-only", action="store_true")
    bootstrap_mode.add_argument("--rotate-root-password-only", action="store_true")
    openwrt_plan = openwrt_commands.add_parser("plan")
    add_openwrt_connection(openwrt_plan, proxy=True)
    openwrt_plan.add_argument("--state-fixture", type=Path)
    openwrt_plan.add_argument("--stage", choices=(*PROTECTED_STAGE_ORDER, "all"))
    openwrt_apply = openwrt_commands.add_parser("apply")
    add_openwrt_connection(openwrt_apply)
    apply_mode = openwrt_apply.add_mutually_exclusive_group(required=True)
    apply_mode.add_argument("--stage", choices=(*PROTECTED_STAGE_ORDER, "all"))
    apply_mode.add_argument("--revert")
    apply_mode.add_argument("--recover-pending")
    openwrt_status = openwrt_commands.add_parser("status")
    add_openwrt_connection(openwrt_status, proxy=True)
    openwrt_status.add_argument("--expect-wan-down", action="store_true")
    openwrt_backup = openwrt_commands.add_parser("backup")
    add_openwrt_connection(openwrt_backup, proxy=True)
    openwrt_backup.add_argument("--kind", choices=("config", "mtd"), required=True)
    openwrt_backup.add_argument("--output-dir", type=Path)
    openwrt_backup.add_argument("--recovery-workflow", action="store_true")
    openwrt_upgrade = openwrt_commands.add_parser("upgrade")
    add_openwrt_connection(openwrt_upgrade)
    openwrt_upgrade.add_argument("--image", required=True, type=Path)
    openwrt_clean_rebuild = openwrt_commands.add_parser("clean-rebuild")
    add_openwrt_connection(openwrt_clean_rebuild)
    openwrt_clean_rebuild.add_argument("--image", required=True, type=Path)
    openwrt_clean_rebuild.add_argument("--confirm", required=True, choices=("CLEAN-REBUILD",))

    photos = commands.add_parser("photos")
    photo_commands = photos.add_subparsers(dest="photos_command", required=True)
    validate_photos = photo_commands.add_parser("validate-export")
    validate_photos.add_argument("export_root", type=Path)
    validate_photos.add_argument("--report", type=Path)
    validate_photos.add_argument("--checkpoint", type=Path)
    validate_photos.add_argument("--workers", type=int, default=1)
    validate_photos.add_argument("--ffmpeg-hwaccel")
    validate_photos.add_argument("--command-timeout", type=float, default=10800.0)
    import_manifest = photo_commands.add_parser("build-import-manifest")
    import_manifest.add_argument("validation_report", type=Path)
    import_manifest.add_argument("--source-manifest", action="append", required=True, type=Path)
    import_manifest.add_argument("--output", required=True, type=Path)
    metadata_plan = photo_commands.add_parser("plan-immich-metadata")
    metadata_plan.add_argument("import_manifest", type=Path)
    metadata_plan.add_argument("--upload-results", required=True, type=Path)
    metadata_plan.add_argument("--output", type=Path)
    metadata_plan.add_argument(
        "--hidden-policy",
        choices=tuple(policy.value for policy in HiddenAssetPolicy),
        default=HiddenAssetPolicy.BLOCK.value,
    )
    metadata_reconcile = photo_commands.add_parser("reconcile-immich-metadata")
    metadata_reconcile.add_argument("metadata_plan", type=Path)
    metadata_reconcile.add_argument(
        "--api-url",
        default=os.environ.get("IMMICH_API_URL", "https://photos.mbastakis.com"),
    )
    metadata_reconcile.add_argument("--api-key-env", default="IMMICH_API_KEY")
    metadata_reconcile.add_argument("--output", type=Path)
    metadata_reconcile.add_argument("--timeout", type=float, default=20.0)
    metadata_reconcile.add_argument("--apply", action="store_true")
    return root


def relative(path: Path) -> Path:
    try:
        return path.resolve().relative_to(INFRA_ROOT.parent)
    except ValueError:
        return path


_OPENWRT_SECRET_ENV = {
    "openwrt_pppoe_username": "OPENWRT_PPPOE_USERNAME",
    "openwrt_pppoe_password": "OPENWRT_PPPOE_PASSWORD",
    "openwrt_root_password": "OPENWRT_ROOT_PASSWORD",
    "openwrt_main_wifi_ssid": "OPENWRT_MAIN_WIFI_SSID",
    "openwrt_main_wifi_psk": "OPENWRT_MAIN_WIFI_PSK",
    "openwrt_guest_wifi_ssid": "OPENWRT_GUEST_WIFI_SSID",
    "openwrt_guest_wifi_psk": "OPENWRT_GUEST_WIFI_PSK",
}


def _resolve_openwrt_secret(alias: str) -> str:
    try:
        environment = _OPENWRT_SECRET_ENV[alias]
    except KeyError as error:
        raise OpenWrtSafetyError(f"unknown OpenWrt secret alias: {alias}") from error
    value = os.environ.get(environment, "")
    if not value:
        raise OperationalError(f"OpenWrt secret environment is absent: {environment}")
    return value


def _openwrt_journal(crypto: ChezmoiCrypto) -> TransactionJournal:
    return TransactionJournal(
        INFRA_ROOT.parent / ".local/openwrt/transactions",
        encryptor=crypto,
        decryptor=crypto,
    )


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "schema":
            check = args.schema_command == "check"
            changed = generate_schemas(check=check)
            if check and changed:
                for path in changed:
                    print(f"outdated schema: {relative(path)}", file=sys.stderr)
                return ExitCode.VALIDATION_FAILURE
            action = "checked" if check else "generated"
            count = len(SCHEMA_MODELS) if check else len(changed)
            print(f"{action} {count} JSON Schemas")
            return ExitCode.VALID

        if args.command == "desired" and args.desired_command == "validate":
            paths = tuple(path.resolve() for path in args.paths) if args.paths else None
            validated = validate_desired_state(paths)
            for path in validated:
                print(f"valid: {relative(path)}")
            return ExitCode.VALID

        if args.command == "openwrt":
            if args.openwrt_command == "firmware":
                if args.firmware_command == "build":
                    bundle = build_firmware(
                        INFRA_ROOT.parent,
                        args.work_dir,
                        archive_to=args.archive_to,
                    )
                    action = "archived" if args.archive_to is not None else "built"
                    print(f"{action} firmware bundle: {bundle}")
                    return ExitCode.VALID
                artifact = verify_firmware_bundle(
                    args.bundle,
                    helper=INFRA_ROOT / "network/openwrt/files/usr/libexec/homeserver-uci",
                    public_key=INFRA_ROOT.parent / "private_dot_ssh/id_ed25519.pub",
                )
                print(f"valid firmware: {artifact}")
                return ExitCode.VALID

            desired_openwrt = load_model(args.config, OpenWrtDesiredState)
            if args.openwrt_command == "plan" and args.state_fixture:
                current_openwrt = json.loads(args.state_fixture.read_text())
                if not isinstance(current_openwrt, Mapping):
                    raise DesiredStateValidationError("OpenWrt state fixture must be an object")
                openwrt_result = plan_openwrt(desired_openwrt, current_openwrt, stage=args.stage)
                print(serialize_plan(openwrt_result), end="")
                return openwrt_result.exit_code

            openwrt_client = OpenWrtSshClient(
                host=args.host,
                known_hosts=args.known_hosts,
                identity=args.identity,
                connect_timeout=args.connect_timeout,
                command_timeout=args.command_timeout,
                proxy_jump=getattr(args, "proxy_jump", None),
            )
            remote = SshRemoteRunner(openwrt_client)
            crypto = ChezmoiCrypto()
            journal = _openwrt_journal(crypto)

            def state_reader() -> Mapping[str, Any]:
                return read_live_state(openwrt_client)

            def config_archive() -> bytes:
                return b"".join(remote.stream(("sysupgrade", "-b", "-"), timeout=300))

            if args.openwrt_command == "plan":
                current_openwrt = state_reader()
                validate_safety(desired_openwrt, current_openwrt)
                stages = PROTECTED_STAGE_ORDER if args.stage in {None, "all"} else (args.stage,)
                operations: list[Any] = []
                for stage in stages:
                    changes = stage_changes_for_state(
                        desired=desired_openwrt,
                        client=openwrt_client,
                        state=current_openwrt,
                        stage=stage,
                        resolve_secret=_resolve_openwrt_secret,
                        accepted_stages=tuple(item.stage for item in journal.accepted()),
                    )
                    operations.extend(plan_stage_changes(changes).operations)
                openwrt_result = Plan(operations=order_operations(operations))
                print(serialize_plan(openwrt_result), end="")
                return openwrt_result.exit_code
            if args.openwrt_command == "status":
                current_openwrt = state_reader()
                validate_safety(desired_openwrt, current_openwrt)
                runtime = current_openwrt.get("runtime", {})
                if args.expect_wan_down and isinstance(runtime, Mapping):
                    wan = runtime.get("wan", {})
                    wan6 = runtime.get("wan6", {})
                    if (isinstance(wan, Mapping) and wan.get("up") is True) or (
                        isinstance(wan6, Mapping) and wan6.get("up") is True
                    ):
                        raise OpenWrtSafetyError("WAN is up while --expect-wan-down is set")
                summary = status_summary(current_openwrt)
                status_stages = summary.get("stages")
                if (
                    isinstance(status_stages, dict)
                    and journal.latest("bootstrap-sanitize") is not None
                ):
                    status_stages["bootstrap-sanitize"] = True
                if args.expect_wan_down:
                    summary["wan_expected_down"] = True
                print(json.dumps(summary, indent=2, sort_keys=True))
                return ExitCode.VALID
            if args.openwrt_command == "bootstrap":
                if args.rotate_root_password_only:
                    root_password = _resolve_openwrt_secret("openwrt_root_password")
                    rotate_root_password(
                        remote=remote,
                        password=root_password,
                    )
                    verify_luci_https_login(
                        host=args.host.split("@", 1)[-1], password=root_password
                    )
                    print("rotated OpenWrt root password")
                    return ExitCode.VALID
                scan_host = args.host.split("@", 1)[-1]

                if args.prepare_clean_rebuild and journal.pending():
                    raise OpenWrtSafetyError(
                        "clean-rebuild preparation refuses pending transactions"
                    )

                def confirm_host_key(pin: object) -> bool:
                    fingerprint = getattr(pin, "fingerprint", "")
                    print(f"directly wired OpenWrt host key: {fingerprint}", file=sys.stderr)
                    print("Confirm directly connected Cudy [yes/no]: ", end="", file=sys.stderr)
                    return input().strip().lower() == "yes"

                scan_and_pin_host_key(
                    host=scan_host,
                    known_hosts=args.known_hosts,
                    confirm=confirm_host_key,
                    replace_existing=args.prepare_clean_rebuild,
                )
                current_openwrt = state_reader()
                if args.prepare_clean_rebuild:
                    validate_safety(desired_openwrt, current_openwrt, allow_prebase_management=True)
                    snapshot = current_openwrt.get("uci", {})
                    if not isinstance(snapshot, Mapping):
                        raise OpenWrtSafetyError("clean-image UCI snapshot is invalid")
                    validate_clean_image_transition(snapshot, sanitized=False)
                    generation = journal.archive_generation()
                    archived = generation.name if generation is not None else "empty lineage"
                    print(f"prepared clean OpenWrt bootstrap generation: {archived}")
                    return ExitCode.VALID
                if args.inspect_clean_image_only:
                    snapshot = current_openwrt.get("uci", {})
                    diagnostic_prefixes = (
                        "system.",
                        "network.",
                        "wireless.",
                        "dropbear.",
                        "uhttpd.",
                    )
                    diagnostic_suffixes = (
                        "._type",
                        ".band",
                        ".channel",
                        ".disabled",
                        ".Interface",
                        ".PasswordAuth",
                        ".RootPasswordAuth",
                        ".listen_http",
                        ".listen_https",
                        ".redirect_https",
                        ".hostname",
                        ".timezone",
                        ".zonename",
                        ".device",
                        ".proto",
                        ".ipaddr",
                        ".netmask",
                    )
                    diagnostic_uci = (
                        {
                            str(path): value
                            for path, value in snapshot.items()
                            if isinstance(path, str)
                            and path.startswith(diagnostic_prefixes)
                            and path.endswith(diagnostic_suffixes)
                        }
                        if isinstance(snapshot, Mapping)
                        else {}
                    )
                    print(
                        json.dumps(
                            {
                                "firewall": current_openwrt.get("firewall"),
                                "identity": current_openwrt.get("identity"),
                                "listeners": current_openwrt.get("listeners"),
                                "radio_bands": current_openwrt.get("runtime", {}).get(
                                    "radio_bands"
                                ),
                                "uci": diagnostic_uci,
                            },
                            indent=2,
                            sort_keys=True,
                        )
                    )
                    return ExitCode.VALID
                validate_safety(
                    desired_openwrt,
                    current_openwrt,
                    allow_prebase_management=journal.latest("base") is None,
                )
                if args.pin_host_key_only:
                    print("pinned and validated directly wired OpenWrt identity")
                    return ExitCode.VALID
                if args.test_rollback_only:
                    elapsed = prove_timed_rollback(
                        openwrt_client,
                        lock_path=INFRA_ROOT.parent / ".local/openwrt/apply.lock",
                        controller_id=f"rollback-proof-{os.getpid()}",
                    )
                    print(f"proved rpcd timed rollback in {elapsed:.1f} seconds")
                    return ExitCode.VALID
                if args.recover_pending_sanitize_only:
                    recovered = recover_pending_bootstrap_sanitize(
                        desired=desired_openwrt,
                        client=openwrt_client,
                        state_reader=state_reader,
                        journal=journal,
                    )
                    print(f"recovered pending OpenWrt transaction: {recovered.transaction_id}")
                    return ExitCode.VALID
                if args.recover_pending_base_only:
                    recovered = recover_pending_base(
                        desired=desired_openwrt,
                        client=openwrt_client,
                        state_reader=state_reader,
                        journal=journal,
                    )
                    print(f"recovered pending OpenWrt transaction: {recovered.transaction_id}")
                    return ExitCode.VALID
                bootstrap_stages = (
                    ("base",)
                    if journal.latest("bootstrap-sanitize") is not None
                    else ("bootstrap-sanitize", "base")
                )
                for stage in bootstrap_stages:
                    apply_openwrt_stage(
                        desired=desired_openwrt,
                        client=openwrt_client,
                        state_reader=state_reader,
                        resolve_secret=_resolve_openwrt_secret,
                        config_archive=config_archive,
                        journal=journal,
                        stage=stage,
                        lock_path=INFRA_ROOT.parent / ".local/openwrt/apply.lock",
                        controller_id=f"bootstrap-{os.getpid()}",
                    )
                root_password = _resolve_openwrt_secret("openwrt_root_password")
                rotate_root_password(remote=remote, password=root_password)
                verify_luci_https_login(host=scan_host, password=root_password)
                print("bootstrapped OpenWrt base configuration")
                return ExitCode.VALID
            if args.openwrt_command == "apply":
                if args.recover_pending:
                    terminal_recovery = recover_pending_stage_transaction(
                        desired=desired_openwrt,
                        client=openwrt_client,
                        state_reader=state_reader,
                        journal=journal,
                        transaction_id=args.recover_pending,
                    )
                    print(
                        "recovered pending OpenWrt transaction: "
                        f"{terminal_recovery.transaction_id} "
                        f"({terminal_recovery.stage}, {terminal_recovery.outcome})"
                    )
                    return ExitCode.VALID
                if args.revert:
                    revert_result = revert_openwrt_transaction(
                        desired=desired_openwrt,
                        client=openwrt_client,
                        state_reader=state_reader,
                        config_archive=config_archive,
                        journal=journal,
                        transaction_id=args.revert,
                        lock_path=INFRA_ROOT.parent / ".local/openwrt/apply.lock",
                        controller_id=f"revert-{os.getpid()}",
                    )
                    print(f"reverted OpenWrt transaction: {args.revert} ({revert_result.stage})")
                    return ExitCode.VALID
                if args.stage == "all":
                    results = apply_openwrt_all(
                        desired=desired_openwrt,
                        client=openwrt_client,
                        state_reader=state_reader,
                        resolve_secret=_resolve_openwrt_secret,
                        config_archive=config_archive,
                        journal=journal,
                        lock_path=INFRA_ROOT.parent / ".local/openwrt/apply.lock",
                        controller_id=f"apply-{os.getpid()}",
                    )
                    applied_count = sum(result.apply is not None for result in results)
                    print(f"applied {applied_count} protected OpenWrt transactions")
                else:
                    stage_result = apply_openwrt_stage(
                        desired=desired_openwrt,
                        client=openwrt_client,
                        state_reader=state_reader,
                        resolve_secret=_resolve_openwrt_secret,
                        config_archive=config_archive,
                        journal=journal,
                        stage=args.stage,
                        lock_path=INFRA_ROOT.parent / ".local/openwrt/apply.lock",
                        controller_id=f"apply-{os.getpid()}",
                    )
                    action = "applied" if stage_result.apply is not None else "converged"
                    print(f"{action} OpenWrt stage: {args.stage}")
                return ExitCode.VALID
            if args.openwrt_command == "backup":
                timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
                if args.kind == "config":
                    backup_state = state_reader()
                    identity = backup_state["identity"]
                    validate_safety(desired_openwrt, backup_state)
                output_dir = args.output_dir or (
                    INFRA_ROOT.parent / ".local/openwrt/backups/cudy-wr3000e-v1"
                )
                records: tuple[Any, ...]
                if args.kind == "config":
                    metadata = backup_config(
                        remote=remote,
                        encryptor=crypto,
                        destination=output_dir / f"config-{timestamp}.tar.age",
                        proxy_jump=args.proxy_jump,
                    )
                    records = (metadata,)
                    board = str(identity["board_name"])
                    release = str(identity["release"])
                else:
                    result = backup_intermediary_mtd(
                        remote=remote,
                        encryptor=crypto,
                        destination_dir=output_dir / f"mtd-{timestamp}",
                        proxy_jump=args.proxy_jump,
                        recovery_workflow=args.recovery_workflow,
                    )
                    records = result.records
                    board = result.board
                    release = result.release
                for record in records:
                    verify_encrypted_backup(
                        source=(
                            output_dir / record.filename
                            if args.kind == "config"
                            else output_dir / f"mtd-{timestamp}" / record.filename
                        ),
                        decryptor=crypto,
                        expected_size=record.plaintext_size,
                        expected_sha256=record.plaintext_sha256,
                    )
                write_backup_manifest(
                    path=output_dir / f"{args.kind}-{timestamp}-manifest.json",
                    board=board,
                    release=release,
                    timestamp=datetime.now(UTC).isoformat(),
                    records=records,
                )
                print(json.dumps([record.__dict__ for record in records], indent=2, sort_keys=True))
                return ExitCode.VALID
            if args.openwrt_command == "upgrade":
                verified_image = verify_firmware_bundle(
                    args.image.parent,
                    helper=INFRA_ROOT / "network/openwrt/files/usr/libexec/homeserver-uci",
                    public_key=INFRA_ROOT.parent / "private_dot_ssh/id_ed25519.pub",
                )
                if verified_image.resolve() != args.image.resolve():
                    raise OpenWrtSafetyError("upgrade image is not the verified bundle artifact")
                digest = hashlib.sha256(args.image.read_bytes()).hexdigest()
                timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

                def reconnect_after_upgrade() -> None:
                    _wait_for_openwrt_reconnect(openwrt_client)

                def backup_before_upgrade() -> object:
                    destination = (
                        INFRA_ROOT.parent
                        / f".local/openwrt/backups/cudy-wr3000e-v1/pre-upgrade-{timestamp}.tar.age"
                    )
                    metadata = backup_config(
                        remote=remote,
                        encryptor=crypto,
                        destination=destination,
                    )
                    verify_encrypted_backup(
                        source=destination,
                        decryptor=crypto,
                        expected_size=metadata.plaintext_size,
                        expected_sha256=metadata.plaintext_sha256,
                    )
                    pre_upgrade_state = state_reader()
                    pre_upgrade_identity = pre_upgrade_state["identity"]
                    write_backup_manifest(
                        path=destination.with_name(f"pre-upgrade-{timestamp}-manifest.json"),
                        board=str(pre_upgrade_identity["board_name"]),
                        release=str(pre_upgrade_identity["release"]),
                        timestamp=datetime.now(UTC).isoformat(),
                        records=(metadata,),
                    )
                    return metadata

                def validate_after_upgrade() -> None:
                    upgraded_state = state_reader()
                    validate_safety(desired_openwrt, upgraded_state)
                    apply_openwrt_all(
                        desired=desired_openwrt,
                        client=openwrt_client,
                        state_reader=state_reader,
                        resolve_secret=_resolve_openwrt_secret,
                        config_archive=config_archive,
                        journal=journal,
                        lock_path=INFRA_ROOT.parent / ".local/openwrt/apply.lock",
                        controller_id=f"upgrade-{os.getpid()}",
                    )
                    status_summary(state_reader())

                upgrade_result = upgrade_firmware(
                    remote=remote,
                    upload=SshImageUploader(openwrt_client),
                    image=args.image,
                    expected_sha256=digest,
                    backup=backup_before_upgrade,
                    reconnect=reconnect_after_upgrade,
                    validate=validate_after_upgrade,
                )
                print(f"upgraded OpenWrt image: {upgrade_result.image_sha256}")
                return ExitCode.VALID
            if args.openwrt_command == "clean-rebuild":
                verified_image = verify_firmware_bundle(
                    args.image.parent,
                    helper=INFRA_ROOT / "network/openwrt/files/usr/libexec/homeserver-uci",
                    public_key=INFRA_ROOT.parent / "private_dot_ssh/id_ed25519.pub",
                )
                if verified_image.resolve() != args.image.resolve():
                    raise OpenWrtSafetyError(
                        "clean-rebuild image is not the verified bundle artifact"
                    )
                current_state = state_reader()
                validate_safety(desired_openwrt, current_state)
                digest = hashlib.sha256(args.image.read_bytes()).hexdigest()
                timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

                def backup_before_clean_rebuild() -> object:
                    destination = (
                        INFRA_ROOT.parent
                        / f".local/openwrt/backups/cudy-wr3000e-v1/pre-clean-{timestamp}.tar.age"
                    )
                    metadata = backup_config(
                        remote=remote,
                        encryptor=crypto,
                        destination=destination,
                    )
                    verify_encrypted_backup(
                        source=destination,
                        decryptor=crypto,
                        expected_size=metadata.plaintext_size,
                        expected_sha256=metadata.plaintext_sha256,
                    )
                    identity = current_state["identity"]
                    write_backup_manifest(
                        path=destination.with_name(f"pre-clean-{timestamp}-manifest.json"),
                        board=str(identity["board_name"]),
                        release=str(identity["release"]),
                        timestamp=datetime.now(UTC).isoformat(),
                        records=(metadata,),
                    )
                    return metadata

                clean_result = clean_rebuild_firmware(
                    remote=remote,
                    upload=SshImageUploader(openwrt_client),
                    image=args.image,
                    expected_sha256=digest,
                    backup=backup_before_clean_rebuild,
                    confirmed=args.confirm == "CLEAN-REBUILD",
                )
                print(f"clean-flashed OpenWrt image: {clean_result.image_sha256}")
                return ExitCode.VALID

        if args.command == "photos" and args.photos_command == "validate-export":
            last_progress = -1

            def report_validation_progress(completed: int, total: int, resumed: int) -> None:
                nonlocal last_progress
                progress_bucket = completed // 100
                if completed not in (resumed, total) and progress_bucket == last_progress:
                    return
                last_progress = progress_bucket
                print(
                    f"validated {completed}/{total} media files ({resumed} resumed)",
                    file=sys.stderr,
                    flush=True,
                )

            report = validate_export(
                args.export_root,
                command_timeout=args.command_timeout,
                workers=args.workers,
                checkpoint_path=args.checkpoint,
                ffmpeg_hwaccel=args.ffmpeg_hwaccel,
                progress=report_validation_progress,
            )
            if args.report:
                write_export_validation_report(report, args.report)
                print(f"wrote validation report: {args.report}", file=sys.stderr)
            else:
                print(serialize_export_validation(report), end="")
            return ExitCode.VALID if report.valid else ExitCode.VALIDATION_FAILURE

        if args.command == "photos" and args.photos_command == "build-import-manifest":
            manifest = build_import_manifest(
                args.validation_report,
                args.source_manifest,
            )
            write_import_manifest(manifest, args.output)
            print(f"wrote import manifest: {args.output}", file=sys.stderr)
            return ExitCode.VALID if manifest.valid else ExitCode.VALIDATION_FAILURE

        if args.command == "photos" and args.photos_command == "plan-immich-metadata":
            metadata_plan_result = build_immich_metadata_plan(
                args.import_manifest,
                args.upload_results,
                hidden_policy=HiddenAssetPolicy(args.hidden_policy),
            )
            if args.output:
                write_immich_metadata_plan(metadata_plan_result, args.output)
                print(f"wrote Immich metadata plan: {args.output}", file=sys.stderr)
            else:
                print(serialize_immich_metadata_plan(metadata_plan_result), end="")
            return ExitCode.VALID if metadata_plan_result.valid else ExitCode.VALIDATION_FAILURE

        if args.command == "photos" and args.photos_command == "reconcile-immich-metadata":
            api_key = os.environ.get(args.api_key_env, "")
            if not api_key:
                raise OperationalError(f"set {args.api_key_env} to a short-lived Immich API key")
            immich_client = ImmichApiClient(args.api_url, api_key, timeout=args.timeout)
            metadata_reconcile_result = reconcile_immich_metadata(
                args.metadata_plan,
                immich_client,
                api_base_url=args.api_url,
                apply_changes=args.apply,
            )
            if args.output:
                write_immich_metadata_reconcile_report(metadata_reconcile_result, args.output)
                print(f"wrote Immich metadata reconcile report: {args.output}", file=sys.stderr)
            else:
                print(serialize_immich_metadata_reconcile(metadata_reconcile_result), end="")
            if not metadata_reconcile_result.valid:
                return ExitCode.VALIDATION_FAILURE
            if metadata_reconcile_result.has_pending and not args.apply:
                return ExitCode.DRIFT
            return ExitCode.VALID

        if args.command == "secrets":
            secret_desired = load_secret_metadata(args.config)
            if args.secrets_command == "list-targets":
                for target in list_targets(secret_desired):
                    print(target)
                return ExitCode.VALID
            if args.secrets_command == "list-secrets":
                for alias, key, secret_id in list_secrets(secret_desired):
                    print(f"{alias}\t{key}\t{secret_id}")
                return ExitCode.VALID

            resolver = SecretResolver(secret_desired, BwsClient())
            values = resolver.target_environment(args.target)
            if args.secrets_command == "render-env":
                render_env_file(args.target, values, args.output)
                print(f"rendered restricted env file: {args.output}", file=sys.stderr)
                return ExitCode.VALID
            if args.secrets_command == "exec":
                command = list(args.exec_command)
                if command and command[0] == "--":
                    command.pop(0)
                if not command:
                    raise DesiredStateValidationError("secrets exec requires a command after --")
                environment = os.environ.copy()
                environment.update(values)
                os.execvpe(command[0], command, environment)

        if args.command == "snapshots":
            snapshot_desired = (
                load_snapshot_desired(args.config) if args.config else load_snapshot_desired()
            )
            if args.snapshots_command == "plan" and args.state_fixture:
                current = json.loads(args.state_fixture.read_text())
            else:
                current = MidcltClient(args.host).call("pool.snapshottask.query")
            if not isinstance(current, list) or not all(isinstance(item, dict) for item in current):
                raise OperationalError("TrueNAS snapshot query returned an unexpected response")
            if args.snapshots_command == "plan":
                plan = plan_snapshots(snapshot_desired, current, prune=args.prune)
                print(serialize_plan(plan), end="")
                return plan.exit_code
            client = MidcltClient(args.host, command_timeout=300.0)
            plan = apply_snapshots(snapshot_desired, current, client, prune=args.prune)
            print(serialize_plan(plan), end="")
            return ExitCode.VALID

        if args.command == "nfs":
            nfs_desired = load_nfs_desired(args.config) if args.config else load_nfs_desired()
            if args.nfs_command == "plan" and args.state_fixture:
                nfs_current = json.loads(args.state_fixture.read_text())
                nfs_client = None
                current_service = nfs_current.get("service", {})
                current_shares = nfs_current.get("shares", [])
            else:
                nfs_client = MidcltClient(args.host)
                services = nfs_client.call("service.query", [["service", "=", "nfs"]])
                if not isinstance(services, list) or len(services) != 1:
                    raise OperationalError(
                        "TrueNAS NFS service query returned an unexpected response"
                    )
                current_service = services[0]
                current_shares = nfs_client.call("sharing.nfs.query")
            if not isinstance(current_service, dict) or not isinstance(current_shares, list):
                raise OperationalError("TrueNAS NFS state is invalid")
            if not all(isinstance(item, dict) for item in current_shares):
                raise OperationalError("TrueNAS NFS share query returned an unexpected response")
            if args.nfs_command == "plan":
                nfs_plan = plan_nfs(nfs_desired, current_service, current_shares)
                print(serialize_plan(nfs_plan), end="")
                return nfs_plan.exit_code
            if nfs_client is None:
                raise OperationalError("NFS apply requires a live client")
            nfs_plan = apply_nfs(nfs_desired, current_service, current_shares, nfs_client)
            print(serialize_plan(nfs_plan), end="")
            return ExitCode.VALID

        if args.command == "smb":
            smb_desired = load_smb_desired(args.config) if args.config else load_smb_desired()
            if args.smb_command == "plan" and args.state_fixture:
                smb_current = json.loads(args.state_fixture.read_text())
                smb_client = None
                current_service = smb_current.get("service", {})
                current_shares = smb_current.get("shares", [])
            else:
                smb_client = MidcltClient(args.host)
                services = smb_client.call("service.query", [["service", "=", "cifs"]])
                if not isinstance(services, list) or len(services) != 1:
                    raise OperationalError(
                        "TrueNAS SMB service query returned an unexpected response"
                    )
                current_service = services[0]
                current_shares = smb_client.call("sharing.smb.query")
            if not isinstance(current_service, dict) or not isinstance(current_shares, list):
                raise OperationalError("TrueNAS SMB state is invalid")
            if not all(isinstance(item, dict) for item in current_shares):
                raise OperationalError("TrueNAS SMB share query returned an unexpected response")
            if args.smb_command == "plan":
                smb_plan = plan_smb(smb_desired, current_service, current_shares)
                print(serialize_plan(smb_plan), end="")
                return smb_plan.exit_code
            if smb_client is None:
                raise OperationalError("SMB apply requires a live client")
            smb_plan = apply_smb(smb_desired, current_service, current_shares, smb_client)
            print(serialize_plan(smb_plan), end="")
            return ExitCode.VALID

        if args.command == "backrest":
            backrest_desired = (
                load_backrest_desired(args.config) if args.config else load_backrest_desired()
            )
            if args.backrest_command == "validate":
                backrest_path = args.config or DEFAULT_BACKREST_CONFIG
                print(f"valid: {relative(backrest_path)}")
                return ExitCode.VALID
            if args.backrest_command == "plan" and args.state_fixture:
                backrest_current = json.loads(args.state_fixture.read_text())
                backrest_client = None
            else:
                backrest_client = BackrestClient.from_environment(args.url)
                backrest_current = backrest_client.get_config()
            if not isinstance(backrest_current, dict):
                raise OperationalError("Backrest config query returned an unexpected response")
            if args.backrest_command == "plan":
                backrest_plan = plan_backrest(backrest_desired, backrest_current)
                print(serialize_plan(backrest_plan), end="")
                return backrest_plan.exit_code
            if backrest_client is None:
                raise OperationalError("Backrest apply requires a live client")
            backrest_plan = apply_backrest(backrest_desired, backrest_current, backrest_client)
            print(serialize_plan(backrest_plan), end="")
            return ExitCode.VALID

        if args.command == "maintenance":
            maintenance_desired = load_maintenance_desired(args.config)
            if args.maintenance_command == "plan" and args.state_fixture:
                maintenance_current = json.loads(args.state_fixture.read_text())
                maintenance_client = None
            else:
                maintenance_client = MidcltClient(args.host)
                maintenance_current = read_maintenance_state(
                    maintenance_desired, maintenance_client
                )
            if not isinstance(maintenance_current, dict):
                raise OperationalError("TrueNAS maintenance state is invalid")
            maintenance_pools = maintenance_current.get("pools")
            maintenance_scrubs = maintenance_current.get("scrubs")
            maintenance_services = maintenance_current.get("services")
            maintenance_smart_tests = maintenance_current.get("smart_tests")
            if not all(
                isinstance(items, list) and all(isinstance(item, dict) for item in items)
                for items in (
                    maintenance_pools,
                    maintenance_scrubs,
                    maintenance_services,
                    maintenance_smart_tests,
                )
            ):
                raise OperationalError("TrueNAS maintenance query returned an unexpected response")
            maintenance_pools = cast(list[dict[str, Any]], maintenance_pools)
            maintenance_scrubs = cast(list[dict[str, Any]], maintenance_scrubs)
            maintenance_services = cast(list[dict[str, Any]], maintenance_services)
            maintenance_smart_tests = cast(list[dict[str, Any]], maintenance_smart_tests)
            if args.maintenance_command == "plan":
                maintenance_plan = plan_maintenance(
                    maintenance_desired,
                    maintenance_pools,
                    maintenance_scrubs,
                    maintenance_services,
                    maintenance_smart_tests,
                )
                print(serialize_plan(maintenance_plan), end="")
                return maintenance_plan.exit_code
            if maintenance_client is None:
                raise OperationalError("maintenance apply requires a live client")
            maintenance_plan = apply_maintenance(
                maintenance_desired,
                maintenance_pools,
                maintenance_scrubs,
                maintenance_services,
                maintenance_smart_tests,
                maintenance_client,
            )
            print(serialize_plan(maintenance_plan), end="")
            return ExitCode.VALID

        if args.command == "audiobookshelf":
            audiobookshelf_desired = load_audiobookshelf_desired(args.config)
            if args.audiobookshelf_command == "validate":
                print(f"valid: {relative(args.config)}")
                return ExitCode.VALID
            root_password = os.environ.get("AUDIOBOOKSHELF_ROOT_PASSWORD", "")
            oidc_client_secret = os.environ.get("AUDIOBOOKSHELF_OIDC_CLIENT_SECRET", "")
            if not root_password or not oidc_client_secret:
                raise OperationalError(
                    "set AUDIOBOOKSHELF_ROOT_PASSWORD and AUDIOBOOKSHELF_OIDC_CLIENT_SECRET"
                )
            audiobookshelf_client = AudiobookshelfClient(args.url or audiobookshelf_desired.api_url)
            audiobookshelf_current = read_audiobookshelf_state(
                audiobookshelf_desired, audiobookshelf_client, root_password
            )
            if args.audiobookshelf_command == "plan":
                audiobookshelf_discovery = (
                    discover_openid(audiobookshelf_desired.openid.issuer_url)
                    if audiobookshelf_current.get("initialized") is True
                    else None
                )
                audiobookshelf_plan = plan_audiobookshelf(
                    audiobookshelf_desired,
                    audiobookshelf_current,
                    audiobookshelf_discovery,
                    oidc_client_secret,
                )
                print(serialize_plan(audiobookshelf_plan), end="")
                return audiobookshelf_plan.exit_code
            audiobookshelf_plan = apply_audiobookshelf(
                audiobookshelf_desired,
                audiobookshelf_current,
                audiobookshelf_client,
                root_password,
                oidc_client_secret,
            )
            print(serialize_plan(audiobookshelf_plan), end="")
            return ExitCode.VALID

        if args.command == "syncthing":
            syncthing_desired = (
                load_syncthing_desired(args.config) if args.config else load_syncthing_desired()
            )
            syncthing_host = cast(SyncthingHost, args.host)
            ignore_files = SyncthingIgnoreFiles(syncthing_host, ssh_host=args.ssh_host)
            if args.syncthing_command == "plan" and args.state_fixture:
                syncthing_current = json.loads(args.state_fixture.read_text())
                syncthing_client = None
                desired_ignore = ignore_files.desired_content()
            else:
                device = (
                    syncthing_desired.truenas
                    if syncthing_host == "truenas"
                    else syncthing_desired.mac
                )
                api_key = read_syncthing_api_key(syncthing_host, ssh_host=args.ssh_host)
                api_url = device.api_url
                if syncthing_host == "truenas":
                    api_url = os.environ.get("SYNCTHING_TRUENAS_API_URL", api_url)
                syncthing_client = SyncthingClient(api_url, api_key)
                syncthing_current = read_syncthing_state(
                    syncthing_desired, syncthing_client, ignore_files
                )
                desired_ignore = ignore_files.desired_content()
            if not isinstance(syncthing_current, dict):
                raise OperationalError("Syncthing state fixture is invalid")
            if args.syncthing_command == "plan":
                syncthing_plan = plan_syncthing(
                    syncthing_desired,
                    syncthing_host,
                    syncthing_current,
                    desired_ignore,
                )
                print(serialize_plan(syncthing_plan), end="")
                return syncthing_plan.exit_code
            if syncthing_client is None:
                raise OperationalError("Syncthing apply requires a live client")
            syncthing_plan = apply_syncthing(
                syncthing_desired,
                syncthing_host,
                syncthing_current,
                syncthing_client,
                ignore_files,
            )
            print(serialize_plan(syncthing_plan), end="")
            return ExitCode.VALID

        if args.command == "apps":
            declarations = (
                load_app_declarations(args.declarations, args.apps)
                if args.declarations
                else load_app_declarations(selected=args.apps)
            )
            app_files = TrueNASAppFiles(args.host)
            if args.apps_command == "plan" and args.state_fixture:
                apps_current = json.loads(args.state_fixture.read_text())
                apps_client = None
            else:
                apps_client = MidcltClient(args.host, command_timeout=1800.0)
                apps_current = read_apps_state(declarations, apps_client, app_files)
            if not isinstance(apps_current, dict):
                raise OperationalError("TrueNAS app state fixture is invalid")
            if args.apps_command == "plan":
                apps_plan = plan_apps(declarations, apps_current)
                print(serialize_plan(apps_plan), end="")
                return apps_plan.exit_code
            if apps_client is None:
                raise OperationalError("TrueNAS app apply requires a live client")
            secret_desired = load_secret_metadata()
            resolver = SecretResolver(secret_desired, BwsClient())
            apps_plan = apply_apps(
                declarations,
                apps_current,
                apps_client,
                app_files,
                resolver,
            )
            print(serialize_plan(apps_plan), end="")
            return ExitCode.VALID

        if args.command == "api-key":
            api_key_desired = ApiKeyPublication(
                name=args.name,
                username=args.username,
                secret_alias=args.secret_alias,
            )
            api_key_secrets = load_secret_metadata()
            try:
                api_key_metadata = api_key_secrets.secrets[args.secret_alias]
            except KeyError as error:
                raise DesiredStateValidationError(
                    f"unknown API-key secret alias: {args.secret_alias}"
                ) from error
            if args.secret_key and args.secret_key != api_key_metadata.key:
                raise DesiredStateValidationError(
                    "API-key secret key does not match committed BWS metadata"
                )
            if args.project_id and args.project_id != str(api_key_secrets.project.id):
                raise DesiredStateValidationError(
                    "API-key BWS project does not match committed metadata"
                )
            if args.api_key_command == "plan" and args.state_fixture:
                api_key_current = json.loads(args.state_fixture.read_text())
                api_key_truenas = None
                api_key_bws = None
                api_keys = api_key_current.get("api_keys", [])
                bws_ids = api_key_current.get("bws_ids_by_key", {})
            else:
                api_key_truenas = MidcltClient(
                    args.host,
                    port=args.port,
                    identity=os.environ.get("TRUENAS_SSH_PRIVATE_KEY"),
                )
                api_keys = api_key_truenas.call(
                    "api_key.query",
                    [["name", "=", args.name]],
                    {"select": ["id", "name", "username", "revoked"]},
                )
                api_key_bws = BwsClient()
                bws_ids = api_key_bws.secret_ids_by_key(str(api_key_secrets.project.id))
            if not isinstance(api_keys, list) or not isinstance(bws_ids, Mapping):
                raise OperationalError("API-key publication state is invalid")
            if args.api_key_command == "plan":
                api_key_plan = plan_api_key_publication(
                    api_key_desired, api_key_secrets, api_keys, bws_ids
                )
                print(serialize_plan(api_key_plan), end="")
                return api_key_plan.exit_code
            if api_key_truenas is None or api_key_bws is None:
                raise OperationalError("API-key apply requires live clients")
            api_key_plan = apply_api_key_publication(
                api_key_desired,
                api_key_secrets,
                api_keys,
                bws_ids,
                api_key_truenas,
                api_key_bws,
            )
            print(serialize_plan(api_key_plan), end="")
            return ExitCode.VALID
    except DesiredStateValidationError as error:
        print(error, file=sys.stderr)
        return ExitCode.VALIDATION_FAILURE
    except (OpenWrtSafetyError, FirmwareVerificationError) as error:
        print(error, file=sys.stderr)
        return ExitCode.VALIDATION_FAILURE
    except ExportValidationError as error:
        print(error, file=sys.stderr)
        return ExitCode.VALIDATION_FAILURE
    except ImportManifestError as error:
        print(error, file=sys.stderr)
        return ExitCode.VALIDATION_FAILURE
    except ImmichMetadataPlanError as error:
        print(error, file=sys.stderr)
        return ExitCode.VALIDATION_FAILURE
    except OperationalError as error:
        print(f"operational failure: {error}", file=sys.stderr)
        return ExitCode.OPERATIONAL_FAILURE
    except OSError as error:
        print(f"operational failure: {error}", file=sys.stderr)
        return ExitCode.OPERATIONAL_FAILURE

    return ExitCode.OPERATIONAL_FAILURE
