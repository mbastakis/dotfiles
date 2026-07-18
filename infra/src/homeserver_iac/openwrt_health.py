from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from ipaddress import IPv4Address, ip_address, ip_network
from typing import Any

from homeserver_iac.openwrt import OpenWrtSafetyError

HealthState = Mapping[str, object]
HealthGate = Callable[[HealthState], None]


def _mapping(parent: Mapping[str, object], key: str, path: str) -> Mapping[str, object]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise OpenWrtSafetyError(f"{path}.{key} must be an object")
    return value


def _runtime(state: HealthState, stage: str) -> Mapping[str, object]:
    return _mapping(_mapping(state, "runtime", "state"), stage, "runtime")


def _require(stage: str, observed: Mapping[str, object], expected: Mapping[str, object]) -> None:
    failures = [
        f"{name} must be {value!r}"
        for name, value in expected.items()
        if name not in observed
        or type(observed[name]) is not type(value)
        or observed[name] != value
    ]
    if failures:
        raise OpenWrtSafetyError(f"{stage} health failed: {'; '.join(failures)}")


def validate_bootstrap_sanitize_health(state: HealthState) -> None:
    """Require factory WAN and wireless surfaces to be absent before base setup."""

    _require(
        "bootstrap-sanitize",
        _runtime(state, "bootstrap-sanitize"),
        {"default_wan": False, "default_wan6": False, "wireless": False},
    )


def validate_base_health(state: HealthState) -> None:
    """Require wired trusted-LAN management and the core LAN services."""

    _require(
        "base",
        _runtime(state, "base"),
        {
            "wired_ssh": True,
            "lan_address": "192.168.1.1/24",
            "dhcp": True,
            "dns": True,
            "firewall": True,
            "management_network": "trusted",
            "ssh_password_auth": False,
            "luci_https_only": True,
        },
    )


def validate_wan_health(state: HealthState) -> None:
    """Require the production VLAN 835 PPPoE path without WAN management."""

    _require(
        "wan",
        _runtime(state, "wan"),
        {
            "up": True,
            "protocol": "pppoe",
            "vlan_id": 835,
            "device": "pppoe-wan",
            "public_ipv4": True,
            "peer_dns": True,
            "mtu": 1492,
            "firewall": True,
            "management_exposed": False,
            "ipv6_stage_consistent": True,
            "wan_ingress_blocked": True,
        },
    )


def validate_main_wifi_health(state: HealthState) -> None:
    """Require the fixed Greek 2.4/5 GHz trusted-radio configuration."""

    observed = _runtime(state, "main-wifi")
    _require(
        "main-wifi",
        observed,
        {
            "up": True,
            "network": "trusted",
            "country": "GR",
            "wps": False,
            "fast_transition": False,
            "same_bss_isolation": False,
            "bridge_isolation": False,
        },
    )
    radios = observed.get("radios")
    if not isinstance(radios, Sequence) or isinstance(radios, (str, bytes)):
        raise OpenWrtSafetyError("main-wifi health failed: radios must be a list")
    normalized: set[tuple[object, object, object]] = set()
    for radio in radios:
        if not isinstance(radio, Mapping):
            raise OpenWrtSafetyError("main-wifi health failed: each radio must be an object")
        normalized.add((radio.get("band"), radio.get("channel"), radio.get("width")))
    if normalized != {("2g", 11, 20), ("5g", 36, 80)} or len(radios) != 2:
        raise OpenWrtSafetyError("main-wifi health failed: radios must be 2g/11/20 and 5g/36/80")


def validate_guest_health(state: HealthState) -> None:
    """Require guest Internet and bidirectional client/trusted isolation."""

    _require(
        "guest",
        _runtime(state, "guest"),
        {
            "up": True,
            "subnet": "192.168.30.0/24",
            "internet": True,
            "router_management_blocked": True,
            "trusted_blocked": True,
            "same_bss_isolation": True,
            "cross_radio_isolation": True,
            "trusted_to_guest_blocked": True,
        },
    )


def validate_ipv6_health(state: HealthState) -> None:
    """Require usable PD, distinct /64s, ULA service, and IPv6 isolation."""

    observed = _runtime(state, "ipv6")
    _require(
        "ipv6",
        observed,
        {
            "trusted_prefix_length": 64,
            "guest_prefix_length": 64,
            "distinct_prefixes": True,
            "trusted_ula": True,
            "guest_ula": True,
            "dns": True,
            "internet": True,
            "icmpv6": True,
            "guest_to_trusted_blocked": True,
            "wan_ingress_blocked": True,
            "management_exposed": False,
            "guest_dhcpv6": True,
            "guest_icmpv6": True,
        },
    )
    delegated_length = observed.get("delegated_prefix_length")
    if type(delegated_length) is not int or delegated_length > 63 or delegated_length < 0:
        raise OpenWrtSafetyError("ipv6 health failed: delegated prefix must be /63 or shorter")


def validate_sqm_health(state: HealthState) -> None:
    """Require the single reviewed CAKE queue and disabled flow offloading."""

    _require(
        "sqm",
        _runtime(state, "sqm"),
        {
            "enabled": True,
            "device": "pppoe-wan",
            "enabled_queues": 1,
            "qdisc": "cake",
            "script": "piece_of_cake.qos",
            "download_kbit": 87890,
            "upload_kbit": 8790,
            "overhead": 50,
            "mpu": 84,
            "multiqueue": False,
            "flow_offloading": False,
            "flow_offloading_hw": False,
            "besteffort": True,
            "noatm": True,
            "cake_mq": False,
            "cake_egress": True,
            "cake_ingress": True,
            "runtime_rates": True,
        },
    )


HEALTH_GATES: Mapping[str, HealthGate] = {
    "bootstrap-sanitize": validate_bootstrap_sanitize_health,
    "base": validate_base_health,
    "wan": validate_wan_health,
    "main-wifi": validate_main_wifi_health,
    "guest": validate_guest_health,
    "ipv6": validate_ipv6_health,
    "sqm": validate_sqm_health,
}


def validate_stage_health(stage: str, state: HealthState) -> None:
    """Run one named health gate against an already normalized observation."""

    try:
        gate = HEALTH_GATES[stage]
    except KeyError as error:
        raise OpenWrtSafetyError(f"unknown OpenWrt health stage: {stage}") from error
    gate(state)


def derive_health_observations(state: HealthState) -> dict[str, Any]:
    """Derive conservative stage health fields from filtered UCI/runtime reads."""

    runtime = state.get("runtime")
    if isinstance(runtime, Mapping) and all(stage in runtime for stage in HEALTH_GATES):
        return dict(state)
    uci_value = state.get("health_uci", state.get("uci"))
    if not isinstance(uci_value, Mapping) or not isinstance(runtime, Mapping):
        raise OpenWrtSafetyError("state lacks filtered UCI/runtime observations")
    uci = uci_value
    processes = runtime.get("processes", {})
    process_state = processes if isinstance(processes, Mapping) else {}
    wan_value = runtime.get("wan", {})
    wan = wan_value if isinstance(wan_value, Mapping) else {}
    wan6_value = runtime.get("wan6", {})
    wan6 = wan6_value if isinstance(wan6_value, Mapping) else {}
    wireless_value = runtime.get("wireless", {})
    wireless = wireless_value if isinstance(wireless_value, Mapping) else {}

    public_ipv4 = False
    addresses = wan.get("ipv4-address", [])
    if isinstance(addresses, Sequence) and not isinstance(addresses, (str, bytes)):
        for address in addresses:
            if isinstance(address, Mapping) and isinstance(address.get("address"), str):
                parsed = ip_address(str(address["address"]))
                public_ipv4 = isinstance(parsed, IPv4Address) and parsed.is_global
    delegated_length = 128
    prefixes = wan6.get("ipv6-prefix", [])
    if isinstance(prefixes, Sequence) and not isinstance(prefixes, (str, bytes)):
        for prefix in prefixes:
            if isinstance(prefix, Mapping) and isinstance(prefix.get("address"), str):
                length = prefix.get("mask", prefix.get("prefix", 128))
                if type(length) is int:
                    delegated_length = min(delegated_length, length)
    up_bss: set[str] = set()
    for radio in wireless.values():
        if not isinstance(radio, Mapping) or radio.get("up") is not True:
            continue
        interfaces = radio.get("interfaces", [])
        if not isinstance(interfaces, Sequence) or isinstance(interfaces, (str, bytes)):
            continue
        for interface in interfaces:
            if isinstance(interface, Mapping):
                section = interface.get("section", interface.get("config"))
                if isinstance(section, str):
                    up_bss.add(section)
    radio_sections = {
        str(value): str(path).split(".")[1]
        for path, value in uci.items()
        if str(path).startswith("wireless.") and str(path).endswith(".band")
    }
    qdisc = str(runtime.get("qdisc", ""))
    firewall_value = state.get("firewall")
    firewall = firewall_value if isinstance(firewall_value, Mapping) else {}
    listeners_value = state.get("listeners")
    listeners = (
        listeners_value
        if isinstance(listeners_value, Sequence) and not isinstance(listeners_value, (str, bytes))
        else []
    )

    def forwarding_exists(source: str, destination: str) -> bool:
        sections = {
            ".".join(str(path).split(".")[:2])
            for path, value in uci.items()
            if str(path).endswith("._type") and value == "forwarding"
        }
        return any(
            uci.get(f"{section}.src") == source and uci.get(f"{section}.dest") == destination
            for section in sections
        )

    def accept_rule_exists(source: str, destination: str) -> bool:
        sections = {
            ".".join(str(path).split(".")[:2])
            for path, value in uci.items()
            if str(path).endswith("._type") and value == "rule"
        }
        allowed_forward_icmp = {
            "destination-unreachable",
            "packet-too-big",
            "time-exceeded",
            "bad-header",
            "unknown-header-type",
        }
        for section in sections:
            rule_source = uci.get(f"{section}.src")
            rule_destination = uci.get(f"{section}.dest")
            if (
                rule_source not in {source, "*"}
                or rule_destination not in {destination, "*"}
                or uci.get(f"{section}.target") != "ACCEPT"
            ):
                continue
            protocol = uci.get(f"{section}.proto")
            protocols = [protocol] if isinstance(protocol, str) else protocol
            icmp_types = uci.get(f"{section}.icmp_type", [])
            if isinstance(icmp_types, str):
                icmp_types = [icmp_types]
            if (
                source == "wan"
                and rule_source == "wan"
                and isinstance(protocols, Sequence)
                and set(str(item) for item in protocols) == {"icmp"}
                and isinstance(icmp_types, Sequence)
                and bool(icmp_types)
                and set(str(item) for item in icmp_types) <= allowed_forward_icmp
            ):
                continue
            return True
        return False

    guest_admin_listener = any(
        isinstance(listener, Mapping) and listener.get("network") == "guest"
        for listener in listeners
    )
    wan_admin_listener = any(
        isinstance(listener, Mapping) and listener.get("network") == "wan" for listener in listeners
    )
    lan_ip = str(uci.get("network.lan.ipaddr", ""))
    lan_mask = str(uci.get("network.lan.netmask", ""))
    try:
        lan_address = str(ip_network(f"{lan_ip}/{lan_mask}", strict=False))
        if lan_ip:
            lan_address = f"{lan_ip}/{lan_address.split('/', 1)[1]}"
    except ValueError:
        lan_address = ""
    ipv6_stage_configured = (
        uci.get("network.wan.ipv6") == "1"
        and uci.get("network.wan6.proto") == "dhcpv6"
        and uci.get("network.lan.ip6assign") == "64"
        and uci.get("network.guest.ip6assign") == "64"
        and bool(uci.get("network.globals.ula_prefix"))
        and uci.get("dhcp.lan.ra") == "server"
        and uci.get("dhcp.guest.ra") == "server"
    )
    ipv6_suppressed = (
        uci.get("network.wan.ipv6") == "0"
        and wan6.get("up") is not True
        and delegated_length == 128
        and not uci.get("network.globals.ula_prefix")
        and not uci.get("network.lan.ip6assign")
        and uci.get("dhcp.lan.ra") == "disabled"
        and uci.get("dhcp.lan.dhcpv6") == "disabled"
    )
    allowed_wan_input_rules = {
        "Allow-DHCPv6",
        "Allow-MLD",
        "Allow-ICMPv6-Input",
    }
    unsafe_wan_input = any(
        uci.get(f"{section}.src") == "wan"
        and uci.get(f"{section}.target") == "ACCEPT"
        and not uci.get(f"{section}.dest")
        and (
            uci.get(f"{section}.family") != "ipv6"
            or uci.get(f"{section}.name") not in allowed_wan_input_rules
        )
        for section in {
            ".".join(str(path).split(".")[:2])
            for path, value in uci.items()
            if str(path).endswith("._type") and value == "rule"
        }
    )
    wan_ingress_blocked = (
        not unsafe_wan_input
        and not forwarding_exists("wan", "lan")
        and not forwarding_exists("wan", "guest")
        and not accept_rule_exists("wan", "lan")
        and not accept_rule_exists("wan", "guest")
    )
    health = {
        "bootstrap-sanitize": {
            "default_wan": uci.get("network.wan.proto") == "dhcp",
            "default_wan6": uci.get("network.wan6.proto") == "dhcpv6",
            "wireless": any(
                path.startswith("wireless.") and path.endswith(".disabled") and value == "0"
                for path, value in uci.items()
            ),
        },
        "base": {
            "wired_ssh": runtime.get("strict_ssh") is True,
            "lan_address": lan_address,
            "dhcp": process_state.get("dnsmasq") is True,
            "dns": process_state.get("dnsmasq") is True,
            "firewall": process_state.get("firewall") is True,
            "management_network": "trusted"
            if uci.get("dropbear.dropbear.Interface") == "lan"
            else "unknown",
            "ssh_password_auth": uci.get("dropbear.dropbear.PasswordAuth") not in {"off", "0"},
            "luci_https_only": not bool(uci.get("uhttpd.main.listen_http"))
            and bool(uci.get("uhttpd.main.listen_https")),
        },
        "wan": {
            "up": wan.get("up") is True,
            "protocol": uci.get("network.wan.proto"),
            "vlan_id": int(str(uci.get("network.wan_vlan.vid", "0"))),
            "device": wan.get("l3_device"),
            "public_ipv4": public_ipv4,
            "peer_dns": bool(wan.get("dns-server")),
            "mtu": (
                int(str(runtime.get("wan_mtu")))
                if str(runtime.get("wan_mtu", "")).isdigit()
                else (
                    wan.get("data", {}).get("mtu")
                    if isinstance(wan.get("data"), Mapping)
                    else wan.get("mtu")
                )
            ),
            "firewall": process_state.get("firewall") is True,
            "management_exposed": bool(firewall.get("wan_management", True)),
            "ipv6_stage_consistent": ipv6_stage_configured or ipv6_suppressed,
            "wan_ingress_blocked": wan_ingress_blocked,
        },
        "main-wifi": {
            "up": {"hs_main_wifi_2g", "hs_main_wifi_5g"} <= up_bss,
            "network": (
                "trusted"
                if all(
                    uci.get(f"wireless.hs_main_wifi_{band}.network") == "lan"
                    for band in ("2g", "5g")
                )
                else "unknown"
            ),
            "country": (
                "GR"
                if set(radio_sections) == {"2g", "5g"}
                and all(
                    uci.get(f"wireless.{section}.country") == "GR"
                    for section in radio_sections.values()
                )
                else "unknown"
            ),
            "wps": any(
                uci.get(f"wireless.hs_main_wifi_{band}.wps_pushbutton") == "1"
                for band in ("2g", "5g")
            ),
            "fast_transition": any(
                uci.get(f"wireless.hs_main_wifi_{band}.ieee80211r") == "1" for band in ("2g", "5g")
            ),
            "same_bss_isolation": any(
                uci.get(f"wireless.hs_main_wifi_{band}.isolate") == "1" for band in ("2g", "5g")
            ),
            "bridge_isolation": any(
                uci.get(f"wireless.hs_main_wifi_{band}.bridge_isolate") == "1"
                for band in ("2g", "5g")
            ),
            "radios": [
                {
                    "band": band,
                    "channel": int(
                        str(uci.get(f"wireless.{radio_sections.get(band, '')}.channel", "0"))
                    ),
                    "width": int(
                        str(
                            uci.get(f"wireless.{radio_sections.get(band, '')}.htmode", "HE0")
                        ).removeprefix("HE")
                    ),
                }
                for band in ("2g", "5g")
            ],
        },
        "guest": {
            "up": {"hs_guest_wifi_2g", "hs_guest_wifi_5g"} <= up_bss
            and uci.get("network.guest.proto") == "static",
            "subnet": "192.168.30.0/24"
            if uci.get("network.guest.ipaddr") == "192.168.30.1"
            else "unknown",
            "internet": forwarding_exists("guest", "wan") and wan.get("up") is True,
            "router_management_blocked": (
                uci.get("firewall.hs_guest_zone.input") == "REJECT" and not guest_admin_listener
            ),
            "trusted_blocked": not forwarding_exists("guest", "lan")
            and not accept_rule_exists("guest", "lan"),
            "same_bss_isolation": all(
                uci.get(f"wireless.hs_guest_wifi_{band}.isolate") == "1" for band in ("2g", "5g")
            ),
            "cross_radio_isolation": all(
                uci.get(f"wireless.hs_guest_wifi_{band}.bridge_isolate") == "1"
                for band in ("2g", "5g")
            ),
            "trusted_to_guest_blocked": not forwarding_exists("lan", "guest")
            and not accept_rule_exists("lan", "guest"),
        },
        "ipv6": {
            "delegated_prefix_length": delegated_length,
            "trusted_prefix_length": int(str(uci.get("network.lan.ip6assign", "0"))),
            "guest_prefix_length": int(str(uci.get("network.guest.ip6assign", "0"))),
            "distinct_prefixes": uci.get("network.lan.ip6hint") != uci.get("network.guest.ip6hint"),
            "trusted_ula": bool(uci.get("network.globals.ula_prefix")),
            "guest_ula": bool(uci.get("network.globals.ula_prefix")),
            "dns": process_state.get("odhcpd") is True,
            "internet": wan6.get("up") is True,
            "icmpv6": uci.get("firewall.hs_ipv6_icmp.target") == "ACCEPT",
            "guest_to_trusted_blocked": not forwarding_exists("guest", "lan")
            and not accept_rule_exists("guest", "lan"),
            "wan_ingress_blocked": uci.get("firewall.hs_wan_zone.forward") == "REJECT"
            and wan_ingress_blocked,
            "management_exposed": bool(firewall.get("wan_management", True)) or wan_admin_listener,
            "guest_dhcpv6": uci.get("firewall.hs_ipv6_guest_dhcp.target") == "ACCEPT",
            "guest_icmpv6": uci.get("firewall.hs_ipv6_guest_icmp.target") == "ACCEPT",
        },
        "sqm": {
            "enabled": uci.get("sqm.wan.enabled") == "1",
            "device": uci.get("sqm.wan.interface"),
            "enabled_queues": 1 if uci.get("sqm.wan.enabled") == "1" else 0,
            "qdisc": uci.get("sqm.wan.qdisc"),
            "script": uci.get("sqm.wan.script"),
            "download_kbit": int(str(uci.get("sqm.wan.download", "0"))),
            "upload_kbit": int(str(uci.get("sqm.wan.upload", "0"))),
            "overhead": int(str(uci.get("sqm.wan.overhead", "0"))),
            "mpu": int(str(uci.get("sqm.wan.tcMPU", "0"))),
            "multiqueue": uci.get("sqm.wan.use_mq") == "1",
            "flow_offloading": uci.get("firewall.defaults.flow_offloading") == "1",
            "flow_offloading_hw": uci.get("firewall.defaults.flow_offloading_hw") == "1",
            "besteffort": "besteffort" in qdisc,
            "noatm": "noatm" in qdisc,
            "cake_mq": "cake_mq" in qdisc,
            "cake_egress": "qdisc cake" in qdisc and "dev pppoe-wan" in qdisc,
            "cake_ingress": "qdisc cake" in qdisc and "ifb" in qdisc,
            "runtime_rates": "8790Kbit" in qdisc and "87890Kbit" in qdisc,
        },
    }
    result = dict(state)
    result["runtime"] = health
    return result


def status_summary(state: HealthState) -> dict[str, object]:
    """Return a deterministic, secret-free summary without contacting the router."""

    raw_runtime = state.get("runtime")
    root_password_set = (
        raw_runtime.get("root_password_set") if isinstance(raw_runtime, Mapping) else None
    )
    state = derive_health_observations(state)
    identity = _mapping(state, "identity", "state")
    public_identity = {
        key: identity.get(key) for key in ("board_name", "model", "release", "target", "profile")
    }
    stage_health: dict[str, bool] = {}
    for stage, gate in HEALTH_GATES.items():
        try:
            gate(state)
        except OpenWrtSafetyError:
            stage_health[stage] = False
        else:
            stage_health[stage] = True
    return {
        "identity": public_identity,
        "root_password_set": root_password_set is True,
        "stages": stage_health,
    }
