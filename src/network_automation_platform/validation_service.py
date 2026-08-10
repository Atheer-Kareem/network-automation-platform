from network_automation_platform.desired_state import DeviceDesiredState
from network_automation_platform.device_state import DeviceState
from network_automation_platform.validation import (
    ValidationReport,
    validate_device_state,
)
from network_automation_platform.validation_expectations import (
    build_desired_state_expectation,
)


class ValidationServiceError(ValueError):
    pass


def validate_device_against_desired_state(
    desired: DeviceDesiredState,
    actual: DeviceState,
) -> ValidationReport:
    if desired.hostname != actual.hostname:
        raise ValidationServiceError(
            f"Device identity mismatch: expected {desired.hostname}, "
            f"got {actual.hostname}"
        )

    expectation = build_desired_state_expectation(desired)

    return validate_device_state(
        actual,
        expectation,
    )
