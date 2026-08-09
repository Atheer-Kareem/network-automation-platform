from dataclasses import dataclass

from network_automation_platform.desired_state import DeviceDesiredState


@dataclass(frozen=True)
class RouterPlatformProfile:
    interface_map: dict[str, str]


@dataclass(frozen=True)
class SwitchPlatformProfile:
    interface_map: dict[str, str]
    trunk_encapsulation: str | None = None
    disable_ip_routing: bool = False


ROUTER_PLATFORM_PROFILES = {
    "cisco_ios_c7200": RouterPlatformProfile(
        interface_map={
            "wan": "FastEthernet0/0",
            "lan": "FastEthernet1/0",
        }
    ),
}

SWITCH_PLATFORM_PROFILES = {
    "cisco_iosv_l2": SwitchPlatformProfile(
        interface_map={
            "uplink": "GigabitEthernet0/0",
            "users_access": "GigabitEthernet0/1",
        },
        trunk_encapsulation="dot1q",
        disable_ip_routing=True,
    ),
}


def render_device(device: DeviceDesiredState) -> str:
    if device.role == "branch_router":
        return _render_router(device)

    if device.role == "branch_switch":
        return _render_switch(device)

    raise ValueError(f"Unsupported device role: {device.role}")


def _render_router(device: DeviceDesiredState) -> str:
    try:
        profile = ROUTER_PLATFORM_PROFILES[device.platform]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported router platform: {device.platform}"
        ) from exc

    lines: list[str] = [
        f"hostname {device.hostname}",
        "!",
    ]

    for interface in device.interfaces:
        if interface.parent is not None:
            continue

        physical_name = profile.interface_map[interface.name]

        lines.extend(
            [
                f"interface {physical_name}",
                f" description {interface.description or interface.name}",
            ]
        )

        if interface.ipv4 is not None:
            lines.append(
                f" ip address {interface.ipv4.ip} "
                f"{interface.ipv4.network.netmask}"
            )

        if interface.enabled:
            lines.append(" no shutdown")

        lines.append("!")

    for interface in device.interfaces:
        if interface.parent is None:
            continue

        parent_name = profile.interface_map[interface.parent]

        lines.extend(
            [
                f"interface {parent_name}.{interface.vlan_id}",
                f" description {interface.description or interface.name}",
                f" encapsulation dot1Q {interface.vlan_id}",
            ]
        )

        if interface.ipv4 is not None:
            lines.append(
                f" ip address {interface.ipv4.ip} "
                f"{interface.ipv4.network.netmask}"
            )

        lines.append("!")

    if device.ospf is not None:
        lines.append(f"router ospf {device.ospf.process_id}")

        for network in device.ospf.networks:
            lines.append(
                f" network {network.network_address} "
                f"{network.hostmask} area {device.ospf.area}"
            )

        lines.append("!")

    return "\n".join(lines)


def _render_switch(device: DeviceDesiredState) -> str:
    try:
        profile = SWITCH_PLATFORM_PROFILES[device.platform]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported switch platform: {device.platform}"
        ) from exc

    lines: list[str] = [
        f"hostname {device.hostname}",
        "!",
    ]

    if profile.disable_ip_routing:
        lines.extend(
            [
                "no ip routing",
                "!",
            ]
        )

    for vlan in device.vlans:
        lines.extend(
            [
                f"vlan {vlan.vlan_id}",
                f" name {vlan.name}",
                "!",
            ]
        )

    for interface in device.interfaces:
        if interface.name == "management_svi":
            lines.extend(
                [
                    f"interface Vlan{interface.vlan_id}",
                    f" description {interface.description or interface.name}",
                ]
            )

            if interface.ipv4 is not None:
                lines.append(
                    f" ip address {interface.ipv4.ip} "
                    f"{interface.ipv4.network.netmask}"
                )

            if interface.enabled:
                lines.append(" no shutdown")

            lines.append("!")
            continue

        physical_name = profile.interface_map[interface.name]

        lines.extend(
            [
                f"interface {physical_name}",
                f" description {interface.description or interface.name}",
            ]
        )

        if interface.mode == "trunk":
            if profile.trunk_encapsulation is not None:
                lines.append(
                    " switchport trunk encapsulation "
                    f"{profile.trunk_encapsulation}"
                )

            lines.append(" switchport mode trunk")

            if interface.allowed_vlans:
                allowed = ",".join(
                    str(vlan_id) for vlan_id in interface.allowed_vlans
                )
                lines.append(
                    f" switchport trunk allowed vlan {allowed}"
                )

        if interface.mode == "access":
            lines.extend(
                [
                    " switchport mode access",
                    f" switchport access vlan {interface.access_vlan}",
                ]
            )

        if interface.enabled:
            lines.append(" no shutdown")

        lines.append("!")

    if device.default_gateway is not None:
        lines.extend(
            [
                f"ip default-gateway {device.default_gateway}",
                "!",
            ]
        )

    return "\n".join(lines)