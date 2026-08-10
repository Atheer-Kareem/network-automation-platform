from pathlib import Path

from network_automation_platform.inventory import load_device_inventory


def test_load_lab_inventory() -> None:
    inventory = load_device_inventory(Path("inventory/lab.yaml"))

    assert len(inventory.devices) == 1

    router = inventory.devices[0]

    assert router.hostname == "br01-rtr01"
    assert router.host == "192.168.64.10"
    assert router.port == 22
    assert router.driver == "cisco_ios"