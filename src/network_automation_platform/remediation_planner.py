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


class RemediationPlanningError(ValueError):
    pass

CONFIGURABLE_INTERFACE_MISMATCH_FIELDS = frozenset(
    {
        "description",
        "ipv4",
        "ipv4_prefixlen",
        "admin_enabled",
    }
)

def _build_interface_remediation(
    expected: InterfaceExpectation,
) -> InterfaceRemediation:
    ipv4: str | None = None

    if expected.ipv4 is not None:
        if expected.ipv4_prefixlen is None:
            raise RemediationPlanningError(
                f"Cannot remediate interface {expected.name}: "
                "IPv4 prefix length is missing"
            )

        ipv4 = f"{expected.ipv4}/{expected.ipv4_prefixlen}"

    return InterfaceRemediation(
        kind="interface",
        interface_name=expected.name,
        description=expected.description,
        ipv4=ipv4,
        enabled=expected.admin_enabled,
    )

def _build_interface_mismatch_remediation(
    expected: InterfaceExpectation,
    mismatched_fields: list[str],
) -> InterfaceRemediation:
    fields = set(mismatched_fields)

    description: str | None = None
    ipv4: str | None = None
    enabled: bool | None = None

    if "description" in fields:
        description = expected.description

    if {"ipv4", "ipv4_prefixlen"} & fields:
        if expected.ipv4 is None:
            raise RemediationPlanningError(
                f"Cannot remediate interface {expected.name}: "
                "desired IPv4 address is missing"
            )

        if expected.ipv4_prefixlen is None:
            raise RemediationPlanningError(
                f"Cannot remediate interface {expected.name}: "
                "IPv4 prefix length is missing"
            )

        ipv4 = (
            f"{expected.ipv4}/"
            f"{expected.ipv4_prefixlen}"
        )

    if "admin_enabled" in fields:
        enabled = expected.admin_enabled

    return InterfaceRemediation(
        kind="interface",
        interface_name=expected.name,
        description=description,
        ipv4=ipv4,
        enabled=enabled,
    )

def build_device_remediation_plan(
    expectation: ValidationExpectation,
    report: ValidationReport,
) -> DeviceRemediationPlan:
    actions: list[RemediationAction] = []

    for check in report.checks:
        if check.status != ValidationStatus.FAIL:
            continue

        if not is_supported_remediation_check(check):
            continue

        interface_name = check.name.removeprefix(
            "interface:"
        )

        expected = next(
            (
                interface
                for interface in expectation.interfaces
                if interface.name == interface_name
            ),
            None,
        )

        if expected is None:
            raise RemediationPlanningError(
                "Validation references interface "
                f"{interface_name}, but it is not present "
                "in the validation expectation"
            )

        if check.reason == "missing":
            remediation = _build_interface_remediation(
                expected
            )
            description = (
                f"Create/configure interface {interface_name}"
            )
        else:
            remediation = _build_interface_mismatch_remediation(
                expected,
                check.mismatched_fields,
            )
            description = (
                f"Remediate interface {interface_name}"
            )

        actions.append(
            RemediationAction(
                description=description,
                remediation=remediation,
            )
        )

    return DeviceRemediationPlan(
        hostname=report.hostname,
        actions=actions,
    )

def is_supported_remediation_check(
    check: ValidationCheck,
) -> bool:
    if (
        check.status != ValidationStatus.FAIL
        or not check.name.startswith("interface:")
    ):
        return False

    if check.reason == "missing":
        return True

    if check.reason != "mismatch":
        return False

    if not check.mismatched_fields:
        return False

    return set(check.mismatched_fields).issubset(
        CONFIGURABLE_INTERFACE_MISMATCH_FIELDS
    )
