from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from pydantic import SecretStr

from network_automation_platform.collectors.cisco_ios import (
    StateCollectionError,
    StateParseError,
    collect_device_state,
    collect_interface_state,
    enrich_interface_state,
    parse_interfaces_switchport,
    parse_ip_interface_brief,
    parse_ip_ospf_neighbor,
    parse_ip_route,
    parse_vlan_brief,
)
from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.inventory import InventoryDevice
from tests.factories import (
    TEST_CORE_IP,
    TEST_OOB_NETWORK,
    TEST_ROUTER_IP,
)


def test_parse_ip_interface_brief() -> None:
    parsed_output = [
        {
            "interface": "FastEthernet0/0",
            "ip_address": str(TEST_CORE_IP),
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
    assert interfaces[0].ipv4 == TEST_CORE_IP
    assert interfaces[0].status == "up"
    assert interfaces[0].protocol == "up"

    assert interfaces[1].name == "FastEthernet1/0"
    assert interfaces[1].ipv4 is None
    assert interfaces[1].status == "administratively down"
    assert interfaces[1].protocol == "down"
    assert interfaces[0].admin_enabled is True
    assert interfaces[1].admin_enabled is False

def test_collect_device_state_enriches_interface_details() -> None:
    device = InventoryDevice(
        hostname="br01-rtr01",
        host=str(TEST_ROUTER_IP),
        port=22,
        driver="cisco_ios",
    )

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test-password"),
        ssh_config_file=Path("inventory/ssh/lab_config"),
        ssh_known_hosts_file=Path("inventory/ssh/known_hosts"),
    )

    brief_response = MagicMock()
    brief_response.failed = False
    brief_response.textfsm_parse_output.return_value = [
        {
            "interface": "GigabitEthernet0/1",
            "ip_address": "10.101.255.1",
            "status": "up",
            "proto": "up",
        },
        {
            "interface": "GigabitEthernet0/2",
            "ip_address": "unassigned",
            "status": "up",
            "proto": "up",
        },
    ]

    detail_response = MagicMock()
    detail_response.failed = False
    detail_response.textfsm_parse_output.return_value = [
        {
            "interface": "GigabitEthernet0/1",
            "description": "WAN transit",
            "ip_address": "10.101.255.1",
            "prefix_length": "30",
        },
        {
            "interface": "GigabitEthernet0/2",
            "description": "Branch LAN trunk",
            "ip_address": "",
            "prefix_length": "",
        },
    ]

    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.send_command.side_effect = [
        brief_response,
        detail_response,
    ]

    with patch(
        "network_automation_platform.collectors.cisco_ios."
        "build_device_connection",
        return_value=connection,
    ):
        state = collect_device_state(
            device,
            settings,
        )

    assert len(state.interfaces) == 2

    assert state.interfaces[0].name == "GigabitEthernet0/1"
    assert state.interfaces[0].ipv4 == IPv4Address(
        "10.101.255.1"
    )
    assert state.interfaces[0].ipv4_prefixlen == 30
    assert state.interfaces[0].description == "WAN transit"
    assert state.interfaces[0].status == "up"
    assert state.interfaces[0].protocol == "up"
    assert state.interfaces[0].admin_enabled is True

    assert state.interfaces[1].name == "GigabitEthernet0/2"
    assert state.interfaces[1].ipv4 is None
    assert state.interfaces[1].ipv4_prefixlen is None
    assert (
        state.interfaces[1].description
        == "Branch LAN trunk"
    )
    assert state.interfaces[1].status == "up"
    assert state.interfaces[1].protocol == "up"
    assert state.interfaces[1].admin_enabled is True

    assert connection.send_command.call_count == 2
    connection.send_command.assert_any_call(
        "show ip interface brief"
    )
    connection.send_command.assert_any_call(
        "show interfaces"
    )

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
            "network":  str(TEST_OOB_NETWORK.network_address),
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
            "network": str(TEST_CORE_IP),
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
    assert routes[0].network == TEST_OOB_NETWORK
    assert routes[0].next_hop is None
    assert routes[0].outgoing_interface == "FastEthernet0/0"

    assert routes[1].protocol == "L"
    assert routes[1].network == IPv4Network(f"{TEST_CORE_IP}/32")

def test_parse_ip_route_rejects_empty_output() -> None:
    with pytest.raises(
        StateParseError,
        match="Unable to parse 'show ip route' output",
    ):
        parse_ip_route([])

def test_collect_interface_state() -> None:
    device = InventoryDevice(
        hostname="br01-rtr01",
        host=str(TEST_CORE_IP),
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
            "ip_address": str(TEST_CORE_IP),
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
        host=str(TEST_CORE_IP),
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
        host=str(TEST_ROUTER_IP),
        port=22,
        driver="cisco_ios",
        state_features={"routes", "ospf"},
    )

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test-password"),
        ssh_config_file=Path("inventory/ssh/lab_config"),
        ssh_known_hosts_file=Path("inventory/ssh/known_hosts"),
    )

    interface_response = MagicMock()
    detail_response = MagicMock()
    detail_response.failed = False
    detail_response.textfsm_parse_output.return_value = [
        {
            "interface": "FastEthernet0/0",
            "description": "OOB management",
            "ip_address": str(TEST_CORE_IP),
            "prefix_length": str(TEST_OOB_NETWORK.prefixlen),
        }
    ]
    interface_response.failed = False
    interface_response.textfsm_parse_output.return_value = [
        {
            "interface": "FastEthernet0/0",
            "ip_address": str(TEST_CORE_IP),
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
            "network": str(TEST_OOB_NETWORK.network_address),
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

    ospf_response = MagicMock()
    ospf_response.failed = False
    ospf_response.textfsm_parse_output.return_value = [
        {
            "neighbor_id": "10.101.255.2",
            "priority": "1",
            "state": "FULL/DR",
            "dead_time": "00:00:35",
            "ip_address": "10.101.255.2",
            "interface": "FastEthernet1/0",
        }
    ]

    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.send_command.side_effect = [
        interface_response,
        detail_response,
        route_response,
        ospf_response,
    ]

    with patch(
        "network_automation_platform.collectors.cisco_ios."
        "build_device_connection",
        return_value=connection,
    ):
        state = collect_device_state(device, settings)

    assert state.hostname == "br01-rtr01"
    assert len(state.interfaces) == 1
    interface = state.interfaces[0]

    assert interface.name == "FastEthernet0/0"
    assert interface.ipv4 == TEST_CORE_IP
    assert interface.ipv4_prefixlen == TEST_OOB_NETWORK.prefixlen
    assert interface.description == "OOB management"
    assert interface.status == "up"
    assert interface.protocol == "up"
    assert interface.admin_enabled is True

    assert len(state.routes) == 1
    assert state.routes[0].protocol == "C"

    assert len(state.ospf_neighbors) == 1
    neighbor = state.ospf_neighbors[0]
    assert str(neighbor.neighbor_id) == "10.101.255.2"
    assert str(neighbor.address) == "10.101.255.2"
    assert neighbor.interface == "FastEthernet1/0"
    assert neighbor.state == "FULL"

    assert connection.send_command.call_count == 4
    assert connection.send_command.call_args_list == [
        call("show ip interface brief"),
        call("show interfaces"),
        call("show ip route"),
        call("show ip ospf neighbor"),
    ]

def test_parse_ip_ospf_neighbor() -> None:
    parsed_output = [
        {
            "neighbor_id": "10.101.255.2",
            "priority": "1",
            "state": "FULL/DR",
            "dead_time": "00:00:35",
            "ip_address": "10.101.255.2",
            "interface": "Gi1/0",
        }
    ]

    neighbors = parse_ip_ospf_neighbor(parsed_output)

    assert len(neighbors) == 1

    neighbor = neighbors[0]

    assert str(neighbor.neighbor_id) == "10.101.255.2"
    assert str(neighbor.address) == "10.101.255.2"
    assert neighbor.interface == "GigabitEthernet1/0"
    assert neighbor.state == "FULL"

def test_parse_ip_ospf_neighbor_returns_empty_list_for_no_neighbors() -> None:
    assert parse_ip_ospf_neighbor([]) == []

def test_parse_vlan_brief() -> None:
    parsed_output = [
        {"vlan_id": "10", "vlan_name": "DATA", "status": "active"},
        {"vlan_id": "20", "vlan_name": "VOICE", "status": "suspend"},
    ]

    vlans = parse_vlan_brief(parsed_output)

    assert len(vlans) == 2
    assert vlans[0].vlan_id == 10
    assert vlans[0].name == "DATA"
    assert vlans[0].status == "active"
    assert vlans[1].vlan_id == 20
    assert vlans[1].name == "VOICE"
    assert vlans[1].status == "suspend"

def test_enrich_interface_state_normalizes_blank_details() -> None:
    interfaces = parse_ip_interface_brief(
        [
            {
                "interface": "GigabitEthernet0/2",
                "ip_address": "unassigned",
                "status": "up",
                "proto": "up",
            }
        ]
    )

    enriched = enrich_interface_state(
        interfaces,
        [
            {
                "interface": "GigabitEthernet0/2",
                "description": "",
                "ip_address": "",
                "prefix_length": "",
            }
        ],
    )

    assert len(enriched) == 1

    interface = enriched[0]

    assert interface.name == "GigabitEthernet0/2"
    assert interface.ipv4 is None
    assert interface.ipv4_prefixlen is None
    assert interface.description is None
    assert interface.status == "up"
    assert interface.protocol == "up"
    assert interface.admin_enabled is True

def test_enrich_interface_state_ignores_unknown_detail_interface() -> None:
    interfaces = parse_ip_interface_brief(
        [
            {
                "interface": "GigabitEthernet0/1",
                "ip_address": "10.101.255.1",
                "status": "up",
                "proto": "up",
            }
        ]
    )

    enriched = enrich_interface_state(
        interfaces,
        [
            {
                "interface": "GigabitEthernet0/99",
                "description": "Unexpected interface",
                "ip_address": "192.0.2.99",
                "prefix_length": "24",
            }
        ],
    )

    assert len(enriched) == 1

    interface = enriched[0]

    assert interface.name == "GigabitEthernet0/1"
    assert str(interface.ipv4) == "10.101.255.1"
    assert interface.ipv4_prefixlen is None
    assert interface.description is None
    assert interface.status == "up"
    assert interface.protocol == "up"
    assert interface.admin_enabled is True

def test_parse_interfaces_switchport() -> None:
    parsed_output = [
        {
            "interface": "Gi1/0/1",
            "switchport": "Enabled",
            "admin_mode": "static access",
            "mode": "trunk",
            "access_vlan": "10",
            "native_vlan": "1",
            "trunking_vlans": ["10,20,30"],
        },
        {
            "interface": "Fa0/24",
            "switchport": "Enabled",
            "admin_mode": "trunk",
            "mode": "trunk",
            "access_vlan": "",
            "native_vlan": "99",
            "trunking_vlans": ["ALL"],
        },
    ]

    switchports = parse_interfaces_switchport(parsed_output)

    assert len(switchports) == 2

    assert switchports[0].interface == "GigabitEthernet1/0/1"
    assert switchports[0].switchport_enabled is True
    assert switchports[0].administrative_mode == "access"
    assert switchports[0].operational_mode == "trunk"
    assert switchports[0].access_vlan == 10
    assert switchports[0].native_vlan == 1
    assert switchports[0].allowed_vlans == [10, 20, 30]

    assert switchports[1].interface == "FastEthernet0/24"
    assert switchports[1].switchport_enabled is True
    assert switchports[1].administrative_mode == "trunk"
    assert switchports[1].operational_mode == "trunk"
    assert switchports[1].access_vlan is None
    assert switchports[1].native_vlan == 99
    assert switchports[1].allowed_vlans == []
