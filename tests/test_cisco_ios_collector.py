from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from network_automation_platform.collectors.cisco_ios import (
    StateCollectionError,
    StateParseError,
    collect_device_state,
    collect_interface_state,
    parse_ip_interface_brief,
    parse_ip_route,
)
from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.inventory import InventoryDevice


def test_parse_ip_interface_brief() -> None:
    parsed_output = [
        {
            "interface": "FastEthernet0/0",
            "ip_address": "192.168.64.10",
            "status": "up",
            "proto": "up",
        },
        {
            "interface": "FastEthernet1/0",
            "ip_address": "unassigned",
            "status": "administratively down",
            "proto": "down",
        },
    ]

    interfaces = parse_ip_interface_brief(parsed_output)

    assert len(interfaces) == 2

    assert interfaces[0].name == "FastEthernet0/0"
    assert interfaces[0].ipv4 == IPv4Address("192.168.64.10")
    assert interfaces[0].status == "up"
    assert interfaces[0].protocol == "up"

    assert interfaces[1].name == "FastEthernet1/0"
    assert interfaces[1].ipv4 is None
    assert interfaces[1].status == "administratively down"
    assert interfaces[1].protocol == "down"

def test_parse_ip_interface_brief_rejects_empty_output() -> None:
    with pytest.raises(
        StateParseError,
        match="Unable to parse 'show ip interface brief' output",
    ):
        parse_ip_interface_brief([])

def test_parse_ip_route() -> None:
    parsed_output = [
        {
            "vrf": "",
            "protocol": "C",
            "type": "",
            "network": "192.168.64.0",
            "prefix_length": "24",
            "distance": "",
            "metric": "",
            "nexthop_ip": "",
            "nexthop_vrf": "",
            "nexthop_if": "FastEthernet0/0",
            "uptime": "",
            "flag": "",
        },
        {
            "vrf": "",
            "protocol": "L",
            "type": "",
            "network": "192.168.64.10",
            "prefix_length": "32",
            "distance": "",
            "metric": "",
            "nexthop_ip": "",
            "nexthop_vrf": "",
            "nexthop_if": "FastEthernet0/0",
            "uptime": "",
            "flag": "",
        },
    ]

    routes = parse_ip_route(parsed_output)

    assert len(routes) == 2

    assert routes[0].protocol == "C"
    assert routes[0].network == IPv4Network("192.168.64.0/24")
    assert routes[0].next_hop is None
    assert routes[0].outgoing_interface == "FastEthernet0/0"

    assert routes[1].protocol == "L"
    assert routes[1].network == IPv4Network("192.168.64.10/32")

def test_parse_ip_route_rejects_empty_output() -> None:
    with pytest.raises(
        StateParseError,
        match="Unable to parse 'show ip route' output",
    ):
        parse_ip_route([])

def test_collect_interface_state() -> None:
    device = InventoryDevice(
        hostname="br01-rtr01",
        host="192.168.64.10",
        port=22,
        driver="cisco_ios",
    )

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test-password"),
        ssh_config_file=Path("inventory/ssh/lab_config"),
        ssh_known_hosts_file=Path("inventory/ssh/known_hosts"),
    )

    response = MagicMock()
    response.failed = False
    response.textfsm_parse_output.return_value = [
        {
            "interface": "FastEthernet0/0",
            "ip_address": "192.168.64.10",
            "status": "up",
            "proto": "up",
        }
    ]

    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.send_command.return_value = response

    with patch(
        "network_automation_platform.collectors.cisco_ios.build_device_connection",
        return_value=connection,
    ) as driver:
        interfaces = collect_interface_state(device, settings)

    driver.assert_called_once_with(device, settings)

    connection.send_command.assert_called_once_with(
        "show ip interface brief"
    )

    assert len(interfaces) == 1
    assert interfaces[0].name == "FastEthernet0/0"

def test_collect_interface_state_rejects_failed_command() -> None:
    device = InventoryDevice(
        hostname="br01-rtr01",
        host="192.168.64.10",
        port=22,
        driver="cisco_ios",
    )

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test-password"),
        ssh_config_file=Path("inventory/ssh/lab_config"),
        ssh_known_hosts_file=Path("inventory/ssh/known_hosts"),
    )

    response = MagicMock()
    response.failed = True

    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.send_command.return_value = response

    with patch(
        "network_automation_platform.collectors.cisco_ios.build_device_connection",
        return_value=connection,
    ), pytest.raises(
        StateCollectionError,
        match="Command failed on br01-rtr01",
    ):
        collect_interface_state(device, settings)

def test_collect_device_state() -> None:
    device = InventoryDevice(
        hostname="br01-rtr01",
        host="192.168.64.10",
        port=22,
        driver="cisco_ios",
    )

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test-password"),
        ssh_config_file=Path("inventory/ssh/lab_config"),
        ssh_known_hosts_file=Path("inventory/ssh/known_hosts"),
    )

    interface_response = MagicMock()
    interface_response.failed = False
    interface_response.textfsm_parse_output.return_value = [
        {
            "interface": "FastEthernet0/0",
            "ip_address": "192.168.64.10",
            "status": "up",
            "proto": "up",
        }
    ]

    route_response = MagicMock()
    route_response.failed = False
    route_response.textfsm_parse_output.return_value = [
        {
            "vrf": "",
            "protocol": "C",
            "type": "",
            "network": "192.168.64.0",
            "prefix_length": "24",
            "distance": "",
            "metric": "",
            "nexthop_ip": "",
            "nexthop_vrf": "",
            "nexthop_if": "FastEthernet0/0",
            "uptime": "",
            "flag": "",
        }
    ]

    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.send_command.side_effect = [
        interface_response,
        route_response,
    ]

    with patch(
        "network_automation_platform.collectors.cisco_ios."
        "build_device_connection",
        return_value=connection,
    ):
        state = collect_device_state(device, settings)

    assert state.hostname == "br01-rtr01"
    assert len(state.interfaces) == 1
    assert state.interfaces[0].name == "FastEthernet0/0"

    assert len(state.routes) == 1
    assert state.routes[0].protocol == "C"

    assert connection.send_command.call_count == 2
