from ipaddress import IPv4Address

import pytest
from pydantic import ValidationError

from network_automation_platform.remediation import (
    RemediationAction,
    SwitchportRemediation,
    VlanRemediation,
)
from network_automation_platform.remediation_planner import (
    RemediationPlanningError,
    build_device_remediation_plan,
    is_supported_remediation_check,
)
from network_automation_platform.validation import (
    InterfaceExpectation,
    OspfNeighborExpectation,
    SwitchportExpectation,
    ValidationCheck,
    ValidationExpectation,
    ValidationReport,
    ValidationStatus,
    VlanExpectation,
)


def test_vlan_remediation_models_desired_vlan_configuration() -> None:
    remediation = VlanRemediation(
        kind="vlan",
        vlan_id=10,
        name="USERS",
    )

    assert remediation.kind == "vlan"
    assert remediation.vlan_id == 10
    assert remediation.name == "USERS"

def test_remediation_action_accepts_vlan_remediation() -> None:
    remediation = VlanRemediation(
        kind="vlan",
        vlan_id=10,
        name="USERS",
    )

    action = RemediationAction(
        description="Create/configure VLAN 10",
        remediation=remediation,
    )

    assert action.remediation == remediation
    assert action.remediation.kind == "vlan"

def test_build_missing_vlan_remediation() -> None:
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

    assert len(plan.actions) == 1

    action = plan.actions[0]

    assert action.description == "Create/configure VLAN 10"
    assert action.remediation.kind == "vlan"
    assert action.remediation.vlan_id == 10
    assert action.remediation.name == "USERS"

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

def test_build_interface_remediation_targets_description_mismatch_only() -> None:
    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
                ipv4="10.101.255.1",
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
        expectation,
        report,
    )

    assert len(plan.actions) == 1

    remediation = plan.actions[0].remediation

    assert remediation.interface_name == "GigabitEthernet0/1"
    assert remediation.description == "WAN transit"
    assert remediation.ipv4 is None
    assert remediation.enabled is None

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

def test_build_interface_remediation_targets_ipv4_prefix_mismatch() -> None:
    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
                ipv4="10.101.255.1",
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
                message="IPv4 prefix length expected 30, got 24",
                reason="mismatch",
                mismatched_fields=["ipv4_prefixlen"],
            )
        ],
    )

    plan = build_device_remediation_plan(
        expectation,
        report,
    )

    remediation = plan.actions[0].remediation

    assert remediation.interface_name == "GigabitEthernet0/1"
    assert remediation.description is None
    assert remediation.ipv4 == "10.101.255.1/30"
    assert remediation.enabled is None

def test_interface_operational_mismatch_is_not_supported_remediation() -> None:
    check = ValidationCheck(
        name="interface:GigabitEthernet0/1",
        status=ValidationStatus.FAIL,
        message="protocol expected up, got down",
        reason="mismatch",
        mismatched_fields=["protocol"],
    )

    assert is_supported_remediation_check(check) is False

def test_ospf_operational_failure_is_not_supported_remediation() -> None:
    check = ValidationCheck(
        name="ospf_neighbor:10.101.255.2",
        status=ValidationStatus.FAIL,
        message="OSPF neighbor 10.101.255.2 is missing",
        reason="missing",
    )

    assert is_supported_remediation_check(check) is False

    plan = build_device_remediation_plan(
        expectation=ValidationExpectation(
            ospf_neighbors=[
                OspfNeighborExpectation(address="10.101.255.2")
            ],
        ),
        report=ValidationReport(
            hostname="br01-rtr01",
            checks=[check],
        ),
    )
    assert plan.has_changes is False


def test_learned_route_failure_is_not_supported_remediation() -> None:
    check = ValidationCheck(
        name="route:10.200.0.1/32",
        status=ValidationStatus.FAIL,
        message="Route 10.200.0.1/32 is missing",
        reason="missing",
    )

    assert is_supported_remediation_check(check) is False

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

def test_interface_combined_configurable_mismatch_is_supported() -> None:
    check = ValidationCheck(
        name="interface:GigabitEthernet0/1",
        status=ValidationStatus.FAIL,
        message=(
            "description expected WAN transit, got OLD; "
            "IPv4 prefix length expected 30, got 24; "
            "admin enabled expected True, got False"
        ),
        reason="mismatch",
        mismatched_fields=[
            "description",
            "ipv4_prefixlen",
            "admin_enabled",
        ],
    )

    assert is_supported_remediation_check(check) is True

def test_interface_mixed_configurable_and_operational_mismatch_is_unsupported() -> None:
    check = ValidationCheck(
        name="interface:GigabitEthernet0/1",
        status=ValidationStatus.FAIL,
        message=(
            "description expected WAN transit, got OLD; "
            "protocol expected up, got down"
        ),
        reason="mismatch",
        mismatched_fields=[
            "description",
            "protocol",
        ],
    )

    assert is_supported_remediation_check(check) is False

def test_build_interface_remediation_targets_multiple_mismatches() -> None:
    expectation = ValidationExpectation(
        interfaces=[
            InterfaceExpectation(
                name="GigabitEthernet0/1",
                ipv4="10.101.255.1",
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
                    "description expected WAN transit, got OLD; "
                    "admin enabled expected True, got False"
                ),
                reason="mismatch",
                mismatched_fields=[
                    "description",
                    "admin_enabled",
                ],
            )
        ],
    )

    plan = build_device_remediation_plan(
        expectation,
        report,
    )

    assert len(plan.actions) == 1

    remediation = plan.actions[0].remediation

    assert remediation.interface_name == "GigabitEthernet0/1"
    assert remediation.description == "WAN transit"
    assert remediation.ipv4 is None
    assert remediation.enabled is True

def test_build_vlan_name_mismatch_remediation() -> None:
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

    assert len(plan.actions) == 1

    action = plan.actions[0]

    assert action.description == "Remediate VLAN 10"
    assert action.remediation.kind == "vlan"
    assert action.remediation.vlan_id == 10
    assert action.remediation.name == "USERS"

def test_vlan_status_mismatch_is_not_supported_remediation() -> None:
    check = ValidationCheck(
        name="vlan:10",
        status=ValidationStatus.FAIL,
        message="status expected active, got suspend",
        reason="mismatch",
        mismatched_fields=["status"],
    )

    assert is_supported_remediation_check(check) is False

def test_vlan_mixed_name_and_status_mismatch_is_unsupported() -> None:
    check = ValidationCheck(
        name="vlan:10",
        status=ValidationStatus.FAIL,
        message=(
            "name expected USERS, got WRONG; "
            "status expected active, got suspend"
        ),
        reason="mismatch",
        mismatched_fields=[
            "name",
            "status",
        ],
    )

    assert is_supported_remediation_check(check) is False

def test_planner_requires_name_for_vlan_remediation() -> None:
    expectation = ValidationExpectation(
        vlans=[
            VlanExpectation(
                vlan_id=10,
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

    with pytest.raises(
        RemediationPlanningError,
        match="desired VLAN name is missing",
    ):
        build_device_remediation_plan(
            expectation=expectation,
            report=report,
        )

def _build_switchport_plan(
    expected: SwitchportExpectation,
    mismatched_fields: list[str],
):
    return build_device_remediation_plan(
        expectation=ValidationExpectation(
            switchports=[expected]
        ),
        report=ValidationReport(
            hostname="br01-sw01",
            checks=[
                ValidationCheck(
                    name=f"switchport:{expected.interface}",
                    status=ValidationStatus.FAIL,
                    message="switchport mismatch",
                    reason="mismatch",
                    mismatched_fields=mismatched_fields,
                )
            ],
        ),
    )

def test_switchport_remediation_models_desired_configuration() -> None:
    remediation = SwitchportRemediation(
        kind="switchport",
        interface_name="GigabitEthernet0/1",
        mode="trunk",
        allowed_vlans=[10, 20, 99],
    )

    assert remediation.kind == "switchport"
    assert remediation.interface_name == "GigabitEthernet0/1"
    assert remediation.mode == "trunk"
    assert remediation.access_vlan is None
    assert remediation.allowed_vlans == [10, 20, 99]

def test_switchport_remediation_rejects_dual_vlan_configuration() -> None:
    with pytest.raises(
        ValidationError,
        match="cannot include both access and allowed VLAN",
    ):
        SwitchportRemediation(
            kind="switchport",
            interface_name="GigabitEthernet0/1",
            access_vlan=10,
            allowed_vlans=[10, 20, 99],
        )

@pytest.mark.parametrize(
    ("mode", "access_vlan", "allowed_vlans"),
    [
        pytest.param(None, 10, None, id="narrow-access-vlan"),
        pytest.param(None, None, [10, 20, 99], id="narrow-allowed-vlans"),
        pytest.param("access", 10, None, id="complete-access"),
        pytest.param(
            "trunk",
            None,
            [10, 20, 99],
            id="complete-trunk",
        ),
    ],
)
def test_switchport_remediation_accepts_valid_v1_shapes(
    mode: str | None,
    access_vlan: int | None,
    allowed_vlans: list[int] | None,
) -> None:
    remediation = SwitchportRemediation(
        kind="switchport",
        interface_name="GigabitEthernet0/1",
        mode=mode,
        access_vlan=access_vlan,
        allowed_vlans=allowed_vlans,
    )

    assert remediation.mode == mode
    assert remediation.access_vlan == access_vlan
    assert remediation.allowed_vlans == allowed_vlans

@pytest.mark.parametrize(
    ("mode", "access_vlan", "allowed_vlans", "message"),
    [
        pytest.param(
            None,
            None,
            [],
            "allowed VLANs cannot be empty",
            id="empty-allowed-vlans",
        ),
        pytest.param(
            "access",
            None,
            None,
            "requires an access VLAN",
            id="access-without-vlan",
        ),
        pytest.param(
            "trunk",
            None,
            None,
            "requires allowed VLANs",
            id="trunk-without-vlans",
        ),
        pytest.param(
            "trunk",
            None,
            [],
            "allowed VLANs cannot be empty",
            id="trunk-with-empty-vlans",
        ),
        pytest.param(
            None,
            None,
            None,
            "requires access or allowed VLAN",
            id="empty-narrow-remediation",
        ),
    ],
)
def test_switchport_remediation_rejects_invalid_v1_shapes(
    mode: str | None,
    access_vlan: int | None,
    allowed_vlans: list[int] | None,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        SwitchportRemediation(
            kind="switchport",
            interface_name="GigabitEthernet0/1",
            mode=mode,
            access_vlan=access_vlan,
            allowed_vlans=allowed_vlans,
        )

def test_remediation_action_accepts_switchport_remediation() -> None:
    remediation = SwitchportRemediation(
        kind="switchport",
        interface_name="GigabitEthernet0/2",
        access_vlan=10,
    )

    action = RemediationAction(
        description="Remediate switchport GigabitEthernet0/2",
        remediation=remediation,
    )

    assert action.remediation == remediation
    assert action.remediation.kind == "switchport"

def test_build_access_vlan_only_switchport_remediation() -> None:
    plan = _build_switchport_plan(
        SwitchportExpectation(
            interface="GigabitEthernet0/2",
            administrative_mode="access",
            access_vlan=10,
        ),
        ["access_vlan"],
    )

    remediation = plan.actions[0].remediation
    assert remediation.mode is None
    assert remediation.access_vlan == 10
    assert remediation.allowed_vlans is None

def test_build_allowed_vlans_only_switchport_remediation_preserves_order(
) -> None:
    plan = _build_switchport_plan(
        SwitchportExpectation(
            interface="GigabitEthernet0/1",
            administrative_mode="trunk",
            allowed_vlans=[99, 10, 20],
        ),
        ["allowed_vlans"],
    )

    remediation = plan.actions[0].remediation
    assert remediation.mode is None
    assert remediation.access_vlan is None
    assert remediation.allowed_vlans == [99, 10, 20]

def test_build_access_to_trunk_mode_switchport_remediation() -> None:
    plan = _build_switchport_plan(
        SwitchportExpectation(
            interface="GigabitEthernet0/1",
            administrative_mode="trunk",
            allowed_vlans=[10, 20, 99],
        ),
        ["administrative_mode"],
    )

    remediation = plan.actions[0].remediation
    assert remediation.mode == "trunk"
    assert remediation.access_vlan is None
    assert remediation.allowed_vlans == [10, 20, 99]

def test_build_trunk_to_access_mode_switchport_remediation() -> None:
    plan = _build_switchport_plan(
        SwitchportExpectation(
            interface="GigabitEthernet0/2",
            administrative_mode="access",
            access_vlan=10,
        ),
        ["administrative_mode"],
    )

    remediation = plan.actions[0].remediation
    assert remediation.mode == "access"
    assert remediation.access_vlan == 10
    assert remediation.allowed_vlans is None

def test_planner_rejects_dual_vlan_mismatch_without_mode_drift() -> None:
    with pytest.raises(
        RemediationPlanningError,
        match="mismatches are ambiguous",
    ):
        _build_switchport_plan(
            SwitchportExpectation(
                interface="GigabitEthernet0/1",
                administrative_mode="trunk",
                access_vlan=10,
                allowed_vlans=[10, 20, 99],
            ),
            ["access_vlan", "allowed_vlans"],
        )

@pytest.mark.parametrize(
    ("mode", "mismatched_fields", "message"),
    [
        pytest.param(
            "access",
            ["administrative_mode", "allowed_vlans"],
            "allowed VLAN mismatch is incompatible",
            id="access-mode-with-allowed-vlan-mismatch",
        ),
        pytest.param(
            "trunk",
            ["administrative_mode", "access_vlan"],
            "access VLAN mismatch is incompatible",
            id="trunk-mode-with-access-vlan-mismatch",
        ),
    ],
)
def test_mode_change_rejects_opposite_vlan_domain_mismatch(
    mode: str,
    mismatched_fields: list[str],
    message: str,
) -> None:
    expected = SwitchportExpectation(
        interface="GigabitEthernet0/1",
        administrative_mode=mode,
        access_vlan=10,
        allowed_vlans=[10, 20, 99],
    )

    with pytest.raises(RemediationPlanningError, match=message):
        _build_switchport_plan(expected, mismatched_fields)

@pytest.mark.parametrize(
    "mode",
    [
        pytest.param(None, id="missing-mode"),
        pytest.param("trunk", id="trunk-mode"),
    ],
)
def test_access_vlan_only_remediation_requires_access_mode(
    mode: str | None,
) -> None:
    with pytest.raises(
        RemediationPlanningError,
        match="administrative mode is not access",
    ):
        _build_switchport_plan(
            SwitchportExpectation(
                interface="GigabitEthernet0/2",
                administrative_mode=mode,
                access_vlan=10,
            ),
            ["access_vlan"],
        )

@pytest.mark.parametrize(
    "mode",
    [
        pytest.param(None, id="missing-mode"),
        pytest.param("access", id="access-mode"),
    ],
)
def test_allowed_vlans_only_remediation_requires_trunk_mode(
    mode: str | None,
) -> None:
    with pytest.raises(
        RemediationPlanningError,
        match="administrative mode is not trunk",
    ):
        _build_switchport_plan(
            SwitchportExpectation(
                interface="GigabitEthernet0/1",
                administrative_mode=mode,
                allowed_vlans=[10, 20, 99],
            ),
            ["allowed_vlans"],
        )

@pytest.mark.parametrize(
    ("reason", "mismatched_fields"),
    [
        pytest.param("missing", [], id="missing-switchport"),
        pytest.param(
            "mismatch",
            ["switchport_enabled"],
            id="switchport-enabled",
        ),
        pytest.param(
            "mismatch",
            ["native_vlan"],
            id="native-vlan",
        ),
        pytest.param(
            "mismatch",
            ["administrative_mode", "switchport_enabled"],
            id="mixed-mode-and-switchport-enabled",
        ),
        pytest.param(
            "mismatch",
            ["allowed_vlans", "native_vlan"],
            id="mixed-allowed-and-native-vlan",
        ),
        pytest.param("mismatch", [], id="empty-mismatch-fields"),
    ],
)
def test_unsupported_switchport_checks_are_fail_closed(
    reason: str,
    mismatched_fields: list[str],
) -> None:
    check = ValidationCheck(
        name="switchport:GigabitEthernet0/1",
        status=ValidationStatus.FAIL,
        message="unsupported switchport drift",
        reason=reason,
        mismatched_fields=mismatched_fields,
    )

    assert is_supported_remediation_check(check) is False

def test_planner_fails_when_expected_switchport_is_missing() -> None:
    report = ValidationReport(
        hostname="br01-sw01",
        checks=[
            ValidationCheck(
                name="switchport:GigabitEthernet0/1",
                status=ValidationStatus.FAIL,
                message="access VLAN mismatch",
                reason="mismatch",
                mismatched_fields=["access_vlan"],
            )
        ],
    )

    with pytest.raises(
        RemediationPlanningError,
        match="switchport GigabitEthernet0/1",
    ):
        build_device_remediation_plan(
            expectation=ValidationExpectation(
                interfaces=[InterfaceExpectation(name="Vlan99")]
            ),
            report=report,
        )

@pytest.mark.parametrize(
    ("expected", "mismatched_fields", "message"),
    [
        pytest.param(
            SwitchportExpectation(
                interface="GigabitEthernet0/2",
                administrative_mode="access",
            ),
            ["access_vlan"],
            "desired access VLAN is missing",
            id="access-vlan-mismatch",
        ),
        pytest.param(
            SwitchportExpectation(
                interface="GigabitEthernet0/2",
                administrative_mode="access",
            ),
            ["administrative_mode"],
            "desired access VLAN is missing",
            id="access-mode-mismatch",
        ),
        pytest.param(
            SwitchportExpectation(
                interface="GigabitEthernet0/1",
                administrative_mode="trunk",
            ),
            ["allowed_vlans"],
            "desired allowed VLANs are missing or empty",
            id="allowed-vlans-mismatch",
        ),
        pytest.param(
            SwitchportExpectation(
                interface="GigabitEthernet0/1",
                administrative_mode="trunk",
                allowed_vlans=[],
            ),
            ["allowed_vlans"],
            "desired allowed VLANs are missing or empty",
            id="empty-allowed-vlans-mismatch",
        ),
        pytest.param(
            SwitchportExpectation(
                interface="GigabitEthernet0/1",
                administrative_mode="trunk",
            ),
            ["administrative_mode"],
            "desired allowed VLANs are missing or empty",
            id="trunk-mode-mismatch",
        ),
        pytest.param(
            SwitchportExpectation(
                interface="GigabitEthernet0/1",
                administrative_mode="trunk",
                allowed_vlans=[],
            ),
            ["administrative_mode"],
            "desired allowed VLANs are missing or empty",
            id="empty-trunk-mode-mismatch",
        ),
    ],
)
def test_planner_requires_switchport_desired_configuration(
    expected: SwitchportExpectation,
    mismatched_fields: list[str],
    message: str,
) -> None:
    with pytest.raises(RemediationPlanningError, match=message):
        _build_switchport_plan(expected, mismatched_fields)
