from ipaddress import IPv4Interface, IPv4Network
from pathlib import Path

import pytest

from network_automation_platform.desired_state import (
    DeviceDesiredState,
    InterfaceDesiredState,
    VlanDesiredState,
)
from network_automation_platform.models import load_branch_intent
from network_automation_platform.planning import build_branch_desired_state
from network_automation_platform.validation_expectations import (
    ValidationExpectationError,
    build_desired_state_expectation,
)
from tests.factories import TEST_CORE_IP, TEST_OOB_NETWORK


def test_build_router_validation_expectation() -> None:
    device = DeviceDesiredState(
        hostname="br01-rtr01",
        role="branch_router",
        platform="cisco_iosv",
        interfaces=[
            InterfaceDesiredState(
                name="wan",
                ipv4=IPv4Interface(f"{TEST_CORE_IP}/{TEST_OOB_NETWORK.prefixlen}"),
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

    assert expectation.interfaces[0].name == "GigabitEthernet0/1"
    assert expectation.interfaces[0].ipv4 == TEST_CORE_IP

    assert expectation.interfaces[1].name == "GigabitEthernet0/2"
    assert expectation.interfaces[1].ipv4 is None

    assert expectation.interfaces[2].name == "GigabitEthernet0/2.10"
    assert expectation.interfaces[2].ipv4.exploded == "10.101.10.1"

    assert expectation.routes[0].network == IPv4Network(f"{TEST_OOB_NETWORK.network_address}/{TEST_OOB_NETWORK.prefixlen}")
    assert expectation.routes[0].protocol == "C"
    assert expectation.routes[0].outgoing_interface == "GigabitEthernet0/1"

    assert expectation.routes[1].network == IPv4Network(
        "10.101.10.0/24"
    )
    assert expectation.routes[1].outgoing_interface == "GigabitEthernet0/2.10"
    assert expectation.interfaces[0].ipv4_prefixlen == 24
    assert expectation.interfaces[0].description == device.interfaces[0].description

def test_build_desired_state_expectation_rejects_unknown_switch_platform() -> None:
    device = DeviceDesiredState(
        hostname="br01-sw01",
        role="branch_switch",
        platform="unknown_switch",
    )

    with pytest.raises(
        ValidationExpectationError,
        match="Unsupported switch platform: unknown_switch",
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
                ipv4=IPv4Interface(f"{TEST_CORE_IP}/{TEST_OOB_NETWORK.prefixlen}"),
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

    assert "GigabitEthernet0/1" in interface_names
    assert "GigabitEthernet0/2" in interface_names
    assert "GigabitEthernet0/2.10" in interface_names
    assert "GigabitEthernet0/2.20" in interface_names
    assert "GigabitEthernet0/2.99" in interface_names

    expected_networks = {
        route.network
        for route in expectation.routes
    }

    assert intent.wan.transit_prefix in expected_networks
    assert intent.networks.users.prefix in expected_networks
    assert intent.networks.voice.prefix in expected_networks
    assert intent.networks.management.prefix in expected_networks

def test_build_switch_validation_expectation() -> None:
    device = DeviceDesiredState(
        hostname="br01-sw01",
        role="branch_switch",
        platform="cisco_iosv_l2",
        vlans=[
            VlanDesiredState(
                vlan_id=10,
                name="USERS",
            ),
            VlanDesiredState(
                vlan_id=20,
                name="VOICE",
            ),
            VlanDesiredState(
                vlan_id=99,
                name="MANAGEMENT",
            ),
        ],
        interfaces=[
            InterfaceDesiredState(
                name="uplink",
                mode="trunk",
                allowed_vlans=[10, 20, 99],
            ),
            InterfaceDesiredState(
                name="users_access",
                mode="access",
                access_vlan=10,
            ),
            InterfaceDesiredState(
                name="voice_access",
                mode="access",
                access_vlan=20,
            ),
            InterfaceDesiredState(
                name="management_svi",
                description="Switch management SVI",
                vlan_id=99,
                ipv4=IPv4Interface("10.101.99.21/24"),
            ),
        ],
    )

    expectation = build_desired_state_expectation(device)

    assert len(expectation.interfaces) == 4
    assert len(expectation.vlans) == 3
    assert len(expectation.switchports) == 3

    interface_names = {
        interface.name
        for interface in expectation.interfaces
    }

    assert interface_names == {
        "GigabitEthernet0/1",
        "GigabitEthernet0/2",
        "GigabitEthernet0/3",
        "Vlan99",
    }

    management_svi = next(
        interface
        for interface in expectation.interfaces
        if interface.name == "Vlan99"
    )
    assert management_svi.ipv4 is not None
    assert str(management_svi.ipv4) == "10.101.99.21"
    assert management_svi.ipv4_prefixlen == 24
    assert management_svi.description == "Switch management SVI"
    assert management_svi.admin_enabled is True

    vlan_ids = {
        vlan.vlan_id
        for vlan in expectation.vlans
    }
    assert vlan_ids == {10, 20, 99}

    uplink = next(
        switchport
        for switchport in expectation.switchports
        if switchport.interface == "GigabitEthernet0/1"
    )
    assert uplink.switchport_enabled is True
    assert uplink.administrative_mode == "trunk"
    assert uplink.allowed_vlans == [10, 20, 99]

    users_access = next(
        switchport
        for switchport in expectation.switchports
        if switchport.interface == "GigabitEthernet0/2"
    )
    assert users_access.administrative_mode == "access"
    assert users_access.access_vlan == 10

    voice_access = next(
        switchport
        for switchport in expectation.switchports
        if switchport.interface == "GigabitEthernet0/3"
    )
    assert voice_access.administrative_mode == "access"
    assert voice_access.access_vlan == 20
