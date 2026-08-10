from typing import Any

from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.connections import build_device_connection
from network_automation_platform.device_state import (
    DeviceState,
    InterfaceState,
    RouteState,
)
from network_automation_platform.inventory import InventoryDevice


class StateCollectionError(RuntimeError):
    pass


class StateParseError(ValueError):
    pass


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
            )
        )

    return interfaces

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
        raise StateCollectionError(
            f"Unable to collect interface state from "
            f"{device.hostname}: {exc}"
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

        routes.append(
            RouteState(
                protocol=route["protocol"],
                network=prefix,
                next_hop=None if not next_hop else next_hop,
                outgoing_interface=route.get("nexthop_if") or None,
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
        raise StateCollectionError(
            f"Unable to collect route state from "
            f"{device.hostname}: {exc}"
        ) from exc

    return parse_ip_route(parsed_output)

def collect_device_state(
    device: InventoryDevice,
    settings: ConnectionSettings,
) -> DeviceState:
    connection = build_device_connection(device, settings)

    try:
        with connection:
            interface_response = connection.send_command(
                "show ip interface brief"
            )

            if interface_response.failed:
                raise StateCollectionError(
                    f"Command failed on {device.hostname}: "
                    "'show ip interface brief'"
                )

            route_response = connection.send_command(
                "show ip route"
            )

            if route_response.failed:
                raise StateCollectionError(
                    f"Command failed on {device.hostname}: "
                    "'show ip route'"
                )

            interfaces = parse_ip_interface_brief(
                interface_response.textfsm_parse_output()
            )
            routes = parse_ip_route(
                route_response.textfsm_parse_output()
            )

    except StateCollectionError:
        raise
    except Exception as exc:
        raise StateCollectionError(
            f"Unable to collect device state from "
            f"{device.hostname}: {exc}"
        ) from exc

    return DeviceState(
        hostname=device.hostname,
        interfaces=interfaces,
        routes=routes,
    )
