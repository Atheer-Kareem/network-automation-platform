from pathlib import Path
from unittest.mock import Mock, patch

from pydantic import SecretStr

from network_automation_platform.branch_deployment import (
    BranchDeviceDeploymentStatus,
    deploy_branch,
)
from network_automation_platform.change_validation import (
    ChangeValidationResult,
    ValidationPhase,
)
from network_automation_platform.connection_settings import (
    ConnectionSettings,
)
from network_automation_platform.deployment import (
    DeploymentResult,
    DeploymentStatus,
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

    approve_mock.assert_called_once_with(
        "br01-sw01",
        remediation_commands,
    )
    pre_change_mock.assert_not_called()
    deploy_mock.assert_not_called()