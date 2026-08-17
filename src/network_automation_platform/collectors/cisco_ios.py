from typing import Any

from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.connections import build_device_connection
from network_automation_platform.device_state import (
    DeviceState,
    InterfaceState,
    OspfNeighborState,
    RouteState,
    SwitchportState,
    VlanState,
)
from network_automation_platform.inventory import InventoryDevice


class StateCollectionError(RuntimeError):
    pass


class StateParseError(ValueError):
    pass


def _redact_connection_secrets(
    message: str,
    settings: ConnectionSettings,
) -> str:
    password = settings.password.get_secret_value()
    if not password:
        return message

    return message.replace(password, "<redacted>")


def parse_ip_interface_brief(
    parsed_output: list[dict[str, Any]],
) -> list[InterfaceState]:
    if not parsed_output:
        raise StateParseError(
            "Unable to parse 'show ip interface brief' output"
        )

    interfaces: list[InterfaceState] = []

    for interface in parsed_output:
        ip_address = interface.get("ip_address")

        interfaces.append(
            InterfaceState(
                name=interface["interface"],
                ipv4=None if ip_address in ("", "unassigned") else ip_address,
                status=interface["status"],
                protocol=interface["proto"],
                admin_enabled=interface["status"] != "administratively down",
            )
        )

    return interfaces

def enrich_interface_state(
    interfaces: list[InterfaceState],
    parsed_output: list[dict[str, Any]],
) -> list[InterfaceState]:
    details_by_name = {
        str(detail["interface"]): detail
        for detail in parsed_output
    }

    enriched_interfaces: list[InterfaceState] = []

    for interface in interfaces:
        detail = details_by_name.get(interface.name)

        if detail is None:
            enriched_interfaces.append(interface)
            continue

        description = str(
            detail.get("description") or ""
        ).strip()

        prefix_length = detail.get("prefix_length")
        ipv4_prefixlen = (
            int(prefix_length)
            if prefix_length not in (None, "")
            else None
        )

        enriched_interfaces.append(
            interface.model_copy(
                update={
                    "description": description or None,
                    "ipv4_prefixlen": ipv4_prefixlen,
                }
            )
        )

    return enriched_interfaces

def collect_interface_state(
    device: InventoryDevice,
    settings: ConnectionSettings,
) -> list[InterfaceState]:
    connection = build_device_connection(device, settings)

    try:
        with connection:
            response = connection.send_command(
                "show ip interface brief"
            )

            if response.failed:
                raise StateCollectionError(
                    f"Command failed on {device.hostname}: "
                    "'show ip interface brief'"
                )

            parsed_output = response.textfsm_parse_output()

    except StateCollectionError:
        raise
    except Exception as exc:
        error_message = _redact_connection_secrets(
            str(exc),
            settings,
        )
        raise StateCollectionError(
            f"Unable to collect interface state from "
            f"{device.hostname}: {error_message}"
        ) from exc

    return parse_ip_interface_brief(parsed_output)

def parse_ip_route(
    parsed_output: list[dict[str, Any]],
) -> list[RouteState]:
    if not parsed_output:
        raise StateParseError(
            "Unable to parse 'show ip route' output"
        )

    routes: list[RouteState] = []

    for route in parsed_output:
        prefix = f"{route['network']}/{route['prefix_length']}"
        next_hop = route.get("nexthop_ip")
        next_hop_interface = route.get("nexthop_if")

        routes.append(
            RouteState(
                protocol=route["protocol"],
                network=prefix,
                next_hop=None if not next_hop else next_hop,
                outgoing_interface=(
                    normalize_ios_interface_name(next_hop_interface)
                    if next_hop_interface
                    else None
                ),
            )
        )

    return routes

def collect_route_state(
    device: InventoryDevice,
    settings: ConnectionSettings,
) -> list[RouteState]:
    connection = build_device_connection(device, settings)

    try:
        with connection:
            response = connection.send_command("show ip route")

            if response.failed:
                raise StateCollectionError(
                    f"Command failed on {device.hostname}: "
                    "'show ip route'"
                )

            parsed_output = response.textfsm_parse_output()

    except StateCollectionError:
        raise
    except Exception as exc:
        error_message = _redact_connection_secrets(
            str(exc),
            settings,
        )
        raise StateCollectionError(
            f"Unable to collect route state from "
            f"{device.hostname}: {error_message}"
        ) from exc

    return parse_ip_route(parsed_output)

def send_and_parse(
    connection,
    device: InventoryDevice,
    command: str,
) -> list[dict[str, object]]:
    response = connection.send_command(command)

    if response.failed:
        raise StateCollectionError(
            f"Command failed on {device.hostname}: "
            f"'{command}'"
        )

    return response.textfsm_parse_output()

def collect_device_state(
    device: InventoryDevice,
    settings: ConnectionSettings,
) -> DeviceState:
    connection = build_device_connection(device, settings)

    try:
        with connection:
            interfaces = parse_ip_interface_brief(
                send_and_parse(
                    connection,
                    device,
                    "show ip interface brief",
                )
            )

            interfaces = enrich_interface_state(
                interfaces,
                send_and_parse(
                    connection,
                    device,
                    "show interfaces",
                ),
            )

            routes = []
            ospf_neighbors = []
            vlans = []
            switchports = []

            if "routes" in device.state_features:
                routes = parse_ip_route(
                    send_and_parse(
                        connection,
                        device,
                        "show ip route",
                    )
                )

            if "ospf" in device.state_features:
                ospf_neighbors = parse_ip_ospf_neighbor(
                    send_and_parse(
                        connection,
                        device,
                        "show ip ospf neighbor",
                    )
                )

            if "vlans" in device.state_features:
                vlans = parse_vlan_brief(
                    send_and_parse(
                        connection,
                        device,
                        "show vlan brief",
                    )
                )

            if "switchports" in device.state_features:
                switchports = parse_interfaces_switchport(
                    send_and_parse(
                        connection,
                        device,
                        "show interfaces switchport",
                    )
                )

    except StateCollectionError:
        raise
    except Exception as exc:
        error_message = _redact_connection_secrets(
            str(exc),
            settings,
        )
        raise StateCollectionError(
            f"Unable to collect device state from "
            f"{device.hostname}: {error_message}"
        ) from exc

    return DeviceState(
        hostname=device.hostname,
        interfaces=interfaces,
        routes=routes,
        ospf_neighbors=ospf_neighbors,
        vlans=vlans,
        switchports=switchports,
    )

def parse_ip_ospf_neighbor(
    parsed_output: list[dict[str, str]],
) -> list[OspfNeighborState]:
    if not parsed_output:
        return []

    return [
        OspfNeighborState(
            neighbor_id=neighbor["neighbor_id"],
            address=neighbor["ip_address"],
            interface=normalize_ios_interface_name(
                neighbor["interface"]
            ),
            state=neighbor["state"].split("/", maxsplit=1)[0],
        )
        for neighbor in parsed_output
    ]

def normalize_ios_interface_name(name: str) -> str:
    prefixes = {
        "Gi": "GigabitEthernet",
        "Fa": "FastEthernet",
        "Eth": "Ethernet",
    }

    if name.startswith(tuple(prefixes.values())):
        return name

    for abbreviation, full_name in prefixes.items():
        if name.startswith(abbreviation):
            return f"{full_name}{name[len(abbreviation):]}"

    return name

def parse_vlan_brief(
    parsed_output: list[dict[str, object]],
) -> list[VlanState]:
    return [
        VlanState(
            vlan_id=int(vlan["vlan_id"]),
            name=str(vlan["vlan_name"]),
            status=str(vlan["status"]),
        )
        for vlan in parsed_output
    ]

def parse_interfaces_switchport(
    parsed_output: list[dict[str, object]],
) -> list[SwitchportState]:
    switchports: list[SwitchportState] = []

    for port in parsed_output:
        administrative_mode = str(port["admin_mode"])
        operational_mode = str(port["mode"])

        normalized_admin_mode = (
            "access"
            if administrative_mode == "static access"
            else administrative_mode
        )

        normalized_operational_mode = (
            "access"
            if operational_mode == "static access"
            else operational_mode
        )

        allowed_vlans: list[int] = []
        should_parse_trunk_vlans = (
            normalized_admin_mode == "trunk"
            or normalized_operational_mode == "trunk"
        )

        if should_parse_trunk_vlans:
            raw_vlans = port.get("trunking_vlans", [])
            if isinstance(raw_vlans, str):
                raw_vlans = [raw_vlans]

            for value in raw_vlans:
                if value == "ALL":
                    continue

                allowed_vlans.extend(
                    int(vlan.strip())
                    for vlan in str(value).split(",")
                    if vlan and vlan.strip()
                )

        access_vlan = port.get("access_vlan")
        native_vlan = port.get("native_vlan")

        switchports.append(
            SwitchportState(
                interface=normalize_ios_interface_name(
                    str(port["interface"])
                ),
                switchport_enabled=port["switchport"] == "Enabled",
                administrative_mode=normalized_admin_mode,
                operational_mode=normalized_operational_mode,
                access_vlan=(
                    int(access_vlan)
                    if access_vlan
                    else None
                ),
                native_vlan=(
                    int(native_vlan)
                    if native_vlan
                    else None
                ),
                allowed_vlans=allowed_vlans,
            )
        )

    return switchports
