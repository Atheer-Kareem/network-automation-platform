from ipaddress import IPv4Interface, IPv4Network
from typing import Literal

from pydantic import BaseModel, Field


class InterfaceDesiredState(BaseModel):
    name: str
    description: str | None = None
    ipv4: IPv4Interface | None = None
    enabled: bool = True
    parent: str | None = None
    vlan_id: int | None = Field(default=None, ge=1, le=4094)
    mode: Literal["access", "trunk"] | None = None
    access_vlan: int | None = Field(default=None, ge=1, le=4094)
    allowed_vlans: list[int] = Field(default_factory=list)


class VlanDesiredState(BaseModel):
    vlan_id: int = Field(ge=1, le=4094)
    name: str


class OspfDesiredState(BaseModel):
    process_id: int = 1
    area: int = 0
    networks: list[IPv4Network]


class DeviceDesiredState(BaseModel):
    hostname: str
    role: Literal["branch_router", "branch_switch"]
    platform: str
    interfaces: list[InterfaceDesiredState] = Field(default_factory=list)
    vlans: list[VlanDesiredState] = Field(default_factory=list)
    ospf: OspfDesiredState | None = None
    default_gateway: str | None = None


class BranchDesiredState(BaseModel):
    branch_id: str
    devices: list[DeviceDesiredState]