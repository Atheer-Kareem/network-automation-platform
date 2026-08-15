from ipaddress import IPv4Interface

from network_automation_platform.remediation import (
    DeviceRemediationPlan,
    InterfaceRemediation,
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




def render_device_remediation(
    plan: DeviceRemediationPlan,
) -> list[str]:
    commands: list[str] = []

    for action in plan.actions:
        remediation = action.remediation

        if isinstance(remediation, InterfaceRemediation):
            commands.extend(
                render_interface_remediation(remediation)
            )
            continue

        raise ValueError(
            f"Unsupported remediation type: "
            f"{type(remediation).__name__}"
        )

    return commands