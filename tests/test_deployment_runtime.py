from ipaddress import IPv4Address, IPv4Interface, IPv4Network
from pathlib import Path
from unittest.mock import MagicMock, patch

from pydantic import SecretStr

from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.deployment import (
    DeploymentResult,
    DeploymentStatus,
)
from network_automation_platform.deployment_runtime import (
    deploy_inventory_device,
)
from network_automation_platform.desired_state import (
    DeviceDesiredState,
    InterfaceDesiredState,
)
from network_automation_platform.device_state import (
    DeviceState,
    InterfaceState,
    RouteState,
)
from network_automation_platform.inventory import InventoryDevice
from network_automation_platform.pre_change_validation import (
    PreChangeExpectation,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    RouteExpectation,
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


def build_current_state() -> DeviceState:
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


def build_desired_state() -> DeviceDesiredState:
    return DeviceDesiredState(
        hostname="br01-rtr01",
        role="branch_router",
        platform="cisco_ios_c7200",
        interfaces=[
            InterfaceDesiredState(
                name="wan",
                ipv4=IPv4Interface("10.101.255.1/30"),
            )
        ],
    )


def build_pre_change_expectation() -> PreChangeExpectation:
    return PreChangeExpectation(
        expected_hostname="br01-rtr01",
        required_interfaces=[
            InterfaceExpectation(
                name="FastEthernet0/0",
                ipv4=IPv4Address("192.168.64.10"),
                status="up",
                protocol="up",
            )
        ],
        required_routes=[
            RouteExpectation(
                network=IPv4Network("192.168.64.0/24"),
                protocol="C",
                outgoing_interface="FastEthernet0/0",
            )
        ],
    )


def test_deploy_inventory_device_wires_concrete_adapters() -> None:
    device = build_device()
    settings = build_settings()
    current_state = build_current_state()
    desired_state = build_desired_state()
    pre_change_expectation = build_pre_change_expectation()

    expected_result = MagicMock(spec=DeploymentResult)
    expected_result.status = DeploymentStatus.SUCCEEDED

    executor = MagicMock()
    state_provider = MagicMock()

    with (
        patch(
            "network_automation_platform.deployment_runtime."
            "CiscoIosDeploymentExecutor",
            return_value=executor,
        ) as executor_class,
        patch(
            "network_automation_platform.deployment_runtime."
            "CiscoIosDeviceStateProvider",
            return_value=state_provider,
        ) as provider_class,
        patch(
            "network_automation_platform.deployment_runtime.deploy_device",
            return_value=expected_result,
        ) as deploy,
    ):
        result = deploy_inventory_device(
            device=device,
            settings=settings,
            candidate_config="interface FastEthernet1/0",
            desired_state=desired_state,
            current_state=current_state,
            pre_change_expectation=pre_change_expectation,
        )

    assert result is expected_result

    executor_class.assert_called_once_with(
        device,
        settings,
    )

    provider_class.assert_called_once_with(
        device,
        settings,
    )

    deploy.assert_called_once_with(
        hostname="br01-rtr01",
        candidate_config="interface FastEthernet1/0",
        desired_state=desired_state,
        current_state=current_state,
        pre_change_expectation=pre_change_expectation,
        executor=executor,
        state_provider=state_provider,
    )