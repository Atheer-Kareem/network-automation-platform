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
    VlanExpectation,
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

def test_description_mismatch_renders_only_description_command() -> None:
    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
                ipv4=IPv4Address("10.101.255.1"),
                ipv4_prefixlen=30,
                description="WAN transit",
                admin_enabled=True,
            )
        ]
    )

    report = ValidationReport(
        hostname="br01-rtr01",
        checks=[
            ValidationCheck(
                name="interface:GigabitEthernet0/1",
                status=ValidationStatus.FAIL,
                message=(
                    "description expected WAN transit, "
                    "got OLD DESCRIPTION"
                ),
                reason="mismatch",
                mismatched_fields=["description"],
            )
        ],
    )

    plan = build_device_remediation_plan(
        expectation=expectation,
        report=report,
    )

    commands = render_device_remediation(plan)

    assert commands == [
        "interface GigabitEthernet0/1",
        "description WAN transit",
    ]

def test_ipv4_prefix_mismatch_renders_only_ip_command() -> None:
    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
                ipv4=IPv4Address("10.101.255.1"),
                ipv4_prefixlen=30,
                description="WAN transit",
                admin_enabled=True,
            )
        ]
    )

    report = ValidationReport(
        hostname="br01-rtr01",
        checks=[
            ValidationCheck(
                name="interface:GigabitEthernet0/1",
                status=ValidationStatus.FAIL,
                message=(
                    "IPv4 prefix length expected 30, got 24"
                ),
                reason="mismatch",
                mismatched_fields=["ipv4_prefixlen"],
            )
        ],
    )

    plan = build_device_remediation_plan(
        expectation=expectation,
        report=report,
    )

    commands = render_device_remediation(plan)

    assert commands == [
        "interface GigabitEthernet0/1",
        "ip address 10.101.255.1 255.255.255.252",
    ]

def test_admin_state_mismatch_renders_only_admin_command() -> None:
    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
                ipv4=IPv4Address("10.101.255.1"),
                ipv4_prefixlen=30,
                description="WAN transit",
                admin_enabled=True,
            )
        ]
    )

    report = ValidationReport(
        hostname="br01-rtr01",
        checks=[
            ValidationCheck(
                name="interface:GigabitEthernet0/1",
                status=ValidationStatus.FAIL,
                message=(
                    "admin enabled expected True, got False"
                ),
                reason="mismatch",
                mismatched_fields=["admin_enabled"],
            )
        ],
    )

    plan = build_device_remediation_plan(
        expectation=expectation,
        report=report,
    )

    commands = render_device_remediation(plan)

    assert commands == [
        "interface GigabitEthernet0/1",
        "no shutdown",
    ]

def test_ipv4_address_mismatch_renders_complete_ip_command() -> None:
    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
                ipv4=IPv4Address("10.101.255.1"),
                ipv4_prefixlen=30,
                description="WAN transit",
                admin_enabled=True,
            )
        ]
    )

    report = ValidationReport(
        hostname="br01-rtr01",
        checks=[
            ValidationCheck(
                name="interface:GigabitEthernet0/1",
                status=ValidationStatus.FAIL,
                message=(
                    "IPv4 expected 10.101.255.1, "
                    "got 10.101.255.2"
                ),
                reason="mismatch",
                mismatched_fields=["ipv4"],
            )
        ],
    )

    plan = build_device_remediation_plan(
        expectation=expectation,
        report=report,
    )

    commands = render_device_remediation(plan)

    assert commands == [
        "interface GigabitEthernet0/1",
        "ip address 10.101.255.1 255.255.255.252",
    ]

def test_admin_disable_mismatch_renders_only_shutdown_command() -> None:
    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
                admin_enabled=False,
            )
        ]
    )

    report = ValidationReport(
        hostname="br01-rtr01",
        checks=[
            ValidationCheck(
                name="interface:GigabitEthernet0/1",
                status=ValidationStatus.FAIL,
                message=(
                    "admin enabled expected False, got True"
                ),
                reason="mismatch",
                mismatched_fields=["admin_enabled"],
            )
        ],
    )

    plan = build_device_remediation_plan(
        expectation=expectation,
        report=report,
    )

    commands = render_device_remediation(plan)

    assert commands == [
        "interface GigabitEthernet0/1",
        "shutdown",
    ]

def test_missing_vlan_drift_renders_targeted_commands() -> None:
    expectation = ValidationExpectation(
        vlans=[
            VlanExpectation(
                vlan_id=10,
                name="USERS",
                status="active",
            )
        ]
    )

    report = ValidationReport(
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

    plan = build_device_remediation_plan(
        expectation=expectation,
        report=report,
    )

    commands = render_device_remediation(plan)

    assert commands == [
        "vlan 10",
        "name USERS",
    ]

def test_vlan_name_mismatch_renders_targeted_commands() -> None:
    expectation = ValidationExpectation(
        vlans=[
            VlanExpectation(
                vlan_id=10,
                name="USERS",
                status="active",
            )
        ]
    )

    report = ValidationReport(
        hostname="br01-sw01",
        checks=[
            ValidationCheck(
                name="vlan:10",
                status=ValidationStatus.FAIL,
                message="name expected USERS, got WRONG",
                reason="mismatch",
                mismatched_fields=["name"],
            )
        ],
    )

    plan = build_device_remediation_plan(
        expectation=expectation,
        report=report,
    )

    commands = render_device_remediation(plan)

    assert commands == [
        "vlan 10",
        "name USERS",
    ]
