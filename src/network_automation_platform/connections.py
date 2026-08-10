from scrapli.driver.core import IOSXEDriver

from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.inventory import InventoryDevice


class DeviceConnectionError(ValueError):
    pass


def build_device_connection(
    device: InventoryDevice,
    settings: ConnectionSettings,
) -> IOSXEDriver:
    if device.driver != "cisco_ios":
        raise DeviceConnectionError(
            f"Unsupported device driver: {device.driver}"
        )

    return IOSXEDriver(
        host=device.host,
        port=device.port,
        auth_username=settings.username,
        auth_password=settings.password.get_secret_value(),
        auth_strict_key=settings.strict_host_key_checking,
        ssh_config_file=str(settings.ssh_config_file),
        ssh_known_hosts_file=str(settings.ssh_known_hosts_file),
        transport="system",
    )
