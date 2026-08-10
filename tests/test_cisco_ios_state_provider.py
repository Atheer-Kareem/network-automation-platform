from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import SecretStr

from network_automation_platform.collectors.cisco_ios import (
    StateCollectionError,
)
from network_automation_platform.connection_settings import (
    ConnectionSettings,
)
from network_automation_platform.device_state import (
    DeviceState,
    InterfaceState,
    RouteState,
)
from network_automation_platform.device_state_provider import (
    DeviceStateCollectionError,
)
from network_automation_platform.inventory import InventoryDevice
from network_automation_platform.state_providers.cisco_ios import (
    CiscoIosDeviceStateProvider,
)


def build_device() -> InventoryDevice:
    return InventoryDevice(
        hostname="br01-rtr01",
        host="192.168.64.10",
        port=22,
        driver="cisco_ios",
    )


def build_settings() -> ConnectionSettings:
    return ConnectionSettings(
        username="netdevops",
        password=SecretStr("test-password"),
        ssh_config_file=Path("inventory/ssh/lab_config"),
        ssh_known_hosts_file=Path("inventory/ssh/known_hosts"),
    )


def build_device_state() -> DeviceState:
    return DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="FastEthernet0/0",
                ipv4=IPv4Address("192.168.64.10"),
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[
            RouteState(
                protocol="C",
                network=IPv4Network("192.168.64.0/24"),
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )


def test_collect_state_returns_device_state() -> None:
    device = build_device()
    settings = build_settings()
    expected_state = build_device_state()

    with patch(
        "network_automation_platform.state_providers.cisco_ios."
        "collect_device_state",
        return_value=expected_state,
    ) as collector:
        provider = CiscoIosDeviceStateProvider(
            device,
            settings,
        )

        state = provider.collect_state(
            "br01-rtr01"
        )

    assert state == expected_state

    collector.assert_called_once_with(
        device,
        settings,
    )


def test_collect_state_rejects_wrong_target() -> None:
    provider = CiscoIosDeviceStateProvider(
        build_device(),
        build_settings(),
    )

    with pytest.raises(
        DeviceStateCollectionError,
        match=(
            "State collection target mismatch: "
            "expected br01-rtr01, got br02-rtr01"
        ),
    ):
        provider.collect_state(
            "br02-rtr01"
        )


def test_collect_state_wraps_collection_failure() -> None:
    device = build_device()
    settings = build_settings()

    with patch(
        "network_automation_platform.state_providers.cisco_ios."
        "collect_device_state",
        side_effect=StateCollectionError(
            "connection failed"
        ),
    ):
        provider = CiscoIosDeviceStateProvider(
            device,
            settings,
        )

        with pytest.raises(
            DeviceStateCollectionError,
            match=(
                "Unable to collect state from "
                "br01-rtr01: connection failed"
            ),
        ):
            provider.collect_state(
                "br01-rtr01"
            )