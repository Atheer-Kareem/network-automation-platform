from ipaddress import ip_address
from pathlib import Path

from network_automation_platform.inventory import load_device_inventory


def test_load_lab_inventory() -> None:
    inventory = load_device_inventory(Path("inventory/lab.yaml"))

    assert len(inventory.devices) == 3

    hostnames = {device.hostname for device in inventory.devices}
    assert hostnames == {"core01", "br01-rtr01", "br01-sw01"}

    assert {device.driver for device in inventory.devices} == {"cisco_ios"}
    assert all(device.port == 22 for device in inventory.devices)

    assert all(
        ip_address(device.host) in inventory.lab.oob.network
        for device in inventory.devices
    )


def test_load_lab_inventory_oob_network() -> None:
    inventory = load_device_inventory(
        Path("inventory/lab.yaml")
    )

    assert inventory.lab is not None
    assert inventory.lab.oob.network.version == 4
    assert inventory.lab.oob.network.prefixlen == 24
    assert str(inventory.lab.oob.network).endswith("/24")


def test_load_lab_inventory_device_addresses() -> None:
    inventory = load_device_inventory(
        Path("inventory/lab.yaml")
    )

    hosts = {
        device.hostname: ip_address(device.host)
        for device in inventory.devices
    }

    assert set(hosts) == {"core01", "br01-rtr01", "br01-sw01"}
    assert all(host in inventory.lab.oob.network for host in hosts.values())


def test_load_lab_inventory_ssh_settings() -> None:
    inventory = load_device_inventory(
        Path("inventory/lab.yaml")
    )

    assert inventory.lab.ssh.username == "netdevops"
    assert inventory.lab.ssh.kex_algorithms == [
        "diffie-hellman-group14-sha1"
    ]
    assert inventory.lab.ssh.host_key_algorithms == [
        "ssh-rsa"
    ]