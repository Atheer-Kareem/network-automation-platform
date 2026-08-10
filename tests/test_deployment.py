from network_automation_platform.change_validation import (
    ChangeValidationResult,
    ValidationPhase,
)
from network_automation_platform.deployment import (
    DeploymentResult,
    DeploymentStatus,
)
from network_automation_platform.validation import (
    ValidationCheck,
    ValidationReport,
    ValidationStatus,
)


def build_validation_result(
    phase: ValidationPhase,
    passed: bool,
) -> ChangeValidationResult:
    return ChangeValidationResult(
        phase=phase,
        report=ValidationReport(
            hostname="br01-rtr01",
            checks=[
                ValidationCheck(
                    name="test-check",
                    status=(
                        ValidationStatus.PASS
                        if passed
                        else ValidationStatus.FAIL
                    ),
                    message="test validation result",
                )
            ],
        ),
    )


def test_blocked_deployment_result_is_not_succeeded() -> None:
    result = DeploymentResult(
        hostname="br01-rtr01",
        status=DeploymentStatus.BLOCKED,
        pre_change=build_validation_result(
            ValidationPhase.PRE_CHANGE,
            False,
        ),
        deployment_attempted=False,
        deployment_succeeded=False,
        post_change=None,
        message="Deployment blocked by pre-change validation",
    )

    assert result.succeeded is False
    assert result.deployment_attempted is False
    assert result.deployment_succeeded is False
    assert result.post_change is None


def test_failed_deployment_result_is_not_succeeded() -> None:
    result = DeploymentResult(
        hostname="br01-rtr01",
        status=DeploymentStatus.FAILED,
        pre_change=build_validation_result(
            ValidationPhase.PRE_CHANGE,
            True,
        ),
        deployment_attempted=True,
        deployment_succeeded=False,
        post_change=None,
        message="Configuration deployment failed",
    )

    assert result.succeeded is False
    assert result.deployment_attempted is True
    assert result.deployment_succeeded is False
    assert result.post_change is None


def test_post_validation_failed_result_is_not_succeeded() -> None:
    result = DeploymentResult(
        hostname="br01-rtr01",
        status=DeploymentStatus.POST_VALIDATION_FAILED,
        pre_change=build_validation_result(
            ValidationPhase.PRE_CHANGE,
            True,
        ),
        deployment_attempted=True,
        deployment_succeeded=True,
        post_change=build_validation_result(
            ValidationPhase.POST_CHANGE,
            False,
        ),
        message="Deployment completed but post-change validation failed",
    )

    assert result.succeeded is False
    assert result.deployment_attempted is True
    assert result.deployment_succeeded is True
    assert result.post_change is not None
    assert result.post_change.passed is False


def test_successful_deployment_result() -> None:
    result = DeploymentResult(
        hostname="br01-rtr01",
        status=DeploymentStatus.SUCCEEDED,
        pre_change=build_validation_result(
            ValidationPhase.PRE_CHANGE,
            True,
        ),
        deployment_attempted=True,
        deployment_succeeded=True,
        post_change=build_validation_result(
            ValidationPhase.POST_CHANGE,
            True,
        ),
        message="Deployment completed successfully",
    )

    assert result.succeeded is True
    assert result.deployment_attempted is True
    assert result.deployment_succeeded is True
    assert result.post_change is not None
    assert result.post_change.passed is True

def test_post_check_failed_result_is_not_succeeded() -> None:
    result = DeploymentResult(
        hostname="br01-rtr01",
        status=DeploymentStatus.POST_CHECK_FAILED,
        pre_change=build_validation_result(
            ValidationPhase.PRE_CHANGE,
            True,
        ),
        deployment_attempted=True,
        deployment_succeeded=True,
        post_change=None,
        message="Post-change state collection failed",
    )

    assert result.succeeded is False
    assert result.deployment_attempted is True
    assert result.deployment_succeeded is True
    assert result.post_change is None