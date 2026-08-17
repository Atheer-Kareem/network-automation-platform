import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from network_automation_platform.branch_deployment import (
    BranchDeploymentResult,
    BranchDeviceDeploymentStatus,
    DeploymentApprovalStatus,
    DeviceBranchDeploymentResult,
)
from network_automation_platform.change_validation import (
    ChangeValidationResult,
    ValidationPhase,
)
from network_automation_platform.deployment import (
    DeploymentResult,
    DeploymentStatus,
)
from network_automation_platform.deployment_reporting import (
    DeploymentFinalOutcome,
    DeploymentReportWriteError,
    build_branch_deployment_report,
    write_branch_deployment_report,
)
from network_automation_platform.validation import (
    ValidationCheck,
    ValidationReport,
    ValidationStatus,
)


def _validation_report(*, drift: bool) -> ValidationReport:
    checks = [
        ValidationCheck(
            name="interface:GigabitEthernet0/1",
            status=ValidationStatus.PASS,
            message="WAN interface matches expectation",
        )
    ]
    if drift:
        checks.append(
            ValidationCheck(
                name="interface:Vlan99",
                status=ValidationStatus.FAIL,
                message="Interface Vlan99 is missing",
                reason="missing",
            )
        )

    return ValidationReport(hostname="br01-sw01", checks=checks)


def _change_result(
    phase: ValidationPhase,
    *,
    passed: bool,
) -> ChangeValidationResult:
    return ChangeValidationResult(
        phase=phase,
        report=ValidationReport(
            hostname="br01-sw01",
            checks=[
                ValidationCheck(
                    name=f"{phase.value}-check",
                    status=(
                        ValidationStatus.PASS
                        if passed
                        else ValidationStatus.FAIL
                    ),
                    message=f"{phase.value} validation",
                )
            ],
        ),
    )


def _deployment_result(status: DeploymentStatus) -> DeploymentResult:
    attempted = status != DeploymentStatus.BLOCKED
    execution_succeeded = status in {
        DeploymentStatus.POST_CHECK_FAILED,
        DeploymentStatus.POST_VALIDATION_FAILED,
        DeploymentStatus.SUCCEEDED,
    }
    post_change = None
    if status in {
        DeploymentStatus.POST_VALIDATION_FAILED,
        DeploymentStatus.SUCCEEDED,
    }:
        post_change = _change_result(
            ValidationPhase.POST_CHANGE,
            passed=status == DeploymentStatus.SUCCEEDED,
        )

    return DeploymentResult(
        hostname="br01-sw01",
        status=status,
        pre_change=_change_result(
            ValidationPhase.PRE_CHANGE,
            passed=status != DeploymentStatus.BLOCKED,
        ),
        deployment_attempted=attempted,
        deployment_succeeded=execution_succeeded,
        post_change=post_change,
        message=f"Deployment result: {status.value}",
    )


def _branch_result(
    *,
    status: BranchDeviceDeploymentStatus,
    approval_status: DeploymentApprovalStatus,
    deployment: DeploymentResult | None = None,
    drift: bool = True,
) -> BranchDeploymentResult:
    return BranchDeploymentResult(
        branch_id="branch-01",
        devices=[
            DeviceBranchDeploymentResult(
                hostname="br01-sw01",
                initial_validation=_validation_report(drift=drift),
                remediation_commands=(
                    ["interface Vlan99", "no shutdown"]
                    if drift
                    else []
                ),
                approval_status=approval_status,
                status=status,
                deployment=deployment,
                message="Branch deployment result",
            )
        ],
    )


@pytest.mark.parametrize(
    (
        "result",
        "expected_approval",
        "expected_outcome",
    ),
    [
        pytest.param(
            _branch_result(
                status=BranchDeviceDeploymentStatus.SKIPPED,
                approval_status=DeploymentApprovalStatus.NOT_REQUIRED,
                drift=False,
            ),
            DeploymentApprovalStatus.NOT_REQUIRED,
            DeploymentFinalOutcome.COMPLIANT,
            id="already-compliant",
        ),
        pytest.param(
            _branch_result(
                status=BranchDeviceDeploymentStatus.BLOCKED,
                approval_status=DeploymentApprovalStatus.NOT_REQUESTED,
            ),
            DeploymentApprovalStatus.NOT_REQUESTED,
            DeploymentFinalOutcome.BLOCKED,
            id="preflight-blocked",
        ),
        pytest.param(
            _branch_result(
                status=BranchDeviceDeploymentStatus.SKIPPED,
                approval_status=DeploymentApprovalStatus.DECLINED,
            ),
            DeploymentApprovalStatus.DECLINED,
            DeploymentFinalOutcome.DECLINED,
            id="operator-declined",
        ),
        pytest.param(
            _branch_result(
                status=BranchDeviceDeploymentStatus.SKIPPED,
                approval_status=DeploymentApprovalStatus.APPROVED,
            ),
            DeploymentApprovalStatus.APPROVED,
            DeploymentFinalOutcome.NOT_EXECUTED,
            id="approved-branch-cancelled",
        ),
    ],
)
def test_report_for_device_that_never_entered_deployment(
    result: BranchDeploymentResult,
    expected_approval: DeploymentApprovalStatus,
    expected_outcome: DeploymentFinalOutcome,
) -> None:
    report = build_branch_deployment_report(result)
    device = report.devices[0]

    assert device.approval_status == expected_approval
    assert device.pre_change_result is None
    assert device.execution_result.attempted is False
    assert device.execution_result.succeeded is False
    assert device.execution_result.deployment_status is None
    assert device.post_change_result is None
    assert device.final_outcome == expected_outcome
    expected_drift_count = (
        0
        if expected_outcome == DeploymentFinalOutcome.COMPLIANT
        else 1
    )
    assert len(device.detected_drift) == expected_drift_count


def test_successful_deployment_report_preserves_all_evidence() -> None:
    result = _branch_result(
        status=BranchDeviceDeploymentStatus.DEPLOYED,
        approval_status=DeploymentApprovalStatus.APPROVED,
        deployment=_deployment_result(DeploymentStatus.SUCCEEDED),
    )

    report = build_branch_deployment_report(result)
    device = report.devices[0]

    assert [check.name for check in device.detected_drift] == [
        "interface:Vlan99"
    ]
    assert device.remediation_commands == ["interface Vlan99", "no shutdown"]
    assert device.approval_status == DeploymentApprovalStatus.APPROVED
    assert device.pre_change_result is not None
    assert device.pre_change_result.passed is True
    assert device.execution_result.attempted is True
    assert device.execution_result.succeeded is True
    assert device.execution_result.deployment_status == DeploymentStatus.SUCCEEDED
    assert device.post_change_result is not None
    assert device.post_change_result.passed is True
    assert device.final_outcome == DeploymentFinalOutcome.SUCCEEDED


@pytest.mark.parametrize(
    ("deployment_status", "expected_outcome"),
    [
        pytest.param(
            DeploymentStatus.FAILED,
            DeploymentFinalOutcome.FAILED,
            id="executor-failure",
        ),
        pytest.param(
            DeploymentStatus.POST_CHECK_FAILED,
            DeploymentFinalOutcome.POST_CHECK_FAILED,
            id="post-change-collection-failure",
        ),
        pytest.param(
            DeploymentStatus.POST_VALIDATION_FAILED,
            DeploymentFinalOutcome.POST_VALIDATION_FAILED,
            id="post-change-validation-failure",
        ),
        pytest.param(
            DeploymentStatus.BLOCKED,
            DeploymentFinalOutcome.BLOCKED,
            id="device-pre-change-blocked",
        ),
    ],
)
def test_deployment_status_maps_to_final_outcome(
    deployment_status: DeploymentStatus,
    expected_outcome: DeploymentFinalOutcome,
) -> None:
    result = _branch_result(
        status=BranchDeviceDeploymentStatus.DEPLOYED,
        approval_status=DeploymentApprovalStatus.APPROVED,
        deployment=_deployment_result(deployment_status),
    )

    device = build_branch_deployment_report(result).devices[0]

    assert device.final_outcome == expected_outcome
    assert device.execution_result.deployment_status == deployment_status


def test_generated_at_is_timezone_aware_and_injectable() -> None:
    generated_at = datetime(2026, 8, 18, 3, 4, 5, tzinfo=UTC)
    result = _branch_result(
        status=BranchDeviceDeploymentStatus.SKIPPED,
        approval_status=DeploymentApprovalStatus.NOT_REQUIRED,
        drift=False,
    )

    report = build_branch_deployment_report(
        result,
        generated_at=generated_at,
    )

    assert report.schema_version == "1"
    assert report.generated_at == generated_at
    assert report.generated_at.utcoffset() is not None


def test_generated_at_rejects_naive_datetime() -> None:
    result = _branch_result(
        status=BranchDeviceDeploymentStatus.SKIPPED,
        approval_status=DeploymentApprovalStatus.NOT_REQUIRED,
        drift=False,
    )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_branch_deployment_report(
            result,
            generated_at=datetime(
                2026,
                8,
                18,
                3,
                4,
                5,
                tzinfo=UTC,
            ).replace(tzinfo=None),
        )


def test_json_writer_creates_stable_json_and_parent_directories(
    tmp_path,
) -> None:
    report = build_branch_deployment_report(
        _branch_result(
            status=BranchDeviceDeploymentStatus.SKIPPED,
            approval_status=DeploymentApprovalStatus.NOT_REQUIRED,
            drift=False,
        ),
        generated_at=datetime(2026, 8, 18, 3, 4, 5, tzinfo=UTC),
    )
    path = tmp_path / "nested" / "deployment-report.json"

    write_branch_deployment_report(report, path)

    contents = path.read_text(encoding="utf-8")
    parsed = json.loads(contents)
    assert contents.endswith("\n")
    assert parsed["schema_version"] == "1"
    assert parsed["generated_at"] == "2026-08-18T03:04:05Z"
    assert parsed["branch_id"] == "branch-01"
    assert "password" not in contents.lower()


def test_json_writer_wraps_filesystem_errors(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = build_branch_deployment_report(
        _branch_result(
            status=BranchDeviceDeploymentStatus.SKIPPED,
            approval_status=DeploymentApprovalStatus.NOT_REQUIRED,
            drift=False,
        )
    )
    path = tmp_path / "report.json"

    def fail_write(*args, **kwargs) -> int:
        raise OSError("disk unavailable")

    monkeypatch.setattr(Path, "write_text", fail_write)

    with pytest.raises(
        DeploymentReportWriteError,
        match="Unable to write deployment report",
    ):
        write_branch_deployment_report(report, path)
