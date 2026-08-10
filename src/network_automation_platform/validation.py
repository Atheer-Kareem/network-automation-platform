from enum import StrEnum
from ipaddress import IPv4Address, IPv4Network

from pydantic import BaseModel, Field, model_validator

from network_automation_platform.device_state import DeviceState, RouteState


class ValidationStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"


class InterfaceExpectation(BaseModel):
    name: str
    ipv4: IPv4Address | None = None
    status: str | None = None
    protocol: str | None = None


class RouteExpectation(BaseModel):
    network: IPv4Network
    protocol: str | None = None
    next_hop: IPv4Address | None = None
    outgoing_interface: str | None = None


class ValidationExpectation(BaseModel):
    interfaces: list[InterfaceExpectation] = Field(default_factory=list)
    routes: list[RouteExpectation] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_checks(self) -> "ValidationExpectation":
        if not self.interfaces and not self.routes:
            raise ValueError(
                "At least one validation expectation is required"
            )

        return self


class ValidationCheck(BaseModel):
    name: str
    status: ValidationStatus
    message: str


class ValidationReport(BaseModel):
    hostname: str
    checks: list[ValidationCheck]

    @property
    def passed(self) -> bool:
        return all(
            check.status == ValidationStatus.PASS
            for check in self.checks
        )


def _route_matches(
    actual: RouteState,
    expected: RouteExpectation,
) -> bool:
    return not (
        (
            expected.protocol is not None
            and actual.protocol != expected.protocol
        )
        or (
            expected.next_hop is not None
            and actual.next_hop != expected.next_hop
        )
        or (
            expected.outgoing_interface is not None
            and actual.outgoing_interface
            != expected.outgoing_interface
        )
    )


def validate_device_state(
    state: DeviceState,
    expectation: ValidationExpectation,
) -> ValidationReport:
    checks: list[ValidationCheck] = []

    for expected in expectation.interfaces:
        actual = next(
            (
                interface
                for interface in state.interfaces
                if interface.name == expected.name
            ),
            None,
        )

        if actual is None:
            checks.append(
                ValidationCheck(
                    name=f"interface:{expected.name}",
                    status=ValidationStatus.FAIL,
                    message=f"Interface {expected.name} is missing",
                )
            )
            continue

        failures: list[str] = []

        if expected.ipv4 is not None and actual.ipv4 != expected.ipv4:
            failures.append(
                f"IPv4 expected {expected.ipv4}, got {actual.ipv4}"
            )

        if (
            expected.status is not None
            and actual.status != expected.status
        ):
            failures.append(
                f"status expected {expected.status}, got {actual.status}"
            )

        if (
            expected.protocol is not None
            and actual.protocol != expected.protocol
        ):
            failures.append(
                f"protocol expected {expected.protocol}, "
                f"got {actual.protocol}"
            )

        if failures:
            checks.append(
                ValidationCheck(
                    name=f"interface:{expected.name}",
                    status=ValidationStatus.FAIL,
                    message="; ".join(failures),
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    name=f"interface:{expected.name}",
                    status=ValidationStatus.PASS,
                    message=f"Interface {expected.name} matches expectation",
                )
            )

    for expected in expectation.routes:
        matching_routes = [
            route
            for route in state.routes
            if route.network == expected.network
        ]

        if not matching_routes:
            checks.append(
                ValidationCheck(
                    name=f"route:{expected.network}",
                    status=ValidationStatus.FAIL,
                    message=f"Route {expected.network} is missing",
                )
            )
            continue

        if any(
            _route_matches(route, expected)
            for route in matching_routes
        ):
            checks.append(
                ValidationCheck(
                    name=f"route:{expected.network}",
                    status=ValidationStatus.PASS,
                    message=f"Route {expected.network} matches expectation",
                )
            )
            continue

        if len(matching_routes) == 1:
            actual = matching_routes[0]
            failures: list[str] = []

            if (
                expected.protocol is not None
                and actual.protocol != expected.protocol
            ):
                failures.append(
                    f"protocol expected {expected.protocol}, "
                    f"got {actual.protocol}"
                )

            if (
                expected.next_hop is not None
                and actual.next_hop != expected.next_hop
            ):
                failures.append(
                    f"next hop expected {expected.next_hop}, "
                    f"got {actual.next_hop}"
                )

            if (
                expected.outgoing_interface is not None
                and actual.outgoing_interface
                != expected.outgoing_interface
            ):
                failures.append(
                    "outgoing interface expected "
                    f"{expected.outgoing_interface}, "
                    f"got {actual.outgoing_interface}"
                )

            message = "; ".join(failures)
        else:
            message = (
                f"Route {expected.network} exists, but none of the "
                "matching entries satisfy the expectation"
            )

        checks.append(
            ValidationCheck(
                name=f"route:{expected.network}",
                status=ValidationStatus.FAIL,
                message=message,
            )
        )

    return ValidationReport(
        hostname=state.hostname,
        checks=checks,
    )
