from network_automation_platform.desired_state import DeviceDesiredState
from network_automation_platform.platform_profiles import (
    ROUTER_PLATFORM_PROFILES,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    RouteExpectation,
    ValidationExpectation,
)


class ValidationExpectationError(ValueError):
    pass


def build_desired_state_expectation(
    device: DeviceDesiredState,
) -> ValidationExpectation:
    if device.role != "branch_router":
        raise ValidationExpectationError(
            f"Unsupported device role for validation: {device.role}"
        )

    try:
        profile = ROUTER_PLATFORM_PROFILES[device.platform]
    except KeyError as exc:
        raise ValidationExpectationError(
            f"Unsupported router platform: {device.platform}"
        ) from exc

    interfaces: list[InterfaceExpectation] = []
    routes: list[RouteExpectation] = []

    for interface in device.interfaces:
        if interface.parent is None:
            try:
                physical_name = profile.interface_map[interface.name]
            except KeyError as exc:
                raise ValidationExpectationError(
                    f"Missing interface mapping for {interface.name} "
                    f"on platform {device.platform}"
                ) from exc
        else:
            try:
                parent_name = profile.interface_map[interface.parent]
            except KeyError as exc:
                raise ValidationExpectationError(
                    f"Missing interface mapping for parent "
                    f"{interface.parent} on platform {device.platform}"
                ) from exc

            physical_name = f"{parent_name}.{interface.vlan_id}"

        interfaces.append(
            InterfaceExpectation(
                name=physical_name,
                ipv4=(
                    interface.ipv4.ip
                    if interface.ipv4 is not None
                    else None
                ),
                admin_enabled=interface.enabled,
            )
        )

        if interface.ipv4 is not None:
            routes.append(
                RouteExpectation(
                    network=interface.ipv4.network,
                    protocol="C",
                    outgoing_interface=physical_name,
                )
            )

    return ValidationExpectation(
        interfaces=interfaces,
        routes=routes,
    )
