from collections.abc import Callable
from enum import StrEnum
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
from network_automation_platform.deployment import DeploymentResult
from network_automation_platform.deployment_runtime import (
    deploy_inventory_device,
)
from network_automation_platform.device_resolution import (
    find_inventory_device,
)
from network_automation_platform.inventory import DeviceInventory
from network_automation_platform.models import load_branch_intent
from network_automation_platform.planning import (
    build_branch_desired_state,
)
from network_automation_platform.pre_change_expectation_builder import (
    build_pre_change_expectation,
)
from network_automation_platform.remediation_planner import (
    build_device_remediation_plan,
    is_supported_remediation_check,
)
from network_automation_platform.validation import (
    ValidationStatus,
)
from network_automation_platform.validation_expectations import (
    build_desired_state_expectation,
)
from network_automation_platform.validation_service import (
    validate_device_against_desired_state,
)

DeploymentApproval = Callable[
    [str, list[str]],
    bool,
]

class BranchDeviceDeploymentStatus(StrEnum):
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    DEPLOYED = "deployed"


class DeviceBranchDeploymentResult(BaseModel):
    hostname: str
    status: BranchDeviceDeploymentStatus
    remediation_commands: list[str] = Field(default_factory=list)
    deployment: DeploymentResult | None = None
    message: str


class BranchDeploymentResult(BaseModel):
    branch_id: str
    devices: list[DeviceBranchDeploymentResult] = Field(
        default_factory=list
    )

    @property
    def blocked(self) -> bool:
        return any(
            device.status == BranchDeviceDeploymentStatus.BLOCKED
            for device in self.devices
        )


def deploy_branch(
    branch_id: str,
    intent_path: Path,
    inventory: DeviceInventory,
    settings: ConnectionSettings,
    approve: DeploymentApproval,
) -> BranchDeploymentResult:
    intent = load_branch_intent(intent_path)
    desired_branch = build_branch_desired_state(intent)

    results: list[DeviceBranchDeploymentResult] = []

    for desired_device in desired_branch.devices:
        inventory_device = find_inventory_device(
            desired_device,
            inventory,
        )

        current_state = collect_device_state(
            inventory_device,
            settings,
        )

        validation = validate_device_against_desired_state(
            desired_device,
            current_state,
        )

        if validation.passed:
            results.append(
                DeviceBranchDeploymentResult(
                    hostname=desired_device.hostname,
                    status=BranchDeviceDeploymentStatus.SKIPPED,
                    message="Device is already compliant",
                )
            )
            continue

        failed_checks = [
            check
            for check in validation.checks
            if check.status == ValidationStatus.FAIL
        ]

        unsupported_checks = [
            check
            for check in failed_checks
            if not is_supported_remediation_check(check)
        ]

        if unsupported_checks:
            names = ", ".join(
                check.name
                for check in unsupported_checks
            )

            results.append(
                DeviceBranchDeploymentResult(
                    hostname=desired_device.hostname,
                    status=BranchDeviceDeploymentStatus.BLOCKED,
                    message=(
                        "Deployment blocked because unsupported "
                        f"drift is present: {names}"
                    ),
                )
            )
            continue

        expectation = build_desired_state_expectation(
            desired_device
        )

        remediation_plan = build_device_remediation_plan(
            expectation=expectation,
            report=validation,
        )

        remediation_commands = render_device_remediation(
            remediation_plan
        )

        if not remediation_commands:
            results.append(
                DeviceBranchDeploymentResult(
                    hostname=desired_device.hostname,
                    status=BranchDeviceDeploymentStatus.BLOCKED,
                    message=(
                        "Deployment blocked because no targeted "
                        "remediation commands were produced"
                    ),
                )
            )
            continue

        if not approve(
            desired_device.hostname,
            remediation_commands,
        ):
            results.append(
                DeviceBranchDeploymentResult(
                    hostname=desired_device.hostname,
                    status=BranchDeviceDeploymentStatus.SKIPPED,
                    remediation_commands=remediation_commands,
                    message="Deployment declined by operator",
                )
            )
            continue
        pre_change_expectation = build_pre_change_expectation(
            device=inventory_device,
            inventory=inventory,
            current_state=current_state,
        )

        deployment = deploy_inventory_device(
            device=inventory_device,
            settings=settings,
            candidate_config="\n".join(remediation_commands),
            desired_state=desired_device,
            current_state=current_state,
            pre_change_expectation=pre_change_expectation,
        )

        results.append(
            DeviceBranchDeploymentResult(
                hostname=desired_device.hostname,
                status=BranchDeviceDeploymentStatus.DEPLOYED,
                remediation_commands=remediation_commands,
                deployment=deployment,
                message=deployment.message,
            )
        )

    return BranchDeploymentResult(
        branch_id=branch_id,
        devices=results,
    )