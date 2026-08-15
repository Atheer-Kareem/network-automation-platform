from pathlib import Path
from unittest.mock import patch

from pydantic import SecretStr

from network_automation_platform.branch_remediation import (
    build_branch_remediation,
)
from network_automation_platform.connection_settings import (
    ConnectionSettings,
)
from network_automation_platform.device_state import DeviceState
from network_automation_platform.inventory import DeviceInventory
from network_automation_platform.remediation import (
    DeviceRemediationPlan,
    InterfaceRemediation,
    RemediationAction,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    ValidationCheck,
    ValidationExpectation,
    ValidationReport,
    ValidationStatus,
)
from tests.factories import (
    TEST_ROUTER_IP,
    TEST_SWITCH_IP,
    make_inventory_device,
)


def test_build_branch_remediation_aggregates_device_results() -> None:
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

    router_plan = DeviceRemediationPlan(
        hostname="br01-rtr01",
    )

    switch_plan = DeviceRemediationPlan(
        hostname="br01-sw01",
    )

    with (
        patch(
            "network_automation_platform.branch_remediation."
            "collect_device_state",
            side_effect=[
                router_state,
                switch_state,
            ],
        ) as collect_mock,
        patch(
            "network_automation_platform.branch_remediation."
            "validate_device_against_desired_state",
            side_effect=[
                router_report,
                switch_report,
            ],
        ) as validate_mock,
        patch(
            "network_automation_platform.branch_remediation."
            "build_desired_state_expectation",
            side_effect=[
                router_expectation,
                switch_expectation,
            ],
        ) as expectation_mock,
        patch(
            "network_automation_platform.branch_remediation."
            "build_device_remediation_plan",
            side_effect=[
                router_plan,
                switch_plan,
            ],
        ) as plan_mock,
        patch(
            "network_automation_platform.branch_remediation."
            "render_device_remediation",
            side_effect=[
                [],
                [],
            ],
        ) as render_mock,
    ):
        result = build_branch_remediation(
            "branch-01",
            intent_path=Path(
                "intent/branches/branch-01.yaml"
            ),
            inventory=inventory,
            settings=settings,
        )

    assert result.branch_id == "branch-01"
    assert result.has_changes is False
    assert len(result.devices) == 2

    assert result.devices[0].hostname == "br01-rtr01"
    assert result.devices[0].plan is router_plan
    assert result.devices[0].commands == []

    assert result.devices[1].hostname == "br01-sw01"
    assert result.devices[1].plan is switch_plan
    assert result.devices[1].commands == []

    assert collect_mock.call_count == 2
    assert validate_mock.call_count == 2
    assert expectation_mock.call_count == 2
    assert plan_mock.call_count == 2
    assert render_mock.call_count == 2

def test_build_branch_remediation_detects_targeted_change() -> None:
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
                name="interface:Vlan99",
                status=ValidationStatus.FAIL,
                message="Interface Vlan99 is missing",
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
        interfaces=[
            InterfaceExpectation(
                name="Vlan99",
            )
        ]
    )

    router_plan = DeviceRemediationPlan(
        hostname="br01-rtr01",
    )

    switch_plan = DeviceRemediationPlan(
        hostname="br01-sw01",
        actions=[
            RemediationAction(
                description="Create/configure interface Vlan99",
                remediation=InterfaceRemediation(
                    kind="interface",
                    interface_name="Vlan99",
                    description="Switch management SVI",
                    ipv4="10.101.99.21/24",
                    enabled=True,
                ),
            )
        ],
    )

    switch_commands = [
        "interface Vlan99",
        "description Switch management SVI",
        "ip address 10.101.99.21 255.255.255.0",
        "no shutdown",
    ]

    with (
        patch(
            "network_automation_platform.branch_remediation."
            "collect_device_state",
            side_effect=[
                router_state,
                switch_state,
            ],
        ),
        patch(
            "network_automation_platform.branch_remediation."
            "validate_device_against_desired_state",
            side_effect=[
                router_report,
                switch_report,
            ],
        ),
        patch(
            "network_automation_platform.branch_remediation."
            "build_desired_state_expectation",
            side_effect=[
                router_expectation,
                switch_expectation,
            ],
        ),
        patch(
            "network_automation_platform.branch_remediation."
            "build_device_remediation_plan",
            side_effect=[
                router_plan,
                switch_plan,
            ],
        ),
        patch(
            "network_automation_platform.branch_remediation."
            "render_device_remediation",
            side_effect=[
                [],
                switch_commands,
            ],
        ),
    ):
        result = build_branch_remediation(
            "branch-01",
            intent_path=Path(
                "intent/branches/branch-01.yaml"
            ),
            inventory=inventory,
            settings=settings,
        )

    assert result.has_changes is True
    assert result.devices[0].commands == []
    assert result.devices[1].commands == switch_commands