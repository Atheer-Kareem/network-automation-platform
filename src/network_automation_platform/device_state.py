from ipaddress import IPv4Address, IPv4Network

from pydantic import BaseModel, Field


class InterfaceState(BaseModel):
    name: str
    ipv4: IPv4Address | None = None
    status: str
    protocol: str
    admin_enabled: bool


class RouteState(BaseModel):
    protocol: str
    network: IPv4Network
    next_hop: IPv4Address | None = None
    outgoing_interface: str | None = None


class OspfNeighborState(BaseModel):
    neighbor_id: IPv4Address
    address: IPv4Address
    interface: str
    state: str


class VlanState(BaseModel):
    vlan_id: int
    name: str
    status: str


class SwitchportState(BaseModel):
    interface: str
    switchport_enabled: bool
    administrative_mode: str
    operational_mode: str
    access_vlan: int | None = None
    native_vlan: int | None = None
    allowed_vlans: list[int] = Field(default_factory=list)


class DeviceState(BaseModel):
    hostname: str
    interfaces: list[InterfaceState]
    routes: list[RouteState]
    ospf_neighbors: list[OspfNeighborState] = Field(default_factory=list)
    vlans: list[VlanState] = Field(default_factory=list)
    switchports: list[SwitchportState] = Field(default_factory=list)