from __future__ import annotations

from ipaddress import IPv4Address, IPv4Interface, IPv6Network, ip_address, ip_interface, ip_network
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from homeserver_iac.models.common import SecretRef, StableId, StrictModel, VersionedDesiredState

MacAddress = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9a-f]{2}(?::[0-9a-f]{2}){5}$"),
]


class OpenWrtDevice(StrictModel):
    vendor: Literal["Cudy"]
    model: Literal["WR3000E"]
    hardware_version: Literal["1.0"]
    board_name: Literal["cudy,wr3000e-v1"]
    compatible_board_ids: tuple[Literal["R53"]]


class OpenWrtImageBuilder(StrictModel):
    filename: Literal["openwrt-imagebuilder-25.12.5-mediatek-filogic.Linux-x86_64.tar.zst"]
    url: Literal[
        "https://downloads.openwrt.org/releases/25.12.5/targets/mediatek/filogic/"
        "openwrt-imagebuilder-25.12.5-mediatek-filogic.Linux-x86_64.tar.zst"
    ]
    sha256: Literal["7fb6cf626582ebcbfb46974da48c1eae577213f38879eaf6b1d982041e843461"]


class OpenWrtPackagePolicy(StrictModel):
    add: tuple[str, ...] = Field(min_length=1)
    forbidden: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_package_policy(self) -> OpenWrtPackagePolicy:
        required = {
            "luci-ssl",
            "luci-app-sqm",
            "sqm-scripts",
            "rpcd",
            "ucode",
            "ucode-mod-ubus",
        }
        forbidden = {"tailscale", "miniupnpd", "luci-app-upnp"}
        if set(self.add) != required or len(self.add) != len(required):
            raise ValueError("firmware.packages.add must contain exactly the required packages")
        if set(self.forbidden) != forbidden or len(self.forbidden) != len(forbidden):
            raise ValueError(
                "firmware.packages.forbidden must contain exactly the forbidden packages"
            )
        return self


class OpenWrtFirmware(StrictModel):
    version: Literal["25.12.5"]
    target: Literal["mediatek"]
    subtarget: Literal["filogic"]
    profile: Literal["cudy_wr3000e-v1"]
    imagebuilder: OpenWrtImageBuilder
    packages: OpenWrtPackagePolicy
    public_key_path: Literal["private_dot_ssh/id_ed25519.pub"]


class OpenWrtSystem(StrictModel):
    hostname: Literal["router"]
    timezone: Literal["EET-2EEST,M3.5.0/3,M10.5.0/4"]
    zonename: Literal["Europe/Athens"]


class SecretValue(StrictModel):
    secret_ref: SecretRef


class OpenWrtDhcpV6(StrictModel):
    request_address: Literal["try"]
    request_prefix: Literal["auto"]


class OpenWrtWan(StrictModel):
    physical_device: Literal["wan"]
    vlan_id: Literal[835]
    protocol: Literal["pppoe"]
    username: SecretValue
    password: SecretValue
    peer_dns: Literal[True]
    ipv6: Literal[True]
    dhcpv6: OpenWrtDhcpV6


class TrustedNetwork(StrictModel):
    interface: Literal["lan"]
    address: str
    dhcp_start: str
    dhcp_end: str
    lease_time: Literal["12h"]
    domain: Literal["home"]
    ipv6_assignment: Literal[64]
    ipv6_hint: Literal["0"]


class GuestNetwork(StrictModel):
    interface: Literal["guest"]
    address: str
    dhcp_start: str
    dhcp_end: str
    lease_time: Literal["12h"]
    ipv6_assignment: Literal[64]
    ipv6_hint: Literal["1"]


class OpenWrtNetworks(StrictModel):
    trusted: TrustedNetwork
    guest: GuestNetwork
    ula_prefix: str

    @model_validator(mode="after")
    def validate_networks(self) -> OpenWrtNetworks:
        trusted = _validate_ipv4_network("trusted", self.trusted)
        guest = _validate_ipv4_network("guest", self.guest)
        if trusted.network.overlaps(guest.network):
            raise ValueError("trusted and guest IPv4 networks must not overlap")

        ula = ip_network(self.ula_prefix, strict=True)
        if (
            not isinstance(ula, IPv6Network)
            or ula.prefixlen != 48
            or ula.network_address.packed[0] != 0xFD
        ):
            raise ValueError("ula_prefix must be a stable RFC4193 locally assigned /48")
        return self


class OpenWrtDns(StrictModel):
    upstreams: tuple[str, ...] = Field(min_length=3, max_length=3)
    strict_order: Literal[True]
    ignore_wan_resolvers: Literal[True]

    @model_validator(mode="after")
    def validate_upstreams(self) -> OpenWrtDns:
        expected = ("192.168.1.19", "1.1.1.1", "1.0.0.1")
        if self.upstreams != expected:
            raise ValueError("dns.upstreams must use Pi-hole first and fixed outage fallbacks")
        return self


def _validate_ipv4_network(name: str, network: TrustedNetwork | GuestNetwork) -> IPv4Interface:
    interface = ip_interface(network.address)
    if not isinstance(interface, IPv4Interface):
        raise ValueError(f"{name}.address must be IPv4")
    start = ip_address(network.dhcp_start)
    end = ip_address(network.dhcp_end)
    if not isinstance(start, IPv4Address) or not isinstance(end, IPv4Address):
        raise ValueError(f"{name} DHCP pool endpoints must be IPv4")
    if start not in interface.network or end not in interface.network:
        raise ValueError(f"{name} DHCP pool endpoints must be inside its subnet")
    if start > end:
        raise ValueError(f"{name} DHCP pool start must not exceed its end")
    if start <= interface.ip <= end or interface.ip == interface.network.network_address:
        raise ValueError(f"{name} router address must be usable and outside its DHCP pool")
    if start in (interface.network.network_address, interface.network.broadcast_address) or end in (
        interface.network.network_address,
        interface.network.broadcast_address,
    ):
        raise ValueError(f"{name} DHCP pool endpoints must be usable host addresses")
    return interface


class OpenWrtReservation(StrictModel):
    id: StableId
    hostname: StableId
    mac: MacAddress
    address: str


class OpenWrtRadio(StrictModel):
    id: StableId
    band: Literal["2g", "5g"]
    channel: int
    width: int

    @model_validator(mode="after")
    def validate_radio(self) -> OpenWrtRadio:
        if self.band == "2g" and (self.channel not in {1, 6, 11} or self.width != 20):
            raise ValueError("2g radio requires channel 1, 6, or 11 and width 20")
        if self.band == "5g" and (self.channel not in {36, 40, 44, 48} or self.width != 80):
            raise ValueError("5g radio requires non-DFS channel 36-48 and width 80")
        return self


class WirelessNetwork(StrictModel):
    ssid: SecretValue
    psk: SecretValue
    encryption: Literal["psk2+ccmp"]


class MainWirelessNetwork(WirelessNetwork):
    enabled: Literal[True]
    isolate_clients: Literal[False]
    isolate_bridge_ports: Literal[False]


class GuestWirelessNetwork(WirelessNetwork):
    isolate_clients: Literal[True]
    isolate_bridge_ports: Literal[True]


class OpenWrtWireless(StrictModel):
    country: Literal["GR"]
    fast_transition: Literal[False]
    wps: Literal[False]
    radios: tuple[OpenWrtRadio, ...] = Field(min_length=2, max_length=2)
    main: MainWirelessNetwork
    guest: GuestWirelessNetwork

    @model_validator(mode="after")
    def validate_radios(self) -> OpenWrtWireless:
        if len({radio.id for radio in self.radios}) != len(self.radios):
            raise ValueError("wireless radio IDs must be unique")
        if {radio.band for radio in self.radios} != {"2g", "5g"}:
            raise ValueError("wireless must map exactly one 2g and one 5g radio")
        return self


class OpenWrtManagement(StrictModel):
    public_key_path: Literal["private_dot_ssh/id_ed25519.pub"]
    root_password: SecretValue
    ssh_password_auth: Literal[False]
    luci_https_only: Literal[True]
    allowed_networks: tuple[Literal["trusted"]]


class OpenWrtSecurity(StrictModel):
    upnp: Literal[False]
    nat_pmp: Literal[False]
    dmz: Literal[False]
    wan_management: Literal[False]
    port_forwards: tuple[()] = ()
    tailscale: Literal[False]
    dns_rebind_allow_domains: tuple[str, ...] = Field(min_length=12, max_length=12)

    @model_validator(mode="after")
    def validate_dns_rebind_allow_domains(self) -> OpenWrtSecurity:
        expected = {
            "audiobooks.mbastakis.com",
            "auth.mbastakis.com",
            "backrest.mbastakis.com",
            "code.mbastakis.com",
            "files.mbastakis.com",
            "home.mbastakis.com",
            "photos.mbastakis.com",
            "pihole.mbastakis.com",
            "push.mbastakis.com",
            "taskboard.mbastakis.com",
            "tasks.mbastakis.com",
            "traefik.mbastakis.com",
        }
        if len(set(self.dns_rebind_allow_domains)) != len(self.dns_rebind_allow_domains):
            raise ValueError("security.dns_rebind_allow_domains must not contain duplicates")
        if set(self.dns_rebind_allow_domains) != expected:
            raise ValueError(
                "security.dns_rebind_allow_domains must contain exactly the private service names"
            )
        return self


class OpenWrtSqm(StrictModel):
    enabled: Literal[True]
    interface_from_wan_l3_device: Literal[True]
    download_kbit: Literal[87890]
    upload_kbit: Literal[8790]
    qdisc: Literal["cake"]
    script: Literal["piece_of_cake.qos"]
    link_layer: Literal["ethernet"]
    overhead: Literal[50]
    mpu: Literal[84]
    multiqueue: Literal[False]
    flow_offloading: Literal[False]


class OpenWrtDesiredState(VersionedDesiredState):
    device: OpenWrtDevice
    firmware: OpenWrtFirmware
    system: OpenWrtSystem
    wan: OpenWrtWan
    networks: OpenWrtNetworks
    dns: OpenWrtDns
    reservations: tuple[OpenWrtReservation, ...] = Field(min_length=2)
    wireless: OpenWrtWireless
    management: OpenWrtManagement
    security: OpenWrtSecurity
    sqm: OpenWrtSqm

    @model_validator(mode="after")
    def validate_contract(self) -> OpenWrtDesiredState:
        if self.ownership.scope != "network.openwrt":
            raise ValueError("ownership.scope must be 'network.openwrt'")

        aliases = {
            "wan.username": self.wan.username.secret_ref.alias,
            "wan.password": self.wan.password.secret_ref.alias,
            "wireless.main.ssid": self.wireless.main.ssid.secret_ref.alias,
            "wireless.main.psk": self.wireless.main.psk.secret_ref.alias,
            "wireless.guest.ssid": self.wireless.guest.ssid.secret_ref.alias,
            "wireless.guest.psk": self.wireless.guest.psk.secret_ref.alias,
            "management.root_password": self.management.root_password.secret_ref.alias,
        }
        expected_aliases = {
            "wan.username": "openwrt_pppoe_username",
            "wan.password": "openwrt_pppoe_password",
            "wireless.main.ssid": "openwrt_main_wifi_ssid",
            "wireless.main.psk": "openwrt_main_wifi_psk",
            "wireless.guest.ssid": "openwrt_guest_wifi_ssid",
            "wireless.guest.psk": "openwrt_guest_wifi_psk",
            "management.root_password": "openwrt_root_password",
        }
        if aliases != expected_aliases:
            raise ValueError("OpenWrt secret fields must use their designated aliases")

        ids = [reservation.id for reservation in self.reservations]
        hostnames = [reservation.hostname for reservation in self.reservations]
        macs = [reservation.mac for reservation in self.reservations]
        addresses = [reservation.address for reservation in self.reservations]
        if any(len(values) != len(set(values)) for values in (ids, hostnames, macs, addresses)):
            raise ValueError("reservation IDs, hostnames, MACs, and addresses must be unique")

        trusted = ip_interface(self.networks.trusted.address)
        pool_start = ip_address(self.networks.trusted.dhcp_start)
        pool_end = ip_address(self.networks.trusted.dhcp_end)
        if not isinstance(pool_start, IPv4Address) or not isinstance(pool_end, IPv4Address):
            raise ValueError("trusted DHCP pool endpoints must be IPv4")
        for reservation in self.reservations:
            address = ip_address(reservation.address)
            if not isinstance(address, IPv4Address) or address not in trusted.network:
                raise ValueError("reservation addresses must be inside the trusted IPv4 subnet")
            if address == trusted.ip or pool_start <= address <= pool_end:
                raise ValueError(
                    "reservation addresses must be outside the pool and router address"
                )

        required = {
            "atlas": ("atlas", "50:46:5d:38:5a:a1", IPv4Address("192.168.1.19")),
            "truenas": ("truenas", "10:fe:ed:04:14:22", IPv4Address("192.168.1.74")),
        }
        by_id = {reservation.id: reservation for reservation in self.reservations}
        for reservation_id, (hostname, mac, address) in required.items():
            required_reservation = by_id.get(reservation_id)
            if (
                required_reservation is None
                or required_reservation.hostname != hostname
                or required_reservation.mac != mac
                or ip_address(required_reservation.address) != address
            ):
                raise ValueError(f"required {reservation_id} reservation is missing or incorrect")
        return self
