from ipaddress import IPv4Address, IPv4Network

import pytest

from network_automation_platform.device_state import (
    DeviceState,
    InterfaceState,
    RouteState,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    RouteExpectation,
    ValidationExpectation,
    ValidationStatus,
    validate_device_state,
)


def test_validate_device_state_fails_missing_interface() -> None:
    state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[],
        routes=[
            RouteState(
                protocol="C",
                network=IPv4Network("192.168.64.0/24"),
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
                ipv4=IPv4Address("192.168.64.10"),
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteExpectation(
                network=IPv4Network("192.168.64.0/24"),
                protocol="C",
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    report = validate_device_state(state, expectation)

    assert report.passed is False
    assert len(report.checks) == 2
    assert report.checks[0].status == ValidationStatus.FAIL
    assert report.checks[0].message == "Interface FastEthernet0/0 is missing"
    assert report.checks[1].status == ValidationStatus.PASS
    assert report.checks[1].message == "Route 192.168.64.0/24 matches expectation"


def test_validate_device_state_fails_wrong_interface_ip() -> None:
    state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="FastEthernet0/0",
                ipv4=IPv4Address("192.168.64.11"),
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteState(
                protocol="C",
                network=IPv4Network("192.168.64.0/24"),
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
                ipv4=IPv4Address("192.168.64.10"),
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteExpectation(
                network=IPv4Network("192.168.64.0/24"),
                protocol="C",
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    report = validate_device_state(state, expectation)

    assert report.passed is False
    assert len(report.checks) == 2
    assert report.checks[0].status == ValidationStatus.FAIL
    assert "IPv4 expected 192.168.64.10, got 192.168.64.11" in report.checks[0].message
    assert report.checks[1].status == ValidationStatus.PASS
    assert report.checks[1].message == "Route 192.168.64.0/24 matches expectation"


def test_validate_device_state_fails_missing_route() -> None:
    state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="FastEthernet0/0",
                ipv4=IPv4Address("192.168.64.10"),
                status="up",
                protocol="up",
            )
        ],
        routes=[],
    )

    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
                ipv4=IPv4Address("192.168.64.10"),
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteExpectation(
                network=IPv4Network("192.168.64.0/24"),
                protocol="C",
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    report = validate_device_state(state, expectation)

    assert report.passed is False
    assert len(report.checks) == 2
    assert report.checks[0].status == ValidationStatus.PASS
    assert report.checks[0].message == "Interface FastEthernet0/0 matches expectation"
    assert report.checks[1].status == ValidationStatus.FAIL
    assert report.checks[1].message == "Route 192.168.64.0/24 is missing"

def test_validate_device_state_fails_wrong_route_protocol() -> None:
    state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="FastEthernet0/0",
                ipv4=IPv4Address("192.168.64.10"),
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteState(
                protocol="O",
                network=IPv4Network("192.168.64.0/24"),
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
                ipv4=IPv4Address("192.168.64.10"),
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteExpectation(
                network=IPv4Network("192.168.64.0/24"),
                protocol="C",
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    report = validate_device_state(state, expectation)

    assert report.passed is False
    assert len(report.checks) == 2
    assert report.checks[0].status == ValidationStatus.PASS
    assert report.checks[0].message == "Interface FastEthernet0/0 matches expectation"
    assert report.checks[1].status == ValidationStatus.FAIL
    assert "protocol expected C, got O" in report.checks[1].message

def test_validate_device_state_passes() -> None:
    state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="FastEthernet0/0",
                ipv4=IPv4Address("192.168.64.10"),
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteState(
                protocol="C",
                network=IPv4Network("192.168.64.0/24"),
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
                ipv4=IPv4Address("192.168.64.10"),
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteExpectation(
                network=IPv4Network("192.168.64.0/24"),
                protocol="C",
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    report = validate_device_state(state, expectation)

    assert report.passed is True
    assert len(report.checks) == 2
    assert all(
        check.status == ValidationStatus.PASS
        for check in report.checks
    )

def test_validation_expectation_rejects_empty() -> None:
    with pytest.raises(
        ValueError,
        match="At least one validation expectation is required",
    ):
        ValidationExpectation()

def test_validate_device_state_passes_when_one_matching_route_satisfies_expectation() -> None:
    state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[],
        routes=[
            RouteState(
                protocol="O",
                network=IPv4Network("10.10.10.0/24"),
                next_hop=IPv4Address("192.0.2.1"),
            ),
            RouteState(
                protocol="O",
                network=IPv4Network("10.10.10.0/24"),
                next_hop=IPv4Address("192.0.2.2"),
            ),
        ],
    )

    expectation = ValidationExpectation(
        routes=[
            RouteExpectation(
                network=IPv4Network("10.10.10.0/24"),
                protocol="O",
                next_hop=IPv4Address("192.0.2.2"),
            )
        ]
    )

    report = validate_device_state(state, expectation)

    assert report.passed is True
    assert report.checks[0].status == ValidationStatus.PASS
