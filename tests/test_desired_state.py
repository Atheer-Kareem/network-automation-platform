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