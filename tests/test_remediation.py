from ipaddress import IPv4Address

import pytest

from network_automation_platform.remediation_planner import (
    RemediationPlanningError,
    build_device_remediation_plan,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    ValidationCheck,
    ValidationExpectation,
    ValidationReport,
    ValidationStatus,
    VlanExpectation,
)


def test_build_missing_interface_remediation() -> None:
    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="Vlan99",
                ipv4=IPv4Address("10.101.99.21"),
                ipv4_prefixlen=24,
                description="Switch management SVI",
                admin_enabled=True,
            )
        ]
    )

    report = ValidationReport(
        hostname="br01-sw01",
        checks=[
            ValidationCheck(
                name="interface:Vlan99",
                status=ValidationStatus.FAIL,
                message="Interface Vlan99 is missing",
                reason="missing",
            )
        ]
    )

    plan = build_device_remediation_plan(
        expectation=expectation,
        report=report,
    )

    assert plan.hostname == "br01-sw01"
    assert plan.has_changes is True
    assert len(plan.actions) == 1

    action = plan.actions[0]

    assert action.description == (
        "Create/configure interface Vlan99"
    )

    remediation = action.remediation

    assert remediation.interface_name == "Vlan99"
    assert remediation.description == "Switch management SVI"
    assert remediation.ipv4 == "10.101.99.21/24"
    assert remediation.enabled is True


def test_planner_ignores_passing_checks() -> None:
    expectation = ValidationExpectation(
        vlans=[
            VlanExpectation(
                vlan_id=99,
                name="MANAGEMENT",
            )
        ]
    )

    report = ValidationReport(
        hostname="br01-sw01",
        checks=[
            ValidationCheck(
                name="interface:Vlan99",
                status=ValidationStatus.PASS,
                message="Interface Vlan99 matches expectation",
            )
        ]
    )

    plan = build_device_remediation_plan(
        expectation=expectation,
        report=report,
    )

    assert plan.has_changes is False


def test_planner_ignores_unsupported_failure() -> None:
    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
            )
        ]
    )

    report = ValidationReport(
        hostname="br01-sw01",
        checks=[
            ValidationCheck(
                name="vlan:99",
                status=ValidationStatus.FAIL,
                message="VLAN 99 is missing",
            )
        ],
    )

    plan = build_device_remediation_plan(
        expectation=expectation,
        report=report,
    )

    assert plan.has_changes is False


def test_planner_fails_when_expected_interface_is_missing() -> None:
    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
            )
        ]
    )

    report = ValidationReport(
        hostname="br01-sw01",
        checks=[
            ValidationCheck(
                name="interface:Vlan99",
                status=ValidationStatus.FAIL,
                message="Interface Vlan99 is missing",
                reason="missing",
            )
        ]
    )

    with pytest.raises(
        RemediationPlanningError,
        match="Vlan99",
    ):
        build_device_remediation_plan(
            expectation=expectation,
            report=report,
        )


def test_planner_requires_prefix_for_ipv4_remediation() -> None:
    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="Vlan99",
                ipv4=IPv4Address("10.101.99.21"),
                ipv4_prefixlen=None,
            )
        ]
    )

    report = ValidationReport(
        hostname="br01-sw01",
        checks=[
            ValidationCheck(
                name="interface:Vlan99",
                status=ValidationStatus.FAIL,
                message="Interface Vlan99 is missing",
                reason="missing",
            )
        ]
    )

    with pytest.raises(
        RemediationPlanningError,
        match="prefix length",
    ):
        build_device_remediation_plan(
            expectation=expectation,
            report=report,
        )