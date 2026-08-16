from ipaddress import IPv4Address, IPv4Interface, IPv4Network

from network_automation_platform.desired_state import (
    DeviceDesiredState,
    InterfaceDesiredState,
)
from network_automation_platform.device_state import (
    DeviceState,
    InterfaceState,
    RouteState,
)
from network_automation_platform.validation_service import (
    validate_device_against_desired_state,
)


def test_validate_device_against_desired_state() -> None:
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
                ipv4_prefixlen=30,
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

    report = validate_device_against_desired_state(
        desired,
        actual,
    )

    assert report.passed is True
