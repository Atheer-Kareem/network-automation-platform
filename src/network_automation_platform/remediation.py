from typing import Literal

from pydantic import BaseModel, Field


class InterfaceRemediation(BaseModel):
    kind: Literal["interface"]
    interface_name: str
    description: str | None = None
    ipv4: str | None = None
    enabled: bool | None = None

class VlanRemediation(BaseModel):
    kind: Literal["vlan"]
    vlan_id: int = Field(ge=1, le=4094)
    name: str

class RemediationAction(BaseModel):
    description: str
    remediation: InterfaceRemediation | VlanRemediation = Field(
        discriminator="kind",
    )


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