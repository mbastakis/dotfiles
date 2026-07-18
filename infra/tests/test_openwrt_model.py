from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from homeserver_iac.models import OpenWrtDesiredState
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.validation import load_yaml

ROUTER_PATH = INFRA_ROOT / "network/openwrt/router.yaml"


def set_path(document: dict[str, Any], path: tuple[str | int, ...], value: Any) -> None:
    target: Any = document
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value


def test_openwrt_desired_state_is_valid() -> None:
    desired = OpenWrtDesiredState.model_validate(load_yaml(ROUTER_PATH))

    assert desired.networks.ula_prefix == "fd84:778b:9ef1::/48"
    assert {radio.band: radio.channel for radio in desired.wireless.radios} == {
        "2g": 11,
        "5g": 36,
    }
    assert {reservation.mac for reservation in desired.reservations} == {
        "10:fe:ed:04:14:22",
        "50:46:5d:38:5a:a1",
    }
    assert desired.dns.upstreams == ("192.168.1.19", "1.1.1.1", "1.0.0.1")


@pytest.mark.parametrize(
    ("path", "value", "error"),
    [
        (("ownership", "scope"), "network.other", "ownership.scope"),
        (("firmware", "version"), "25.12.4", "firmware.version"),
        (("wan", "vlan_id"), 0, "wan.vlan_id"),
        (("networks", "guest", "address"), "192.0.0.1/8", "must not overlap"),
        (("networks", "guest", "dhcp_end"), "192.168.31.249", "inside its subnet"),
        (("networks", "guest", "dhcp_start"), "192.168.30.250", "must not exceed"),
        (("networks", "ula_prefix"), "fd00::/64", "RFC4193"),
        (("dns", "upstreams", 0), "9.9.9.9", "Pi-hole first"),
        (("reservations", 1, "id"), "atlas", "must be unique"),
        (("reservations", 1, "hostname"), "atlas", "must be unique"),
        (("reservations", 1, "mac"), "50:46:5d:38:5a:a1", "must be unique"),
        (("reservations", 1, "address"), "192.168.1.19", "must be unique"),
        (("reservations", 0, "address"), "192.168.1.100", "outside the pool"),
        (("reservations", 0, "address"), "192.168.1.20", "atlas reservation"),
        (("reservations", 0, "mac"), "50:46:5d:38:5a:a2", "atlas reservation"),
        (
            ("wireless", "radios"),
            [
                {"id": "radio-a", "band": "2g", "channel": 1, "width": 20},
                {"id": "radio-b", "band": "2g", "channel": 6, "width": 20},
            ],
            "exactly one 2g",
        ),
        (("wireless", "radios", 0, "channel"), 2, "2g radio"),
        (("wireless", "radios", 1, "channel"), 52, "5g radio"),
        (("wireless", "wps"), True, "wireless.wps"),
        (("wireless", "fast_transition"), True, "wireless.fast_transition"),
        (("wireless", "main", "encryption"), "sae", "wireless.main.encryption"),
        (("wireless", "main", "enabled"), False, "wireless.main.enabled"),
        (("wireless", "main", "isolate_clients"), True, "isolate_clients"),
        (("wireless", "main", "isolate_bridge_ports"), True, "isolate_bridge_ports"),
        (("wireless", "guest", "isolate_clients"), False, "isolate_clients"),
        (("wireless", "guest", "isolate_bridge_ports"), False, "isolate_bridge_ports"),
        (("management", "ssh_password_auth"), True, "ssh_password_auth"),
        (("security", "upnp"), True, "security.upnp"),
        (("security", "port_forwards"), [{"wan": "lan"}], "port_forwards"),
        (("security", "tailscale"), True, "security.tailscale"),
        (
            ("security", "dns_rebind_allow_domains", 0),
            "unmanaged.mbastakis.com",
            "private service names",
        ),
        (("sqm", "download_kbit"), 90000, "sqm.download_kbit"),
        (("sqm", "qdisc"), "fq_codel", "sqm.qdisc"),
        (("sqm", "flow_offloading"), True, "sqm.flow_offloading"),
    ],
)
def test_openwrt_rejects_unsafe_cross_field_state(
    path: tuple[str | int, ...], value: Any, error: str
) -> None:
    document = deepcopy(load_yaml(ROUTER_PATH))
    set_path(document, path, value)

    with pytest.raises(ValidationError) as caught:
        OpenWrtDesiredState.model_validate(document)

    assert error in str(caught.value)


def test_openwrt_rejects_literal_secret_fields() -> None:
    document = deepcopy(load_yaml(ROUTER_PATH))
    document["wan"]["password"] = "not-a-secret-reference"

    with pytest.raises(ValidationError):
        OpenWrtDesiredState.model_validate(document)
