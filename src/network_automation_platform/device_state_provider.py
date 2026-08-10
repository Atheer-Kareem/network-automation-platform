from typing import Protocol

from network_automation_platform.device_state import DeviceState


class DeviceStateCollectionError(RuntimeError):
    pass


class DeviceStateProvider(Protocol):
    def collect_state(
        self,
        hostname: str,
    ) -> DeviceState:
        ...

