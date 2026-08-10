from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.connections import build_device_connection
from network_automation_platform.deployment_executor import (
    DeploymentExecutionError,
)
from network_automation_platform.inventory import InventoryDevice


class CiscoIosDeploymentExecutor:
    def __init__(
        self,
        device: InventoryDevice,
        settings: ConnectionSettings,
    ) -> None:
        self._device = device
        self._settings = settings

    def apply_config(
        self,
        hostname: str,
        config: str,
    ) -> None:
        if hostname != self._device.hostname:
            raise DeploymentExecutionError(
                "Deployment target mismatch: "
                f"expected {self._device.hostname}, got {hostname}"
            )

        commands = [
            line.strip()
            for line in config.splitlines()
            if line.strip() and line.strip() != "!"
        ]

        if not commands:
            raise DeploymentExecutionError(
                "Candidate configuration is empty"
            )

        try:
            connection = build_device_connection(
                self._device,
                self._settings,
            )

            with connection:
                response = connection.send_configs(commands)

                if response.failed:
                    raise DeploymentExecutionError(
                        "One or more configuration commands failed"
                    )

        except DeploymentExecutionError:
            raise
        except Exception as exc:
            raise DeploymentExecutionError(
                f"Unable to apply configuration to "
                f"{self._device.hostname}: {exc}"
            ) from exc