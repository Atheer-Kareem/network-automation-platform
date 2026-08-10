from enum import StrEnum

from pydantic import BaseModel

from network_automation_platform.change_validation import (
    ChangeValidationResult,
)


class DeploymentStatus(StrEnum):
    BLOCKED = "blocked"
    FAILED = "failed"
    POST_CHECK_FAILED = "post_check_failed"
    POST_VALIDATION_FAILED = "post_validation_failed"
    SUCCEEDED = "succeeded"


class DeploymentResult(BaseModel):
    hostname: str
    status: DeploymentStatus
    pre_change: ChangeValidationResult
    deployment_attempted: bool
    deployment_succeeded: bool
    post_change: ChangeValidationResult | None = None
    message: str

    @property
    def succeeded(self) -> bool:
        return self.status == DeploymentStatus.SUCCEEDED