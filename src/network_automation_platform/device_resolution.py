from network_automation_platform.desired_state import DeviceDesiredState
from network_automation_platform.inventory import (
    DeviceInventory,
    InventoryDevice,
)


class DeviceResolutionError(ValueError):
    pass


def find_inventory_device(
    desired_device: DeviceDesiredState,
    inventory: DeviceInventory,
) -> InventoryDevice:
    for inventory_device in inventory.devices:
        if inventory_device.hostname == desired_device.hostname:
            return inventory_device

    raise DeviceResolutionError(
        f"Device {desired_device.hostname} not found in inventory"
    )