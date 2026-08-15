from ipaddress import IPv4Address

from network_automation_platform.device_state import DeviceState
from network_automation_platform.inventory import (
    DeviceInventory,
    InventoryDevice,
)
from network_automation_platform.pre_change_validation import (
    PreChangeExpectation,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    RouteExpectation,
)


class PreChangeExpectationBuildError(ValueError):
    pass


def build_pre_change_expectation(
    device: InventoryDevice,
    inventory: DeviceInventory,
    current_state: DeviceState,
) -> PreChangeExpectation:
    if inventory.lab is None:
        raise PreChangeExpectationBuildError(
            "Lab settings are required for deployment safety checks"
        )

    if current_state.hostname != device.hostname:
        raise PreChangeExpectationBuildError(
            "Current state target mismatch: "
            f"expected {device.hostname}, "
            f"got {current_state.hostname}"
        )

    management_ip = IPv4Address(device.host)

    oob_interface = next(
        (
            interface
            for interface in current_state.interfaces
            if interface.ipv4 == management_ip
        ),
        None,
    )

    if oob_interface is None:
        raise PreChangeExpectationBuildError(
            f"Unable to identify OOB management interface "
            f"for {device.hostname} using {management_ip}"
        )

    if (
        oob_interface.status != "up"
        or oob_interface.protocol != "up"
        or not oob_interface.admin_enabled
    ):
        raise PreChangeExpectationBuildError(
            f"OOB management interface {oob_interface.name} "
            "is not operational"
        )

    required_routes: list[RouteExpectation] = []

    oob_route = next(
        (
            route
            for route in current_state.routes
            if (
                route.network == inventory.lab.oob.network
                and route.outgoing_interface
                == oob_interface.name
            )
        ),
        None,
    )

    if oob_route is not None:
        required_routes.append(
            RouteExpectation(
                network=oob_route.network,
                protocol=oob_route.protocol,
                outgoing_interface=oob_route.outgoing_interface,
            )
        )

    return PreChangeExpectation(
        expected_hostname=device.hostname,
        required_interfaces=[
            InterfaceExpectation(
                name=oob_interface.name,
                ipv4=management_ip,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        required_routes=required_routes,
    )