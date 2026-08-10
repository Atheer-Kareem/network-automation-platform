from pydantic import BaseModel, Field, model_validator

from network_automation_platform.device_state import DeviceState
from network_automation_platform.validation import (
    InterfaceExpectation,
    RouteExpectation,
    ValidationExpectation,
    ValidationReport,
    validate_device_state,
)


class PreChangeExpectation(BaseModel):
    expected_hostname: str
    required_interfaces: list[InterfaceExpectation] = Field(
        default_factory=list
    )
    required_routes: list[RouteExpectation] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def require_prerequisites(self) -> "PreChangeExpectation":
        if not self.required_interfaces and not self.required_routes:
            raise ValueError(
                "At least one pre-change prerequisite is required"
            )

        return self


class PreChangeValidationError(ValueError):
    pass


def validate_pre_change_state(
    actual: DeviceState,
    expectation: PreChangeExpectation,
) -> ValidationReport:
    if actual.hostname != expectation.expected_hostname:
        raise PreChangeValidationError(
            "Device identity mismatch: "
            f"expected {expectation.expected_hostname}, "
            f"got {actual.hostname}"
        )

    validation_expectation = ValidationExpectation(
        interfaces=expectation.required_interfaces,
        routes=expectation.required_routes,
    )

    return validate_device_state(
        actual,
        validation_expectation,
    )
