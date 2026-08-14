from pathlib import Path

from pydantic import BaseModel, Field

from network_automation_platform.collectors.cisco_ios import (
    collect_device_state,
)
from network_automation_platform.connection_settings import (
    ConnectionSettings,
)
from network_automation_platform.desired_state import DeviceDesiredState
from network_automation_platform.inventory import (
    DeviceInventory,
    InventoryDevice,
)
from network_automation_platform.models import load_branch_intent
from network_automation_platform.planning import (
    build_branch_desired_state,
)
from network_automation_platform.validation import ValidationReport
from network_automation_platform.validation_service import (
    validate_device_against_desired_state,
)


class DeviceValidationResult(BaseModel):
    hostname: str
    report: ValidationReport


class BranchValidationResult(BaseModel):
    branch_id: str
    devices: list[DeviceValidationResult] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(device.report.passed for device in self.devices)

class BranchValidationError(ValueError):
    pass

def validate_branch(
    branch_id: str,
    *,
    intent_path: Path,
    inventory: DeviceInventory,
    settings: ConnectionSettings,
) -> BranchValidationResult:
    intent = load_branch_intent(intent_path)
    desired_branch = build_branch_desired_state(intent)

    results: list[DeviceValidationResult] = []

    for desired_device in desired_branch.devices:
        inventory_device = _find_inventory_device(
            desired_device,
            inventory,
        )

        state = collect_device_state(
            inventory_device,
            settings,
        )

        report = validate_device_against_desired_state(
            desired_device,
            state,
        )

        results.append(
            DeviceValidationResult(
                hostname=desired_device.hostname,
                report=report,
            )
        )

    return BranchValidationResult(
        branch_id=branch_id,
        devices=results,
    )


def _find_inventory_device(
    desired_device: DeviceDesiredState,
    inventory: DeviceInventory,
) -> InventoryDevice:
    for inventory_device in inventory.devices:
        if inventory_device.hostname == desired_device.hostname:
            return inventory_device

    raise BranchValidationError(
        f"Device {desired_device.hostname} not found in inventory"
    )