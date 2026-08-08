from ipaddress import IPv4Interface, IPv4Network
from typing import Literal

from pydantic import BaseModel, Field


class InterfaceDesiredState(BaseModel):
    name: str
    description: str | None = None
    ipv4: IPv4Interface | None = None
    enabled: bool = True


class VlanDesiredState(BaseModel):
    vlan_id: int
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


class BranchDesiredState(BaseModel):
    branch_id: str
    devices: list[DeviceDesiredState]