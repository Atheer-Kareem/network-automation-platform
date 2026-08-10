from enum import StrEnum

from pydantic import BaseModel

from network_automation_platform.desired_state import DeviceDesiredState
from network_automation_platform.device_state import DeviceState
from network_automation_platform.pre_change_validation import (
    PreChangeExpectation,
    validate_pre_change_state,
)
from network_automation_platform.validation import ValidationReport
from network_automation_platform.validation_service import (
    validate_device_against_desired_state,
)


class ValidationPhase(StrEnum):
    PRE_CHANGE = "pre_change"
    POST_CHANGE = "post_change"


class ChangeValidationResult(BaseModel):
    phase: ValidationPhase
    report: ValidationReport

    @property
    def passed(self) -> bool:
        return self.report.passed


def run_post_change_validation(
    desired: DeviceDesiredState,
    actual: DeviceState,
) -> ChangeValidationResult:
    report = validate_device_against_desired_state(
        desired,
        actual,
    )

    return ChangeValidationResult(
        phase=ValidationPhase.POST_CHANGE,
        report=report,
    )

def run_pre_change_validation(
    expectation: PreChangeExpectation,
    actual: DeviceState,
) -> ChangeValidationResult:
    report = validate_pre_change_state(
        actual,
        expectation,
    )

    return ChangeValidationResult(
        phase=ValidationPhase.PRE_CHANGE,
        report=report,
    )
