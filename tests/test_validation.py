from ipaddress import IPv4Address

import pytest

from network_automation_platform.device_state import (
    DeviceState,
    InterfaceState,
    RouteState,
    SwitchportState,
    VlanState,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    RouteExpectation,
    SwitchportExpectation,
    ValidationExpectation,
    ValidationStatus,
    VlanExpectation,
    validate_device_state,
)
from tests.factories import (
    TEST_CORE_IP,
    TEST_OOB_NETWORK,
    TEST_ROUTER_IP,
)


def test_validate_device_state_fails_missing_interface() -> None:
    state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[],
        routes=[
            RouteState(
                protocol="C",
                network=TEST_OOB_NETWORK,
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
                ipv4=TEST_CORE_IP,
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteExpectation(
                network=TEST_OOB_NETWORK,
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
    assert report.checks[1].message == f"Route {TEST_OOB_NETWORK} matches expectation"


def test_validate_device_state_fails_wrong_interface_ip() -> None:
    state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="FastEthernet0/0",
                ipv4=TEST_ROUTER_IP,
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

    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
                ipv4=TEST_CORE_IP,
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteExpectation(
                network=TEST_OOB_NETWORK,
                protocol="C",
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    report = validate_device_state(state, expectation)

    assert report.passed is False
    assert len(report.checks) == 2
    assert report.checks[0].status == ValidationStatus.FAIL
    assert f"IPv4 expected {TEST_CORE_IP}, got {TEST_ROUTER_IP}" in report.checks[0].message
    assert report.checks[1].status == ValidationStatus.PASS
    assert report.checks[1].message == f"Route {TEST_OOB_NETWORK} matches expectation"


def test_validate_device_state_fails_missing_route() -> None:
    state = DeviceState(
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
        routes=[],
    )

    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
                ipv4=TEST_CORE_IP,
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteExpectation(
                network=TEST_OOB_NETWORK,
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
    assert report.checks[1].message == f"Route {TEST_OOB_NETWORK} is missing"

def test_validate_device_state_fails_wrong_route_protocol() -> None:
    state = DeviceState(
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
                protocol="O",
                network=TEST_OOB_NETWORK,
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )

    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
                ipv4=TEST_CORE_IP,
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteExpectation(
                network=TEST_OOB_NETWORK,
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

    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
                ipv4=TEST_CORE_IP,
                status="up",
                protocol="up",
            )
        ],
        routes=[
            RouteExpectation(
                network=TEST_OOB_NETWORK,
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
                network=TEST_OOB_NETWORK,
                next_hop=IPv4Address("192.0.2.1"),
            ),
            RouteState(
                protocol="O",
                network=TEST_OOB_NETWORK,
                next_hop=IPv4Address("192.0.2.2"),
            ),
        ],
    )

    expectation = ValidationExpectation(
        routes=[
            RouteExpectation(
                network=TEST_OOB_NETWORK,
                protocol="O",
                next_hop=IPv4Address("192.0.2.2"),
            )
        ]
    )

    report = validate_device_state(state, expectation)

    assert report.passed is True
    assert report.checks[0].status == ValidationStatus.PASS

def test_validate_device_state_passes_vlan() -> None:
    state = DeviceState(
        hostname="br01-sw01",
        interfaces=[],
        routes=[],
        vlans=[
            VlanState(
                vlan_id=10,
                name="USERS",
                status="active",
            )
        ],
    )

    expectation = ValidationExpectation(
        vlans=[
            VlanExpectation(
                vlan_id=10,
                name="USERS",
                status="active",
            )
        ]
    )

    report = validate_device_state(state, expectation)

    assert report.passed is True
    assert len(report.checks) == 1
    assert report.checks[0].name == "vlan:10"
    assert report.checks[0].status == ValidationStatus.PASS


def test_validate_device_state_fails_vlan_mismatch() -> None:
    state = DeviceState(
        hostname="br01-sw01",
        interfaces=[],
        routes=[],
        vlans=[
            VlanState(
                vlan_id=10,
                name="WRONG",
                status="active",
            )
        ],
    )

    expectation = ValidationExpectation(
        vlans=[
            VlanExpectation(
                vlan_id=10,
                name="USERS",
                status="active",
            )
        ]
    )

    report = validate_device_state(state, expectation)

    assert report.passed is False
    assert len(report.checks) == 1
    assert report.checks[0].name == "vlan:10"
    assert report.checks[0].status == ValidationStatus.FAIL
    assert "name expected USERS, got WRONG" in report.checks[0].message


def test_validate_device_state_fails_missing_vlan() -> None:
    state = DeviceState(
        hostname="br01-sw01",
        interfaces=[],
        routes=[],
    )

    expectation = ValidationExpectation(
        vlans=[
            VlanExpectation(
                vlan_id=99,
                name="MANAGEMENT",
                status="active",
            )
        ]
    )

    report = validate_device_state(state, expectation)

    assert report.passed is False
    assert len(report.checks) == 1
    assert report.checks[0].name == "vlan:99"
    assert report.checks[0].status == ValidationStatus.FAIL
    assert report.checks[0].message == "VLAN 99 is missing"
    assert report.checks[0].reason is None


def test_validate_device_state_passes_switchport() -> None:
    state = DeviceState(
        hostname="br01-sw01",
        interfaces=[],
        routes=[],
        switchports=[
            SwitchportState(
                interface="GigabitEthernet0/2",
                switchport_enabled=True,
                administrative_mode="access",
                operational_mode="access",
                access_vlan=10,
            )
        ],
    )

    expectation = ValidationExpectation(
        switchports=[
            SwitchportExpectation(
                interface="GigabitEthernet0/2",
                switchport_enabled=True,
                administrative_mode="access",
                access_vlan=10,
            )
        ]
    )

    report = validate_device_state(state, expectation)

    assert report.passed is True
    assert len(report.checks) == 1
    assert report.checks[0].name == "switchport:GigabitEthernet0/2"
    assert report.checks[0].status == ValidationStatus.PASS


def test_validate_device_state_fails_switchport_mismatch() -> None:
    state = DeviceState(
        hostname="br01-sw01",
        interfaces=[],
        routes=[],
        switchports=[
            SwitchportState(
                interface="GigabitEthernet0/2",
                switchport_enabled=True,
                administrative_mode="access",
                operational_mode="access",
                access_vlan=20,
            )
        ],
    )

    expectation = ValidationExpectation(
        switchports=[
            SwitchportExpectation(
                interface="GigabitEthernet0/2",
                switchport_enabled=True,
                administrative_mode="access",
                access_vlan=10,
            )
        ]
    )

    report = validate_device_state(state, expectation)

    assert report.passed is False
    assert len(report.checks) == 1
    assert report.checks[0].name == "switchport:GigabitEthernet0/2"
    assert report.checks[0].status == ValidationStatus.FAIL
    assert "access VLAN expected 10, got 20" in report.checks[0].message


def test_validate_device_state_fails_missing_switchport() -> None:
    state = DeviceState(
        hostname="br01-sw01",
        interfaces=[],
        routes=[],
    )

    expectation = ValidationExpectation(
        switchports=[
            SwitchportExpectation(
                interface="GigabitEthernet0/1",
                switchport_enabled=True,
                administrative_mode="trunk",
                allowed_vlans=[10, 20, 99],
            )
        ]
    )

    report = validate_device_state(state, expectation)

    assert report.passed is False
    assert len(report.checks) == 1
    assert report.checks[0].name == "switchport:GigabitEthernet0/1"
    assert report.checks[0].status == ValidationStatus.FAIL
    assert (
        report.checks[0].message
        == "Switchport GigabitEthernet0/1 is missing"
    )


def test_validate_device_state_compares_allowed_vlans_without_order() -> None:
    state = DeviceState(
        hostname="br01-sw01",
        interfaces=[],
        routes=[],
        switchports=[
            SwitchportState(
                interface="GigabitEthernet0/1",
                switchport_enabled=True,
                administrative_mode="trunk",
                operational_mode="trunk",
                native_vlan=1,
                allowed_vlans=[99, 10, 20],
            )
        ],
    )

    expectation = ValidationExpectation(
        switchports=[
            SwitchportExpectation(
                interface="GigabitEthernet0/1",
                switchport_enabled=True,
                administrative_mode="trunk",
                allowed_vlans=[10, 20, 99],
            )
        ]
    )

    report = validate_device_state(state, expectation)

    assert report.passed is True
    assert len(report.checks) == 1
    assert report.checks[0].status == ValidationStatus.PASS
