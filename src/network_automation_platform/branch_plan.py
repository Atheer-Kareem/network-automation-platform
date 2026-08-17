from pathlib import Path

from pydantic import BaseModel, Field

from network_automation_platform.cisco_ios_remediation import (
    render_device_remediation,
)
from network_automation_platform.collectors.cisco_ios import collect_device_state
from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.device_resolution import (
    find_inventory_device,
)
from network_automation_platform.inventory import DeviceInventory
from network_automation_platform.models import load_branch_intent
from network_automation_platform.planning import build_branch_desired_state
from network_automation_platform.remediation_planner import (
    build_device_remediation_plan,
)
from network_automation_platform.renderers.cisco_ios import render_device
from network_automation_platform.validation import ValidationReport
from network_automation_platform.validation_expectations import (
    build_desired_state_expectation,
)
from network_automation_platform.validation_service import (
    validate_device_against_desired_state,
)


class DevicePlanResult(BaseModel):
    hostname: str
    candidate_config: str
    validation: ValidationReport
    remediation_commands: list[str] = Field(default_factory=list)



class BranchPlanResult(BaseModel):
    branch_id: str
    devices: list[DevicePlanResult] = Field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return any(
            not device.validation.passed
            for device in self.devices
        )

def plan_branch(
    branch_id: str,
    intent_path: Path,
    inventory: DeviceInventory,
    settings: ConnectionSettings,
) -> BranchPlanResult:
    intent = load_branch_intent(intent_path)
    desired_branch = build_branch_desired_state(intent)

    results: list[DevicePlanResult] = []

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

        remediation_commands = render_device_remediation(
            remediation_plan,
            platform=desired_device.platform,
        )
        candidate_config = render_device(desired_device)

        results.append(
            DevicePlanResult(
                hostname=desired_device.hostname,
                candidate_config=candidate_config,
                validation=validation,
                remediation_commands=remediation_commands
            )
        )

    return BranchPlanResult(
        branch_id=branch_id,
        devices=results,
    )
