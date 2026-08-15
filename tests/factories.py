from ipaddress import IPv4Address, IPv4Network

from network_automation_platform.inventory import (
    DeviceInventory,
    InventoryDevice,
    LabSettings,
    LabSshSettings,
    OobNetwork,
    StateFeature,
)

TEST_OOB_NETWORK = IPv4Network("192.0.2.0/24")

TEST_CORE_IP = IPv4Address("192.0.2.10")
TEST_ROUTER_IP = IPv4Address("192.0.2.11")
TEST_SWITCH_IP = IPv4Address("192.0.2.12")


def make_inventory_device(
    *,
    hostname: str = "br01-rtr01",
    host: str = str(TEST_ROUTER_IP),
    state_features: set[StateFeature] | None = None,
) -> InventoryDevice:
    return InventoryDevice(
        hostname=hostname,
        host=host,
        port=22,
        driver="cisco_ios",
        state_features=state_features or set(),
    )


def make_lab_inventory(
    *,
    devices: list[InventoryDevice] | None = None,
) -> DeviceInventory:
    return DeviceInventory(
        lab=LabSettings(
            oob=OobNetwork(
                network=TEST_OOB_NETWORK,
            ),
            ssh=LabSshSettings(
                username="netdevops",
                kex_algorithms=[
                    "diffie-hellman-group14-sha1",
                ],
                host_key_algorithms=[
                    "ssh-rsa",
                ],
            ),
        ),
        devices=devices or [],
    )