from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest
from pydantic import SecretStr

from network_automation_platform.branch_deployment import (
    BranchDeviceDeploymentStatus,
    DeploymentApprovalStatus,
    deploy_branch,
)
from network_automation_platform.change_validation import (
    ChangeValidationResult,
    ValidationPhase,
)
from network_automation_platform.collectors.cisco_ios import (
    StateCollectionError,
)
from network_automation_platform.connection_settings import (
    ConnectionSettings,
)
from network_automation_platform.deployment import (
    DeploymentResult,
    DeploymentStatus,
)
from network_automation_platform.device_state import (
    DeviceState,
    InterfaceState,
)
from network_automation_platform.inventory import DeviceInventory
from network_automation_platform.pre_change_expectation_builder import (
    PreChangeExpectationBuildError,
)
from network_automation_platform.pre_change_validation import (
    PreChangeExpectation,
)
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
    make_lab_inventory,
)


def test_deploy_branch_skips_compliant_devices() -> None:
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

    states = [
        DeviceState(
            hostname="br01-rtr01",
            interfaces=[],
            routes=[],
        ),
        DeviceState(
            hostname="br01-sw01",
            interfaces=[],
            routes=[],
        ),
    ]

    reports = [
        ValidationReport(
            hostname="br01-rtr01",
            checks=[
                ValidationCheck(
                    name="router-check",
                    status=ValidationStatus.PASS,
                    message="Router matches expectation",
                )
            ],
        ),
        ValidationReport(
            hostname="br01-sw01",
            checks=[
                ValidationCheck(
                    name="switch-check",
                    status=ValidationStatus.PASS,
                    message="Switch matches expectation",
                )
            ],
        ),
    ]

    with (
        patch(
            "network_automation_platform.branch_deployment."
            "collect_device_state",
            side_effect=states,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "validate_device_against_desired_state",
            side_effect=reports,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "deploy_inventory_device",
        ) as deploy_mock,
    ):
        result = deploy_branch(
            "branch-01",
            intent_path=Path(
                "intent/branches/branch-01.yaml"
            ),
            inventory=inventory,
            settings=settings,
            approve=lambda *_: True,
        )

    assert len(result.devices) == 2
    assert result.blocked is False

    assert (
        result.devices[0].status
        == BranchDeviceDeploymentStatus.SKIPPED
    )
    assert (
        result.devices[1].status
        == BranchDeviceDeploymentStatus.SKIPPED
    )
    assert result.devices[0].initial_validation is reports[0]
    assert result.devices[1].initial_validation is reports[1]
    assert all(
        device.approval_status
        == DeploymentApprovalStatus.NOT_REQUIRED
        for device in result.devices
    )

    deploy_mock.assert_not_called()


def test_deploy_branch_initial_collection_failure_prevents_approval_and_write(
) -> None:
    approve_mock = Mock()

    with (
        patch(
            "network_automation_platform.branch_deployment."
            "_build_branch_preflight",
            side_effect=StateCollectionError(
                "Unable to collect device state from br01-rtr01: "
                "connection refused"
            ),
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "deploy_inventory_device",
        ) as deploy_mock,
        pytest.raises(StateCollectionError),
    ):
        deploy_branch(
            "branch-01",
            intent_path=Path("intent/branches/branch-01.yaml"),
            inventory=make_lab_inventory(),
            settings=ConnectionSettings(
                username="netdevops",
                password=SecretStr("test"),
                ssh_config_file=Path("/tmp/lab_config"),
                ssh_known_hosts_file=Path("/tmp/known_hosts"),
            ),
            approve=approve_mock,
        )

    approve_mock.assert_not_called()
    deploy_mock.assert_not_called()

def test_deploy_branch_blocks_unsupported_drift() -> None:
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

    states = [
        DeviceState(
            hostname="br01-rtr01",
            interfaces=[],
            routes=[],
        ),
        DeviceState(
            hostname="br01-sw01",
            interfaces=[],
            routes=[],
        ),
    ]

    reports = [
        ValidationReport(
            hostname="br01-rtr01",
            checks=[
                ValidationCheck(
                    name="router-check",
                    status=ValidationStatus.PASS,
                    message="Router matches expectation",
                )
            ],
        ),
        ValidationReport(
            hostname="br01-sw01",
            checks=[
                ValidationCheck(
                    name="vlan:99",
                    status=ValidationStatus.FAIL,
                    message="VLAN 99 is missing",
                )
            ],
        ),
    ]

    with (
        patch(
            "network_automation_platform.branch_deployment."
            "collect_device_state",
            side_effect=states,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "validate_device_against_desired_state",
            side_effect=reports,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "deploy_inventory_device",
        ) as deploy_mock,
    ):
        result = deploy_branch(
            "branch-01",
            intent_path=Path(
                "intent/branches/branch-01.yaml"
            ),
            inventory=inventory,
            settings=settings,
            approve=lambda *_: True,
        )

    assert result.blocked is True

    assert (
        result.devices[0].status
        == BranchDeviceDeploymentStatus.SKIPPED
    )

    assert (
        result.devices[1].status
        == BranchDeviceDeploymentStatus.BLOCKED
    )

    assert "unsupported drift" in result.devices[1].message
    assert "vlan:99" in result.devices[1].message
    assert (
        result.devices[0].approval_status
        == DeploymentApprovalStatus.NOT_REQUIRED
    )
    assert (
        result.devices[1].approval_status
        == DeploymentApprovalStatus.NOT_REQUESTED
    )
    assert result.devices[0].initial_validation is reports[0]
    assert result.devices[1].initial_validation is reports[1]

    deploy_mock.assert_not_called()


def test_deploy_branch_blocks_ospf_operational_drift() -> None:
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
    states = [
        DeviceState(hostname="br01-rtr01", interfaces=[], routes=[]),
        DeviceState(hostname="br01-sw01", interfaces=[], routes=[]),
    ]
    reports = [
        ValidationReport(
            hostname="br01-rtr01",
            checks=[
                ValidationCheck(
                    name="ospf_neighbor:10.101.255.2",
                    status=ValidationStatus.FAIL,
                    message="OSPF neighbor 10.101.255.2 is missing",
                    reason="missing",
                )
            ],
        ),
        ValidationReport(
            hostname="br01-sw01",
            checks=[
                ValidationCheck(
                    name="switch-check",
                    status=ValidationStatus.PASS,
                    message="Switch matches expectation",
                )
            ],
        ),
    ]

    with (
        patch(
            "network_automation_platform.branch_deployment."
            "collect_device_state",
            side_effect=states,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "validate_device_against_desired_state",
            side_effect=reports,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "deploy_inventory_device",
        ) as deploy_mock,
    ):
        result = deploy_branch(
            "branch-01",
            intent_path=Path("intent/branches/branch-01.yaml"),
            inventory=inventory,
            settings=settings,
            approve=lambda *_: True,
        )

    assert result.blocked is True
    assert (
        result.devices[0].status
        == BranchDeviceDeploymentStatus.BLOCKED
    )
    assert "unsupported drift" in result.devices[0].message
    assert "ospf_neighbor:10.101.255.2" in result.devices[0].message
    assert (
        result.devices[1].status
        == BranchDeviceDeploymentStatus.SKIPPED
    )
    deploy_mock.assert_not_called()


def test_deploy_branch_blocks_learned_route_drift_before_approval() -> None:
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
    states = [
        DeviceState(hostname="br01-rtr01", interfaces=[], routes=[]),
        DeviceState(hostname="br01-sw01", interfaces=[], routes=[]),
    ]
    reports = [
        ValidationReport(
            hostname="br01-rtr01",
            checks=[
                ValidationCheck(
                    name="route:10.200.0.1/32",
                    status=ValidationStatus.FAIL,
                    message="Route 10.200.0.1/32 is missing",
                    reason="missing",
                )
            ],
        ),
        ValidationReport(
            hostname="br01-sw01",
            checks=[
                ValidationCheck(
                    name="switch-check",
                    status=ValidationStatus.PASS,
                    message="Switch matches expectation",
                )
            ],
        ),
    ]
    approve_mock = Mock(return_value=True)

    with (
        patch(
            "network_automation_platform.branch_deployment."
            "collect_device_state",
            side_effect=states,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "validate_device_against_desired_state",
            side_effect=reports,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "deploy_inventory_device",
        ) as deploy_mock,
    ):
        result = deploy_branch(
            "branch-01",
            intent_path=Path("intent/branches/branch-01.yaml"),
            inventory=inventory,
            settings=settings,
            approve=approve_mock,
        )

    assert result.blocked is True
    assert result.devices[0].status == BranchDeviceDeploymentStatus.BLOCKED
    assert "unsupported drift" in result.devices[0].message
    assert "route:10.200.0.1/32" in result.devices[0].message
    approve_mock.assert_not_called()
    deploy_mock.assert_not_called()

def test_deploy_branch_applies_only_targeted_remediation() -> None:
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
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=TEST_ROUTER_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
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

    switch_expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="Vlan99",
            )
        ]
    )

    switch_remediation = DeviceRemediationPlan(
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

    remediation_commands = [
        "interface Vlan99",
        "description Switch management SVI",
        "ip address 10.101.99.21 255.255.255.0",
        "no shutdown",
    ]

    pre_change_result = ChangeValidationResult(
        phase=ValidationPhase.PRE_CHANGE,
        report=ValidationReport(
            hostname="br01-sw01",
            checks=[
                ValidationCheck(
                    name="pre-change-check",
                    status=ValidationStatus.PASS,
                    message="Pre-change validation passed",
                )
            ],
        ),
    )

    post_change_result = ChangeValidationResult(
        phase=ValidationPhase.POST_CHANGE,
        report=ValidationReport(
            hostname="br01-sw01",
            checks=[
                ValidationCheck(
                    name="post-change-check",
                    status=ValidationStatus.PASS,
                    message="Post-change validation passed",
                )
            ],
        ),
    )

    deployment_result = DeploymentResult(
        hostname="br01-sw01",
        status=DeploymentStatus.SUCCEEDED,
        pre_change=pre_change_result,
        deployment_attempted=True,
        deployment_succeeded=True,
        post_change=post_change_result,
        message="Deployment completed and validated successfully",
    )
    pre_change_expectation = PreChangeExpectation(
    expected_hostname="br01-sw01",
        required_interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/0",
                ipv4=TEST_SWITCH_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
    )
    with (
        patch(
            "network_automation_platform.branch_deployment."
            "collect_device_state",
            side_effect=[
                router_state,
                switch_state,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "validate_device_against_desired_state",
            side_effect=[
                router_report,
                switch_report,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_desired_state_expectation",
            return_value=switch_expectation,
        ) as expectation_mock,
        patch(
            "network_automation_platform.branch_deployment."
            "build_device_remediation_plan",
            return_value=switch_remediation,
        ) as remediation_mock,
        patch(
            "network_automation_platform.branch_deployment."
            "render_device_remediation",
            return_value=remediation_commands,
        ) as render_mock,
        patch(
            "network_automation_platform.branch_deployment."
            "build_pre_change_expectation",
            return_value=pre_change_expectation,
        ) as pre_change_mock,
        patch(
            "network_automation_platform.branch_deployment."
            "deploy_inventory_device",
            return_value=deployment_result,
        ) as deploy_mock,
    ):
        result = deploy_branch(
            "branch-01",
            intent_path=Path(
                "intent/branches/branch-01.yaml"
            ),
            inventory=inventory,
            settings=settings,
            approve=lambda *_: True,
        )

    assert result.blocked is False

    assert (
        result.devices[0].status
        == BranchDeviceDeploymentStatus.SKIPPED
    )

    assert (
        result.devices[1].status
        == BranchDeviceDeploymentStatus.DEPLOYED
    )

    assert (
        result.devices[1].remediation_commands
        == remediation_commands
    )
    assert result.devices[1].initial_validation is switch_report
    assert (
        result.devices[1].approval_status
        == DeploymentApprovalStatus.APPROVED
    )

    expectation_mock.assert_called_once()
    remediation_mock.assert_called_once()
    render_mock.assert_called_once()
    pre_change_mock.assert_called_once()

    deploy_mock.assert_called_once()

    call_kwargs = deploy_mock.call_args.kwargs

    assert call_kwargs["candidate_config"] == "\n".join(
        remediation_commands
    )

    assert (
        call_kwargs["candidate_config"]
        != "hostname br01-sw01"
    )
    assert call_kwargs["candidate_config"] == "\n".join(
        remediation_commands
    )

def test_deploy_branch_does_not_write_when_operator_declines() -> None:
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
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=TEST_ROUTER_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
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

    switch_expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="Vlan99",
            )
        ]
    )

    switch_remediation = DeviceRemediationPlan(
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

    remediation_commands = [
        "interface Vlan99",
        "description Switch management SVI",
        "ip address 10.101.99.21 255.255.255.0",
        "no shutdown",
    ]

    approve_mock = Mock(return_value=False)
    pre_change_expectation = PreChangeExpectation(
        expected_hostname="br01-sw01",
        required_interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/0",
                ipv4=TEST_SWITCH_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
    )
    with (
        patch(
            "network_automation_platform.branch_deployment."
            "collect_device_state",
            side_effect=[
                router_state,
                switch_state,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "validate_device_against_desired_state",
            side_effect=[
                router_report,
                switch_report,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_desired_state_expectation",
            return_value=switch_expectation,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_device_remediation_plan",
            return_value=switch_remediation,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "render_device_remediation",
            return_value=remediation_commands,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_pre_change_expectation",
            return_value=pre_change_expectation,
        ) as pre_change_mock,
        patch(
            "network_automation_platform.branch_deployment."
            "deploy_inventory_device",
            return_value=None,
        ) as deploy_mock,
    ):
        result = deploy_branch(
            "branch-01",
            intent_path=Path(
                "intent/branches/branch-01.yaml"
            ),
            inventory=inventory,
            settings=settings,
            approve=approve_mock,
        )

    assert result.blocked is False

    assert (
        result.devices[0].status
        == BranchDeviceDeploymentStatus.SKIPPED
    )

    assert (
        result.devices[1].status
        == BranchDeviceDeploymentStatus.SKIPPED
    )

    assert (
        result.devices[1].message
        == "Deployment declined by operator"
    )

    assert (
        result.devices[1].remediation_commands
        == remediation_commands
    )
    assert result.devices[1].initial_validation is switch_report
    assert (
        result.devices[1].approval_status
        == DeploymentApprovalStatus.DECLINED
    )

    approve_mock.assert_called_once_with(
        "br01-sw01",
        remediation_commands,
    )
    pre_change_mock.assert_called_once()
    deploy_mock.assert_not_called()

def test_deploy_branch_does_not_write_before_branch_preflight_completes() -> None:
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

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test"),
        ssh_config_file=Path("/tmp/lab_config"),
        ssh_known_hosts_file=Path("/tmp/known_hosts"),
    )

    router_state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=TEST_ROUTER_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
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
                name="interface:GigabitEthernet0/1",
                status=ValidationStatus.FAIL,
                message="Interface GigabitEthernet0/1 is missing",
                reason="missing",
            )
        ],
    )

    switch_report = ValidationReport(
        hostname="br01-sw01",
        checks=[
            ValidationCheck(
                name="vlan:99",
                status=ValidationStatus.FAIL,
                message="VLAN 99 is missing",
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

    router_remediation = DeviceRemediationPlan(
        hostname="br01-rtr01",
        actions=[
            RemediationAction(
                description=(
                    "Create/configure interface "
                    "GigabitEthernet0/1"
                ),
                remediation=InterfaceRemediation(
                    kind="interface",
                    interface_name="GigabitEthernet0/1",
                    description="WAN transit",
                    ipv4="10.101.255.1/30",
                    enabled=True,
                ),
            )
        ],
    )

    remediation_commands = [
        "interface GigabitEthernet0/1",
        "description WAN transit",
        "ip address 10.101.255.1 255.255.255.252",
        "no shutdown",
    ]

    approve_mock = Mock(
        side_effect=AssertionError(
            "Approval was requested before "
            "branch-wide preflight completed"
        )
    )

    with (
        patch(
            "network_automation_platform.branch_deployment."
            "collect_device_state",
            side_effect=[
                router_state,
                switch_state,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "validate_device_against_desired_state",
            side_effect=[
                router_report,
                switch_report,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_desired_state_expectation",
            return_value=router_expectation,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_device_remediation_plan",
            return_value=router_remediation,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "render_device_remediation",
            return_value=remediation_commands,
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "deploy_inventory_device",
        ) as deploy_mock,
    ):
        result = deploy_branch(
            "branch-01",
            intent_path=Path(
                "intent/branches/branch-01.yaml"
            ),
            inventory=inventory,
            settings=settings,
            approve=approve_mock,
        )

    assert result.blocked is True

    assert len(result.devices) == 2

    assert (
        result.devices[1].status
        == BranchDeviceDeploymentStatus.BLOCKED
    )

    assert "unsupported drift" in result.devices[1].message
    assert "vlan:99" in result.devices[1].message
    assert (
        result.devices[0].status
        == BranchDeviceDeploymentStatus.BLOCKED
    )

    assert (
        result.devices[0].message
        == (
            "Deployment blocked because branch "
            "preflight failed on: br01-sw01"
        )
    )

    approve_mock.assert_not_called()
    deploy_mock.assert_not_called()

def test_deploy_branch_collects_all_approvals_before_any_write() -> None:
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

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test"),
        ssh_config_file=Path("/tmp/lab_config"),
        ssh_known_hosts_file=Path("/tmp/known_hosts"),
    )

    router_state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=TEST_ROUTER_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[],
    )

    switch_state = DeviceState(
        hostname="br01-sw01",
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=TEST_SWITCH_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[],
    )

    router_report = ValidationReport(
        hostname="br01-rtr01",
        checks=[
            ValidationCheck(
                name="interface:GigabitEthernet0/1",
                status=ValidationStatus.FAIL,
                message="Interface GigabitEthernet0/1 is missing",
                reason="missing",
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

    router_remediation = DeviceRemediationPlan(
        hostname="br01-rtr01",
        actions=[
            RemediationAction(
                description=(
                    "Create/configure interface "
                    "GigabitEthernet0/1"
                ),
                remediation=InterfaceRemediation(
                    kind="interface",
                    interface_name="GigabitEthernet0/1",
                    description="WAN transit",
                    ipv4="10.101.255.1/30",
                    enabled=True,
                ),
            )
        ],
    )

    switch_remediation = DeviceRemediationPlan(
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

    router_commands = [
        "interface GigabitEthernet0/1",
        "description WAN transit",
        "ip address 10.101.255.1 255.255.255.252",
        "no shutdown",
    ]

    switch_commands = [
        "interface Vlan99",
        "description Switch management SVI",
        "ip address 10.101.99.21 255.255.255.0",
        "no shutdown",
    ]

    approve_mock = Mock(
        side_effect=[
            True,
            False,
        ]
    )

    with (
        patch(
            "network_automation_platform.branch_deployment."
            "collect_device_state",
            side_effect=[
                router_state,
                switch_state,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "validate_device_against_desired_state",
            side_effect=[
                router_report,
                switch_report,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_desired_state_expectation",
            side_effect=[
                router_expectation,
                switch_expectation,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_device_remediation_plan",
            side_effect=[
                router_remediation,
                switch_remediation,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "render_device_remediation",
            side_effect=[
                router_commands,
                switch_commands,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "deploy_inventory_device",
        ) as deploy_mock,
    ):
        result = deploy_branch(
            "branch-01",
            intent_path=Path(
                "intent/branches/branch-01.yaml"
            ),
            inventory=inventory,
            settings=settings,
            approve=approve_mock,
        )

    assert result.blocked is False
    assert len(result.devices) == 2

    assert (
        result.devices[0].status
        == BranchDeviceDeploymentStatus.SKIPPED
    )
    assert (
        result.devices[0].message
        == (
            "Deployment not executed because operator "
            "approval was declined for: br01-sw01"
        )
    )
    assert (
        result.devices[0].remediation_commands
        == router_commands
    )
    assert result.devices[0].initial_validation is router_report
    assert (
        result.devices[0].approval_status
        == DeploymentApprovalStatus.APPROVED
    )

    assert (
        result.devices[1].status
        == BranchDeviceDeploymentStatus.SKIPPED
    )
    assert (
        result.devices[1].message
        == "Deployment declined by operator"
    )
    assert (
        result.devices[1].remediation_commands
        == switch_commands
    )
    assert result.devices[1].initial_validation is switch_report
    assert (
        result.devices[1].approval_status
        == DeploymentApprovalStatus.DECLINED
    )

    approve_mock.assert_has_calls(
        [
            call(
                "br01-rtr01",
                router_commands,
            ),
            call(
                "br01-sw01",
                switch_commands,
            ),
        ]
    )
    assert approve_mock.call_count == 2

    deploy_mock.assert_not_called()

def test_deploy_branch_executes_only_after_all_approvals() -> None:
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

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test"),
        ssh_config_file=Path("/tmp/lab_config"),
        ssh_known_hosts_file=Path("/tmp/known_hosts"),
    )

    router_state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=TEST_ROUTER_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[],
    )

    switch_state = DeviceState(
        hostname="br01-sw01",
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=TEST_SWITCH_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[],
    )

    router_report = ValidationReport(
        hostname="br01-rtr01",
        checks=[
            ValidationCheck(
                name="interface:GigabitEthernet0/1",
                status=ValidationStatus.FAIL,
                message="Interface GigabitEthernet0/1 is missing",
                reason="missing",
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

    router_remediation = DeviceRemediationPlan(
        hostname="br01-rtr01",
        actions=[
            RemediationAction(
                description=(
                    "Create/configure interface "
                    "GigabitEthernet0/1"
                ),
                remediation=InterfaceRemediation(
                    kind="interface",
                    interface_name="GigabitEthernet0/1",
                    description="WAN transit",
                    ipv4="10.101.255.1/30",
                    enabled=True,
                ),
            )
        ],
    )

    switch_remediation = DeviceRemediationPlan(
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

    router_commands = [
        "interface GigabitEthernet0/1",
        "description WAN transit",
        "ip address 10.101.255.1 255.255.255.252",
        "no shutdown",
    ]

    switch_commands = [
        "interface Vlan99",
        "description Switch management SVI",
        "ip address 10.101.99.21 255.255.255.0",
        "no shutdown",
    ]

    router_pre_change = ChangeValidationResult(
        phase=ValidationPhase.PRE_CHANGE,
        report=ValidationReport(
            hostname="br01-rtr01",
            checks=[
                ValidationCheck(
                    name="pre-change-check",
                    status=ValidationStatus.PASS,
                    message="Pre-change validation passed",
                )
            ],
        ),
    )

    router_post_change = ChangeValidationResult(
        phase=ValidationPhase.POST_CHANGE,
        report=ValidationReport(
            hostname="br01-rtr01",
            checks=[
                ValidationCheck(
                    name="post-change-check",
                    status=ValidationStatus.PASS,
                    message="Post-change validation passed",
                )
            ],
        ),
    )

    switch_pre_change = ChangeValidationResult(
        phase=ValidationPhase.PRE_CHANGE,
        report=ValidationReport(
            hostname="br01-sw01",
            checks=[
                ValidationCheck(
                    name="pre-change-check",
                    status=ValidationStatus.PASS,
                    message="Pre-change validation passed",
                )
            ],
        ),
    )

    switch_post_change = ChangeValidationResult(
        phase=ValidationPhase.POST_CHANGE,
        report=ValidationReport(
            hostname="br01-sw01",
            checks=[
                ValidationCheck(
                    name="post-change-check",
                    status=ValidationStatus.PASS,
                    message="Post-change validation passed",
                )
            ],
        ),
    )

    router_deployment = DeploymentResult(
        hostname="br01-rtr01",
        status=DeploymentStatus.SUCCEEDED,
        pre_change=router_pre_change,
        deployment_attempted=True,
        deployment_succeeded=True,
        post_change=router_post_change,
        message="Deployment completed and validated successfully",
    )

    switch_deployment = DeploymentResult(
        hostname="br01-sw01",
        status=DeploymentStatus.SUCCEEDED,
        pre_change=switch_pre_change,
        deployment_attempted=True,
        deployment_succeeded=True,
        post_change=switch_post_change,
        message="Deployment completed and validated successfully",
    )

    events: list[str] = []

    def approve(
        hostname: str,
        commands: list[str],
    ) -> bool:
        events.append(f"approve:{hostname}")
        return True

    def deploy(
        **kwargs: object,
    ) -> DeploymentResult:
        device = kwargs["device"]

        hostname = device.hostname
        events.append(f"deploy:{hostname}")

        if hostname == "br01-rtr01":
            return router_deployment

        return switch_deployment

    with (
        patch(
            "network_automation_platform.branch_deployment."
            "collect_device_state",
            side_effect=[
                router_state,
                switch_state,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "validate_device_against_desired_state",
            side_effect=[
                router_report,
                switch_report,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_desired_state_expectation",
            side_effect=[
                router_expectation,
                switch_expectation,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_device_remediation_plan",
            side_effect=[
                router_remediation,
                switch_remediation,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "render_device_remediation",
            side_effect=[
                router_commands,
                switch_commands,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "deploy_inventory_device",
            side_effect=deploy,
        ) as deploy_mock,
    ):
        result = deploy_branch(
            "branch-01",
            intent_path=Path(
                "intent/branches/branch-01.yaml"
            ),
            inventory=inventory,
            settings=settings,
            approve=approve,
        )

    assert result.blocked is False

    assert (
        result.devices[0].status
        == BranchDeviceDeploymentStatus.DEPLOYED
    )
    assert (
        result.devices[1].status
        == BranchDeviceDeploymentStatus.DEPLOYED
    )
    assert result.devices[0].initial_validation is router_report
    assert result.devices[1].initial_validation is switch_report
    assert all(
        device.approval_status == DeploymentApprovalStatus.APPROVED
        for device in result.devices
    )

    assert (
        result.devices[0].deployment.status
        == DeploymentStatus.SUCCEEDED
    )
    assert (
        result.devices[1].deployment.status
        == DeploymentStatus.SUCCEEDED
    )

    assert events == [
        "approve:br01-rtr01",
        "approve:br01-sw01",
        "deploy:br01-rtr01",
        "deploy:br01-sw01",
    ]

    assert deploy_mock.call_count == 2


def test_deploy_branch_blocks_when_pre_change_safety_cannot_be_built() -> None:
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

    settings = ConnectionSettings(
        username="netdevops",
        password=SecretStr("test"),
        ssh_config_file=Path("/tmp/lab_config"),
        ssh_known_hosts_file=Path("/tmp/known_hosts"),
    )

    router_state = DeviceState(
        hostname="br01-rtr01",
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=TEST_ROUTER_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[],
    )

    switch_state = DeviceState(
        hostname="br01-sw01",
        interfaces=[
            InterfaceState(
                name="GigabitEthernet0/0",
                ipv4=TEST_SWITCH_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
        routes=[],
    )

    router_report = ValidationReport(
        hostname="br01-rtr01",
        checks=[
            ValidationCheck(
                name="interface:GigabitEthernet0/1",
                status=ValidationStatus.FAIL,
                message="Interface GigabitEthernet0/1 is missing",
                reason="missing",
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

    router_remediation = DeviceRemediationPlan(
        hostname="br01-rtr01",
        actions=[
            RemediationAction(
                description=(
                    "Create/configure interface "
                    "GigabitEthernet0/1"
                ),
                remediation=InterfaceRemediation(
                    kind="interface",
                    interface_name="GigabitEthernet0/1",
                    description="WAN transit",
                    ipv4="10.101.255.1/30",
                    enabled=True,
                ),
            )
        ],
    )

    switch_remediation = DeviceRemediationPlan(
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

    router_commands = [
        "interface GigabitEthernet0/1",
        "description WAN transit",
        "ip address 10.101.255.1 255.255.255.252",
        "no shutdown",
    ]

    switch_commands = [
        "interface Vlan99",
        "description Switch management SVI",
        "ip address 10.101.99.21 255.255.255.0",
        "no shutdown",
    ]

    router_pre_change_expectation = PreChangeExpectation(
        expected_hostname="br01-rtr01",
        required_interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/0",
                ipv4=TEST_ROUTER_IP,
                status="up",
                protocol="up",
                admin_enabled=True,
            )
        ],
    )

    approve_mock = Mock(
        side_effect=AssertionError(
            "Approval was requested despite failed branch preflight"
        )
    )

    with (
        patch(
            "network_automation_platform.branch_deployment."
            "collect_device_state",
            side_effect=[
                router_state,
                switch_state,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "validate_device_against_desired_state",
            side_effect=[
                router_report,
                switch_report,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_desired_state_expectation",
            side_effect=[
                router_expectation,
                switch_expectation,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_device_remediation_plan",
            side_effect=[
                router_remediation,
                switch_remediation,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "render_device_remediation",
            side_effect=[
                router_commands,
                switch_commands,
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "build_pre_change_expectation",
            side_effect=[
                router_pre_change_expectation,
                PreChangeExpectationBuildError(
                    "OOB management interface GigabitEthernet0/0 "
                    "is not operational"
                ),
            ],
        ),
        patch(
            "network_automation_platform.branch_deployment."
            "deploy_inventory_device",
        ) as deploy_mock,
    ):
        result = deploy_branch(
            "branch-01",
            intent_path=Path(
                "intent/branches/branch-01.yaml"
            ),
            inventory=inventory,
            settings=settings,
            approve=approve_mock,
        )

    assert result.blocked is True
    assert len(result.devices) == 2

    assert (
        result.devices[0].status
        == BranchDeviceDeploymentStatus.BLOCKED
    )
    assert (
        result.devices[0].message
        == (
            "Deployment blocked because branch preflight "
            "failed on: br01-sw01"
        )
    )
    assert (
        result.devices[0].remediation_commands
        == router_commands
    )

    assert (
        result.devices[1].status
        == BranchDeviceDeploymentStatus.BLOCKED
    )
    assert (
        result.devices[1].message
        == (
            "Deployment safety preflight failed: "
            "OOB management interface GigabitEthernet0/0 "
            "is not operational"
        )
    )
    assert (
        result.devices[1].remediation_commands
        == switch_commands
    )

    approve_mock.assert_not_called()
    deploy_mock.assert_not_called()
