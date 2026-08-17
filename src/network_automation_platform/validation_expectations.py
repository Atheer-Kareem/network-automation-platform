from network_automation_platform.desired_state import DeviceDesiredState
from network_automation_platform.platform_profiles import (
    ROUTER_PLATFORM_PROFILES,
    SWITCH_PLATFORM_PROFILES,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    OspfNeighborExpectation,
    RouteExpectation,
    SwitchportExpectation,
    ValidationExpectation,
    VlanExpectation,
)


class ValidationExpectationError(ValueError):
    pass

def _build_router_expectation(
    device: DeviceDesiredState,
) -> ValidationExpectation:
    try:
        profile = ROUTER_PLATFORM_PROFILES[device.platform]
    except KeyError as exc:
        raise ValidationExpectationError(
            f"Unsupported router platform: {device.platform}"
        ) from exc

    interfaces: list[InterfaceExpectation] = []
    routes: list[RouteExpectation] = []
    ospf_neighbors: list[OspfNeighborExpectation] = []

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
                ipv4_prefixlen=(
                    interface.ipv4.network.prefixlen
                    if interface.ipv4 is not None
                    else None
                ),
                description=interface.description,
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

    if device.ospf is not None:
        try:
            wan_interface = profile.interface_map["wan"]
        except KeyError as exc:
            raise ValidationExpectationError(
                f"Missing interface mapping for wan on platform "
                f"{device.platform}"
            ) from exc

        ospf_neighbors.append(
            OspfNeighborExpectation(
                address=device.ospf.neighbor_address,
                interface=wan_interface,
                state="FULL",
            )
        )

        routes.extend(
            RouteExpectation(
                network=network,
                protocol="O",
                next_hop=device.ospf.neighbor_address,
                outgoing_interface=wan_interface,
            )
            for network in device.ospf.learned_routes
        )

    return ValidationExpectation(
        interfaces=interfaces,
        routes=routes,
        ospf_neighbors=ospf_neighbors,
    )

def _build_switch_expectation(
    device: DeviceDesiredState,
) -> ValidationExpectation:
    try:
        profile = SWITCH_PLATFORM_PROFILES[device.platform]
    except KeyError as exc:
        raise ValidationExpectationError(
            f"Unsupported switch platform: {device.platform}"
        ) from exc

    interfaces: list[InterfaceExpectation] = []
    vlans: list[VlanExpectation] = []
    switchports: list[SwitchportExpectation] = []

    for vlan in device.vlans:
        vlans.append(
            VlanExpectation(
                vlan_id=vlan.vlan_id,
                name=vlan.name,
                status="active",
            )
        )

    for interface in device.interfaces:
        if interface.name == "management_svi":
            if interface.vlan_id is None:
                raise ValidationExpectationError(
                    "Management SVI requires a VLAN ID"
                )

            interfaces.append(
                InterfaceExpectation(
                    name=f"Vlan{interface.vlan_id}",
                    ipv4=(
                        interface.ipv4.ip
                        if interface.ipv4 is not None
                        else None
                    ),
                    ipv4_prefixlen=(
                        interface.ipv4.network.prefixlen
                        if interface.ipv4 is not None
                        else None
                    ),
                    description=interface.description,
                    admin_enabled=interface.enabled,
                )
            )
            continue

        try:
            physical_name = profile.interface_map[interface.name]
        except KeyError as exc:
            raise ValidationExpectationError(
                f"Missing interface mapping for "
                f"{interface.name} on platform "
                f"{device.platform}"
            ) from exc

        interfaces.append(
            InterfaceExpectation(
                name=physical_name,
                description=interface.description,
                admin_enabled=interface.enabled,
            )
        )

        if interface.mode == "trunk":
            switchports.append(
                SwitchportExpectation(
                    interface=physical_name,
                    switchport_enabled=True,
                    administrative_mode="trunk",
                    allowed_vlans=interface.allowed_vlans,
                )
            )

        elif interface.mode == "access":
            switchports.append(
                SwitchportExpectation(
                    interface=physical_name,
                    switchport_enabled=True,
                    administrative_mode="access",
                    access_vlan=interface.access_vlan,
                )
            )

    return ValidationExpectation(
        interfaces=interfaces,
        vlans=vlans,
        switchports=switchports,
    )

def build_desired_state_expectation(
    device: DeviceDesiredState,
) -> ValidationExpectation:
    if device.role == "branch_router":
        return _build_router_expectation(device)

    if device.role == "branch_switch":
        return _build_switch_expectation(device)

    raise ValidationExpectationError(
        f"Unsupported device role for validation: {device.role}"
    )
