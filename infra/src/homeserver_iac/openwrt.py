from __future__ import annotations

import fcntl
import hashlib
import io
import json
import os
import re
import subprocess
import tempfile
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Protocol, cast

from homeserver_iac.models.common import (
    Operation,
    OperationKind,
    Plan,
    SecretRef,
    order_operations,
)
from homeserver_iac.runtime import OperationalError

SCOPE = "network.openwrt"
HELPER_PATH = "/usr/libexec/homeserver-uci"
EXPECTED_BOARD = "cudy,wr3000e-v1"
EXPECTED_MODEL = "Cudy WR3000E v1"
EXPECTED_RELEASE = "25.12.5"
EXPECTED_TARGET = "mediatek/filogic"
EXPECTED_PROFILE = "cudy_wr3000e-v1"

REQUIRED_PACKAGES = frozenset(
    {
        "base-files",
        "dnsmasq",
        "dropbear",
        "firewall4",
        "kmod-ifb",
        "kmod-mt7915e",
        "kmod-mt7981-firmware",
        "kmod-sched-cake",
        "luci-app-sqm",
        "luci-ssl",
        "mt7981-wo-firmware",
        "odhcp6c",
        "odhcpd-ipv6only",
        "ppp",
        "ppp-mod-pppoe",
        "rpcd",
        "sqm-scripts",
        "tc-tiny",
        "ubus",
        "uci",
        "ucode",
        "ucode-mod-ubus",
        "uhttpd",
    }
)
FORBIDDEN_PACKAGES = frozenset({"tailscale", "miniupnpd", "luci-app-upnp"})

STAGE_PACKAGES: dict[str, frozenset[str]] = {
    "bootstrap-sanitize": frozenset({"network"}),
    "base": frozenset({"system", "network", "dhcp", "firewall", "dropbear", "uhttpd"}),
    "wan": frozenset({"network", "dhcp", "firewall"}),
    "main-wifi": frozenset({"wireless"}),
    "guest": frozenset({"network", "dhcp", "firewall", "wireless"}),
    "ipv6": frozenset({"network", "dhcp", "firewall"}),
    "sqm": frozenset({"sqm", "firewall"}),
}
MANAGED_PACKAGES = frozenset().union(*STAGE_PACKAGES.values())
STAGE_ORDER = ("base", "wan", "main-wifi", "guest", "ipv6", "sqm")
PROTECTED_STAGE_ORDER = ("base", "wan", "guest", "ipv6")
STAGE_RESOURCE_FIELDS: dict[str, dict[str, frozenset[str] | None]] = {
    "bootstrap-sanitize": {},
    "base": {
        "system": None,
        "management": None,
        "reservation-*": None,
        "network-trusted": frozenset(
            {"interface", "address", "dhcp_start", "dhcp_end", "lease_time", "domain"}
        ),
    },
    "wan": {
        "wan": frozenset(
            {"physical_device", "vlan_id", "protocol", "username", "password", "peer_dns"}
        ),
    },
    "main-wifi": {"wireless-settings": None, "wireless-main": None},
    "guest": {
        "network-guest": frozenset(
            {"interface", "address", "dhcp_start", "dhcp_end", "lease_time"}
        ),
        "wireless-guest": None,
    },
    "ipv6": {
        "network-global": frozenset({"ula_prefix"}),
        "wan": frozenset({"ipv6", "dhcpv6.request_address", "dhcpv6.request_prefix"}),
        "network-trusted": frozenset({"ipv6_assignment", "ipv6_hint"}),
        "network-guest": frozenset({"ipv6_assignment", "ipv6_hint"}),
    },
    "sqm": {"sqm": None},
}
HS_STAGE_PREFIXES = {
    "hs_base_": "base",
    "hs_wan_": "wan",
    "hs_main_wifi_": "main-wifi",
    "hs_guest_": "guest",
    "hs_ipv6_": "ipv6",
    "hs_sqm_": "sqm",
}
STAGE_DEPENDENCIES: dict[str, frozenset[str]] = {
    "bootstrap-sanitize": frozenset(),
    "base": frozenset(),
    "wan": frozenset({"base"}),
    "main-wifi": frozenset({"base", "wan"}),
    "guest": frozenset({"base", "wan", "main-wifi"}),
    "ipv6": frozenset({"base", "wan", "guest"}),
    "sqm": frozenset({"base", "wan"}),
}
STAGE_TIMEOUTS = {
    "bootstrap-sanitize": (120, 300),
    "base": (180, 360),
    "wan": (300, 600),
    "main-wifi": (120, 300),
    "guest": (180, 360),
    "ipv6": (300, 600),
    "sqm": (120, 300),
}
PACKAGE_HEALTH_CLOSURE: dict[str, frozenset[str]] = {
    "network": frozenset({"base", "wan", "guest", "ipv6", "sqm"}),
    "firewall": frozenset({"base", "wan", "guest", "ipv6", "sqm"}),
    "dhcp": frozenset({"base", "guest", "ipv6"}),
    "wireless": frozenset({"main-wifi", "guest"}),
    "sqm": frozenset({"sqm"}),
    "system": frozenset({"base"}),
    "dropbear": frozenset({"base"}),
    "uhttpd": frozenset({"base"}),
}
_IDENTIFIER = re.compile(r"^[A-Za-z0-9_@.\[\]-]+$")
_UCI_NAME = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_-]{0,63}$")
_HOST = re.compile(r"^(?:[A-Za-z0-9_.-]+@)?[A-Za-z0-9_.:-]+$")
_READ_ONLY_COMMANDS: dict[str, tuple[str, ...]] = {
    "board": ("ubus", "call", "system", "board"),
    "wireless": ("ubus", "call", "network.wireless", "status"),
    "wan": ("ifstatus", "wan"),
    "wan6": ("ifstatus", "wan6"),
}
_READ_ONLY_TEXT_COMMANDS: dict[str, tuple[str, ...]] = {
    "packages": ("apk", "info"),
    "qdisc": ("tc", "-s", "qdisc", "show"),
    "listeners": ("netstat", "-lntp"),
    "wan_mtu": ("cat", "/sys/class/net/pppoe-wan/mtu"),
}
_READ_ONLY_PROBES: dict[str, tuple[str, ...]] = {
    "dnsmasq": ("pgrep", "-x", "dnsmasq"),
    "odhcpd": ("pidof", "odhcpd"),
    "firewall": ("nft", "list", "table", "inet", "fw4"),
}
_READ_ONLY_HELPER_METHODS = frozenset(
    {
        ("homeserver", "snapshot"),
        ("homeserver", "compare"),
        ("homeserver", "lock-status"),
        ("homeserver", "root-password-status"),
        ("uci", "changes"),
    }
)
_FIXED_REMOTE_OPERATIONS = frozenset(
    {
        ("ubus", "call", "system", "board"),
        ("sysupgrade", "-b", "-"),
        ("cat", "/proc/mtd"),
        ("passwd", "root"),
        ("sha256sum", "/tmp/homeserver-sysupgrade.bin"),
        ("sysupgrade", "-T", "/tmp/homeserver-sysupgrade.bin"),
        ("sysupgrade", "/tmp/homeserver-sysupgrade.bin"),
        ("sysupgrade", "-n", "/tmp/homeserver-sysupgrade.bin"),
        *(("cat", f"/dev/mtd{index}") for index in range(6)),
    }
)
_FIXED_READ_OPERATIONS = frozenset({("cat", "/sys/class/net/pppoe-wan/mtu")})


class OpenWrtSafetyError(ValueError):
    """The observed router is incompatible or violates a fail-closed policy."""


class ApplyAmbiguousError(OperationalError):
    """rpcd may have accepted apply; callers must inspect or await timed rollback."""


class LockContentionError(OperationalError):
    """Another controller transaction owns the local or router lock."""


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: bytes = b""
    stderr: bytes = b""


class CommandRunner(Protocol):
    def __call__(
        self, argv: Sequence[str], *, input_data: bytes | None, timeout: float
    ) -> CommandResult: ...


def subprocess_runner(
    argv: Sequence[str], *, input_data: bytes | None, timeout: float
) -> CommandResult:
    try:
        result = subprocess.run(
            argv,
            input=input_data,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError as error:
        raise OperationalError(f"command not found: {argv[0]}") from error
    except subprocess.TimeoutExpired as error:
        raise OperationalError(f"command timed out after {timeout:g}s: {argv[0]}") from error
    return CommandResult(result.returncode, result.stdout, result.stderr)


class OpenWrtSshClient:
    """Strict SSH transport. Remote commands are fixed argv, and helper data is stdin-only."""

    def __init__(
        self,
        *,
        host: str,
        known_hosts: Path,
        identity: Path,
        connect_timeout: int = 10,
        command_timeout: int = 60,
        proxy_jump: str | None = None,
        runner: CommandRunner = subprocess_runner,
    ) -> None:
        if not _HOST.fullmatch(host) or host.startswith("-"):
            raise ValueError("invalid SSH host")
        if proxy_jump is not None and (
            not _HOST.fullmatch(proxy_jump) or "@" in proxy_jump or proxy_jump.startswith("-")
        ):
            raise ValueError("invalid ProxyJump host")
        if connect_timeout < 1 or command_timeout < 1:
            raise ValueError("SSH timeouts must be positive")
        self.host = host
        self.known_hosts = known_hosts
        self.identity = identity
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout
        self.proxy_jump = proxy_jump
        self.runner = runner

    def _argv(self, remote: Sequence[str], *, mutating: bool) -> tuple[str, ...]:
        if not remote or (
            tuple(remote) not in _FIXED_REMOTE_OPERATIONS | _FIXED_READ_OPERATIONS
            and any(part != HELPER_PATH and not _IDENTIFIER.fullmatch(part) for part in remote)
        ):
            raise ValueError("remote command contains an invalid token")
        if mutating and self.proxy_jump is not None:
            raise OpenWrtSafetyError("mutating operations require a direct wired SSH route")
        argv = [
            "ssh",
            "-F",
            "/dev/null",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={self.known_hosts}",
            "-o",
            f"ConnectTimeout={self.connect_timeout}",
            "-i",
            str(self.identity),
        ]
        if self.proxy_jump is not None:
            argv.extend(("-J", self.proxy_jump))
        argv.extend((self.host, "--", *remote))
        return tuple(argv)

    def _run(
        self,
        remote: Sequence[str],
        *,
        mutating: bool,
        input_data: bytes | None = None,
        sensitive: bool = False,
        operation: str | None = None,
    ) -> bytes:
        result = self.runner(
            self._argv(remote, mutating=mutating),
            input_data=input_data,
            timeout=self.command_timeout,
        )
        if result.returncode:
            # Never include remote output: it can contain request-derived secret material.
            label = "sensitive helper" if sensitive else f"SSH {operation or 'operation'}"
            raise OperationalError(f"{label} failed with exit {result.returncode}")
        return result.stdout

    def read_json(self, name: str) -> Mapping[str, Any]:
        try:
            remote = _READ_ONLY_COMMANDS[name]
        except KeyError as error:
            raise ValueError("read operation is not allowlisted") from error
        output = self._run(remote, mutating=False, operation=f"read {name}")
        try:
            value = json.loads(output)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise OperationalError(f"SSH read returned invalid JSON: {name}") from error
        if not isinstance(value, Mapping):
            raise OperationalError(f"SSH read returned a non-object: {name}")
        return value

    def read_text(self, name: str) -> str:
        try:
            remote = _READ_ONLY_TEXT_COMMANDS[name]
        except KeyError as error:
            raise ValueError("text read operation is not allowlisted") from error
        output = self._run(remote, mutating=False, operation=f"read {name}")
        try:
            return output.decode()
        except UnicodeDecodeError as error:
            raise OperationalError(f"SSH read returned invalid text: {name}") from error

    def probe(self, name: str) -> bool:
        try:
            remote = _READ_ONLY_PROBES[name]
        except KeyError as error:
            raise ValueError("probe operation is not allowlisted") from error
        result = self.runner(
            self._argv(remote, mutating=False),
            input_data=None,
            timeout=self.command_timeout,
        )
        return result.returncode == 0

    def read_optional_text(self, name: str) -> str:
        try:
            remote = _READ_ONLY_TEXT_COMMANDS[name]
        except KeyError as error:
            raise ValueError("text read operation is not allowlisted") from error
        result = self.runner(
            self._argv(remote, mutating=False),
            input_data=None,
            timeout=self.command_timeout,
        )
        if result.returncode:
            return ""
        try:
            return result.stdout.decode().strip()
        except UnicodeDecodeError as error:
            raise OperationalError(f"SSH read returned invalid text: {name}") from error

    def helper_call(self, envelope: Mapping[str, Any]) -> Mapping[str, Any]:
        payload = json.dumps(envelope, separators=(",", ":"), sort_keys=True).encode()
        if len(payload) > 65_536:
            raise ValueError("helper request exceeds 65536 bytes")
        method = (envelope.get("object"), envelope.get("method"))
        result = self.runner(
            self._argv(
                (HELPER_PATH,),
                mutating=method not in _READ_ONLY_HELPER_METHODS,
            ),
            input_data=payload,
            timeout=self.command_timeout,
        )
        if result.returncode:
            error_code: int | None = None
            try:
                rejected = json.loads(result.stdout)
                if (
                    isinstance(rejected, Mapping)
                    and set(rejected) == {"ok", "error"}
                    and rejected.get("ok") is False
                    and isinstance(rejected.get("error"), int)
                    and 1 <= rejected["error"] <= 99
                ):
                    error_code = rejected["error"]
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
            suffix = f" (code {error_code})" if error_code is not None else ""
            operation = ".".join(part for part in method if isinstance(part, str))
            raise OperationalError(
                f"sensitive helper {operation} failed with exit {result.returncode}{suffix}"
            )
        output = result.stdout
        try:
            value = json.loads(output)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise OperationalError("sensitive helper returned invalid JSON") from error
        if not isinstance(value, Mapping) or value.get("ok") is not True:
            raise OperationalError("sensitive helper rejected request")
        return value

    def filtered_snapshot(self, configs: Iterable[str]) -> Mapping[str, Any]:
        config_names = tuple(sorted(set(configs)))
        if not config_names or any(name not in MANAGED_PACKAGES for name in config_names):
            raise ValueError("snapshot contains an unknown UCI package")
        response = self.helper_call(
            {
                "object": "homeserver",
                "method": "snapshot",
                "arguments": {"configs": config_names},
            }
        )
        values = response.get("values")
        if not isinstance(values, Mapping):
            raise OperationalError("sensitive helper returned no filtered snapshot")
        return values

    def run_operation(
        self,
        command: Sequence[str],
        *,
        input_data: bytes | None,
        timeout: float,
        mutating: bool,
    ) -> CommandResult:
        if tuple(command) not in _FIXED_REMOTE_OPERATIONS:
            raise OpenWrtSafetyError("remote operation is not allowlisted")
        if timeout < 1:
            raise ValueError("operation timeout must be positive")
        return self.runner(
            self._argv(command, mutating=mutating),
            input_data=input_data,
            timeout=timeout,
        )


def _health_uci_aliases(
    snapshot: Mapping[str, Any], section_types: Mapping[str, Any]
) -> dict[str, Any]:
    aliases = dict(snapshot)
    singleton_aliases = {
        ("system", "system"): "system.system",
        ("dhcp", "dnsmasq"): "dhcp.dnsmasq",
        ("firewall", "defaults"): "firewall.defaults",
        ("dropbear", "dropbear"): "dropbear.dropbear",
        ("uhttpd", "uhttpd"): "uhttpd.main",
    }
    rule_aliases = {
        "Allow-DHCPv6": "hs_ipv6_dhcpv6",
        "Allow-ICMPv6-Input": "hs_ipv6_icmp",
        "Allow-ICMPv6-Forward": "hs_ipv6_forward",
        "Allow-Guest-DHCPv6": "hs_ipv6_guest_dhcp",
        "Allow-Guest-ICMPv6": "hs_ipv6_guest_icmp",
    }
    for section_id, section_type in section_types.items():
        config, _ = section_id.split(".", 1)
        alias = singleton_aliases.get((config, str(section_type)))
        if section_type == "zone":
            zone_name = snapshot.get(f"{section_id}.name")
            alias = {
                "lan": "firewall.hs_base_trusted",
                "wan": "firewall.hs_wan_zone",
                "guest": "firewall.hs_guest_zone",
            }.get(str(zone_name))
        elif section_type == "forwarding":
            pair = (
                str(snapshot.get(f"{section_id}.src")),
                str(snapshot.get(f"{section_id}.dest")),
            )
            alias_name = {
                ("lan", "wan"): "hs_wan_trusted_forward",
                ("guest", "wan"): "hs_guest_wan_forward",
            }.get(pair)
            alias = f"firewall.{alias_name}" if alias_name else None
        elif section_type == "rule":
            alias_name = rule_aliases.get(str(snapshot.get(f"{section_id}.name")))
            alias = f"firewall.{alias_name}" if alias_name else None
        if alias is None:
            continue
        prefix = section_id + "."
        for path, value in snapshot.items():
            if path.startswith(prefix):
                aliases[alias + path.removeprefix(section_id)] = value
    return aliases


def read_live_state(client: OpenWrtSshClient) -> dict[str, Any]:
    """Collect the bounded read-only surface used by live plan and status."""

    board = client.read_json("board")
    release = board.get("release", {})
    release_mapping = release if isinstance(release, Mapping) else {}
    board_name = board.get("board_name")
    model = board.get("model")
    identity = {
        "board_name": board_name,
        "model": model,
        "board_ids": ["R53"] if board_name == EXPECTED_BOARD and model == EXPECTED_MODEL else [],
        "release": release_mapping.get("version"),
        "target": release_mapping.get("target"),
        "profile": EXPECTED_PROFILE if board_name == EXPECTED_BOARD else None,
    }
    packages = [line.strip() for line in client.read_text("packages").splitlines() if line.strip()]
    snapshot = client.filtered_snapshot(MANAGED_PACKAGES)
    wan = client.read_json("wan") if snapshot.get("network.wan._type") == "interface" else {}
    wan6 = client.read_json("wan6") if snapshot.get("network.wan6._type") == "interface" else {}
    wireless = client.read_json("wireless")
    section_types = {
        ".".join(path.split(".")[:2]): value
        for path, value in snapshot.items()
        if path.endswith("._type")
    }
    redirects = sorted(
        section for section, section_type in section_types.items() if section_type == "redirect"
    )
    includes = sorted(
        section for section, section_type in section_types.items() if section_type == "include"
    )
    wan_admin = False
    for section, section_type in section_types.items():
        if (
            section_type == "zone"
            and snapshot.get(f"{section}.name") == "wan"
            and snapshot.get(f"{section}.input") == "ACCEPT"
        ):
            wan_admin = True
        if section_type != "rule":
            continue
        if (
            snapshot.get(f"{section}.src") == "wan"
            and snapshot.get(f"{section}.target") == "ACCEPT"
        ):
            protocol = snapshot.get(f"{section}.proto")
            protocols = (
                protocol
                if isinstance(protocol, Sequence) and not isinstance(protocol, str)
                else [protocol]
            )
            ports = snapshot.get(f"{section}.dest_port")
            values = (
                ports if isinstance(ports, Sequence) and not isinstance(ports, str) else [ports]
            )
            port_tokens = {
                token
                for value in values
                for token in re.split(r"[\s,]+", str(value or ""))
                if token
            }
            management_port = any(
                token in {"22", "80", "443"}
                or (
                    "-" in token
                    and all(part.isdigit() for part in token.split("-", 1))
                    and int(token.split("-", 1)[0]) <= 443 <= int(token.split("-", 1)[1])
                )
                for token in port_tokens
            )
            unrestricted = not port_tokens and any(
                item in {None, "", "all", "tcp"} for item in protocols
            )
            if management_port or unrestricted:
                wan_admin = True
    listeners: list[dict[str, Any]] = []
    dropbear_interfaces: list[Any] = []
    for section, section_type in section_types.items():
        if section_type == "dropbear":
            interface = snapshot.get(f"{section}.Interface")
            dropbear_interfaces.append(interface)
            if interface != "lan":
                listeners.append({"network": "wan", "service": "dropbear"})
        if section_type == "uhttpd":
            https_listeners = snapshot.get(f"{section}.listen_https", [])
            if isinstance(https_listeners, str):
                https_listeners = [https_listeners]
            if isinstance(https_listeners, Sequence):
                for address in https_listeners:
                    if isinstance(address, str) and not address.startswith("192.168.1.1:"):
                        listeners.append({"network": "wan", "service": "uhttpd"})
    listener_output = client.read_text("listeners")
    for line in listener_output.splitlines():
        fields = line.split()
        if len(fields) < 7 or not fields[0].startswith("tcp"):
            continue
        local_address = fields[3]
        process = fields[-1]
        wildcard = local_address.startswith(("0.0.0.0:", "[::]:", ":::", "*:"))
        if wildcard and "uhttpd" in process:
            listeners.append({"network": "wan", "service": "uhttpd"})
        if wildcard and "dropbear" in process and "lan" not in dropbear_interfaces:
            listeners.append({"network": "wan", "service": "dropbear"})
    radio_bands = sorted(
        str(value)
        for path, value in snapshot.items()
        if path.startswith("wireless.") and path.endswith(".band")
    )
    sqm_enabled = snapshot.get("sqm.wan.enabled") == "1"
    runtime = {
        # Reaching this point required several new strict-host-key SSH processes,
        # so this is a positive reconnect observation rather than an assumption.
        "strict_ssh": True,
        "wan": wan,
        "wan6": wan6,
        "wireless": wireless,
        "qdisc": client.read_text("qdisc"),
        "wan_mtu": client.read_optional_text("wan_mtu"),
        "processes": {
            "dnsmasq": client.probe("dnsmasq"),
            "odhcpd": client.probe("odhcpd"),
            "firewall": client.probe("firewall"),
        },
        "root_password_set": client.helper_call(
            {"object": "homeserver", "method": "root-password-status", "arguments": {}}
        ).get("password_set"),
        "radio_bands": radio_bands,
        "sqm": {
            "enabled": sqm_enabled,
            "enabled_queues": 1 if sqm_enabled else 0,
            "device": snapshot.get("sqm.wan.interface"),
            "flow_offloading": snapshot.get("firewall.defaults.flow_offloading") == "1",
            "flow_offloading_hw": snapshot.get("firewall.defaults.flow_offloading_hw") == "1",
        },
    }
    return {
        "identity": identity,
        "packages": packages,
        "uci": dict(snapshot),
        "health_uci": _health_uci_aliases(snapshot, section_types),
        "resources": {},
        "firewall": {
            "redirects": redirects,
            "includes": includes,
            "dmz": any(
                "dmz" in section.lower()
                or (
                    section_type == "zone"
                    and str(snapshot.get(f"{section}.name", "")).lower() == "dmz"
                )
                for section, section_type in section_types.items()
            ),
            "wan_management": wan_admin,
        },
        "listeners": listeners,
        "services": {
            "upnp": "miniupnpd" in packages,
            "nat_pmp": "miniupnpd" in packages,
            "tailscale": "tailscale" in packages,
        },
        "runtime": runtime,
    }


def _plain_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        result = model_dump(mode="python")
        if isinstance(result, Mapping):
            return result
    raise TypeError("desired state must be a mapping or Pydantic model")


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical(child) for key, child in sorted(value.items())}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_canonical(child) for child in value]
    return value


def normalize_state(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a filtered helper/live fixture without retaining counters or ordering noise."""

    identity = cast(Mapping[str, Any], raw.get("identity", {}))
    packages_raw = raw.get("packages", [])
    packages: set[str] = set()
    if isinstance(packages_raw, Mapping):
        packages.update(str(name) for name in packages_raw)
    elif isinstance(packages_raw, Sequence) and not isinstance(packages_raw, str):
        for package in packages_raw:
            name = str(package).split(" - ", 1)[0].split("=", 1)[0]
            packages.add(name)

    resources: dict[str, dict[str, Any]] = {}
    resources_raw = raw.get("resources", {})
    if isinstance(resources_raw, Mapping):
        for resource_id, resource in resources_raw.items():
            if isinstance(resource, Mapping):
                resources[str(resource_id)] = dict(_canonical(resource))
    elif isinstance(resources_raw, Sequence) and not isinstance(resources_raw, str):
        for resource in resources_raw:
            if isinstance(resource, Mapping) and isinstance(resource.get("id"), str):
                resources[str(resource["id"])] = {
                    str(key): _canonical(value)
                    for key, value in resource.items()
                    if key not in {"id", "runtime", "counters"}
                }

    return {
        "identity": {
            "board_name": identity.get("board_name"),
            "model": identity.get("model"),
            "board_ids": sorted(str(item) for item in identity.get("board_ids", [])),
            "release": identity.get("release"),
            "target": identity.get("target"),
            "profile": identity.get("profile"),
        },
        "packages": sorted(packages),
        "resources": dict(sorted(resources.items())),
        "firewall": _canonical(raw.get("firewall", {})),
        "listeners": _canonical(raw.get("listeners", [])),
        "services": _canonical(raw.get("services", {})),
        "runtime": _canonical(raw.get("runtime", {})),
    }


def _desired_resources(
    desired: Any,
) -> tuple[dict[str, dict[str, Any]], dict[str, tuple[str, ...]]]:
    document = _plain_mapping(desired)
    resources: dict[str, dict[str, Any]] = {}
    aliases: dict[str, tuple[str, ...]] = {}
    source: Iterable[tuple[Any, Any]]
    explicit = document.get("resources")
    if isinstance(explicit, Mapping):
        source = explicit.items()
    else:
        source_items: list[tuple[str, Any]] = []
        for key in ("system", "wan", "management", "security", "sqm"):
            if key in document:
                source_items.append((key, document[key]))
        networks = document.get("networks", {})
        if isinstance(networks, Mapping) and networks:
            source_items.append(("network-global", {"ula_prefix": networks.get("ula_prefix")}))
            source_items.extend(
                (f"network-{key}", value)
                for key, value in networks.items()
                if isinstance(value, Mapping)
            )
        wireless = document.get("wireless", {})
        if isinstance(wireless, Mapping) and wireless:
            source_items.append(
                (
                    "wireless-settings",
                    {
                        "country": wireless.get("country"),
                        "fast_transition": wireless.get("fast_transition"),
                        "wps": wireless.get("wps"),
                        "radios": wireless.get("radios"),
                    },
                )
            )
            source_items.extend(
                (f"wireless-{key}", value)
                for key, value in wireless.items()
                if key in {"main", "guest"} and isinstance(value, Mapping)
            )
        reservations = document.get("reservations", [])
        if isinstance(reservations, Sequence) and not isinstance(reservations, str):
            source_items.extend(
                (f"reservation-{item.get('id')}", item)
                for item in reservations
                if isinstance(item, Mapping) and item.get("id")
            )
        source = source_items

    def scrub(value: Any, found: list[str]) -> Any:
        if isinstance(value, Mapping):
            secret_ref = value.get("secret_ref")
            if isinstance(secret_ref, Mapping) and isinstance(secret_ref.get("alias"), str):
                found.append(str(secret_ref["alias"]))
                return {"secret_ref": str(secret_ref["alias"])}
            return {str(key): scrub(child, found) for key, child in sorted(value.items())}
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return [scrub(child, found) for child in value]
        return value

    for resource_id, value in source:
        if not isinstance(value, Mapping):
            continue
        found: list[str] = []
        resources[str(resource_id)] = cast(dict[str, Any], scrub(value, found))
        aliases[str(resource_id)] = tuple(sorted(set(found)))
    return dict(sorted(resources.items())), aliases


def _flatten_resource(value: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, child in value.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(child, Mapping) and "secret_ref" not in child:
            flattened.update(_flatten_resource(child, path))
        else:
            flattened[path] = child
    return flattened


def _resource_pattern(resource_id: str) -> str:
    if resource_id.startswith("reservation-"):
        return "reservation-*"
    return resource_id


def _stage_projection(
    resources: Mapping[str, Mapping[str, Any]], stage: str
) -> dict[str, dict[str, Any]]:
    try:
        ownership = STAGE_RESOURCE_FIELDS[stage]
    except KeyError as error:
        raise ValueError("unknown OpenWrt stage") from error
    projected: dict[str, dict[str, Any]] = {}
    for resource_id, resource in resources.items():
        fields = ownership.get(_resource_pattern(resource_id), frozenset())
        if fields == frozenset():
            continue
        flattened = _flatten_resource(resource)
        projected[resource_id] = (
            flattened if fields is None else {field: flattened.get(field) for field in fields}
        )
    return projected


def _stale_owner(resource_id: str) -> str | None:
    owners = {
        stage for prefix, stage in HS_STAGE_PREFIXES.items() if resource_id.startswith(prefix)
    }
    return owners.pop() if len(owners) == 1 else None


def validate_safety(
    desired: Any,
    current: Mapping[str, Any],
    *,
    allow_prebase_management: bool = False,
) -> None:
    state = normalize_state(current)
    identity = state["identity"]
    failures: list[str] = []
    expected_identity = {
        "board_name": EXPECTED_BOARD,
        "model": EXPECTED_MODEL,
        "release": EXPECTED_RELEASE,
        "target": EXPECTED_TARGET,
        "profile": EXPECTED_PROFILE,
    }
    for key, expected in expected_identity.items():
        if identity.get(key) != expected:
            failures.append(f"identity.{key} must be {expected}")
    if "R53" not in identity.get("board_ids", []):
        failures.append("identity.board_ids must contain R53")

    packages = set(state["packages"])
    missing = sorted(REQUIRED_PACKAGES - packages)
    forbidden = sorted(FORBIDDEN_PACKAGES & packages)
    if missing:
        failures.append(f"required packages absent: {', '.join(missing)}")
    if forbidden:
        failures.append(f"forbidden packages present: {', '.join(forbidden)}")

    firewall = state["firewall"]
    if isinstance(firewall, Mapping):
        if firewall.get("redirects"):
            failures.append("firewall contains redirects or port forwards")
        if firewall.get("includes"):
            failures.append("firewall contains unmanaged include scripts")
        if firewall.get("dmz"):
            failures.append("firewall contains a DMZ")
        if firewall.get("wan_management"):
            failures.append("WAN management is enabled")
    services = state["services"]
    if isinstance(services, Mapping) and any(
        services.get(name) for name in ("upnp", "nat_pmp", "tailscale")
    ):
        failures.append("forbidden network service is enabled")
    listeners = state["listeners"]
    if isinstance(listeners, Sequence) and not allow_prebase_management:
        for listener in listeners:
            if (
                isinstance(listener, Mapping)
                and listener.get("network") in {"wan", "guest"}
                and listener.get("service") in {"dropbear", "uhttpd", "luci", "ssh", "https"}
            ):
                failures.append("management listener is exposed outside trusted LAN")
                break

    uci = current.get("uci", {})
    if isinstance(uci, Mapping):
        section_types = {
            ".".join(str(path).split(".")[:2]): value
            for path, value in uci.items()
            if str(path).endswith("._type")
        }
        for section, section_type in section_types.items():
            if section_type != "device" or uci.get(f"{section}.type") != "8021q":
                continue
            if uci.get(f"{section}.vid") != "835" or uci.get(f"{section}.ifname") != "wan":
                failures.append("unexpected WAN VLAN or physical device")
        password_auth_enabled = any(
            section_type == "dropbear"
            and (
                uci.get(f"{section}.PasswordAuth") not in {None, "0", "off"}
                or uci.get(f"{section}.RootPasswordAuth") not in {None, "0", "off"}
            )
            for section, section_type in section_types.items()
        )
        if password_auth_enabled and not allow_prebase_management:
            failures.append("root SSH password authentication is enabled")

    # Ensure the desired security contract itself cannot request prohibited exposure.
    document = _plain_mapping(desired)
    security = document.get("security", {})
    if isinstance(security, Mapping) and (
        security.get("upnp")
        or security.get("nat_pmp")
        or security.get("dmz")
        or security.get("wan_management")
        or security.get("tailscale")
        or security.get("port_forwards")
    ):
        failures.append("desired security policy requests forbidden exposure")
    if failures:
        raise OpenWrtSafetyError("; ".join(sorted(set(failures))))


def plan_openwrt(desired: Any, raw_current: Mapping[str, Any], *, stage: str | None = None) -> Plan:
    validate_safety(desired, raw_current)
    current = normalize_state(raw_current)["resources"]
    expected, aliases = _desired_resources(desired)
    if stage is not None and stage != "all":
        current = _stage_projection(current, stage)
        expected = _stage_projection(expected, stage)
    operations: list[Operation] = []
    for resource_id, value in expected.items():
        current_value = current.get(resource_id)
        if current_value is None:
            kind = OperationKind.CREATE
            changed_fields: tuple[str, ...] = ()
            summary = "OpenWrt resource is absent"
        else:
            desired_fields = _flatten_resource(value)
            current_fields = _flatten_resource(current_value)
            changed_fields = tuple(
                sorted(
                    key
                    for key in desired_fields.keys() | current_fields.keys()
                    if desired_fields.get(key) != current_fields.get(key)
                )
            )
            kind = OperationKind.UPDATE if changed_fields else OperationKind.UNCHANGED
            summary = (
                "OpenWrt resource differs from desired state"
                if changed_fields
                else "OpenWrt resource is current"
            )
        operations.append(
            Operation(
                kind=kind,
                scope=SCOPE,
                resource_id=resource_id,
                summary=summary,
                changed_fields=changed_fields,
                secret_refs=tuple(
                    SecretRef(alias=alias)
                    for alias in aliases[resource_id]
                    if stage is None
                    or stage == "all"
                    or any(
                        isinstance(field, Mapping) and field.get("secret_ref") == alias
                        for field in value.values()
                    )
                ),
            )
        )
    for resource_id in sorted(current.keys() - expected.keys()):
        if resource_id.startswith("hs_") and (
            stage is None or stage == "all" or _stale_owner(resource_id) == stage
        ):
            operations.append(
                Operation(
                    kind=OperationKind.STALE,
                    scope=SCOPE,
                    resource_id=resource_id,
                    summary="Router-owned resource is not declared",
                )
            )
        elif not resource_id.startswith("hs_"):
            operations.append(
                Operation(
                    kind=OperationKind.WARNING,
                    scope=SCOPE,
                    resource_id=resource_id,
                    summary="Unmanaged OpenWrt resource is preserved",
                )
            )
    return Plan(operations=order_operations(operations))


def required_health_stages(
    packages: Iterable[str], enabled_stages: Iterable[str], mutated_stage: str
) -> tuple[str, ...]:
    enabled = set(enabled_stages) | {mutated_stage}
    closure = {mutated_stage}
    for package in packages:
        closure.update(PACKAGE_HEALTH_CLOSURE.get(package, ()))
    return tuple(
        stage for stage in (*STAGE_ORDER, "bootstrap-sanitize") if stage in closure & enabled
    )


def required_revert_health_stages(
    packages: Iterable[str], previously_enabled_stages: Iterable[str]
) -> tuple[str, ...]:
    enabled = set(previously_enabled_stages)
    closure: set[str] = set()
    for package in packages:
        closure.update(PACKAGE_HEALTH_CLOSURE.get(package, ()))
    return tuple(stage for stage in STAGE_ORDER if stage in closure & enabled)


def effective_stage_policy(
    stage: str, packages: Iterable[str], enabled_stages: Iterable[str]
) -> tuple[int, int, tuple[str, ...]]:
    if stage not in STAGE_PACKAGES:
        raise ValueError("unknown apply stage")
    missing_dependencies = STAGE_DEPENDENCIES[stage] - set(enabled_stages)
    if missing_dependencies:
        raise OpenWrtSafetyError(
            f"stage dependencies are not enabled: {', '.join(sorted(missing_dependencies))}"
        )
    package_set = frozenset(packages)
    if not package_set or not package_set <= STAGE_PACKAGES[stage]:
        raise OpenWrtSafetyError("stage packages exceed the ownership allowlist")
    health = required_health_stages(package_set, enabled_stages, stage)
    rollback = max(STAGE_TIMEOUTS[item][0] for item in health)
    session = max(max(STAGE_TIMEOUTS[item][1] for item in health), rollback + 180)
    return rollback, session, health


def orchestrate_all(
    apply_one: Callable[[str, frozenset[str]], ApplyResult],
) -> tuple[ApplyResult, ...]:
    """Run final stages as six transactions, never as one combined rpcd apply."""

    enabled: set[str] = set()
    results: list[ApplyResult] = []
    for stage in STAGE_ORDER:
        result = apply_one(stage, frozenset(enabled))
        if result.stage != stage:
            raise OperationalError("all-stage callback returned a mismatched stage")
        results.append(result)
        enabled.add(stage)
    return tuple(results)


@contextmanager
def local_apply_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise LockContentionError("another OpenWrt apply owns the controller lock") from error
        os.ftruncate(descriptor, 0)
        os.write(descriptor, f"pid={os.getpid()}\n".encode())
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


@dataclass(frozen=True)
class ApplyResult:
    stage: str
    sid: str
    rollback_timeout: int
    session_lifetime: int
    health_stages: tuple[str, ...]


def prove_timed_rollback(
    client: OpenWrtSshClient,
    *,
    lock_path: Path,
    controller_id: str,
    rollback_timeout: int = 30,
    poll_interval: float = 1.0,
) -> float:
    """Apply a temporary hostname and require rpcd to restore it without confirmation."""

    if rollback_timeout < 30 or poll_interval <= 0:
        raise ValueError("rollback proof timing is invalid")
    snapshot = client.filtered_snapshot(("system",))
    hostname_fields = [
        (path, value)
        for path, value in snapshot.items()
        if path.startswith("system.") and path.endswith(".hostname") and isinstance(value, str)
    ]
    if len(hostname_fields) != 1:
        raise OpenWrtSafetyError("rollback proof requires exactly one readable system hostname")
    hostname_path, original_hostname = hostname_fields[0]
    section = hostname_path.split(".", 2)[1]
    temporary_hostname = "homeserver-rollback-proof"
    if original_hostname == temporary_hostname:
        temporary_hostname = "homeserver-rollback-proof-2"

    with local_apply_lock(lock_path):
        acquired = client.helper_call(
            {
                "object": "homeserver",
                "method": "lock-acquire",
                "arguments": {
                    "controller": controller_id,
                    "pid": os.getpid(),
                    "stage": "base",
                },
            }
        )
        if acquired.get("acquired") is not True:
            raise LockContentionError("router apply lock is held during rollback proof")
        sid: str | None = None
        apply_started = False
        restored = False
        started = time.monotonic()
        try:
            created = client.helper_call(
                {
                    "object": "session",
                    "method": "create",
                    "arguments": {"timeout": rollback_timeout + 180},
                }
            )
            if not isinstance(created.get("sid"), str):
                raise OperationalError("rpcd rollback proof returned no SID")
            sid = str(created["sid"])
            client.helper_call(
                {
                    "object": "session",
                    "method": "grant",
                    "arguments": {
                        "ubus_rpc_session": sid,
                        "scope": "uci",
                        "objects": ["system"],
                    },
                }
            )
            client.helper_call(
                {
                    "object": "uci",
                    "method": "set",
                    "arguments": {
                        "ubus_rpc_session": sid,
                        "config": "system",
                        "section": section,
                        "values": {"hostname": temporary_hostname},
                    },
                }
            )
            client.helper_call(
                {
                    "object": "uci",
                    "method": "apply",
                    "arguments": {
                        "ubus_rpc_session": sid,
                        "rollback": True,
                        "timeout": rollback_timeout,
                    },
                }
            )
            apply_started = True

            observed_temporary = False
            deadline = started + rollback_timeout + 20
            while time.monotonic() < deadline:
                current = client.filtered_snapshot(("system",)).get(hostname_path)
                observed_temporary = observed_temporary or current == temporary_hostname
                if observed_temporary and current == original_hostname:
                    restored = True
                    break
                time.sleep(poll_interval)
            if not observed_temporary:
                raise OpenWrtSafetyError(
                    "rpcd rollback proof never observed the temporary hostname"
                )
            if not restored:
                raise OpenWrtSafetyError(
                    "rpcd rollback proof did not restore the original hostname"
                )

            client.helper_call(
                {
                    "object": "session",
                    "method": "destroy",
                    "arguments": {"ubus_rpc_session": sid},
                }
            )
            client.helper_call(
                {
                    "object": "homeserver",
                    "method": "lock-release",
                    "arguments": {"controller": controller_id, "sid": sid},
                }
            )
            sid = None
            lock_status = client.helper_call(
                {"object": "homeserver", "method": "lock-status", "arguments": {}}
            )
            if lock_status.get("present") is not False:
                raise OpenWrtSafetyError("router lock remains after rollback proof")
            return time.monotonic() - started
        except Exception:
            if not apply_started:
                if sid is not None:
                    with suppress(OperationalError):
                        client.helper_call(
                            {
                                "object": "session",
                                "method": "destroy",
                                "arguments": {"ubus_rpc_session": sid},
                            }
                        )
                with suppress(OperationalError):
                    client.helper_call(
                        {
                            "object": "homeserver",
                            "method": "lock-release",
                            "arguments": {"controller": controller_id, "sid": sid or "none"},
                        }
                    )
            elif restored and sid is not None:
                with suppress(OperationalError):
                    client.helper_call(
                        {
                            "object": "session",
                            "method": "destroy",
                            "arguments": {"ubus_rpc_session": sid},
                        }
                    )
                with suppress(OperationalError):
                    client.helper_call(
                        {
                            "object": "homeserver",
                            "method": "lock-release",
                            "arguments": {"controller": controller_id, "sid": sid},
                        }
                    )
            raise


HealthCheck = Callable[[str], None]
BackupBeforeApply = Callable[[str], None]
ReadAfterApply = Callable[[str], None]


def apply_stage(
    *,
    client: OpenWrtSshClient,
    stage: str,
    packages: Iterable[str],
    mutations: Sequence[Mapping[str, Any]],
    expected_projection: Mapping[str, Any],
    enabled_stages: Iterable[str],
    health_check: HealthCheck,
    backup_before_apply: BackupBeforeApply,
    lock_path: Path,
    controller_id: str,
    read_after_apply: ReadAfterApply | None = None,
    health_stages_override: Sequence[str] | None = None,
    health_timeout: float = 30.0,
    health_poll_interval: float = 2.0,
) -> ApplyResult:
    package_set = frozenset(packages)
    if health_timeout <= 0 or health_poll_interval <= 0:
        raise ValueError("health convergence timing is invalid")
    rollback, lifetime, health_stages = effective_stage_policy(stage, package_set, enabled_stages)
    if health_stages_override is not None:
        if any(item not in STAGE_TIMEOUTS for item in health_stages_override):
            raise OpenWrtSafetyError("revert health override contains an unknown stage")
        health_stages = tuple(dict.fromkeys(health_stages_override))
        timed_stages = (stage, *health_stages)
        rollback = max(STAGE_TIMEOUTS[item][0] for item in timed_stages)
        lifetime = max(max(STAGE_TIMEOUTS[item][1] for item in timed_stages), rollback + 180)
    with local_apply_lock(lock_path):
        lock = client.helper_call(
            {
                "object": "homeserver",
                "method": "lock-acquire",
                "arguments": {"controller": controller_id, "pid": os.getpid(), "stage": stage},
            }
        )
        if lock.get("acquired") is not True:
            cleared = client.helper_call(
                {"object": "homeserver", "method": "lock-clear-stale", "arguments": {}}
            )
            if cleared.get("cleared") is not True:
                raise LockContentionError(
                    "router apply lock is held or stale with pending rpcd state"
                )
            lock = client.helper_call(
                {
                    "object": "homeserver",
                    "method": "lock-acquire",
                    "arguments": {
                        "controller": controller_id,
                        "pid": os.getpid(),
                        "stage": stage,
                    },
                }
            )
            if lock.get("acquired") is not True:
                raise LockContentionError("router apply lock could not be reacquired")
        sid: str | None = None
        apply_started = False
        try:
            backup_before_apply(stage)
            created = client.helper_call(
                {"object": "session", "method": "create", "arguments": {"timeout": lifetime}}
            )
            if not isinstance(created.get("sid"), str):
                raise OperationalError("rpcd session creation returned no SID")
            sid = str(created["sid"])
            client.helper_call(
                {
                    "object": "session",
                    "method": "grant",
                    "arguments": {
                        "ubus_rpc_session": sid,
                        "scope": "uci",
                        "objects": sorted(package_set),
                    },
                }
            )
            section_aliases: dict[str, str] = {}
            for mutation in mutations:
                arguments = mutation.get("arguments")
                method = mutation.get("method")
                if method not in {"add", "set", "delete", "rename", "order"} or not isinstance(
                    arguments, Mapping
                ):
                    raise OpenWrtSafetyError("mutation is not an allowlisted UCI operation")
                config = arguments.get("config")
                if config not in package_set:
                    raise OpenWrtSafetyError("mutation package exceeds stage ACL")
                capture = mutation.get("capture_section_as")
                if capture is not None:
                    if method != "add" or not isinstance(capture, str) or "." not in capture:
                        raise OpenWrtSafetyError("section capture metadata is invalid")
                    capture_config, capture_section = capture.split(".", 1)
                    if (
                        capture_config != config
                        or not _UCI_NAME.fullmatch(capture_section)
                        or capture in section_aliases
                    ):
                        raise OpenWrtSafetyError("section capture metadata is invalid")
                resolved_arguments = dict(arguments)
                if method == "order":
                    sections = arguments.get("sections")
                    if not isinstance(sections, Sequence) or isinstance(sections, (str, bytes)):
                        raise OpenWrtSafetyError("section order metadata is invalid")
                    resolved_sections: list[str] = []
                    for section in sections:
                        if not isinstance(section, str) or not _UCI_NAME.fullmatch(section):
                            raise OpenWrtSafetyError("section order metadata is invalid")
                        resolved_sections.append(
                            section_aliases.get(f"{config}.{section}", section)
                        )
                    resolved_arguments["sections"] = resolved_sections
                try:
                    response = client.helper_call(
                        {
                            "object": "uci",
                            "method": method,
                            "arguments": {**resolved_arguments, "ubus_rpc_session": sid},
                        }
                    )
                except OperationalError as error:
                    section = arguments.get("section") or arguments.get("name") or "<section>"
                    raise OperationalError(
                        f"{stage} staging {method} failed for {config}.{section}"
                    ) from error
                if isinstance(capture, str):
                    generated = response.get("section")
                    if not isinstance(generated, str) or not _UCI_NAME.fullmatch(generated):
                        raise OperationalError("anonymous UCI section creation returned no ID")
                    section_aliases[capture] = generated
            staged_projection: dict[str, Any] = {}
            for path, wanted in expected_projection.items():
                if not isinstance(path, str) or len(path.split(".", 2)) != 3:
                    raise OpenWrtSafetyError("expected projection path is invalid")
                config, section, option = path.split(".", 2)
                section_id = f"{config}.{section}"
                actual_section = section_aliases.get(section_id, section)
                actual_path = f"{config}.{actual_section}.{option}"
                if actual_path in staged_projection:
                    raise OpenWrtSafetyError("expected projection aliases collide")
                if (
                    actual_section != section
                    and option == "_name"
                    and expected_projection.get(f"{section_id}._anonymous") is True
                ):
                    wanted = actual_section
                staged_projection[actual_path] = wanted
            compared = client.helper_call(
                {
                    "object": "homeserver",
                    "method": "compare",
                    "arguments": {
                        "ubus_rpc_session": sid,
                        "expected": staged_projection,
                    },
                }
            )
            if compared.get("match") is not True:
                raw_mismatches = compared.get("mismatches")
                mismatches = (
                    sorted(
                        {
                            path
                            for path in raw_mismatches
                            if isinstance(path, str)
                            and 1 <= len(path) <= 256
                            and _IDENTIFIER.fullmatch(path)
                        }
                    )
                    if isinstance(raw_mismatches, Sequence)
                    and not isinstance(raw_mismatches, (str, bytes))
                    else []
                )
                visible = mismatches[:16]
                suffix = (
                    f" (+{len(mismatches) - len(visible)} more)" if len(mismatches) > 16 else ""
                )
                detail = f": {', '.join(visible)}{suffix}" if visible else ""
                raise OpenWrtSafetyError(f"{stage} staged projection mismatch{detail}")
            try:
                apply_started = True
                client.helper_call(
                    {
                        "object": "uci",
                        "method": "apply",
                        "arguments": {
                            "ubus_rpc_session": sid,
                            "rollback": True,
                            "timeout": rollback,
                        },
                    }
                )
            except OperationalError as error:
                # rpcd may have committed and armed rollback. Never retry this call.
                raise ApplyAmbiguousError(
                    "uci apply outcome is ambiguous; validate externally or await timeout; "
                    "not retried"
                ) from error
            try:
                health_deadline = time.monotonic() + min(health_timeout, rollback - 10)
                while True:
                    try:
                        for health_stage in health_stages:
                            health_check(health_stage)
                        break
                    except (OpenWrtSafetyError, OperationalError) as error:
                        if time.monotonic() >= health_deadline:
                            raise OpenWrtSafetyError(
                                f"{stage} health did not converge within "
                                f"{min(health_timeout, rollback - 10):g}s: {error}"
                            ) from error
                        time.sleep(health_poll_interval)
            except Exception:
                # Connectivity still exists if the helper accepts this call. Roll back
                # explicitly; otherwise preserve the SID/lock and let rpcd's timer fire.
                try:
                    client.helper_call(
                        {
                            "object": "uci",
                            "method": "rollback",
                            "arguments": {"ubus_rpc_session": sid},
                        }
                    )
                    client.helper_call(
                        {
                            "object": "session",
                            "method": "destroy",
                            "arguments": {"ubus_rpc_session": sid},
                        }
                    )
                    client.helper_call(
                        {
                            "object": "homeserver",
                            "method": "lock-release",
                            "arguments": {"controller": controller_id, "sid": sid},
                        }
                    )
                    if read_after_apply is not None:
                        read_after_apply(stage)
                except OperationalError:
                    pass
                raise
            client.helper_call(
                {
                    "object": "uci",
                    "method": "confirm",
                    "arguments": {"ubus_rpc_session": sid},
                }
            )
            client.helper_call(
                {
                    "object": "session",
                    "method": "destroy",
                    "arguments": {"ubus_rpc_session": sid},
                }
            )
            client.helper_call(
                {
                    "object": "homeserver",
                    "method": "lock-release",
                    "arguments": {"controller": controller_id, "sid": sid},
                }
            )
            if read_after_apply is not None:
                read_after_apply(stage)
            return ApplyResult(stage, sid, rollback, lifetime, health_stages)
        except Exception:
            # Before apply, cleanup is safe. After apply/ambiguity, preserve SID and remote lock
            # so rpcd's process-lifetime rollback can resolve without a second writer.
            if not apply_started:
                if sid is not None:
                    with suppress(OperationalError):
                        client.helper_call(
                            {
                                "object": "session",
                                "method": "destroy",
                                "arguments": {"ubus_rpc_session": sid},
                            }
                        )
                with suppress(OperationalError):
                    client.helper_call(
                        {
                            "object": "homeserver",
                            "method": "lock-release",
                            "arguments": {"controller": controller_id, "sid": sid or "none"},
                        }
                    )
            raise


class ChunkEncryptor(Protocol):
    def encrypt(self, chunks: Iterable[bytes], destination: BinaryIO) -> None: ...


class ChunkDecryptor(Protocol):
    def decrypt(self, chunks: Iterable[bytes], destination: BinaryIO) -> None: ...


@dataclass(frozen=True)
class BackupMetadata:
    plaintext_size: int
    plaintext_sha256: str
    ciphertext_size: int
    ciphertext_sha256: str


@dataclass(frozen=True)
class TransactionIndex:
    transaction_id: str
    stage: str
    timestamp: str
    bundle: str
    ciphertext_size: int
    ciphertext_sha256: str


class HashingChunks:
    def __init__(self, chunks: Iterable[bytes]) -> None:
        self._chunks = chunks
        self.size = 0
        self.digest = hashlib.sha256()

    def __iter__(self) -> Iterator[bytes]:
        for chunk in self._chunks:
            if not isinstance(chunk, bytes):
                raise TypeError("backup source must yield bytes")
            self.size += len(chunk)
            self.digest.update(chunk)
            yield chunk


class HashingWriter:
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


def stream_encrypted_backup(
    source: Iterable[bytes], encryptor: ChunkEncryptor, destination: BinaryIO
) -> BackupMetadata:
    """Encrypt a binary stream without creating any plaintext file."""

    plaintext = HashingChunks(source)
    ciphertext = HashingWriter(destination)
    encryptor.encrypt(plaintext, cast(BinaryIO, ciphertext))
    ciphertext.flush()
    return BackupMetadata(
        plaintext_size=plaintext.size,
        plaintext_sha256=plaintext.digest.hexdigest(),
        ciphertext_size=ciphertext.size,
        ciphertext_sha256=ciphertext.digest.hexdigest(),
    )


def write_transaction_bundle(
    *,
    payload: Mapping[str, Any],
    encryptor: ChunkEncryptor,
    bundle_path: Path,
    index_path: Path,
) -> TransactionIndex:
    """Write authoritative transaction state only through the encryption stream."""

    transaction_id = payload.get("transaction_id")
    stage = payload.get("stage")
    timestamp = payload.get("timestamp")
    if not isinstance(transaction_id, str) or not re.fullmatch(
        r"[a-zA-Z0-9_-]{8,128}", transaction_id
    ):
        raise ValueError("transaction ID is invalid")
    if stage not in STAGE_PACKAGES:
        raise ValueError("transaction stage is invalid")
    if not isinstance(timestamp, str) or not timestamp:
        raise ValueError("transaction timestamp is invalid")
    if bundle_path.exists() or index_path.exists():
        raise FileExistsError("transaction output already exists")

    plaintext = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    bundle_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=bundle_path.parent, prefix=f".{bundle_path.name}."
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as destination:
            metadata = stream_encrypted_backup((plaintext,), encryptor, destination)
        os.replace(temporary, bundle_path)
    except Exception:
        with suppress(FileNotFoundError):
            temporary.unlink()
        raise

    index = TransactionIndex(
        transaction_id=transaction_id,
        stage=stage,
        timestamp=timestamp,
        bundle=bundle_path.name,
        ciphertext_size=metadata.ciphertext_size,
        ciphertext_sha256=metadata.ciphertext_sha256,
    )
    index_payload = json.dumps(index.__dict__, indent=2, sort_keys=True) + "\n"
    index_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=index_path.parent, prefix=f".{index_path.name}."
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w") as destination:
            destination.write(index_payload)
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary, index_path)
    except Exception:
        with suppress(FileNotFoundError):
            temporary.unlink()
        with suppress(FileNotFoundError):
            bundle_path.unlink()
        raise
    return index


def _transaction_index(path: Path) -> TransactionIndex:
    try:
        raw = json.loads(path.read_text())
        index = TransactionIndex(**raw)
    except (OSError, TypeError, json.JSONDecodeError) as error:
        raise OpenWrtSafetyError("transaction index is invalid") from error
    if (
        index.stage not in STAGE_PACKAGES
        or not re.fullmatch(r"[a-zA-Z0-9_-]{8,128}", index.transaction_id)
        or not re.fullmatch(r"[0-9a-f]{64}", index.ciphertext_sha256)
        or index.ciphertext_size < 1
        or Path(index.bundle).name != index.bundle
    ):
        raise OpenWrtSafetyError("transaction index is invalid")
    return index


def read_transaction_bundle(
    *, index_path: Path, decryptor: ChunkDecryptor, maximum_plaintext: int = 16 * 1024 * 1024
) -> Mapping[str, Any]:
    """Verify ciphertext metadata and decrypt authoritative state only in memory."""

    index = _transaction_index(index_path)
    bundle_path = index_path.parent / index.bundle
    try:
        ciphertext = bundle_path.read_bytes()
    except OSError as error:
        raise OpenWrtSafetyError("transaction ciphertext is unavailable") from error
    if len(ciphertext) != index.ciphertext_size or (
        hashlib.sha256(ciphertext).hexdigest() != index.ciphertext_sha256
    ):
        raise OpenWrtSafetyError("transaction ciphertext integrity check failed")

    plaintext = io.BytesIO()
    try:
        decryptor.decrypt((ciphertext,), plaintext)
    except Exception as error:
        raise OpenWrtSafetyError("transaction decryption failed") from error
    if plaintext.tell() > maximum_plaintext:
        raise OpenWrtSafetyError("transaction plaintext exceeds the safety limit")
    try:
        payload = json.loads(plaintext.getvalue())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OpenWrtSafetyError("transaction plaintext is invalid") from error
    if not isinstance(payload, Mapping):
        raise OpenWrtSafetyError("transaction plaintext is invalid")
    if payload.get("transaction_id") != index.transaction_id or payload.get("stage") != index.stage:
        raise OpenWrtSafetyError("transaction identity does not match its index")
    return payload


def validate_revert_bundle(
    payload: Mapping[str, Any],
    *,
    current_projection: Mapping[str, Any],
    current_parent_transaction_id: str | None,
) -> None:
    """Reject historical restore when current state or accepted lineage has moved on."""

    expected = payload.get("expected_post_projection")
    parent = payload.get("parent_transaction_id")
    if not isinstance(expected, Mapping):
        raise OpenWrtSafetyError("transaction has no expected post-state")
    if _canonical(expected) != _canonical(current_projection):
        raise OpenWrtSafetyError("transaction revert is stale for current owned fields")
    if parent != current_parent_transaction_id:
        raise OpenWrtSafetyError("transaction revert lineage does not match current state")
