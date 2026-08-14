from pathlib import Path
from unittest.mock import patch

from pydantic import SecretStr

from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.connections import build_device_connection
from network_automation_platform.inventory import InventoryDevice


def test_build_cisco_ios_connection() -> None:
    device = InventoryDevice(
        hostname="br01-rtr01",
        host="192.168.100.10",
        port=22,
        driver="cisco_ios",
    )

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test-password"),
        ssh_config_file=Path("inventory/ssh/lab_config"),
        ssh_known_hosts_file=Path("inventory/ssh/known_hosts"),
    )

    with patch(
        "network_automation_platform.connections.IOSXEDriver"
    ) as driver:
        build_device_connection(device, settings)

    driver.assert_called_once_with(
        host="192.168.100.10",
        port=22,
        auth_username="netdevops",
        auth_password="test-password",
        auth_strict_key=True,
        ssh_config_file="inventory/ssh/lab_config",
        ssh_known_hosts_file="inventory/ssh/known_hosts",
        transport="system",
    )