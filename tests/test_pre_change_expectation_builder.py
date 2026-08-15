from ipaddress import IPv4Address, IPv4Network

import pytest

from network_automation_platform.device_state import (
    DeviceState,
    InterfaceState,
    RouteState,
)
from network_automation_platform.pre_change_expectation_builder import (
    PreChangeExpectationBuildError,
    build_pre_change_expectation,
)
from tests.factories import make_inventory_device, make_lab_inventory


def test_build_pre_change_expectation_protects_oob_path() -> None:
    device = make_inventory_device(
        hostname="br01-sw01",
        host="192.0.2.12",
    )

    inventory = make_lab_inventory(
        devices=[device]
    )

    current_state = DeviceState(
        hostname="br01-sw01",
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=IPv4Address("192.0.2.12"),
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[
            RouteState(
                protocol="C",
                network=IPv4Network("192.0.2.0/24"),
                outgoing_interface="GigabitEthernet0/0",
            )
        ],
    )

    expectation = build_pre_change_expectation(
        device=device,
        inventory=inventory,
        current_state=current_state,
    )

    assert expectation.expected_hostname == "br01-sw01"

    assert len(expectation.required_interfaces) == 1

    required_interface = expectation.required_interfaces[0]

    assert required_interface.name == "GigabitEthernet0/0"
    assert required_interface.ipv4 == IPv4Address("192.0.2.12")
    assert required_interface.status == "up"
    assert required_interface.protocol == "up"
    assert required_interface.admin_enabled is True

    assert len(expectation.required_routes) == 1
    assert (
        expectation.required_routes[0].network
        == IPv4Network("192.0.2.0/24")
    )


def test_build_pre_change_expectation_allows_no_oob_route() -> None:
    device = make_inventory_device(
        hostname="br01-sw01",
        host="192.0.2.12",
    )

    inventory = make_lab_inventory(
        devices=[device]
    )

    current_state = DeviceState(
        hostname="br01-sw01",
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=IPv4Address("192.0.2.12"),
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[],
    )

    expectation = build_pre_change_expectation(
        device=device,
        inventory=inventory,
        current_state=current_state,
    )

    assert len(expectation.required_interfaces) == 1
    assert expectation.required_routes == []


def test_build_pre_change_expectation_rejects_missing_oob_interface() -> None:
    device = make_inventory_device(
        hostname="br01-sw01",
        host="192.0.2.12",
    )

    inventory = make_lab_inventory(
        devices=[device]
    )

    current_state = DeviceState(
        hostname="br01-sw01",
        interfaces=[],
        routes=[],
    )

    with pytest.raises(
        PreChangeExpectationBuildError,
        match="Unable to identify OOB management interface",
    ):
        build_pre_change_expectation(
            device=device,
            inventory=inventory,
            current_state=current_state,
        )


def test_build_pre_change_expectation_rejects_down_oob_interface() -> None:
    device = make_inventory_device(
        hostname="br01-sw01",
        host="192.0.2.12",
    )

    inventory = make_lab_inventory(
        devices=[device]
    )

    current_state = DeviceState(
        hostname="br01-sw01",
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=IPv4Address("192.0.2.12"),
                status="down",
                protocol="down",
                admin_enabled=True,
            )
        ],
        routes=[],
    )

    with pytest.raises(
        PreChangeExpectationBuildError,
        match="is not operational",
    ):
        build_pre_change_expectation(
            device=device,
            inventory=inventory,
            current_state=current_state,
        )