from network_automation_platform.inventory import DeviceInventory


class SshConfigError(ValueError):
    pass


def render_ssh_config(inventory: DeviceInventory) -> str:
    if inventory.lab is None:
        raise SshConfigError(
            "Lab settings are required to render SSH configuration"
        )

    blocks: list[str] = []

    for device in inventory.devices:
        lines = [
            f"Host {device.hostname} {device.host}",
            f"    HostName {device.host}",
            f"    User {inventory.lab.ssh.username}",
            f"    Port {device.port}",
        ]

        for algorithm in inventory.lab.ssh.kex_algorithms:
            lines.append(
                f"    KexAlgorithms +{algorithm}"
            )

        for algorithm in inventory.lab.ssh.host_key_algorithms:
            lines.append(
                f"    HostKeyAlgorithms +{algorithm}"
            )

        blocks.append("\n".join(lines))

    header = (
        "# Generated from inventory/lab.yaml. "
        "Do not edit manually."
    )

    return (
        header
        + "\n\n"
        + "\n\n".join(blocks)
        + "\n"
    )