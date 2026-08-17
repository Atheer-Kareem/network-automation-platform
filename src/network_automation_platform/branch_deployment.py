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
from network_automation_platform.desired_state import (
    DeviceDesiredState,
)
from network_automation_platform.device_resolution import (
    find_inventory_device,
)
from network_automation_platform.device_state import DeviceState
from network_automation_platform.inventory import (
    DeviceInventory,
    InventoryDevice,
)
from network_automation_platform.models import load_branch_intent
from network_automation_platform.planning import (
    build_branch_desired_state,
)
from network_automation_platform.pre_change_expectation_builder import (
    PreChangeExpectationBuildError,
    build_pre_change_expectation,
)
from network_automation_platform.pre_change_validation import (
    PreChangeExpectation,
)
from network_automation_platform.remediation_planner import (
    build_device_remediation_plan,
    is_supported_remediation_check,
)
from network_automation_platform.validation import (
    ValidationReport,
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

class BranchDevicePreflightStatus(StrEnum):
    COMPLIANT = "compliant"
    READY = "ready"
    BLOCKED = "blocked"


class DeviceDeploymentPreflight(BaseModel):
    hostname: str
    status: BranchDevicePreflightStatus
    desired_state: DeviceDesiredState
    inventory_device: InventoryDevice
    current_state: DeviceState
    validation: ValidationReport
    remediation_commands: list[str] = Field(
        default_factory=list
    )
    pre_change_expectation: PreChangeExpectation | None = None
    message: str


class BranchDeploymentPreflight(BaseModel):
    branch_id: str
    devices: list[DeviceDeploymentPreflight] = Field(
        default_factory=list
    )

    @property
    def blocked(self) -> bool:
        return any(
            device.status
            == BranchDevicePreflightStatus.BLOCKED
            for device in self.devices
        )

def _build_branch_preflight(
    branch_id: str,
    intent_path: Path,
    inventory: DeviceInventory,
    settings: ConnectionSettings,
) -> BranchDeploymentPreflight:
    intent = load_branch_intent(intent_path)
    desired_branch = build_branch_desired_state(intent)

    devices: list[DeviceDeploymentPreflight] = []

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
            devices.append(
                DeviceDeploymentPreflight(
                    hostname=desired_device.hostname,
                    status=(
                        BranchDevicePreflightStatus.COMPLIANT
                    ),
                    desired_state=desired_device,
                    inventory_device=inventory_device,
                    current_state=current_state,
                    validation=validation,
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

            devices.append(
                DeviceDeploymentPreflight(
                    hostname=desired_device.hostname,
                    status=(
                        BranchDevicePreflightStatus.BLOCKED
                    ),
                    desired_state=desired_device,
                    inventory_device=inventory_device,
                    current_state=current_state,
                    validation=validation,
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
            remediation_plan,
            platform=desired_device.platform,
        )

        if not remediation_commands:
            devices.append(
                DeviceDeploymentPreflight(
                    hostname=desired_device.hostname,
                    status=(
                        BranchDevicePreflightStatus.BLOCKED
                    ),
                    desired_state=desired_device,
                    inventory_device=inventory_device,
                    current_state=current_state,
                    validation=validation,
                    message=(
                        "Deployment blocked because no targeted "
                        "remediation commands were produced"
                    ),
                )
            )
            continue

        try:
            pre_change_expectation = build_pre_change_expectation(
                device=inventory_device,
                inventory=inventory,
                current_state=current_state,
            )
        except PreChangeExpectationBuildError as exc:
            devices.append(
                DeviceDeploymentPreflight(
                    hostname=desired_device.hostname,
                    status=BranchDevicePreflightStatus.BLOCKED,
                    desired_state=desired_device,
                    inventory_device=inventory_device,
                    current_state=current_state,
                    validation=validation,
                    remediation_commands=remediation_commands,
                    message=(
                        "Deployment safety preflight failed: "
                        f"{exc}"
                    ),
                )
            )
            continue

        devices.append(
            DeviceDeploymentPreflight(
                hostname=desired_device.hostname,
                status=BranchDevicePreflightStatus.READY,
                desired_state=desired_device,
                inventory_device=inventory_device,
                current_state=current_state,
                validation=validation,
                remediation_commands=remediation_commands,
                pre_change_expectation=pre_change_expectation,
                message="Device is ready for deployment",
            )
        )

    return BranchDeploymentPreflight(
        branch_id=branch_id,
        devices=devices,
    )


def deploy_branch(
    branch_id: str,
    intent_path: Path,
    inventory: DeviceInventory,
    settings: ConnectionSettings,
    approve: DeploymentApproval,
) -> BranchDeploymentResult:
    preflight = _build_branch_preflight(
        branch_id=branch_id,
        intent_path=intent_path,
        inventory=inventory,
        settings=settings,
    )

    if preflight.blocked:
        blocked_hostnames = [
            device.hostname
            for device in preflight.devices
            if (
                device.status
                == BranchDevicePreflightStatus.BLOCKED
            )
        ]

        blocked_summary = ", ".join(blocked_hostnames)

        results: list[
            DeviceBranchDeploymentResult
        ] = []

        for device in preflight.devices:
            if (
                device.status
                == BranchDevicePreflightStatus.COMPLIANT
            ):
                results.append(
                    DeviceBranchDeploymentResult(
                        hostname=device.hostname,
                        status=(
                            BranchDeviceDeploymentStatus.SKIPPED
                        ),
                        message=device.message,
                    )
                )
                continue

            if (
                device.status
                == BranchDevicePreflightStatus.BLOCKED
            ):
                results.append(
                    DeviceBranchDeploymentResult(
                        hostname=device.hostname,
                        status=(
                            BranchDeviceDeploymentStatus.BLOCKED
                        ),
                        remediation_commands=(
                            device.remediation_commands
                        ),
                        message=device.message,
                    )
                )
                continue

            results.append(
                DeviceBranchDeploymentResult(
                    hostname=device.hostname,
                    status=(
                        BranchDeviceDeploymentStatus.BLOCKED
                    ),
                    remediation_commands=(
                        device.remediation_commands
                    ),
                    message=(
                        "Deployment blocked because branch "
                        "preflight failed on: "
                        f"{blocked_summary}"
                    ),
                )
            )

        return BranchDeploymentResult(
            branch_id=branch_id,
            devices=results,
        )

    approval_decisions: dict[str, bool] = {}

    for device in preflight.devices:
        if device.status != BranchDevicePreflightStatus.READY:
            continue

        approval_decisions[device.hostname] = approve(
            device.hostname,
            device.remediation_commands,
        )

    declined_hostnames = [
        hostname
        for hostname, approved
        in approval_decisions.items()
        if not approved
    ]

    if declined_hostnames:
        results = []

        declined_summary = ", ".join(
            declined_hostnames
        )

        for device in preflight.devices:
            if (
                device.status
                == BranchDevicePreflightStatus.COMPLIANT
            ):
                results.append(
                    DeviceBranchDeploymentResult(
                        hostname=device.hostname,
                        status=(
                            BranchDeviceDeploymentStatus.SKIPPED
                        ),
                        message=device.message,
                    )
                )
                continue

            if not approval_decisions[device.hostname]:
                message = "Deployment declined by operator"
            else:
                message = (
                    "Deployment not executed because operator "
                    "approval was declined for: "
                    f"{declined_summary}"
                )

            results.append(
                DeviceBranchDeploymentResult(
                    hostname=device.hostname,
                    status=BranchDeviceDeploymentStatus.SKIPPED,
                    remediation_commands=(
                        device.remediation_commands
                    ),
                    message=message,
                )
            )

        return BranchDeploymentResult(
            branch_id=branch_id,
            devices=results,
        )

    results = []

    for device in preflight.devices:
        if (
            device.status
            == BranchDevicePreflightStatus.COMPLIANT
        ):
            results.append(
                DeviceBranchDeploymentResult(
                    hostname=device.hostname,
                    status=BranchDeviceDeploymentStatus.SKIPPED,
                    message=device.message,
                )
            )
            continue

        if device.pre_change_expectation is None:
            raise RuntimeError(
                "Ready deployment preflight is missing "
                f"pre-change expectation for {device.hostname}"
            )

        deployment = deploy_inventory_device(
            device=device.inventory_device,
            settings=settings,
            candidate_config="\n".join(
                device.remediation_commands
            ),
            desired_state=device.desired_state,
            current_state=device.current_state,
            pre_change_expectation=(
                device.pre_change_expectation
            ),
        )

        results.append(
            DeviceBranchDeploymentResult(
                hostname=device.hostname,
                status=BranchDeviceDeploymentStatus.DEPLOYED,
                remediation_commands=(
                    device.remediation_commands
                ),
                deployment=deployment,
                message=deployment.message,
            )
        )

    return BranchDeploymentResult(
        branch_id=branch_id,
        devices=results,
    )
