
import pytest

from network_automation_platform.device_state import (
    DeviceState,
    InterfaceState,
    RouteState,
)
from network_automation_platform.pre_change_validation import (
    PreChangeExpectation,
    PreChangeValidationError,
    validate_pre_change_state,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    RouteExpectation,
    ValidationStatus,
)
from tests.factories import (
    TEST_CORE_IP,
    TEST_OOB_NETWORK,
)


def test_pre_change_validation_passes() -> None:
    actual = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="FastEthernet0/0",
                ipv4=TEST_CORE_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            ),
            InterfaceState(
                name="FastEthernet1/0",
                status="administratively down",
                protocol="down",
                admin_enabled=False,
            ),
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
            ),
            InterfaceExpectation(
                name="FastEthernet1/0",
            ),
        ],
        required_routes=[
            RouteExpectation(
                network=TEST_OOB_NETWORK,
                protocol="C",
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    report = validate_pre_change_state(actual, expectation)

    assert report.passed is True
    assert all(
        check.status == ValidationStatus.PASS
        for check in report.checks
    )


def test_pre_change_validation_fails_missing_required_interface() -> None:
    actual = DeviceState(
        hostname="br01-rtr01",
        interfaces=[],
        routes=[],
    )

    expectation = PreChangeExpectation(
        expected_hostname="br01-rtr01",
        required_interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
            )
        ],
    )

    report = validate_pre_change_state(actual, expectation)

    assert report.passed is False
    assert report.checks[0].status == ValidationStatus.FAIL
    assert report.checks[0].message == (
        "Interface FastEthernet0/0 is missing"
    )


def test_pre_change_validation_fails_missing_required_route() -> None:
    actual = DeviceState(
        hostname="br01-rtr01",
        interfaces=[],
        routes=[],
    )

    expectation = PreChangeExpectation(
        expected_hostname="br01-rtr01",
        required_routes=[
            RouteExpectation(
                network=TEST_OOB_NETWORK,
                protocol="C",
            )
        ],
    )

    report = validate_pre_change_state(actual, expectation)

    assert report.passed is False
    assert report.checks[0].status == ValidationStatus.FAIL
    assert report.checks[0].message == (
        f"Route {TEST_OOB_NETWORK} is missing"
    )


def test_pre_change_validation_rejects_wrong_device() -> None:
    actual = DeviceState(
        hostname="wrong-router",
        interfaces=[],
        routes=[],
    )

    expectation = PreChangeExpectation(
        expected_hostname="br01-rtr01",
        required_interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
            )
        ],
    )

    with pytest.raises(
        PreChangeValidationError,
        match=(
            "Device identity mismatch: "
            "expected br01-rtr01, got wrong-router"
        ),
    ):
        validate_pre_change_state(actual, expectation)


def test_pre_change_expectation_rejects_no_prerequisites() -> None:
    with pytest.raises(
        ValueError,
        match="At least one pre-change prerequisite is required",
    ):
        PreChangeExpectation(
            expected_hostname="br01-rtr01",
        )
