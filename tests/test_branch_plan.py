from pathlib import Path
from unittest.mock import patch

from pydantic import SecretStr

from network_automation_platform.branch_plan import plan_branch
from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.device_state import DeviceState
from network_automation_platform.inventory import (
    DeviceInventory,
    InventoryDevice,
)
from network_automation_platform.validation import (
    ValidationCheck,
    ValidationReport,
    ValidationStatus,
)
from tests.factories import (
    TEST_ROUTER_IP,
    TEST_SWITCH_IP,
    make_inventory_device,
)


def test_plan_branch_aggregates_device_plans() -> None:
    inventory = DeviceInventory(
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

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test"),
        ssh_config_file=Path("/tmp/lab_config"),
        ssh_known_hosts_file=Path("/tmp/known_hosts"),
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

    router_candidate = "hostname br01-rtr01"
    switch_candidate = "hostname br01-sw01"

    with (
        patch(
            "network_automation_platform.branch_plan."
            "collect_device_state",
            side_effect=[
                router_state,
                switch_state,
            ],
        ) as collect_mock,
        patch(
            "network_automation_platform.branch_plan."
            "validate_device_against_desired_state",
            side_effect=[
                router_report,
                switch_report,
            ],
        ) as validate_mock,
        patch(
            "network_automation_platform.branch_plan."
            "render_device",
            side_effect=[
                router_candidate,
                switch_candidate,
            ],
        ) as render_mock,
    ):
        result = plan_branch(
            "branch-01",
            intent_path=Path(
                "intent/branches/branch-01.yaml"
            ),
            inventory=inventory,
            settings=settings,
        )

    assert result.branch_id == "branch-01"
    assert result.has_drift is False
    assert len(result.devices) == 2

    assert result.devices[0].hostname == "br01-rtr01"
    assert result.devices[0].validation is router_report
    assert (
        result.devices[0].candidate_config
        == router_candidate
    )

    assert result.devices[1].hostname == "br01-sw01"
    assert result.devices[1].validation is switch_report
    assert (
        result.devices[1].candidate_config
        == switch_candidate
    )

    assert collect_mock.call_count == 2
    assert validate_mock.call_count == 2
    assert render_mock.call_count == 2


def test_plan_branch_reports_drift() -> None:
    inventory = DeviceInventory(
        devices=[
            InventoryDevice(
                hostname="br01-rtr01",
                host=str(TEST_ROUTER_IP),
                driver="cisco_ios",
            ),
            InventoryDevice(
                hostname="br01-sw01",
                host=str(TEST_SWITCH_IP),
                driver="cisco_ios",
            ),
        ]
    )

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test"),
        ssh_config_file=Path("/tmp/lab_config"),
        ssh_known_hosts_file=Path("/tmp/known_hosts"),
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
                name="interface:Vlan99",
                status=ValidationStatus.FAIL,
                message="Interface Vlan99 is missing",
            )
        ],
    )

    with (
        patch(
            "network_automation_platform.branch_plan."
            "collect_device_state",
            side_effect=[
                router_state,
                switch_state,
            ],
        ),
        patch(
            "network_automation_platform.branch_plan."
            "validate_device_against_desired_state",
            side_effect=[
                router_report,
                switch_report,
            ],
        ),
        patch(
            "network_automation_platform.branch_plan."
            "render_device",
            side_effect=[
                "hostname br01-rtr01",
                "hostname br01-sw01",
            ],
        ),
    ):
        result = plan_branch(
            "branch-01",
            intent_path=Path(
                "intent/branches/branch-01.yaml"
            ),
            inventory=inventory,
            settings=settings,
        )

    assert result.has_drift is True
    assert result.devices[0].validation.passed is True
    assert result.devices[1].validation.passed is False