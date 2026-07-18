from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, replace
from ipaddress import IPv4Interface, ip_interface
from typing import Any

from homeserver_iac.models.common import Operation, OperationKind, Plan, SecretRef, order_operations
from homeserver_iac.models.openwrt import OpenWrtDesiredState
from homeserver_iac.openwrt import SCOPE, STAGE_PACKAGES, OpenWrtSafetyError

SecretResolver = Callable[[str], str]


@dataclass(frozen=True)
class UciSection:
    config: str
    name: str
    section_type: str
    values: Mapping[str, str | tuple[str, ...]]


@dataclass(frozen=True)
class StageChanges:
    stage: str
    packages: frozenset[str]
    mutations: tuple[Mapping[str, Any], ...]
    expected_projection: Mapping[str, Any]
    owned_paths: tuple[str, ...]
    created_sections: tuple[str, ...]
    deleted_sections: tuple[str, ...]


_SECRET_PATH_ALIASES = {
    "network.wan.username": "openwrt_pppoe_username",
    "network.wan.password": "openwrt_pppoe_password",
    "wireless.hs_guest_wifi_2g.ssid": "openwrt_guest_wifi_ssid",
    "wireless.hs_guest_wifi_2g.key": "openwrt_guest_wifi_psk",
    "wireless.hs_guest_wifi_5g.ssid": "openwrt_guest_wifi_ssid",
    "wireless.hs_guest_wifi_5g.key": "openwrt_guest_wifi_psk",
}

_RETIRED_FACTORY_WAN_RULE_NAMES = frozenset(
    {
        "Allow-DHCP-Renew",
        "Allow-Ping",
        "Allow-IGMP",
        "Allow-DHCPv6",
        "Allow-ICMPv6-Input",
        "Allow-ICMPv6-Forward",
        "Allow-IPSec-ESP",
        "Allow-ISAKMP",
    }
)
_ANSIBLE_OWNED_SECTION_PREFIXES = {
    "base": ("hs_base_host_",),
}


def _network_values(address: str) -> tuple[str, str]:
    interface = ip_interface(address)
    if not isinstance(interface, IPv4Interface):
        raise OpenWrtSafetyError("OpenWrt interface address must be IPv4")
    return str(interface.ip), str(interface.netmask)


def _radio_sections(snapshot: Mapping[str, Any]) -> dict[str, str]:
    radios: dict[str, str] = {}
    for path, value in snapshot.items():
        parts = path.split(".")
        if len(parts) == 3 and parts[0] == "wireless" and parts[2] == "band":
            band = str(value)
            if band in radios:
                raise OpenWrtSafetyError("wireless radio bands are not unique")
            radios[band] = parts[1]
    if set(radios) != {"2g", "5g"}:
        raise OpenWrtSafetyError("wireless radios cannot be mapped uniquely by band")
    return radios


def _bind_existing_sections(
    sections: Sequence[UciSection], snapshot: Mapping[str, Any]
) -> tuple[UciSection, ...]:
    """Bind singleton/default anonymous sections instead of creating duplicates."""

    section_types = {
        ".".join(str(path).split(".")[:2]): value
        for path, value in snapshot.items()
        if str(path).endswith("._type")
    }
    singleton_types = {"system", "dnsmasq", "defaults", "dropbear", "uhttpd"}
    bound: list[UciSection] = []
    claimed: set[str] = set()
    for desired_section in sections:
        exact = f"{desired_section.config}.{desired_section.name}"
        if exact in section_types:
            bound.append(desired_section)
            claimed.add(exact)
            continue
        candidates = [
            section_id
            for section_id, section_type in section_types.items()
            if section_id.startswith(desired_section.config + ".")
            and section_type == desired_section.section_type
            and section_id not in claimed
        ]
        if desired_section.section_type in {"zone", "rule", "device"}:
            wanted_name = desired_section.values.get("name")
            candidates = [
                item for item in candidates if snapshot.get(f"{item}.name") == wanted_name
            ]
        elif desired_section.section_type == "forwarding":
            candidates = [
                item
                for item in candidates
                if snapshot.get(f"{item}.src") == desired_section.values.get("src")
                and snapshot.get(f"{item}.dest") == desired_section.values.get("dest")
            ]
        elif desired_section.section_type not in singleton_types:
            candidates = []
        if len(candidates) > 1:
            raise OpenWrtSafetyError(
                "multiple existing UCI sections match "
                f"{desired_section.config}.{desired_section.section_type}"
            )
        if candidates:
            actual_name = candidates[0].split(".", 1)[1]
            bound.append(replace(desired_section, name=actual_name))
            claimed.add(candidates[0])
        else:
            bound.append(desired_section)
    return tuple(bound)


def _secret(resolver: SecretResolver | None, alias: str) -> str:
    if resolver is None:
        return f"<secret:{alias}>"
    value = resolver(alias)
    if not value or "\0" in value or "\n" in value or "\r" in value:
        raise OpenWrtSafetyError(f"secret alias is absent or invalid: {alias}")
    return value


def _wifi_ssid(resolver: SecretResolver | None, alias: str) -> str:
    value = _secret(resolver, alias)
    if not 1 <= len(value.encode()) <= 32:
        raise OpenWrtSafetyError(f"Wi-Fi SSID alias has invalid byte length: {alias}")
    return value


def _wifi_psk(resolver: SecretResolver | None, alias: str) -> str:
    value = _secret(resolver, alias)
    is_passphrase = value.isascii() and value.isprintable() and 8 <= len(value) <= 63
    is_raw_psk = len(value) == 64 and all(
        character in "0123456789abcdefABCDEF" for character in value
    )
    if not (is_passphrase or is_raw_psk):
        raise OpenWrtSafetyError(f"Wi-Fi PSK alias has invalid length or format: {alias}")
    return value


def desired_uci_sections(
    desired: OpenWrtDesiredState,
    stage: str,
    *,
    snapshot: Mapping[str, Any],
    resolve_secret: SecretResolver | None = None,
    accepted_stages: Collection[str] = (),
) -> tuple[UciSection, ...]:
    """Render only one stage's UCI ownership projection."""

    trusted_ip, trusted_mask = _network_values(desired.networks.trusted.address)
    guest_ip, guest_mask = _network_values(desired.networks.guest.address)
    guest_limit = (
        int(desired.networks.guest.dhcp_end.split(".")[-1])
        - int(desired.networks.guest.dhcp_start.split(".")[-1])
        + 1
    )
    sections: list[UciSection] = []

    if stage == "bootstrap-sanitize":
        return ()
    if stage == "base":
        sections.extend(
            (
                UciSection("network", "br_lan", "device", {"name": "br-lan", "type": "bridge"}),
                UciSection(
                    "network",
                    "lan",
                    "interface",
                    {
                        "device": "br-lan",
                        "proto": "static",
                        "ipaddr": trusted_ip,
                        "netmask": trusted_mask,
                    },
                ),
                UciSection(
                    "firewall",
                    "defaults",
                    "defaults",
                    {
                        "input": "REJECT",
                        "output": "ACCEPT",
                        "forward": "REJECT",
                        "synflood_protect": "1",
                    },
                ),
                UciSection(
                    "firewall",
                    "hs_base_trusted",
                    "zone",
                    {
                        "name": "lan",
                        "network": ("lan",),
                        "input": "ACCEPT",
                        "output": "ACCEPT",
                        "forward": "ACCEPT",
                    },
                ),
                UciSection(
                    "dropbear",
                    "dropbear",
                    "dropbear",
                    {
                        "Interface": "lan",
                        "PasswordAuth": "off",
                        "RootPasswordAuth": "off",
                        "Port": "22",
                    },
                ),
                UciSection(
                    "uhttpd",
                    "main",
                    "uhttpd",
                    {
                        "listen_http": (),
                        "listen_https": (f"{trusted_ip}:443",),
                        "redirect_https": "1",
                    },
                ),
            )
        )
    elif stage == "wan":
        ipv6_accepted = "ipv6" in accepted_stages
        wan_values: dict[str, str | tuple[str, ...]] = {
            "device": "wan.835",
            "proto": "pppoe",
            "username": _secret(resolve_secret, desired.wan.username.secret_ref.alias),
            "password": _secret(resolve_secret, desired.wan.password.secret_ref.alias),
            "peerdns": "1",
        }
        if not ipv6_accepted:
            # PPPoE defaults to automatic DHCPv6. Keep the WAN stage IPv4-only
            # until the independently protected IPv6 stage is accepted.
            wan_values["ipv6"] = "0"
        sections.extend(
            (
                UciSection(
                    "network",
                    "wan_vlan",
                    "device",
                    {"name": "wan.835", "type": "8021q", "ifname": "wan", "vid": "835"},
                ),
                UciSection(
                    "network",
                    "wan",
                    "interface",
                    wan_values,
                ),
                UciSection(
                    "firewall",
                    "hs_wan_zone",
                    "zone",
                    {
                        "name": "wan",
                        "network": ("wan", "wan6"),
                        "input": "REJECT",
                        "output": "ACCEPT",
                        "forward": "REJECT",
                        "masq": "1",
                        "mtu_fix": "1",
                    },
                ),
                UciSection(
                    "firewall",
                    "hs_wan_trusted_forward",
                    "forwarding",
                    {"src": "lan", "dest": "wan"},
                ),
            )
        )
        if not ipv6_accepted:
            sections.extend(
                (
                    UciSection("network", "globals", "globals", {"ula_prefix": ()}),
                    UciSection(
                        "network",
                        "lan",
                        "interface",
                        {"ip6assign": (), "ip6hint": ()},
                    ),
                    UciSection(
                        "dhcp",
                        "lan",
                        "dhcp",
                        {"ra": "disabled", "dhcpv6": "disabled", "ndp": "disabled"},
                    ),
                )
            )
    elif stage == "guest":
        radios = _radio_sections(snapshot)
        sections.extend(
            (
                UciSection("network", "br_guest", "device", {"name": "br-guest", "type": "bridge"}),
                UciSection(
                    "network",
                    "guest",
                    "interface",
                    {
                        "device": "br-guest",
                        "proto": "static",
                        "ipaddr": guest_ip,
                        "netmask": guest_mask,
                    },
                ),
                UciSection(
                    "dhcp",
                    "guest",
                    "dhcp",
                    {
                        "interface": "guest",
                        "start": desired.networks.guest.dhcp_start.split(".")[-1],
                        "limit": str(guest_limit),
                        "leasetime": desired.networks.guest.lease_time,
                    },
                ),
                UciSection(
                    "firewall",
                    "hs_guest_zone",
                    "zone",
                    {
                        "name": "guest",
                        "network": ("guest",),
                        "input": "REJECT",
                        "output": "ACCEPT",
                        "forward": "REJECT",
                    },
                ),
                UciSection(
                    "firewall",
                    "hs_guest_wan_forward",
                    "forwarding",
                    {"src": "guest", "dest": "wan"},
                ),
                UciSection(
                    "firewall",
                    "hs_guest_dns",
                    "rule",
                    {
                        "name": "Allow-Guest-DNS",
                        "src": "guest",
                        "dest_port": "53",
                        "proto": ("tcp", "udp"),
                        "target": "ACCEPT",
                    },
                ),
                UciSection(
                    "firewall",
                    "hs_guest_dhcp",
                    "rule",
                    {
                        "name": "Allow-Guest-DHCP",
                        "src": "guest",
                        "dest_port": "67-68",
                        "proto": "udp",
                        "family": "ipv4",
                        "target": "ACCEPT",
                    },
                ),
            )
        )
        for band, radio_section in radios.items():
            sections.append(
                UciSection(
                    "wireless",
                    f"hs_guest_wifi_{band}",
                    "wifi-iface",
                    {
                        "device": radio_section,
                        "mode": "ap",
                        "network": "guest",
                        "ssid": _wifi_ssid(
                            resolve_secret, desired.wireless.guest.ssid.secret_ref.alias
                        ),
                        "encryption": desired.wireless.guest.encryption,
                        "key": _wifi_psk(
                            resolve_secret, desired.wireless.guest.psk.secret_ref.alias
                        ),
                        "isolate": "1",
                        "bridge_isolate": "1",
                    },
                )
            )
    elif stage == "ipv6":
        sections.extend(
            (
                UciSection(
                    "network", "globals", "globals", {"ula_prefix": desired.networks.ula_prefix}
                ),
                UciSection("network", "wan", "interface", {"ipv6": "1"}),
                UciSection(
                    "network",
                    "wan6",
                    "interface",
                    {"device": "@wan", "proto": "dhcpv6", "reqaddress": "try", "reqprefix": "auto"},
                ),
                UciSection("network", "lan", "interface", {"ip6assign": "64", "ip6hint": "0"}),
                UciSection("network", "guest", "interface", {"ip6assign": "64", "ip6hint": "1"}),
                UciSection(
                    "dhcp", "lan", "dhcp", {"ra": "server", "dhcpv6": "server", "ndp": "disabled"}
                ),
                UciSection(
                    "dhcp", "guest", "dhcp", {"ra": "server", "dhcpv6": "server", "ndp": "disabled"}
                ),
                UciSection(
                    "firewall",
                    "hs_ipv6_dhcpv6",
                    "rule",
                    {
                        "name": "Allow-DHCPv6",
                        "src": "wan",
                        "proto": "udp",
                        "dest_port": "546",
                        "family": "ipv6",
                        "target": "ACCEPT",
                    },
                ),
                UciSection(
                    "firewall",
                    "hs_ipv6_mld",
                    "rule",
                    {
                        "name": "Allow-MLD",
                        "src": "wan",
                        "proto": "icmp",
                        "family": "ipv6",
                        "icmp_type": ("130/0", "131/0", "132/0", "143/0"),
                        "target": "ACCEPT",
                    },
                ),
                UciSection(
                    "firewall",
                    "hs_ipv6_icmp",
                    "rule",
                    {
                        "name": "Allow-ICMPv6-Input",
                        "src": "wan",
                        "proto": "icmp",
                        "family": "ipv6",
                        "icmp_type": (
                            "destination-unreachable",
                            "packet-too-big",
                            "time-exceeded",
                            "bad-header",
                            "unknown-header-type",
                            "router-solicitation",
                            "neighbour-solicitation",
                            "router-advertisement",
                            "neighbour-advertisement",
                        ),
                        "limit": "1000/sec",
                        "target": "ACCEPT",
                    },
                ),
                UciSection(
                    "firewall",
                    "hs_ipv6_forward",
                    "rule",
                    {
                        "name": "Allow-ICMPv6-Forward",
                        "src": "wan",
                        "dest": "*",
                        "proto": "icmp",
                        "family": "ipv6",
                        "icmp_type": (
                            "destination-unreachable",
                            "packet-too-big",
                            "time-exceeded",
                            "bad-header",
                            "unknown-header-type",
                        ),
                        "limit": "1000/sec",
                        "target": "ACCEPT",
                    },
                ),
                UciSection(
                    "firewall",
                    "hs_ipv6_guest_dhcp",
                    "rule",
                    {
                        "name": "Allow-Guest-DHCPv6",
                        "src": "guest",
                        "proto": "udp",
                        "dest_port": "547",
                        "family": "ipv6",
                        "target": "ACCEPT",
                    },
                ),
                UciSection(
                    "firewall",
                    "hs_ipv6_guest_icmp",
                    "rule",
                    {
                        "name": "Allow-Guest-ICMPv6",
                        "src": "guest",
                        "proto": "icmp",
                        "family": "ipv6",
                        "icmp_type": (
                            "destination-unreachable",
                            "packet-too-big",
                            "time-exceeded",
                            "bad-header",
                            "unknown-header-type",
                            "router-solicitation",
                            "neighbour-solicitation",
                            "router-advertisement",
                            "neighbour-advertisement",
                        ),
                        "limit": "1000/sec",
                        "target": "ACCEPT",
                    },
                ),
            )
        )
    else:
        raise ValueError("unknown OpenWrt stage")
    return _bind_existing_sections(sections, snapshot)


def _section_exists(snapshot: Mapping[str, Any], config: str, section: str) -> bool:
    prefix = f"{config}.{section}."
    return any(path.startswith(prefix) for path in snapshot)


def _uci_equal(current: Any, desired: Any) -> bool:
    if isinstance(current, Sequence) and not isinstance(current, (str, bytes)):
        current = tuple(current)
    if isinstance(desired, Sequence) and not isinstance(desired, (str, bytes)):
        desired = tuple(desired)
    return bool(current == desired)


def _stale_sections(snapshot: Mapping[str, Any], stage: str, declared: set[str]) -> tuple[str, ...]:
    prefix = f"hs_{stage.replace('-', '_')}_"
    excluded = _ANSIBLE_OWNED_SECTION_PREFIXES.get(stage, ())
    observed = {
        ".".join(path.split(".")[:2])
        for path in snapshot
        if len(path.split(".")) == 3
        and path.split(".")[1].startswith(prefix)
        and not path.split(".")[1].startswith(excluded)
    }
    return tuple(sorted(observed - declared))


def _retired_factory_wan_rules(snapshot: Mapping[str, Any]) -> tuple[str, ...]:
    sections = {
        ".".join(str(path).split(".")[:2])
        for path, value in snapshot.items()
        if str(path).startswith("firewall.") and str(path).endswith("._type") and value == "rule"
    }
    return tuple(
        sorted(
            section
            for section in sections
            if not section.split(".", 1)[1].startswith("hs_")
            and snapshot.get(f"{section}.src") == "wan"
            and snapshot.get(f"{section}.name") in _RETIRED_FACTORY_WAN_RULE_NAMES
        )
    )


def validate_clean_image_transition(snapshot: Mapping[str, Any], *, sanitized: bool) -> None:
    expected = {
        "network.lan._type": "interface",
        "network.lan.device": "br-lan",
        "network.lan.proto": "static",
        "network.lan.ipaddr": ["192.168.1.1/24"],
        "network.lan.netmask": None,
    }
    if sanitized:
        wan_matches = not any(
            str(path).startswith(("network.wan.", "network.wan6.")) for path in snapshot
        )
    else:
        expected.update(
            {
                "network.wan._type": "interface",
                "network.wan.device": "wan",
                "network.wan.proto": "dhcp",
                "network.wan6._type": "interface",
                "network.wan6.device": "wan",
                "network.wan6.proto": "dhcpv6",
            }
        )
        wan_matches = True
    radio_sections = {
        str(path).split(".")[1]
        for path, value in snapshot.items()
        if str(path).startswith("wireless.")
        and str(path).endswith("._type")
        and value == "wifi-device"
    }
    wifi_iface_sections = {
        str(path).split(".")[1]
        for path, value in snapshot.items()
        if str(path).startswith("wireless.")
        and str(path).endswith("._type")
        and value == "wifi-iface"
    }
    if any(snapshot.get(path) != value for path, value in expected.items()) or (
        not wan_matches
        or len(radio_sections) != 2
        or len(wifi_iface_sections) < 2
        or any(
            snapshot.get(f"wireless.{interface}.disabled") != "1"
            for interface in wifi_iface_sections
        )
    ):
        raise OpenWrtSafetyError("bootstrap-sanitize requires the exact clean-image WAN state")


def build_stage_changes(
    desired: OpenWrtDesiredState,
    stage: str,
    *,
    snapshot: Mapping[str, Any],
    resolve_secret: SecretResolver | None = None,
    secret_matches: Mapping[str, bool] | None = None,
    accepted_stages: Collection[str] = (),
) -> StageChanges:
    if stage not in STAGE_PACKAGES:
        raise ValueError("unknown OpenWrt stage")
    if stage == "bootstrap-sanitize":
        validate_clean_image_transition(snapshot, sanitized=False)
        deleted = ("network.wan", "network.wan6")
        bootstrap_mutations = tuple(
            {"method": "delete", "arguments": {"config": "network", "section": name}}
            for name in ("wan", "wan6")
        )
        return StageChanges(
            stage,
            STAGE_PACKAGES[stage],
            bootstrap_mutations,
            {f"{item}._section_absent": None for item in deleted},
            (),
            (),
            deleted,
        )

    sections = desired_uci_sections(
        desired,
        stage,
        snapshot=snapshot,
        resolve_secret=resolve_secret,
        accepted_stages=accepted_stages,
    )
    mutations: list[Mapping[str, Any]] = []
    expected: dict[str, Any] = {}
    owned: list[str] = []
    created: list[str] = []
    declared = {f"{section.config}.{section.name}" for section in sections}
    matches = secret_matches or {}
    for section in sections:
        section_id = f"{section.config}.{section.name}"
        exists = _section_exists(snapshot, section.config, section.name)
        if not exists:
            created.append(section_id)
            mutations.append(
                {
                    "method": "add",
                    "arguments": {
                        "config": section.config,
                        "type": section.section_type,
                        "name": section.name,
                    },
                }
            )
        changed: dict[str, Any] = {}
        for option, value in section.values.items():
            path = f"{section_id}.{option}"
            owned.append(path)
            if value == ():
                expected[path] = None
                if path in snapshot:
                    mutations.append(
                        {
                            "method": "delete",
                            "arguments": {
                                "config": section.config,
                                "section": section.name,
                                "option": option,
                            },
                        }
                    )
                continue
            expected[path] = value
            if matches.get(path) is True:
                continue
            if not _uci_equal(snapshot.get(path), value):
                changed[option] = value
        if changed:
            mutations.append(
                {
                    "method": "set",
                    "arguments": {
                        "config": section.config,
                        "section": section.name,
                        "values": changed,
                    },
                }
            )

    removed_sections = set(_stale_sections(snapshot, stage, declared))
    if stage == "wan":
        removed_sections.update(_retired_factory_wan_rules(snapshot))
    for section_id in sorted(removed_sections):
        config, section_name = section_id.split(".", 1)
        mutations.append(
            {
                "method": "delete",
                "arguments": {"config": config, "section": section_name},
            }
        )
        expected[f"{section_id}._section_absent"] = None
    return StageChanges(
        stage=stage,
        packages=STAGE_PACKAGES[stage],
        mutations=tuple(mutations),
        expected_projection=expected,
        owned_paths=tuple(sorted(owned)),
        created_sections=tuple(sorted(created)),
        deleted_sections=tuple(sorted(removed_sections)),
    )


def plan_stage_changes(changes: StageChanges) -> Plan:
    """Serialize a UCI changeset as field-only, secret-reference operations."""

    changed_fields: dict[str, set[str]] = {}
    kinds: dict[str, OperationKind] = {}
    for mutation in changes.mutations:
        arguments = mutation["arguments"]
        config = str(arguments["config"])
        section = str(arguments.get("section") or arguments.get("name"))
        resource_id = f"{config}.{section}"
        method = mutation["method"]
        if method == "add":
            kinds[resource_id] = OperationKind.CREATE
        elif method == "delete" and "option" not in arguments:
            kinds[resource_id] = OperationKind.DELETE
        elif method == "delete":
            kinds.setdefault(resource_id, OperationKind.UPDATE)
            changed_fields.setdefault(resource_id, set()).add(str(arguments["option"]))
        else:
            kinds.setdefault(resource_id, OperationKind.UPDATE)
            values = arguments.get("values", {})
            if isinstance(values, Mapping):
                changed_fields.setdefault(resource_id, set()).update(str(key) for key in values)

    declared = {".".join(path.split(".")[:2]) for path in changes.expected_projection}
    operations: list[Operation] = []
    for resource_id in sorted(declared | kinds.keys()):
        kind = kinds.get(resource_id, OperationKind.UNCHANGED)
        aliases = sorted(
            {
                alias
                for path, alias in _SECRET_PATH_ALIASES.items()
                if path.startswith(resource_id + ".")
            }
        )
        operations.append(
            Operation(
                kind=kind,
                scope=SCOPE,
                resource_id=resource_id,
                summary=(
                    "OpenWrt UCI section is current"
                    if kind is OperationKind.UNCHANGED
                    else "OpenWrt UCI section differs from desired stage state"
                ),
                changed_fields=tuple(sorted(changed_fields.get(resource_id, set()))),
                secret_refs=tuple(SecretRef(alias=alias) for alias in aliases),
            )
        )
    return Plan(operations=order_operations(operations))
