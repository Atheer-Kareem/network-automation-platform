from network_automation_platform.change_validation import (
    run_post_change_validation,
    run_pre_change_validation,
)
from network_automation_platform.deployment import (
    DeploymentResult,
    DeploymentStatus,
)
from network_automation_platform.deployment_executor import (
    DeploymentExecutionError,
    DeploymentExecutor,
)
from network_automation_platform.desired_state import DeviceDesiredState
from network_automation_platform.device_state import DeviceState
from network_automation_platform.device_state_provider import (
    DeviceStateCollectionError,
    DeviceStateProvider,
)
from network_automation_platform.pre_change_validation import (
    PreChangeExpectation,
)


class DeploymentServiceError(ValueError):
    pass

def deploy_device(
    hostname: str,
    candidate_config: str,
    desired_state: DeviceDesiredState,
    current_state: DeviceState,
    pre_change_expectation: PreChangeExpectation,
    executor: DeploymentExecutor,
    state_provider: DeviceStateProvider,
) -> DeploymentResult:
    if current_state.hostname != hostname:
        raise DeploymentServiceError(
            "Current state target mismatch: "
            f"expected {hostname}, got {current_state.hostname}"
        )

    if desired_state.hostname != hostname:
        raise DeploymentServiceError(
            "Desired state target mismatch: "
            f"expected {hostname}, got {desired_state.hostname}"
    )

    pre_change = run_pre_change_validation(
            pre_change_expectation,
            current_state,
    )

    if not pre_change.passed:
        return DeploymentResult(
            hostname=hostname,
            status=DeploymentStatus.BLOCKED,
            pre_change=pre_change,
            deployment_attempted=False,
            deployment_succeeded=False,
            post_change=None,
            message="Deployment blocked by pre-change validation",
        )

    try:
        executor.apply_config(
            hostname,
            candidate_config,
        )
    except DeploymentExecutionError as exc:
        return DeploymentResult(
            hostname=hostname,
            status=DeploymentStatus.FAILED,
            pre_change=pre_change,
            deployment_attempted=True,
            deployment_succeeded=False,
            post_change=None,
            message=str(exc),
        )

    try:
        post_state = state_provider.collect_state(hostname)
    except DeviceStateCollectionError as exc:
        return DeploymentResult(
            hostname=hostname,
            status=DeploymentStatus.POST_CHECK_FAILED,
            pre_change=pre_change,
            deployment_attempted=True,
            deployment_succeeded=True,
            post_change=None,
            message=(
                "Configuration applied but post-change state "
                f"collection failed: {exc}"
            ),
        )

    post_change = run_post_change_validation(
        desired_state,
        post_state,
    )

    if not post_change.passed:
        return DeploymentResult(
            hostname=hostname,
            status=DeploymentStatus.POST_VALIDATION_FAILED,
            pre_change=pre_change,
            deployment_attempted=True,
            deployment_succeeded=True,
            post_change=post_change,
            message=(
                "Configuration applied but post-change "
                "validation failed"
            ),
        )

    return DeploymentResult(
        hostname=hostname,
        status=DeploymentStatus.SUCCEEDED,
        pre_change=pre_change,
        deployment_attempted=True,
        deployment_succeeded=True,
        post_change=post_change,
        message="Deployment completed and validated successfully",
    )