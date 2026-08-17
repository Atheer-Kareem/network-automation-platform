from ipaddress import IPv4Interface

from network_automation_platform.platform_profiles import (
    SWITCH_PLATFORM_PROFILES,
    SwitchPlatformProfile,
)
from network_automation_platform.remediation import (
    DeviceRemediationPlan,
    InterfaceRemediation,
    SwitchportRemediation,
    VlanRemediation,
)


def render_interface_remediation(
    remediation: InterfaceRemediation,
) -> list[str]:
    commands = [
        f"interface {remediation.interface_name}",
    ]

    if remediation.description is not None:
        commands.append(
            f"description {remediation.description}"
        )

    if remediation.ipv4 is not None:
        interface = IPv4Interface(remediation.ipv4)

        commands.append(
            "ip address "
            f"{interface.ip} "
            f"{interface.network.netmask}"
        )

    if remediation.enabled is True:
        commands.append("no shutdown")

    if remediation.enabled is False:
        commands.append("shutdown")

    return commands


def render_vlan_remediation(
    remediation: VlanRemediation,
) -> list[str]:
    return [
        f"vlan {remediation.vlan_id}",
        f"name {remediation.name}",
    ]

def render_switchport_remediation(
    remediation: SwitchportRemediation,
    profile: SwitchPlatformProfile,
) -> list[str]:
    commands = [f"interface {remediation.interface_name}"]

    if remediation.mode == "access":
        commands.append("switchport mode access")

    if remediation.mode == "trunk":
        if profile.trunk_encapsulation is not None:
            commands.append(
                "switchport trunk encapsulation "
                f"{profile.trunk_encapsulation}"
            )

        commands.append("switchport mode trunk")

    if remediation.access_vlan is not None:
        commands.append(
            f"switchport access vlan {remediation.access_vlan}"
        )

    if remediation.allowed_vlans is not None:
        allowed = ",".join(
            str(vlan_id) for vlan_id in remediation.allowed_vlans
        )
        commands.append(
            f"switchport trunk allowed vlan {allowed}"
        )

    return commands

def render_device_remediation(
    plan: DeviceRemediationPlan,
    platform: str | None = None,
) -> list[str]:
    commands: list[str] = []

    for action in plan.actions:
        remediation = action.remediation

        if isinstance(remediation, InterfaceRemediation):
            commands.extend(
                render_interface_remediation(remediation)
            )
            continue

        if isinstance(remediation, VlanRemediation):
            commands.extend(
                render_vlan_remediation(remediation)
            )
            continue

        if isinstance(remediation, SwitchportRemediation):
            try:
                profile = SWITCH_PLATFORM_PROFILES[platform]
            except KeyError as exc:
                raise ValueError(
                    f"Unsupported switch platform for remediation: "
                    f"{platform}"
                ) from exc

            commands.extend(
                render_switchport_remediation(
                    remediation,
                    profile,
                )
            )
            continue

        raise ValueError(
            f"Unsupported remediation type: "
            f"{type(remediation).__name__}"
        )

    return commands
