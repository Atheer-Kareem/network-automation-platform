from ipaddress import IPv4Network
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

StateFeature = Literal[
    "routes",
    "ospf",
    "vlans",
    "switchports",
]

class OobNetwork(BaseModel):
    network: IPv4Network

class LabSshSettings(BaseModel):
    username: str
    kex_algorithms: list[str] = Field(default_factory=list)
    host_key_algorithms: list[str] = Field(default_factory=list)

class LabSettings(BaseModel):
    oob: OobNetwork
    ssh: LabSshSettings

class InventoryDevice(BaseModel):
    hostname: str
    host: str
    port: int = Field(default=22, ge=1, le=65535)
    driver: Literal["cisco_ios"]
    state_features: set[StateFeature] = Field(default_factory=set)

class DeviceInventory(BaseModel):
    lab: LabSettings | None = None
    devices: list[InventoryDevice]

def load_device_inventory(path: Path) -> DeviceInventory:
    with path.open(encoding="utf-8") as file:
        raw_inventory = yaml.safe_load(file)

    return DeviceInventory.model_validate(raw_inventory)
