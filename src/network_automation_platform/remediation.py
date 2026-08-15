from typing import Literal

from pydantic import BaseModel, Field


class InterfaceRemediation(BaseModel):
    kind: Literal["interface"]
    interface_name: str
    description: str | None = None
    ipv4: str | None = None
    enabled: bool | None = None


class RemediationAction(BaseModel):
    description: str
    remediation: InterfaceRemediation


class DeviceRemediationPlan(BaseModel):
    hostname: str
    actions: list[RemediationAction] = Field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.actions)


class BranchRemediationPlan(BaseModel):
    branch_id: str
    devices: list[DeviceRemediationPlan] = Field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(device.has_changes for device in self.devices)