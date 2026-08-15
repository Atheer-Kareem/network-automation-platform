from pathlib import Path
from unittest.mock import patch

from pydantic import SecretStr

from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.connections import build_device_connection
from tests.factories import (
    TEST_ROUTER_IP,
    make_inventory_device,
)


def test_build_cisco_ios_connection() -> None:
    device = make_inventory_device()

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test-password"),
        ssh_config_file=Path("/tmp/lab_config"),
        ssh_known_hosts_file=Path("/tmp/known_hosts"),
    )

    with patch(
        "network_automation_platform.connections.IOSXEDriver"
    ) as driver:
        build_device_connection(device, settings)

    driver.assert_called_once_with(
        host=str(TEST_ROUTER_IP),
        port=22,
        auth_username="netdevops",
        auth_password="test-password",
        auth_strict_key=True,
        ssh_config_file="/tmp/lab_config",
        ssh_known_hosts_file="/tmp/known_hosts",
        transport="system",
    )