from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from homeserver_iac.openwrt import OpenWrtSafetyError
from homeserver_iac.openwrt_health import (
    HEALTH_GATES,
    derive_health_observations,
    status_summary,
    validate_stage_health,
)


def healthy_state() -> dict[str, Any]:
    return {
        "identity": {
            "board_name": "cudy,wr3000e-v1",
            "model": "Cudy WR3000E v1",
            "release": "25.12.5",
            "target": "mediatek/filogic",
            "profile": "cudy_wr3000e-v1",
        },
        "runtime": {
            "bootstrap-sanitize": {
                "default_wan": False,
                "default_wan6": False,
                "wireless": False,
            },
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
            "wan": {
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
            "main-wifi": {
                "up": True,
                "network": "trusted",
                "country": "GR",
                "wps": False,
                "fast_transition": False,
                "same_bss_isolation": False,
                "bridge_isolation": False,
                "radios": [
                    {"band": "2g", "channel": 11, "width": 20},
                    {"band": "5g", "channel": 36, "width": 80},
                ],
            },
            "guest": {
                "up": True,
                "subnet": "192.168.30.0/24",
                "internet": True,
                "router_management_blocked": True,
                "trusted_blocked": True,
                "same_bss_isolation": True,
                "cross_radio_isolation": True,
                "trusted_to_guest_blocked": True,
            },
            "ipv6": {
                "delegated_prefix_length": 63,
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
            "sqm": {
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
        },
    }


@pytest.mark.parametrize("stage", HEALTH_GATES)
def test_each_stage_accepts_healthy_normalized_observations(stage: str) -> None:
    validate_stage_health(stage, healthy_state())


@pytest.mark.parametrize(
    ("stage", "field", "unsafe", "message"),
    [
        ("bootstrap-sanitize", "default_wan", True, "default_wan"),
        ("base", "wired_ssh", False, "wired_ssh"),
        ("wan", "management_exposed", True, "management_exposed"),
        ("wan", "ipv6_stage_consistent", False, "ipv6_stage_consistent"),
        ("wan", "wan_ingress_blocked", False, "wan_ingress_blocked"),
        ("main-wifi", "same_bss_isolation", True, "same_bss_isolation"),
        ("main-wifi", "bridge_isolation", True, "bridge_isolation"),
        ("guest", "same_bss_isolation", False, "same_bss_isolation"),
        ("ipv6", "delegated_prefix_length", 64, "delegated prefix"),
        ("sqm", "flow_offloading", True, "flow_offloading"),
    ],
)
def test_stage_health_fails_closed_on_representative_unsafe_state(
    stage: str, field: str, unsafe: object, message: str
) -> None:
    state = healthy_state()
    state["runtime"][stage][field] = unsafe

    with pytest.raises(OpenWrtSafetyError, match=message):
        validate_stage_health(stage, state)


def test_main_wifi_rejects_wrong_radio_mapping() -> None:
    state = healthy_state()
    state["runtime"]["main-wifi"]["radios"][1]["channel"] = 52

    with pytest.raises(OpenWrtSafetyError, match="2g/11/20"):
        validate_stage_health("main-wifi", state)


def test_main_wifi_health_derives_isolation_drift_from_uci() -> None:
    observed = derive_health_observations(
        {
            "uci": {
                "wireless.hs_main_wifi_2g.isolate": "1",
                "wireless.hs_main_wifi_5g.bridge_isolate": "1",
            },
            "runtime": {},
        }
    )

    assert observed["runtime"]["main-wifi"]["same_bss_isolation"] is True
    assert observed["runtime"]["main-wifi"]["bridge_isolation"] is True


def test_missing_or_unknown_health_input_fails_closed() -> None:
    with pytest.raises(OpenWrtSafetyError, match=r"runtime\.base"):
        validate_stage_health("base", {"runtime": {}})
    with pytest.raises(OpenWrtSafetyError, match="unknown OpenWrt health stage"):
        validate_stage_health("retired", healthy_state())


def test_status_summary_is_stable_redacted_and_marks_failures() -> None:
    state = healthy_state()
    state["runtime"]["wan"]["password"] = "must-not-leak"
    state["runtime"]["guest"]["trusted_blocked"] = False

    summary = status_summary(state)

    assert summary["identity"] == state["identity"]
    assert summary["stages"] == {
        "bootstrap-sanitize": True,
        "base": True,
        "wan": True,
        "main-wifi": True,
        "guest": False,
        "ipv6": True,
        "sqm": True,
    }
    assert "must-not-leak" not in repr(summary)


def test_status_summary_requires_normalized_identity_mapping() -> None:
    state = deepcopy(healthy_state())
    state["identity"] = "not-normalized"

    with pytest.raises(OpenWrtSafetyError, match=r"state\.identity"):
        status_summary(state)


def test_health_is_derived_from_filtered_live_observations() -> None:
    state = {
        "identity": healthy_state()["identity"],
        "firewall": {"wan_management": False},
        "uci": {
            "network.lan.ipaddr": "192.168.1.1",
            "network.lan.netmask": "255.255.255.0",
            "dropbear.dropbear.Interface": "lan",
            "dropbear.dropbear.PasswordAuth": "off",
            "uhttpd.main.listen_http": [],
            "uhttpd.main.listen_https": ["192.168.1.1:443"],
            "sqm.wan.enabled": "1",
            "sqm.wan.interface": "pppoe-wan",
            "sqm.wan.qdisc": "cake",
            "sqm.wan.script": "piece_of_cake.qos",
            "sqm.wan.download": "87890",
            "sqm.wan.upload": "8790",
            "sqm.wan.overhead": "50",
            "sqm.wan.tcMPU": "84",
            "sqm.wan.use_mq": "0",
            "firewall.defaults.flow_offloading": "0",
            "firewall.defaults.flow_offloading_hw": "0",
            "firewall.rogue._type": "rule",
            "firewall.rogue.src": "guest",
            "firewall.rogue.dest": "*",
            "firewall.rogue.target": "ACCEPT",
        },
        "runtime": {
            "strict_ssh": True,
            "wan": {},
            "wan6": {},
            "wireless": {},
            "qdisc": (
                "qdisc cake 1: dev pppoe-wan root bandwidth 8790Kbit besteffort "
                "noatm overhead 50 mpu 84\nqdisc cake 2: dev ifb4pppoe-wan root "
                "bandwidth 87890Kbit besteffort noatm overhead 50 mpu 84"
            ),
            "processes": {"dnsmasq": True, "odhcpd": True, "firewall": True},
        },
    }
    observed = derive_health_observations(state)
    validate_stage_health("base", observed)
    validate_stage_health("sqm", observed)
    assert observed["runtime"]["guest"]["trusted_blocked"] is False

    state["runtime"]["strict_ssh"] = False
    with pytest.raises(OpenWrtSafetyError, match="wired_ssh"):
        validate_stage_health("base", derive_health_observations(state))
