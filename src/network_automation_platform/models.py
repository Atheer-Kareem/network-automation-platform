from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class Site(BaseModel):
    id: str
    name: str
    region: str


class Device(BaseModel):
    hostname: str
    platform: str
    management_ip: IPv4Address


class DeviceRoles(BaseModel):
    router: Device
    switch: Device


class Network(BaseModel):
    vlan_id: int = Field(ge=1, le=4094)
    prefix: IPv4Network


class Networks(BaseModel):
    users: Network
    voice: Network
    management: Network


class Wan(BaseModel):
    transit_prefix: IPv4Network


class Routing(BaseModel):
    protocol: Literal["ospf"]
    area: int = Field(ge=0)
    neighbor_address: IPv4Address


class BranchIntent(BaseModel):
    site: Site
    device_roles: DeviceRoles
    networks: Networks
    wan: Wan
    routing: Routing

    @model_validator(mode="after")
    def validate_management_addresses(self) -> "BranchIntent":
        management_network = self.networks.management.prefix

        for device in (
            self.device_roles.router,
            self.device_roles.switch,
        ):
            if device.management_ip not in management_network:
                raise ValueError(
                    f"{device.hostname} management IP "
                    f"{device.management_ip} is not within "
                    f"{management_network}"
                )

        wan_network = self.wan.transit_prefix
        neighbor_address = self.routing.neighbor_address
        router_wan_address = wan_network.network_address + 1

        if neighbor_address not in wan_network:
            raise ValueError(
                f"OSPF neighbor address {neighbor_address} is not within "
                f"WAN transit network {wan_network}"
            )

        if neighbor_address == router_wan_address:
            raise ValueError(
                f"OSPF neighbor address {neighbor_address} cannot be "
                "the branch router WAN address"
            )

        return self


def load_branch_intent(path: Path) -> BranchIntent:
    with path.open(encoding="utf-8") as file:
        raw_intent = yaml.safe_load(file)

    return BranchIntent.model_validate(raw_intent)
