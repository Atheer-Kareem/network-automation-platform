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

        actions.append(
            RemediationAction(
                description=(
                    f"Create/configure interface {interface_name}"
                ),
                remediation=_build_interface_remediation(
                    expected
                ),
            )
        )

    return DeviceRemediationPlan(
        hostname=report.hostname,
        actions=actions,
    )

def is_supported_remediation_check(
    check: ValidationCheck,
) -> bool:
    return (
        check.status == ValidationStatus.FAIL
        and check.name.startswith("interface:")
        and check.reason == "missing"
    )