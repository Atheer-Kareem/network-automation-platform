from enum import StrEnum
from ipaddress import IPv4Address, IPv4Network
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from network_automation_platform.device_state import DeviceState, RouteState

ValidationReason = Literal[
    "missing",
    "mismatch",
]

class ValidationStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"


class InterfaceExpectation(BaseModel):
    name: str
    ipv4: IPv4Address | None = None
    ipv4_prefixlen: int | None = Field(
        default=None,
        ge=0,
        le=32,
    )
    description: str | None = None
    status: str | None = None
    protocol: str | None = None
    admin_enabled: bool | None = None


class RouteExpectation(BaseModel):
    network: IPv4Network
    protocol: str | None = None
    next_hop: IPv4Address | None = None
    outgoing_interface: str | None = None

class VlanExpectation(BaseModel):
    vlan_id: int
    name: str | None = None
    status: str | None = None


class SwitchportExpectation(BaseModel):
    interface: str
    switchport_enabled: bool | None = None
    administrative_mode: str | None = None
    access_vlan: int | None = None
    native_vlan: int | None = None
    allowed_vlans: list[int] | None = None

class ValidationExpectation(BaseModel):
    interfaces: list[InterfaceExpectation] = Field(default_factory=list)
    routes: list[RouteExpectation] = Field(default_factory=list)
    vlans: list[VlanExpectation] = Field(default_factory=list)
    switchports: list[SwitchportExpectation] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def require_checks(self) -> "ValidationExpectation":
        if not any(
            (
                self.interfaces,
                self.routes,
                self.vlans,
                self.switchports,
            )
        ):
            raise ValueError(
                "At least one validation expectation is required"
            )

        return self



class ValidationCheck(BaseModel):
    name: str
    status: ValidationStatus
    message: str
    reason: ValidationReason | None = None
    mismatched_fields: list[str] = Field(default_factory=list)


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
                    reason="missing",
                )
            )
            continue

        failures: list[str] = []
        mismatched_fields: list[str] = []

        if (
            expected.ipv4 is not None
            and actual.ipv4 != expected.ipv4
        ):
            failures.append(
                f"IPv4 expected {expected.ipv4}, got {actual.ipv4}"
            )
            mismatched_fields.append("ipv4")

        if (
            expected.ipv4_prefixlen is not None
            and actual.ipv4_prefixlen
            != expected.ipv4_prefixlen
        ):
            failures.append(
                "IPv4 prefix length expected "
                f"{expected.ipv4_prefixlen}, "
                f"got {actual.ipv4_prefixlen}"
            )
            mismatched_fields.append("ipv4_prefixlen")

        if (
            expected.description is not None
            and actual.description != expected.description
        ):
            failures.append(
                f"description expected {expected.description}, "
                f"got {actual.description}"
            )
            mismatched_fields.append("description")

        if (
            expected.status is not None
            and actual.status != expected.status
        ):
            failures.append(
                f"status expected {expected.status}, "
                f"got {actual.status}"
            )
            mismatched_fields.append("status")

        if (
            expected.protocol is not None
            and actual.protocol != expected.protocol
        ):
            failures.append(
                f"protocol expected {expected.protocol}, "
                f"got {actual.protocol}"
            )
            mismatched_fields.append("protocol")

        if (
            expected.admin_enabled is not None
            and actual.admin_enabled
            != expected.admin_enabled
        ):
            failures.append(
                "admin enabled expected "
                f"{expected.admin_enabled}, "
                f"got {actual.admin_enabled}"
            )
            mismatched_fields.append("admin_enabled")

        if failures:
            checks.append(
                ValidationCheck(
                    name=f"interface:{expected.name}",
                    status=ValidationStatus.FAIL,
                    message="; ".join(failures),
                    reason="mismatch",
                    mismatched_fields=mismatched_fields,
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    name=f"interface:{expected.name}",
                    status=ValidationStatus.PASS,
                    message=(
                        f"Interface {expected.name} "
                        "matches expectation"
                    ),
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

    for expected in expectation.vlans:
        actual = next(
            (
                vlan
                for vlan in state.vlans
                if vlan.vlan_id == expected.vlan_id
            ),
            None,
        )

        if actual is None:
            checks.append(
                ValidationCheck(
                    name=f"vlan:{expected.vlan_id}",
                    status=ValidationStatus.FAIL,
                    message=f"VLAN {expected.vlan_id} is missing",
                )
            )
            continue

        failures: list[str] = []

        if (
            expected.name is not None
            and actual.name != expected.name
        ):
            failures.append(
                f"name expected {expected.name}, got {actual.name}"
            )

        if (
            expected.status is not None
            and actual.status != expected.status
        ):
            failures.append(
                f"status expected {expected.status}, got {actual.status}"
            )

        if failures:
            checks.append(
                ValidationCheck(
                    name=f"vlan:{expected.vlan_id}",
                    status=ValidationStatus.FAIL,
                    message="; ".join(failures),
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    name=f"vlan:{expected.vlan_id}",
                    status=ValidationStatus.PASS,
                    message=(
                        f"VLAN {expected.vlan_id} "
                        "matches expectation"
                    ),
                )
            )

    for expected in expectation.switchports:
        actual = next(
            (
                switchport
                for switchport in state.switchports
                if switchport.interface == expected.interface
            ),
            None,
        )

        if actual is None:
            checks.append(
                ValidationCheck(
                    name=f"switchport:{expected.interface}",
                    status=ValidationStatus.FAIL,
                    message=(
                        f"Switchport {expected.interface} is missing"
                    ),
                )
            )
            continue

        failures: list[str] = []

        if (
            expected.switchport_enabled is not None
            and actual.switchport_enabled
            != expected.switchport_enabled
        ):
            failures.append(
                "switchport enabled expected "
                f"{expected.switchport_enabled}, "
                f"got {actual.switchport_enabled}"
            )

        if (
            expected.administrative_mode is not None
            and actual.administrative_mode
            != expected.administrative_mode
        ):
            failures.append(
                "administrative mode expected "
                f"{expected.administrative_mode}, "
                f"got {actual.administrative_mode}"
            )

        if (
            expected.access_vlan is not None
            and actual.access_vlan != expected.access_vlan
        ):
            failures.append(
                f"access VLAN expected {expected.access_vlan}, "
                f"got {actual.access_vlan}"
            )

        if (
            expected.native_vlan is not None
            and actual.native_vlan != expected.native_vlan
        ):
            failures.append(
                f"native VLAN expected {expected.native_vlan}, "
                f"got {actual.native_vlan}"
            )

        if expected.allowed_vlans is not None:
            expected_vlans = set(expected.allowed_vlans)
            actual_vlans = set(actual.allowed_vlans)

            if actual_vlans != expected_vlans:
                failures.append(
                    "allowed VLANs expected "
                    f"{sorted(expected_vlans)}, "
                    f"got {sorted(actual_vlans)}"
                )

        if failures:
            checks.append(
                ValidationCheck(
                    name=f"switchport:{expected.interface}",
                    status=ValidationStatus.FAIL,
                    message="; ".join(failures),
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    name=f"switchport:{expected.interface}",
                    status=ValidationStatus.PASS,
                    message=(
                        f"Switchport {expected.interface} "
                        "matches expectation"
                    ),
                )
            )

    return ValidationReport(
        hostname=state.hostname,
        checks=checks,
    )
