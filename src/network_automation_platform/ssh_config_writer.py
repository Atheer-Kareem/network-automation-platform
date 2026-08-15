from pathlib import Path

from network_automation_platform.inventory import load_device_inventory
from network_automation_platform.ssh_config import render_ssh_config


def write_ssh_config(
    inventory_path: Path,
    output_path: Path,
) -> None:
    inventory = load_device_inventory(inventory_path)
    config = render_ssh_config(inventory)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        config,
        encoding="utf-8",
    )