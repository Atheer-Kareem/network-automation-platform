from ipaddress import IPv4Address, IPv4Interface, IPv4Network

import pytest

from network_automation_platform.change_validation import (
    ValidationPhase,
    run_post_change_validation,
    run_pre_change_validation,
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
from network_automation_platform.pre_change_validation import (
    PreChangeExpectation,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    RouteExpectation,
)
from network_automation_platform.validation_service import (
    ValidationServiceError,
)
from tests.factories import (
    TEST_CORE_IP,
    TEST_OOB_NETWORK,
)


def test_run_post_change_validation_passes() -> None:
    desired = DeviceDesiredState(
        hostname="br01-rtr01",
        role="branch_router",
        platform="cisco_iosv",
        interfaces=[
            InterfaceDesiredState(
                name="wan",
                ipv4=IPv4Interface("10.101.255.1/30"),
            )
        ],
    )

    actual = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/1",
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
                outgoing_interface="GigabitEthernet0/1",
            )
        ],
    )

    result = run_post_change_validation(
        desired,
        actual,
    )

    assert result.phase == ValidationPhase.POST_CHANGE
    assert result.passed is True
    assert result.report.passed is True


def test_run_post_change_validation_fails() -> None:
    desired = DeviceDesiredState(
        hostname="br01-rtr01",
        role="branch_router",
        platform="cisco_iosv",
        interfaces=[
            InterfaceDesiredState(
                name="wan",
                ipv4=IPv4Interface("10.101.255.1/30"),
            )
        ],
    )

    actual = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=TEST_CORE_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[
            RouteState(
                protocol="C",
                network=TEST_OOB_NETWORK,
                outgoing_interface="GigabitEthernet0/0",
            )
        ],
    )

    result = run_post_change_validation(
        desired,
        actual,
    )

    assert result.phase == ValidationPhase.POST_CHANGE
    assert result.passed is False
    assert result.report.passed is False

def test_run_post_change_validation_rejects_wrong_device() -> None:
    desired = DeviceDesiredState(
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

    actual = DeviceState(
        hostname="some-other-router",
        interfaces=[],
        routes=[],
    )

    with pytest.raises(
        ValidationServiceError,
        match=(
            "Device identity mismatch: "
            "expected br01-rtr01, got some-other-router"
        ),
    ):
        run_post_change_validation(
            desired,
            actual,
        )

def test_run_pre_change_validation_returns_pre_change_phase() -> None:
    actual = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="FastEthernet0/0",
                ipv4=TEST_CORE_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[
            RouteState(
                protocol="C",
                network=TEST_OOB_NETWORK,
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    expectation = PreChangeExpectation(
        expected_hostname="br01-rtr01",
        required_interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
                ipv4=TEST_CORE_IP,
                status="up",
                protocol="up",
            )
        ],
        required_routes=[
            RouteExpectation(
                network=TEST_OOB_NETWORK,
                protocol="C",
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    result = run_pre_change_validation(
        expectation,
        actual,
    )

    assert result.phase == ValidationPhase.PRE_CHANGE
    assert result.passed is True
    assert result.report.passed is True
