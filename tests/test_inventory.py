from pathlib import Path

from network_automation_platform.inventory import load_device_inventory


def test_load_lab_inventory() -> None:
    inventory = load_device_inventory(Path("inventory/lab.yaml"))

    assert len(inventory.devices) == 3

    core = inventory.devices[0]
    router = inventory.devices[1]
    switch = inventory.devices[2]

    assert core.hostname == "core01"
    assert core.host == "192.168.100.10"
    assert core.port == 22
    assert core.driver == "cisco_ios"

    assert router.hostname == "br01-rtr01"
    assert router.host == "192.168.100.11"
    assert router.port == 22
    assert router.driver == "cisco_ios"

    assert switch.hostname == "br01-sw01"
    assert switch.host == "192.168.100.12"
    assert switch.port == 22
    assert switch.driver == "cisco_ios"