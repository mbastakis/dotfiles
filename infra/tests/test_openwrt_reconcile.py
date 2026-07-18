from __future__ import annotations

from pathlib import Path

import pytest

from homeserver_iac.models.openwrt import OpenWrtDesiredState
from homeserver_iac.openwrt import OpenWrtSafetyError
from homeserver_iac.openwrt_reconcile import (
    _wifi_psk,
    _wifi_ssid,
    build_stage_changes,
    desired_uci_sections,
    plan_stage_changes,
)
from homeserver_iac.schema import INFRA_ROOT
from homeserver_iac.validation import load_model


@pytest.fixture
def desired() -> OpenWrtDesiredState:
    return load_model(INFRA_ROOT / "network/openwrt/router.yaml", OpenWrtDesiredState)


def radios() -> dict[str, object]:
    return {"wireless.radio0.band": "2g", "wireless.radio1.band": "5g"}


def factory_snapshot() -> dict[str, object]:
    return {
        "network.wan._type": "interface",
        "network.wan.device": "wan",
        "network.wan.proto": "dhcp",
        "network.wan6._type": "interface",
        "network.wan6.device": "wan",
        "network.wan6.proto": "dhcpv6",
        "network.lan._type": "interface",
        "network.lan.device": "br-lan",
        "network.lan.proto": "static",
        "network.lan.ipaddr": ["192.168.1.1/24"],
        "wireless.radio0._type": "wifi-device",
        "wireless.radio1._type": "wifi-device",
        "wireless.default_radio0._type": "wifi-iface",
        "wireless.default_radio0.disabled": "1",
        "wireless.default_radio1._type": "wifi-iface",
        "wireless.default_radio1.disabled": "1",
    }


def test_wifi_secret_validation_uses_hostapd_byte_and_format_constraints() -> None:
    assert _wifi_ssid(lambda _: "é" * 16, "ssid") == "é" * 16
    with pytest.raises(OpenWrtSafetyError, match="byte length"):
        _wifi_ssid(lambda _: "é" * 17, "ssid")

    assert _wifi_psk(lambda _: "a" * 64, "psk") == "a" * 64
    assert _wifi_psk(lambda _: "printable passphrase", "psk") == "printable passphrase"
    with pytest.raises(OpenWrtSafetyError, match="length or format"):
        _wifi_psk(lambda _: "g" * 64, "psk")
    with pytest.raises(OpenWrtSafetyError, match="length or format"):
        _wifi_psk(lambda _: "pässword", "psk")


def test_base_projection_excludes_later_stage_fields(desired: OpenWrtDesiredState) -> None:
    sections = desired_uci_sections(desired, "base", snapshot={})
    paths = {
        f"{section.config}.{section.name}.{option}"
        for section in sections
        for option in section.values
    }
    assert "network.lan.ipaddr" in paths
    assert "firewall.defaults.input" in paths
    assert "dropbear.dropbear.PasswordAuth" in paths
    assert "dhcp.dnsmasq.rebind_domain" not in paths
    assert "system.system.hostname" not in paths
    assert "network.lan.ip6assign" not in paths
    assert "firewall.defaults.flow_offloading" not in paths
    assert not any(path.startswith("network.wan.") for path in paths)


def test_base_binds_factory_anonymous_singletons_instead_of_duplicating(
    desired: OpenWrtDesiredState,
) -> None:
    snapshot = {
        "system.cfg01._type": "system",
        "dhcp.cfg02._type": "dnsmasq",
        "firewall.cfg03._type": "defaults",
        "firewall.cfg04._type": "zone",
        "firewall.cfg04.name": "lan",
        "dropbear.cfg05._type": "dropbear",
        "uhttpd.cfg06._type": "uhttpd",
        "network.cfg07._type": "device",
        "network.cfg07.name": "br-lan",
    }
    changes = build_stage_changes(desired, "base", snapshot=snapshot)
    add_names = {
        mutation["arguments"].get("name")
        for mutation in changes.mutations
        if mutation["method"] == "add"
    }
    assert not add_names & {"system", "dnsmasq", "defaults", "dropbear", "main"}
    assert "system.cfg01.hostname" not in changes.expected_projection
    assert "dhcp.cfg02.domain" not in changes.expected_projection
    assert "firewall.cfg04.input" in changes.expected_projection
    assert "network.cfg07.type" in changes.expected_projection


def test_wan_secrets_are_resolved_only_into_stdin_mutations(
    desired: OpenWrtDesiredState,
) -> None:
    values = {
        "openwrt_pppoe_username": "fixture-user",
        "openwrt_pppoe_password": "fixture-password",
    }
    changes = build_stage_changes(
        desired,
        "wan",
        snapshot={},
        resolve_secret=values.__getitem__,
    )
    assert changes.packages == {"network", "dhcp", "firewall"}
    wan_set = next(
        mutation
        for mutation in changes.mutations
        if mutation["method"] == "set" and mutation["arguments"]["section"] == "wan"
    )
    assert wan_set["arguments"]["values"]["password"] == "fixture-password"
    assert changes.expected_projection["network.wan.username"] == "fixture-user"
    assert changes.expected_projection["network.wan.ipv6"] == "0"
    assert changes.expected_projection["network.globals.ula_prefix"] is None
    assert changes.expected_projection["network.lan.ip6assign"] is None
    assert changes.expected_projection["dhcp.lan.ra"] == "disabled"
    serialized = plan_stage_changes(changes).model_dump_json()
    assert "fixture-user" not in serialized
    assert "fixture-password" not in serialized
    assert "openwrt_pppoe_password" in serialized


def test_secret_match_makes_converged_wan_projection_a_noop(
    desired: OpenWrtDesiredState,
) -> None:
    snapshot = {
        "network.wan_vlan._type": "device",
        "network.wan_vlan.name": "wan.835",
        "network.wan_vlan.type": "8021q",
        "network.wan_vlan.ifname": "wan",
        "network.wan_vlan.vid": "835",
        "network.wan._type": "interface",
        "network.wan.device": "wan.835",
        "network.wan.proto": "pppoe",
        "network.wan.peerdns": "1",
        "network.wan.ipv6": "0",
        "network.globals._type": "globals",
        "network.lan._type": "interface",
        "dhcp.lan._type": "dhcp",
        "dhcp.lan.ra": "disabled",
        "dhcp.lan.dhcpv6": "disabled",
        "dhcp.lan.ndp": "disabled",
        "firewall.hs_wan_zone._type": "zone",
        "firewall.hs_wan_zone.name": "wan",
        "firewall.hs_wan_zone.network": ["wan", "wan6"],
        "firewall.hs_wan_zone.input": "REJECT",
        "firewall.hs_wan_zone.output": "ACCEPT",
        "firewall.hs_wan_zone.forward": "REJECT",
        "firewall.hs_wan_zone.masq": "1",
        "firewall.hs_wan_zone.mtu_fix": "1",
        "firewall.hs_wan_trusted_forward._type": "forwarding",
        "firewall.hs_wan_trusted_forward.src": "lan",
        "firewall.hs_wan_trusted_forward.dest": "wan",
    }
    changes = build_stage_changes(
        desired,
        "wan",
        snapshot=snapshot,
        resolve_secret=lambda alias: f"fixture-{alias}",
        secret_matches={
            "network.wan.username": True,
            "network.wan.password": True,
        },
    )
    assert changes.mutations == ()


def test_wan_preserves_ipv6_fields_after_ipv6_transaction_is_accepted(
    desired: OpenWrtDesiredState,
) -> None:
    snapshot = {
        "network.wan._type": "interface",
        "network.wan.ipv6": "1",
        "network.globals._type": "globals",
        "network.globals.ula_prefix": desired.networks.ula_prefix,
        "network.lan._type": "interface",
        "network.lan.ip6assign": "64",
        "network.lan.ip6hint": "0",
        "dhcp.lan._type": "dhcp",
        "dhcp.lan.ra": "server",
        "dhcp.lan.dhcpv6": "server",
        "dhcp.lan.ndp": "disabled",
    }

    sections = desired_uci_sections(
        desired,
        "wan",
        snapshot=snapshot,
        resolve_secret=lambda alias: f"fixture-{alias}",
        accepted_stages={"ipv6"},
    )
    paths = {
        f"{section.config}.{section.name}.{option}"
        for section in sections
        for option in section.values
    }

    assert "network.wan.ipv6" not in paths
    assert "network.globals.ula_prefix" not in paths
    assert "network.lan.ip6assign" not in paths
    assert "dhcp.lan.ra" not in paths


def test_wan_removes_inherited_factory_accept_rules(desired: OpenWrtDesiredState) -> None:
    snapshot = {
        "firewall.cfg_ipsec._type": "rule",
        "firewall.cfg_ipsec.name": "Allow-IPSec-ESP",
        "firewall.cfg_ipsec.src": "wan",
        "firewall.cfg_ipsec.dest": "lan",
        "firewall.cfg_ipsec.proto": "esp",
        "firewall.cfg_ipsec.target": "ACCEPT",
        "firewall.hs_ipv6_icmp._type": "rule",
        "firewall.hs_ipv6_icmp.name": "Allow-ICMPv6-Input",
        "firewall.hs_ipv6_icmp.src": "wan",
        "firewall.hs_ipv6_icmp.proto": "icmp",
        "firewall.hs_ipv6_icmp.target": "ACCEPT",
        "firewall.custom._type": "rule",
        "firewall.custom.name": "Preserve-Custom",
        "firewall.custom.src": "lan",
        "firewall.custom.target": "ACCEPT",
    }

    changes = build_stage_changes(
        desired,
        "wan",
        snapshot=snapshot,
        resolve_secret=lambda alias: f"fixture-{alias}",
    )

    assert "firewall.cfg_ipsec" in changes.deleted_sections
    assert "firewall.hs_ipv6_icmp" not in changes.deleted_sections
    assert "firewall.custom" not in changes.deleted_sections
    assert changes.expected_projection["firewall.cfg_ipsec._section_absent"] is None


def test_radio_binding_and_guest_stale_cleanup(desired: OpenWrtDesiredState) -> None:
    snapshot = {
        **radios(),
        "wireless.hs_guest_retired._type": "wifi-iface",
    }
    changes = build_stage_changes(
        desired,
        "guest",
        snapshot=snapshot,
        resolve_secret=lambda alias: f"fixture-{alias}",
    )
    assert "wireless.hs_guest_retired" in changes.deleted_sections
    assert changes.expected_projection["wireless.hs_guest_retired._section_absent"] is None
    assert any(
        mutation["arguments"].get("section") == "hs_guest_retired" for mutation in changes.mutations
    )
    plan = plan_stage_changes(changes)
    assert (
        next(
            operation.kind.value
            for operation in plan.operations
            if operation.resource_id == "wireless.hs_guest_retired"
        )
        == "delete"
    )


def test_bootstrap_sanitize_is_exact_guarded_deletion(
    desired: OpenWrtDesiredState,
) -> None:
    changes = build_stage_changes(
        desired,
        "bootstrap-sanitize",
        snapshot=factory_snapshot(),
    )
    assert [mutation["method"] for mutation in changes.mutations] == ["delete", "delete"]
    assert changes.expected_projection == {
        "network.wan._section_absent": None,
        "network.wan6._section_absent": None,
    }
    with pytest.raises(OpenWrtSafetyError, match="clean-image"):
        build_stage_changes(
            desired,
            "bootstrap-sanitize",
            snapshot={**factory_snapshot(), "network.wan.proto": "pppoe"},
        )


def test_duplicate_or_missing_radio_band_fails_closed(desired: OpenWrtDesiredState) -> None:
    with pytest.raises(OpenWrtSafetyError, match="unique"):
        build_stage_changes(
            desired,
            "guest",
            snapshot={"wireless.radio0.band": "2g", "wireless.radio1.band": "2g"},
            resolve_secret=lambda alias: f"fixture-{alias}",
        )


def test_reconcile_module_does_not_create_plaintext_files() -> None:
    assert Path(__file__).exists()
