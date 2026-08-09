from pathlib import Path

from network_automation_platform.models import load_branch_intent
from network_automation_platform.planning import build_branch_desired_state
from network_automation_platform.renderers.cisco_ios import render_device


def load_desired_devices():
    intent = load_branch_intent(Path("intent/branches/branch-01.yaml"))
    desired_state = build_branch_desired_state(intent)
    return desired_state.devices


def test_render_cisco_router_configuration() -> None:
    devices = load_desired_devices()

    router = next(
        device for device in devices if device.role == "branch_router"
    )
    config = render_device(router)
    assert router.platform == "cisco_ios_c7200"

    assert "hostname br01-rtr01" in config
    assert "interface FastEthernet0/0" in config
    assert "ip address 10.101.255.1 255.255.255.252" in config

    assert "interface FastEthernet1/0.10" in config
    assert "encapsulation dot1Q 10" in config
    assert "ip address 10.101.10.1 255.255.255.0" in config

    assert "interface FastEthernet1/0.20" in config
    assert "encapsulation dot1Q 20" in config

    assert "interface FastEthernet1/0.99" in config
    assert "encapsulation dot1Q 99" in config

    assert "router ospf 1" in config
    assert "network 10.101.10.0 0.0.0.255 area 0" in config
    assert "network 10.101.99.0 0.0.0.255 area 0" in config

def test_render_cisco_switch_configuration() -> None:
    devices = load_desired_devices()

    switch = next(
        device for device in devices if device.role == "branch_switch"
    )

    assert switch.platform == "cisco_iosv_l2"

    config = render_device(switch)

    assert "hostname br01-sw01" in config
    assert "no ip routing" in config

    assert "vlan 10" in config
    assert "name USERS" in config
    assert "vlan 20" in config
    assert "name VOICE" in config
    assert "vlan 99" in config
    assert "name MANAGEMENT" in config

    assert "interface GigabitEthernet0/0" in config
    assert "switchport trunk encapsulation dot1q" in config
    assert "switchport mode trunk" in config
    assert "switchport trunk allowed vlan 10,20,99" in config

    assert "interface GigabitEthernet0/1" in config
    assert "switchport mode access" in config
    assert "switchport access vlan 10" in config

    assert "interface Vlan99" in config
    assert "ip address 10.101.99.21 255.255.255.0" in config
    assert "ip default-gateway 10.101.99.1" in config

    encapsulation_index = config.index(
        "switchport trunk encapsulation dot1q"
    )
    trunk_mode_index = config.index("switchport mode trunk")

    assert encapsulation_index < trunk_mode_index
