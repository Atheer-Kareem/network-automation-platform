from network_automation_platform.collectors.cisco_ios import (
    StateCollectionError,
    collect_device_state,
)
from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.device_state import DeviceState
from network_automation_platform.device_state_provider import (
    DeviceStateCollectionError,
)
from network_automation_platform.inventory import InventoryDevice


class CiscoIosDeviceStateProvider:
    def __init__(
        self,
        device: InventoryDevice,
        settings: ConnectionSettings,
    ) -> None:
        self._device = device
        self._settings = settings

    def collect_state(
        self,
        hostname: str,
    ) -> DeviceState:
        if hostname != self._device.hostname:
            raise DeviceStateCollectionError(
                "State collection target mismatch: "
                f"expected {self._device.hostname}, got {hostname}"
            )

        try:
            return collect_device_state(
                self._device,
                self._settings,
            )
        except StateCollectionError as exc:
            raise DeviceStateCollectionError(
                f"Unable to collect state from "
                f"{self._device.hostname}: {exc}"
            ) from exc