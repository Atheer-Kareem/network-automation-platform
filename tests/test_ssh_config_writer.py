from pathlib import Path

from network_automation_platform.inventory import load_device_inventory
from network_automation_platform.ssh_config_writer import (
    write_ssh_config,
)


def test_write_ssh_config(tmp_path: Path) -> None:
    output_path = tmp_path / "lab_config"

    write_ssh_config(
        Path("inventory/lab.yaml"),
        output_path,
    )

    content = output_path.read_text(
        encoding="utf-8"
    )

    inventory = load_device_inventory(
        Path("inventory/lab.yaml")
    )

    for device in inventory.devices:
        assert (
            f"Host {device.hostname} {device.host}"
            in content
        )
        assert f"HostName {device.host}" in content