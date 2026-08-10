from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class InventoryDevice(BaseModel):
    hostname: str
    host: str
    port: int = Field(default=22, ge=1, le=65535)
    driver: Literal["cisco_ios"]


class DeviceInventory(BaseModel):
    devices: list[InventoryDevice]


def load_device_inventory(path: Path) -> DeviceInventory:
    with path.open(encoding="utf-8") as file:
        raw_inventory = yaml.safe_load(file)

    return DeviceInventory.model_validate(raw_inventory)
