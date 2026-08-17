from pathlib import Path
from unittest.mock import patch

from pydantic import SecretStr

from network_automation_platform.branch_plan import plan_branch
from network_automation_platform.connection_settings import ConnectionSettings
from network_automation_platform.device_state import DeviceState
from network_automation_platform.inventory import DeviceInventory
from network_automation_platform.remediation import (
    DeviceRemediationPlan,
    RemediationAction,
    VlanRemediation,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    ValidationCheck,
    ValidationExpectation,
    ValidationReport,
    ValidationStatus,
    VlanExpectation,
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

    router_expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
            )
        ]
    )

    switch_expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
            )
        ]
    )

    router_remediation = DeviceRemediationPlan(
        hostname="br01-rtr01",
    )

    switch_remediation = DeviceRemediationPlan(
        hostname="br01-sw01",
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
            "build_desired_state_expectation",
            side_effect=[
                router_expectation,
                switch_expectation,
            ],
        ) as expectation_mock,
        patch(
            "network_automation_platform.branch_plan."
            "build_device_remediation_plan",
            side_effect=[
                router_remediation,
                switch_remediation,
            ],
        ) as remediation_mock,
        patch(
            "network_automation_platform.branch_plan."
            "render_device_remediation",
            side_effect=[
                [],
                [],
            ],
        ) as remediation_render_mock,
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
    assert result.devices[0].remediation_commands == []

    assert result.devices[1].hostname == "br01-sw01"
    assert result.devices[1].validation is switch_report
    assert (
        result.devices[1].candidate_config
        == switch_candidate
    )
    assert result.devices[1].remediation_commands == []

    assert collect_mock.call_count == 2
    assert validate_mock.call_count == 2
    assert expectation_mock.call_count == 2
    assert remediation_mock.call_count == 2
    assert remediation_render_mock.call_count == 2
    assert render_mock.call_count == 2


def test_plan_branch_reports_drift_with_targeted_remediation() -> None:
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
                name="vlan:10",
                status=ValidationStatus.FAIL,
                message="VLAN 10 is missing",
                reason="missing",
            )
        ],
    )

    router_expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
            )
        ]
    )

    switch_expectation = ValidationExpectation(
        vlans=[
            VlanExpectation(
                vlan_id=10,
                name="USERS",
                status="active",
            )
        ]
    )

    router_remediation = DeviceRemediationPlan(
        hostname="br01-rtr01",
    )

    switch_remediation = DeviceRemediationPlan(
        hostname="br01-sw01",
        actions=[
            RemediationAction(
                description="Create/configure VLAN 10",
                remediation=VlanRemediation(
                    kind="vlan",
                    vlan_id=10,
                    name="USERS",
                ),
            )
        ],
    )

    router_candidate = "hostname br01-rtr01"
    switch_candidate = "hostname br01-sw01"

    switch_commands = [
        "vlan 10",
        "name USERS",
    ]

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
            "build_desired_state_expectation",
            side_effect=[
                router_expectation,
                switch_expectation,
            ],
        ),
        patch(
            "network_automation_platform.branch_plan."
            "build_device_remediation_plan",
            side_effect=[
                router_remediation,
                switch_remediation,
            ],
        ),
        patch(
            "network_automation_platform.branch_plan."
            "render_device_remediation",
            side_effect=[
                [],
                switch_commands,
            ],
        ),
        patch(
            "network_automation_platform.branch_plan."
            "render_device",
            side_effect=[
                router_candidate,
                switch_candidate,
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
    assert result.devices[0].remediation_commands == []
    assert (
        result.devices[0].candidate_config
        == router_candidate
    )

    assert result.devices[1].validation.passed is False
    assert (
        result.devices[1].candidate_config
        == switch_candidate
    )
    assert (
        result.devices[1].remediation_commands
        == switch_commands
    )