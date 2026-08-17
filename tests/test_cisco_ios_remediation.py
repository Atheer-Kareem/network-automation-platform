from ipaddress import IPv4Address

import pytest

from network_automation_platform.cisco_ios_remediation import (
    render_device_remediation,
    render_interface_remediation,
    render_switchport_remediation,
)
from network_automation_platform.device_state import (
    DeviceState,
    SwitchportState,
)
from network_automation_platform.platform_profiles import (
    SwitchPlatformProfile,
)
from network_automation_platform.remediation import (
    DeviceRemediationPlan,
    InterfaceRemediation,
    RemediationAction,
    SwitchportRemediation,
)
from network_automation_platform.remediation_planner import (
    build_device_remediation_plan,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    SwitchportExpectation,
    ValidationCheck,
    ValidationExpectation,
    ValidationReport,
    ValidationStatus,
    VlanExpectation,
    validate_device_state,
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

def test_render_narrow_access_vlan_switchport_remediation() -> None:
    remediation = SwitchportRemediation(
        kind="switchport",
        interface_name="GigabitEthernet0/2",
        access_vlan=10,
    )

    commands = render_switchport_remediation(
        remediation,
        SwitchPlatformProfile(interface_map={}),
    )

    assert commands == [
        "interface GigabitEthernet0/2",
        "switchport access vlan 10",
    ]

def test_render_narrow_allowed_vlans_switchport_remediation() -> None:
    remediation = SwitchportRemediation(
        kind="switchport",
        interface_name="GigabitEthernet0/1",
        allowed_vlans=[99, 10, 20],
    )

    commands = render_switchport_remediation(
        remediation,
        SwitchPlatformProfile(
            interface_map={},
            trunk_encapsulation="dot1q",
        ),
    )

    assert commands == [
        "interface GigabitEthernet0/1",
        "switchport trunk allowed vlan 99,10,20",
    ]

def test_render_complete_access_switchport_remediation() -> None:
    remediation = SwitchportRemediation(
        kind="switchport",
        interface_name="GigabitEthernet0/2",
        mode="access",
        access_vlan=10,
    )

    commands = render_switchport_remediation(
        remediation,
        SwitchPlatformProfile(interface_map={}),
    )

    assert commands == [
        "interface GigabitEthernet0/2",
        "switchport mode access",
        "switchport access vlan 10",
    ]

def test_render_complete_trunk_switchport_remediation() -> None:
    plan = DeviceRemediationPlan(
        hostname="br01-sw01",
        actions=[
            RemediationAction(
                description="Remediate switchport GigabitEthernet0/1",
                remediation=SwitchportRemediation(
                    kind="switchport",
                    interface_name="GigabitEthernet0/1",
                    mode="trunk",
                    allowed_vlans=[99, 10, 20],
                ),
            )
        ],
    )

    commands = render_device_remediation(
        plan,
        platform="cisco_iosv_l2",
    )

    assert commands == [
        "interface GigabitEthernet0/1",
        "switchport trunk encapsulation dot1q",
        "switchport mode trunk",
        "switchport trunk allowed vlan 99,10,20",
    ]

def test_render_trunk_omits_unspecified_encapsulation() -> None:
    remediation = SwitchportRemediation(
        kind="switchport",
        interface_name="GigabitEthernet0/1",
        mode="trunk",
        allowed_vlans=[10, 20, 99],
    )

    commands = render_switchport_remediation(
        remediation,
        SwitchPlatformProfile(interface_map={}),
    )

    assert commands == [
        "interface GigabitEthernet0/1",
        "switchport mode trunk",
        "switchport trunk allowed vlan 10,20,99",
    ]

def test_switchport_remediation_rejects_unsupported_platform() -> None:
    plan = DeviceRemediationPlan(
        hostname="br01-sw01",
        actions=[
            RemediationAction(
                description="Remediate switchport GigabitEthernet0/1",
                remediation=SwitchportRemediation(
                    kind="switchport",
                    interface_name="GigabitEthernet0/1",
                    mode="trunk",
                    allowed_vlans=[10, 20, 99],
                ),
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="Unsupported switch platform for remediation: unknown",
    ):
        render_device_remediation(plan, platform="unknown")

def test_access_vlan_drift_validates_plans_and_renders_narrow_commands(
) -> None:
    state = DeviceState(
        hostname="br01-sw01",
        interfaces=[],
        routes=[],
        switchports=[
            SwitchportState(
                interface="GigabitEthernet0/2",
                switchport_enabled=True,
                administrative_mode="access",
                operational_mode="access",
                access_vlan=20,
            )
        ],
    )
    expectation = ValidationExpectation(
        switchports=[
            SwitchportExpectation(
                interface="GigabitEthernet0/2",
                switchport_enabled=True,
                administrative_mode="access",
                access_vlan=10,
            )
        ]
    )

    report = validate_device_state(state, expectation)
    check = report.checks[0]
    assert check.reason == "mismatch"
    assert check.mismatched_fields == ["access_vlan"]

    plan = build_device_remediation_plan(expectation, report)
    commands = render_device_remediation(
        plan,
        platform="cisco_iosv_l2",
    )

    assert commands == [
        "interface GigabitEthernet0/2",
        "switchport access vlan 10",
    ]

def test_access_to_trunk_drift_validates_plans_and_renders_complete_unit(
) -> None:
    state = DeviceState(
        hostname="br01-sw01",
        interfaces=[],
        routes=[],
        switchports=[
            SwitchportState(
                interface="GigabitEthernet0/1",
                switchport_enabled=True,
                administrative_mode="access",
                operational_mode="access",
                access_vlan=1,
                allowed_vlans=[],
            )
        ],
    )
    expectation = ValidationExpectation(
        switchports=[
            SwitchportExpectation(
                interface="GigabitEthernet0/1",
                switchport_enabled=True,
                administrative_mode="trunk",
                allowed_vlans=[10, 20, 99],
            )
        ]
    )

    report = validate_device_state(state, expectation)
    check = report.checks[0]
    assert check.reason == "mismatch"
    assert check.mismatched_fields == [
        "administrative_mode",
        "allowed_vlans",
    ]

    plan = build_device_remediation_plan(expectation, report)
    commands = render_device_remediation(
        plan,
        platform="cisco_iosv_l2",
    )

    assert commands == [
        "interface GigabitEthernet0/1",
        "switchport trunk encapsulation dot1q",
        "switchport mode trunk",
        "switchport trunk allowed vlan 10,20,99",
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
