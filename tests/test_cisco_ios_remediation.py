from ipaddress import IPv4Address

from network_automation_platform.cisco_ios_remediation import (
    render_device_remediation,
    render_interface_remediation,
)
from network_automation_platform.remediation import (
    DeviceRemediationPlan,
    InterfaceRemediation,
    RemediationAction,
)
from network_automation_platform.remediation_planner import (
    build_device_remediation_plan,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    ValidationCheck,
    ValidationExpectation,
    ValidationReport,
    ValidationStatus,
)


def test_missing_interface_drift_renders_targeted_commands() -> None:
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
        ],
    )

    plan = build_device_remediation_plan(
        expectation=expectation,
        report=report,
    )

    commands = render_device_remediation(plan)

    assert commands == [
        "interface Vlan99",
        "description Switch management SVI",
        "ip address 10.101.99.21 255.255.255.0",
        "no shutdown",
    ]

def test_render_device_remediation() -> None:
    plan = DeviceRemediationPlan(
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

    commands = render_device_remediation(plan)

    assert commands == [
        "interface Vlan99",
        "description Switch management SVI",
        "ip address 10.101.99.21 255.255.255.0",
        "no shutdown",
    ]

def test_render_interface_remediation() -> None:
    remediation = InterfaceRemediation(
        kind="interface",
        interface_name="Vlan99",
        description="Switch management SVI",
        ipv4="10.101.99.21/24",
        enabled=True,
    )

    commands = render_interface_remediation(
        remediation
    )

    assert commands == [
        "interface Vlan99",
        "description Switch management SVI",
        "ip address 10.101.99.21 255.255.255.0",
        "no shutdown",
    ]