from ipaddress import IPv4Address, IPv4Network

from pydantic import BaseModel


class InterfaceState(BaseModel):
    name: str
    ipv4: IPv4Address | None = None
    status: str
    protocol: str


class RouteState(BaseModel):
    protocol: str
    network: IPv4Network
    next_hop: IPv4Address | None = None
    outgoing_interface: str | None = None


class DeviceState(BaseModel):
    hostname: str
    interfaces: list[InterfaceState]
    routes: list[RouteState]
