from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.deployment import DeploymentResult
from network_automation_platform.deployment_service import deploy_device
from network_automation_platform.desired_state import DeviceDesiredState
from network_automation_platform.device_state import DeviceState
from network_automation_platform.executors.cisco_ios import (
    CiscoIosDeploymentExecutor,
)
from network_automation_platform.inventory import InventoryDevice
from network_automation_platform.pre_change_validation import (
    PreChangeExpectation,
)
from network_automation_platform.state_providers.cisco_ios import (
    CiscoIosDeviceStateProvider,
)


def deploy_inventory_device(
    device: InventoryDevice,
    settings: ConnectionSettings,
    candidate_config: str,
    desired_state: DeviceDesiredState,
    current_state: DeviceState,
    pre_change_expectation: PreChangeExpectation,
) -> DeploymentResult:
    executor = CiscoIosDeploymentExecutor(
        device,
        settings,
    )

    state_provider = CiscoIosDeviceStateProvider(
        device,
        settings,
    )

    return deploy_device(
        hostname=device.hostname,
        candidate_config=candidate_config,
        desired_state=desired_state,
        current_state=current_state,
        pre_change_expectation=pre_change_expectation,
        executor=executor,
        state_provider=state_provider,
    )