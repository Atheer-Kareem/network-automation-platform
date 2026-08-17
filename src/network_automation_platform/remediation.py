from typing import Literal

from pydantic import BaseModel, Field, model_validator


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

class SwitchportRemediation(BaseModel):
    kind: Literal["switchport"]
    interface_name: str
    mode: Literal["access", "trunk"] | None = None
    access_vlan: int | None = None
    allowed_vlans: list[int] | None = None

    @model_validator(mode="after")
    def require_exclusive_vlan_configuration(
        self,
    ) -> "SwitchportRemediation":
        if (
            self.access_vlan is not None
            and self.allowed_vlans is not None
        ):
            raise ValueError(
                "Switchport remediation cannot include both access "
                "and allowed VLAN configuration"
            )

        if self.allowed_vlans == []:
            raise ValueError(
                "Switchport remediation allowed VLANs cannot be empty"
            )

        if self.mode == "access" and self.access_vlan is None:
            raise ValueError(
                "Access-mode switchport remediation requires an "
                "access VLAN"
            )

        if self.mode == "trunk" and not self.allowed_vlans:
            raise ValueError(
                "Trunk-mode switchport remediation requires allowed "
                "VLANs"
            )

        if (
            self.mode is None
            and self.access_vlan is None
            and self.allowed_vlans is None
        ):
            raise ValueError(
                "Narrow switchport remediation requires access or "
                "allowed VLAN configuration"
            )

        return self

class RemediationAction(BaseModel):
    description: str
    remediation: (
        InterfaceRemediation
        | VlanRemediation
        | SwitchportRemediation
    ) = Field(
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
