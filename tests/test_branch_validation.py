from pathlib import Path
from unittest.mock import patch

from network_automation_platform.branch_validation import (
    validate_branch,
)
from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.device_state import DeviceState
from network_automation_platform.inventory import DeviceInventory, InventoryDevice
from network_automation_platform.validation import (
    ValidationCheck,
    ValidationReport,
    ValidationStatus,
)


def test_validate_branch_aggregates_device_results() -> None:
    inventory = DeviceInventory(
        devices=[
            InventoryDevice(
                hostname="br01-rtr01",
                host="192.168.100.11",
                driver="cisco_ios",
            ),
            InventoryDevice(
                hostname="br01-sw01",
                host="192.168.100.12",
                driver="cisco_ios",
            ),
        ]
    )

    settings = ConnectionSettings(
        username="netdevops",
        password="test",
        ssh_config_file=Path("inventory/ssh/lab_config"),
        ssh_known_hosts_file=Path("inventory/ssh/known_hosts"),
    )

    router_state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[],
        routes=[],
    )

    switch_state = DeviceState(
        hostname="br01-sw01",
        interfaces=[],
        routes=[],
    )

    router_report = ValidationReport(
        hostname="br01-rtr01",
        checks=[
            ValidationCheck(
                name="router-check",
                status=ValidationStatus.PASS,
                message="Router matches expectation",
            )
        ],
    )

    switch_report = ValidationReport(
        hostname="br01-sw01",
        checks=[
            ValidationCheck(
                name="switch-check",
                status=ValidationStatus.PASS,
                message="Switch matches expectation",
            )
        ],
    )

    with (
        patch(
            "network_automation_platform.branch_validation."
            "collect_device_state",
            side_effect=[router_state, switch_state],
        ) as collect_mock,
        patch(
            "network_automation_platform.branch_validation."
            "validate_device_against_desired_state",
            side_effect=[router_report, switch_report],
        ) as validate_mock,
    ):
        result = validate_branch(
            "branch-01",
            intent_path=Path("intent/branches/branch-01.yaml"),
            inventory=inventory,
            settings=settings,
        )

    assert result.branch_id == "branch-01"
    assert result.passed is True
    assert len(result.devices) == 2

    assert result.devices[0].hostname == "br01-rtr01"
    assert result.devices[0].report is router_report

    assert result.devices[1].hostname == "br01-sw01"
    assert result.devices[1].report is switch_report

    assert collect_mock.call_count == 2
    assert validate_mock.call_count == 2