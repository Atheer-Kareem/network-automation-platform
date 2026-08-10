from ipaddress import IPv4Interface, IPv4Network
from pathlib import Path

import pytest

from network_automation_platform.desired_state import (
    DeviceDesiredState,
    InterfaceDesiredState,
)
from network_automation_platform.models import load_branch_intent
from network_automation_platform.planning import build_branch_desired_state
from network_automation_platform.validation_expectations import (
    ValidationExpectationError,
    build_desired_state_expectation,
)


def test_build_router_validation_expectation() -> None:
    device = DeviceDesiredState(
        hostname="br01-rtr01",
        role="branch_router",
        platform="cisco_ios_c7200",
        interfaces=[
            InterfaceDesiredState(
                name="wan",
                ipv4=IPv4Interface("192.168.64.10/24"),
            ),
            InterfaceDesiredState(
                name="lan",
            ),
            InterfaceDesiredState(
                name="users",
                parent="lan",
                vlan_id=10,
                ipv4=IPv4Interface("10.101.10.1/24"),
            ),
        ],
    )

    expectation = build_desired_state_expectation(device)

    assert len(expectation.interfaces) == 3
    assert len(expectation.routes) == 2

    assert expectation.interfaces[0].name == "FastEthernet0/0"
    assert expectation.interfaces[0].ipv4.exploded == "192.168.64.10"

    assert expectation.interfaces[1].name == "FastEthernet1/0"
    assert expectation.interfaces[1].ipv4 is None

    assert expectation.interfaces[2].name == "FastEthernet1/0.10"
    assert expectation.interfaces[2].ipv4.exploded == "10.101.10.1"

    assert expectation.routes[0].network == IPv4Network(
        "192.168.64.0/24"
    )
    assert expectation.routes[0].protocol == "C"
    assert expectation.routes[0].outgoing_interface == "FastEthernet0/0"

    assert expectation.routes[1].network == IPv4Network(
        "10.101.10.0/24"
    )
    assert expectation.routes[1].outgoing_interface == "FastEthernet1/0.10"

def test_build_desired_state_expectation_rejects_unsupported_role() -> None:
    device = DeviceDesiredState(
        hostname="br01-sw01",
        role="branch_switch",
        platform="cisco_iosv_l2",
    )

    with pytest.raises(
        ValidationExpectationError,
        match="Unsupported device role for validation: branch_switch",
    ):
        build_desired_state_expectation(device)

def test_build_desired_state_expectation_rejects_unknown_platform() -> None:
    device = DeviceDesiredState(
        hostname="br01-rtr01",
        role="branch_router",
        platform="unknown_router",
        interfaces=[
            InterfaceDesiredState(
                name="wan",
                ipv4=IPv4Interface("192.168.64.10/24"),
            )
        ],
    )

    with pytest.raises(
        ValidationExpectationError,
        match="Unsupported router platform: unknown_router",
    ):
        build_desired_state_expectation(device)

def test_build_expectation_from_branch_desired_state() -> None:
    intent = load_branch_intent(
        Path("intent/branches/branch-01.yaml")
    )

    desired_state = build_branch_desired_state(intent)

    router = next(
        device
        for device in desired_state.devices
        if device.role == "branch_router"
    )

    expectation = build_desired_state_expectation(router)

    interface_names = {
        interface.name
        for interface in expectation.interfaces
    }

    assert "FastEthernet0/0" in interface_names
    assert "FastEthernet1/0" in interface_names

    expected_networks = {
        route.network
        for route in expectation.routes
    }

    assert intent.wan.transit_prefix in expected_networks
    assert intent.networks.users.prefix in expected_networks
    assert intent.networks.voice.prefix in expected_networks
    assert intent.networks.management.prefix in expected_networks
