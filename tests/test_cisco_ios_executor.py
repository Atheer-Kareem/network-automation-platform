from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from network_automation_platform.connection_settings import (
    ConnectionSettings,
)
from network_automation_platform.deployment_executor import (
    DeploymentExecutionError,
)
from network_automation_platform.executors.cisco_ios import (
    CiscoIosDeploymentExecutor,
)
from network_automation_platform.inventory import InventoryDevice
from tests.factories import (
    TEST_ROUTER_IP,
)


def build_device() -> InventoryDevice:
    return InventoryDevice(
        hostname="br01-rtr01",
        host=str(TEST_ROUTER_IP),
        port=22,
        driver="cisco_ios",
    )


def build_settings() -> ConnectionSettings:
    return ConnectionSettings(
        username="netdevops",
        password=SecretStr("test-password"),
        ssh_config_file=Path("/tmp/lab_config"),
        ssh_known_hosts_file=Path("/tmp/known_hosts"),
    )


def test_apply_config_sends_configuration_commands() -> None:
    device = build_device()
    settings = build_settings()

    connection = MagicMock()
    connection.__enter__.return_value = connection

    response = MagicMock()
    response.failed = False

    connection.send_configs.return_value = response

    with patch(
        "network_automation_platform.executors.cisco_ios."
        "build_device_connection",
        return_value=connection,
    ):
        executor = CiscoIosDeploymentExecutor(
            device,
            settings,
        )

        executor.apply_config(
            "br01-rtr01",
            """
interface FastEthernet1/0
 description Deployment test
 no shutdown
!
""",
        )

    connection.send_configs.assert_called_once_with(
        [
            "interface FastEthernet1/0",
            "description Deployment test",
            "no shutdown",
        ]
    )


def test_apply_config_rejects_wrong_target() -> None:
    executor = CiscoIosDeploymentExecutor(
        build_device(),
        build_settings(),
    )

    with pytest.raises(
        DeploymentExecutionError,
        match=(
            "Deployment target mismatch: "
            "expected br01-rtr01, got br02-rtr01"
        ),
    ):
        executor.apply_config(
            "br02-rtr01",
            "hostname br02-rtr01",
        )


def test_apply_config_rejects_empty_config() -> None:
    executor = CiscoIosDeploymentExecutor(
        build_device(),
        build_settings(),
    )

    with pytest.raises(
        DeploymentExecutionError,
        match="Candidate configuration is empty",
    ):
        executor.apply_config(
            "br01-rtr01",
            "\n!\n",
        )


def test_apply_config_rejects_failed_configuration() -> None:
    device = build_device()
    settings = build_settings()

    connection = MagicMock()
    connection.__enter__.return_value = connection

    response = MagicMock()
    response.failed = True

    connection.send_configs.return_value = response

    with patch(
        "network_automation_platform.executors.cisco_ios."
        "build_device_connection",
        return_value=connection,
    ):
        executor = CiscoIosDeploymentExecutor(
            device,
            settings,
        )

        with pytest.raises(
            DeploymentExecutionError,
            match="One or more configuration commands failed",
        ):
            executor.apply_config(
                "br01-rtr01",
                "interface FastEthernet1/0",
            )


def test_apply_config_wraps_connection_failure() -> None:
    device = build_device()
    settings = build_settings()

    with patch(
        "network_automation_platform.executors.cisco_ios."
        "build_device_connection",
        side_effect=RuntimeError("connection failed"),
    ):
        executor = CiscoIosDeploymentExecutor(
            device,
            settings,
        )

        with pytest.raises(
            DeploymentExecutionError,
            match=(
                "Unable to apply configuration to "
                "br01-rtr01: connection failed"
            ),
        ):
            executor.apply_config(
                "br01-rtr01",
                "interface FastEthernet1/0",
            )