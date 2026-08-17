from pathlib import Path

from network_automation_platform.models import load_branch_intent
from network_automation_platform.planning import build_branch_desired_state


def test_build_branch_desired_state() -> None:
    intent = load_branch_intent(Path("intent/branches/branch-01.yaml"))

    desired_state = build_branch_desired_state(intent)

    assert desired_state.branch_id == "branch-01"
    assert len(desired_state.devices) == 2


def test_router_desired_state_contains_ospf_networks() -> None:
    intent = load_branch_intent(Path("intent/branches/branch-01.yaml"))

    desired_state = build_branch_desired_state(intent)

    router = next(
        device
        for device in desired_state.devices
        if device.role == "branch_router"
    )

    assert router.ospf is not None
    assert intent.networks.users.prefix in router.ospf.networks
    assert intent.networks.management.prefix in router.ospf.networks
    assert router.ospf.neighbor_address == intent.routing.neighbor_address
    assert router.ospf.learned_routes == intent.routing.learned_routes


def test_switch_desired_state_contains_standard_vlans() -> None:
    intent = load_branch_intent(Path("intent/branches/branch-01.yaml"))

    desired_state = build_branch_desired_state(intent)

    switch = next(
        device
        for device in desired_state.devices
        if device.role == "branch_switch"
    )

    vlan_ids = {vlan.vlan_id for vlan in switch.vlans}

    assert vlan_ids == {10, 20, 99}

def test_router_desired_state_contains_vlan_gateways() -> None:
    intent = load_branch_intent(Path("intent/branches/branch-01.yaml"))
    desired_state = build_branch_desired_state(intent)

    router = next(
        device
        for device in desired_state.devices
        if device.role == "branch_router"
    )

    users = next(
        interface
        for interface in router.interfaces
        if interface.name == "users"
    )

    assert users.parent == "lan"
    assert users.vlan_id == 10
    assert str(users.ipv4) == "10.101.10.1/24"

def test_switch_desired_state_contains_trunk_and_management_svi() -> None:
    intent = load_branch_intent(Path("intent/branches/branch-01.yaml"))
    desired_state = build_branch_desired_state(intent)

    switch = next(
        device
        for device in desired_state.devices
        if device.role == "branch_switch"
    )

    uplink = next(
        interface
        for interface in switch.interfaces
        if interface.name == "uplink"
    )

    management_svi = next(
        interface
        for interface in switch.interfaces
        if interface.name == "management_svi"
    )

    assert uplink.mode == "trunk"
    assert uplink.allowed_vlans == [10, 20, 99]
    assert management_svi.vlan_id == 99
    assert str(management_svi.ipv4) == "10.101.99.21/24"
    assert switch.default_gateway == "10.101.99.1"
