from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from network_automation_platform.branch_deployment import (
    BranchDeploymentResult,
    BranchDeviceDeploymentStatus,
    DeploymentApprovalStatus,
    DeviceBranchDeploymentResult,
)
from network_automation_platform.change_validation import (
    ChangeValidationResult,
)
from network_automation_platform.deployment import DeploymentStatus
from network_automation_platform.validation import (
    ValidationCheck,
    ValidationStatus,
)


class DeploymentFinalOutcome(StrEnum):
    COMPLIANT = "compliant"
    BLOCKED = "blocked"
    DECLINED = "declined"
    NOT_EXECUTED = "not_executed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    POST_CHECK_FAILED = "post_check_failed"
    POST_VALIDATION_FAILED = "post_validation_failed"


class DeploymentExecutionReport(BaseModel):
    attempted: bool
    succeeded: bool
    deployment_status: DeploymentStatus | None = None
    message: str | None = None


class DeviceDeploymentReport(BaseModel):
    hostname: str
    detected_drift: list[ValidationCheck] = Field(default_factory=list)
    remediation_commands: list[str] = Field(default_factory=list)
    approval_status: DeploymentApprovalStatus
    pre_change_result: ChangeValidationResult | None = None
    execution_result: DeploymentExecutionReport
    post_change_result: ChangeValidationResult | None = None
    final_outcome: DeploymentFinalOutcome
    message: str


class BranchDeploymentReport(BaseModel):
    schema_version: Literal["1"] = "1"
    generated_at: datetime
    branch_id: str
    devices: list[DeviceDeploymentReport] = Field(default_factory=list)


class DeploymentReportWriteError(OSError):
    pass


def _final_outcome(
    device: DeviceBranchDeploymentResult,
) -> DeploymentFinalOutcome:
    if device.deployment is not None:
        return DeploymentFinalOutcome(device.deployment.status.value)

    if device.status == BranchDeviceDeploymentStatus.BLOCKED:
        return DeploymentFinalOutcome.BLOCKED

    if device.approval_status == DeploymentApprovalStatus.DECLINED:
        return DeploymentFinalOutcome.DECLINED

    if device.approval_status == DeploymentApprovalStatus.APPROVED:
        return DeploymentFinalOutcome.NOT_EXECUTED

    if device.approval_status == DeploymentApprovalStatus.NOT_REQUIRED:
        return DeploymentFinalOutcome.COMPLIANT

    return DeploymentFinalOutcome.BLOCKED


def _build_device_report(
    device: DeviceBranchDeploymentResult,
) -> DeviceDeploymentReport:
    deployment = device.deployment

    return DeviceDeploymentReport(
        hostname=device.hostname,
        detected_drift=[
            check
            for check in device.initial_validation.checks
            if check.status == ValidationStatus.FAIL
        ],
        remediation_commands=device.remediation_commands,
        approval_status=device.approval_status,
        pre_change_result=(
            deployment.pre_change if deployment is not None else None
        ),
        execution_result=DeploymentExecutionReport(
            attempted=(
                deployment.deployment_attempted
                if deployment is not None
                else False
            ),
            succeeded=(
                deployment.deployment_succeeded
                if deployment is not None
                else False
            ),
            deployment_status=(
                deployment.status if deployment is not None else None
            ),
            message=deployment.message if deployment is not None else None,
        ),
        post_change_result=(
            deployment.post_change if deployment is not None else None
        ),
        final_outcome=_final_outcome(device),
        message=device.message,
    )


def build_branch_deployment_report(
    result: BranchDeploymentResult,
    *,
    generated_at: datetime | None = None,
) -> BranchDeploymentReport:
    report_time = generated_at or datetime.now(UTC)

    if report_time.tzinfo is None or report_time.utcoffset() is None:
        raise ValueError("generated_at must be timezone-aware")

    return BranchDeploymentReport(
        generated_at=report_time,
        branch_id=result.branch_id,
        devices=[
            _build_device_report(device)
            for device in result.devices
        ],
    )


def write_branch_deployment_report(
    report: BranchDeploymentReport,
    path: Path,
) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            report.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise DeploymentReportWriteError(
            f"Unable to write deployment report to {path}: {exc}"
        ) from exc
