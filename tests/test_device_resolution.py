import pytest

from network_automation_platform.desired_state import DeviceDesiredState
from network_automation_platform.device_resolution import (
    DeviceResolutionError,
    find_inventory_device,
)
from network_automation_platform.inventory import (
    DeviceInventory,
    InventoryDevice,
)


def test_find_inventory_device() -> None:
    desired = DeviceDesiredState(
        hostname="br01-rtr01",
        role="branch_router",
        platform="cisco_iosv",
    )

    inventory = DeviceInventory(
        devices=[
            InventoryDevice(
                hostname="br01-rtr01",
                host="192.168.100.11",
                driver="cisco_ios",
            )
        ]
    )

    device = find_inventory_device(
        desired,
        inventory,
    )

    assert device.hostname == "br01-rtr01"
    assert device.host == "192.168.100.11"


def test_find_inventory_device_rejects_missing_device() -> None:
    desired = DeviceDesiredState(
        hostname="br01-rtr01",
        role="branch_router",
        platform="cisco_iosv",
    )

    inventory = DeviceInventory(devices=[])

    with pytest.raises(
        DeviceResolutionError,
        match="Device br01-rtr01 not found in inventory",
    ):
        find_inventory_device(
            desired,
            inventory,
        )