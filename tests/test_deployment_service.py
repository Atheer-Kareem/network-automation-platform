from ipaddress import IPv4Address, IPv4Interface, IPv4Network
from unittest.mock import Mock

import pytest

from network_automation_platform.deployment import DeploymentStatus
from network_automation_platform.deployment_executor import (
    DeploymentExecutionError,
)
from network_automation_platform.deployment_service import (
    DeploymentServiceError,
    deploy_device,
)
from network_automation_platform.desired_state import (
    DeviceDesiredState,
    InterfaceDesiredState,
)
from network_automation_platform.device_state import (
    DeviceState,
    InterfaceState,
    RouteState,
)
from network_automation_platform.device_state_provider import (
    DeviceStateCollectionError,
)
from network_automation_platform.pre_change_validation import (
    PreChangeExpectation,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    RouteExpectation,
)


def build_current_state() -> DeviceState:
    return DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="FastEthernet1/0",
                ipv4=IPv4Address("192.168.100.10"),
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[
            RouteState(
                protocol="C",
                network=IPv4Network("192.168.100.0/24"),
                outgoing_interface="FastEthernet1/0",
            )
        ],
    )


def build_passing_pre_change_expectation() -> PreChangeExpectation:
    return PreChangeExpectation(
        expected_hostname="br01-rtr01",
        required_interfaces=[
            InterfaceExpectation(
                name="FastEthernet1/0",
                ipv4=IPv4Address("192.168.100.10"),
                status="up",
                protocol="up",
            )
        ],
        required_routes=[
            RouteExpectation(
                network=IPv4Network("192.168.100.0/24"),
                protocol="C",
                outgoing_interface="FastEthernet1/0",
            )
        ],
    )


def build_desired_state() -> DeviceDesiredState:
    return DeviceDesiredState(
        hostname="br01-rtr01",
        role="branch_router",
        platform="cisco_ios_c7200",
        interfaces=[
            InterfaceDesiredState(
                name="wan",
                ipv4=IPv4Interface("10.101.255.1/30"),
            )
        ],
    )


def build_post_change_state() -> DeviceState:
    return DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="FastEthernet1/0",
                ipv4=IPv4Address("10.101.255.1"),
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[
            RouteState(
                protocol="C",
                network=IPv4Network("10.101.255.0/30"),
                outgoing_interface="FastEthernet1/0",
            )
        ],
    )


def test_failed_pre_change_validation_blocks_deployment() -> None:
    executor = Mock()
    state_provider = Mock()

    expectation = PreChangeExpectation(
        expected_hostname="br01-rtr01",
        required_interfaces=[
            InterfaceExpectation(
                name="FastEthernet1/1",
                status="up",
            )
        ],
    )

    result = deploy_device(
        hostname="br01-rtr01",
        candidate_config="interface FastEthernet1/0",
        desired_state=build_desired_state(),
        current_state=build_current_state(),
        pre_change_expectation=expectation,
        executor=executor,
        state_provider=state_provider,
    )

    assert result.status == DeploymentStatus.BLOCKED
    assert result.succeeded is False
    assert result.deployment_attempted is False
    assert result.deployment_succeeded is False
    assert result.post_change is None

    executor.apply_config.assert_not_called()
    state_provider.collect_state.assert_not_called()


def test_deployment_execution_failure_returns_failed_result() -> None:
    executor = Mock()
    state_provider = Mock()

    executor.apply_config.side_effect = DeploymentExecutionError(
        "Unable to apply configuration"
    )

    result = deploy_device(
        hostname="br01-rtr01",
        candidate_config="interface FastEthernet1/0",
        desired_state=build_desired_state(),
        current_state=build_current_state(),
        pre_change_expectation=build_passing_pre_change_expectation(),
        executor=executor,
        state_provider=state_provider,
    )

    assert result.status == DeploymentStatus.FAILED
    assert result.succeeded is False
    assert result.deployment_attempted is True
    assert result.deployment_succeeded is False
    assert result.post_change is None
    assert result.message == "Unable to apply configuration"

    executor.apply_config.assert_called_once_with(
        "br01-rtr01",
        "interface FastEthernet1/0",
    )
    state_provider.collect_state.assert_not_called()


def test_post_change_state_collection_failure_does_not_mark_success() -> None:
    executor = Mock()
    state_provider = Mock()

    state_provider.collect_state.side_effect = DeviceStateCollectionError(
        "Unable to collect fresh device state"
    )

    result = deploy_device(
        hostname="br01-rtr01",
        candidate_config="interface FastEthernet1/0",
        desired_state=build_desired_state(),
        current_state=build_current_state(),
        pre_change_expectation=build_passing_pre_change_expectation(),
        executor=executor,
        state_provider=state_provider,
    )

    assert result.status == DeploymentStatus.POST_CHECK_FAILED
    assert result.succeeded is False
    assert result.deployment_attempted is True
    assert result.deployment_succeeded is True
    assert result.post_change is None
    assert (
        result.message
        == "Configuration applied but post-change state "
        "collection failed: Unable to collect fresh device state"
    )

    executor.apply_config.assert_called_once()
    state_provider.collect_state.assert_called_once_with(
        "br01-rtr01"
    )


def test_post_change_validation_failure_does_not_mark_deployment_successful() -> None:
    executor = Mock()
    state_provider = Mock()

    state_provider.collect_state.return_value = build_current_state()

    result = deploy_device(
        hostname="br01-rtr01",
        candidate_config="interface FastEthernet1/0",
        desired_state=build_desired_state(),
        current_state=build_current_state(),
        pre_change_expectation=build_passing_pre_change_expectation(),
        executor=executor,
        state_provider=state_provider,
    )

    assert result.status == DeploymentStatus.POST_VALIDATION_FAILED
    assert result.succeeded is False
    assert result.deployment_attempted is True
    assert result.deployment_succeeded is True
    assert result.post_change is not None
    assert result.post_change.passed is False

    executor.apply_config.assert_called_once()
    state_provider.collect_state.assert_called_once_with(
        "br01-rtr01"
    )


def test_deployment_succeeds_only_after_post_validation() -> None:
    executor = Mock()
    state_provider = Mock()

    state_provider.collect_state.return_value = build_post_change_state()

    result = deploy_device(
        hostname="br01-rtr01",
        candidate_config="interface FastEthernet1/0",
        desired_state=build_desired_state(),
        current_state=build_current_state(),
        pre_change_expectation=build_passing_pre_change_expectation(),
        executor=executor,
        state_provider=state_provider,
    )

    assert result.status == DeploymentStatus.SUCCEEDED
    assert result.succeeded is True
    assert result.deployment_attempted is True
    assert result.deployment_succeeded is True
    assert result.post_change is not None
    assert result.post_change.passed is True

    executor.apply_config.assert_called_once_with(
        "br01-rtr01",
        "interface FastEthernet1/0",
    )
    state_provider.collect_state.assert_called_once_with(
        "br01-rtr01"
    )

def test_deployment_rejects_current_state_for_wrong_device() -> None:
    executor = Mock()
    state_provider = Mock()

    current_state = build_current_state().model_copy(
        update={"hostname": "br02-rtr01"}
    )

    with pytest.raises(
        DeploymentServiceError,
        match=(
            "Current state target mismatch: "
            "expected br01-rtr01, got br02-rtr01"
        ),
    ):
        deploy_device(
            hostname="br01-rtr01",
            candidate_config="interface FastEthernet1/0",
            desired_state=build_desired_state(),
            current_state=current_state,
            pre_change_expectation=build_passing_pre_change_expectation(),
            executor=executor,
            state_provider=state_provider,
        )

    executor.apply_config.assert_not_called()
    state_provider.collect_state.assert_not_called()

def test_deployment_rejects_desired_state_for_wrong_device() -> None:
    executor = Mock()
    state_provider = Mock()

    desired_state = build_desired_state().model_copy(
        update={"hostname": "br02-rtr01"}
    )

    with pytest.raises(
        DeploymentServiceError,
        match=(
            "Desired state target mismatch: "
            "expected br01-rtr01, got br02-rtr01"
        ),
    ):
        deploy_device(
            hostname="br01-rtr01",
            candidate_config="interface FastEthernet1/0",
            desired_state=desired_state,
            current_state=build_current_state(),
            pre_change_expectation=build_passing_pre_change_expectation(),
            executor=executor,
            state_provider=state_provider,
        )

    executor.apply_config.assert_not_called()
    state_provider.collect_state.assert_not_called()