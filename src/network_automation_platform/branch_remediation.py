from pathlib import Path

from pydantic import BaseModel, Field

from network_automation_platform.cisco_ios_remediation import (
    render_device_remediation,
)
from network_automation_platform.collectors.cisco_ios import (
    collect_device_state,
)
from network_automation_platform.connection_settings import (
    ConnectionSettings,
)
from network_automation_platform.device_resolution import (
    find_inventory_device,
)
from network_automation_platform.inventory import DeviceInventory
from network_automation_platform.models import load_branch_intent
from network_automation_platform.planning import (
    build_branch_desired_state,
)
from network_automation_platform.remediation import (
    DeviceRemediationPlan,
)
from network_automation_platform.remediation_planner import (
    build_device_remediation_plan,
)
from network_automation_platform.validation_expectations import (
    build_desired_state_expectation,
)
from network_automation_platform.validation_service import (
    validate_device_against_desired_state,
)


class DeviceBranchRemediationResult(BaseModel):
    hostname: str
    plan: DeviceRemediationPlan
    commands: list[str] = Field(default_factory=list)


class BranchRemediationResult(BaseModel):
    branch_id: str
    devices: list[DeviceBranchRemediationResult] = Field(
        default_factory=list
    )

    @property
    def has_changes(self) -> bool:
        return any(
            device.plan.has_changes
            for device in self.devices
        )


def build_branch_remediation(
    branch_id: str,
    intent_path: Path,
    inventory: DeviceInventory,
    settings: ConnectionSettings,
) -> BranchRemediationResult:
    intent = load_branch_intent(intent_path)
    desired_branch = build_branch_desired_state(intent)

    results: list[DeviceBranchRemediationResult] = []

    for desired_device in desired_branch.devices:
        inventory_device = find_inventory_device(
            desired_device,
            inventory,
        )

        state = collect_device_state(
            inventory_device,
            settings,
        )

        validation = validate_device_against_desired_state(
            desired_device,
            state,
        )

        expectation = build_desired_state_expectation(
            desired_device
        )

        remediation_plan = build_device_remediation_plan(
            expectation=expectation,
            report=validation,
        )

        commands = render_device_remediation(
            remediation_plan,
            platform=desired_device.platform,
        )

        results.append(
            DeviceBranchRemediationResult(
                hostname=desired_device.hostname,
                plan=remediation_plan,
                commands=commands,
            )
        )

    return BranchRemediationResult(
        branch_id=branch_id,
        devices=results,
    )
