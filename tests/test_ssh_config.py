import pytest

from network_automation_platform.ssh_config import (
    SshConfigError,
    render_ssh_config,
)
from tests.factories import (
    TEST_ROUTER_IP,
    TEST_SWITCH_IP,
    make_inventory_device,
    make_lab_inventory,
)


def test_render_ssh_config() -> None:
    inventory = make_lab_inventory(
        devices=[
            make_inventory_device(
                hostname="br01-rtr01",
                host=str(TEST_ROUTER_IP),
            ),
            make_inventory_device(
                hostname="br01-sw01",
                host=str(TEST_SWITCH_IP),
            ),
        ]
    )

    config = render_ssh_config(inventory)

    assert f"Host br01-rtr01 {TEST_ROUTER_IP}" in config
    assert f"HostName {TEST_ROUTER_IP}" in config
    assert f"Host br01-sw01 {TEST_SWITCH_IP}" in config
    assert f"HostName {TEST_SWITCH_IP}" in config
    assert "User netdevops" in config
    assert "KexAlgorithms +diffie-hellman-group14-sha1" in config
    assert "HostKeyAlgorithms +ssh-rsa" in config
    assert config.startswith(
    "# Generated from inventory/lab.yaml. Do not edit manually."
)


def test_render_ssh_config_requires_lab_settings() -> None:
    inventory = make_lab_inventory(devices=[])
    inventory.lab = None

    with pytest.raises(
        SshConfigError,
        match="Lab settings are required",
    ):
        render_ssh_config(inventory)

