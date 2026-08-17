from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from network_automation_platform.models import BranchIntent, load_branch_intent


def load_raw_branch_intent() -> dict[str, Any]:
    with Path("intent/branches/branch-01.yaml").open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def test_branch_01_intent_is_valid() -> None:
    intent = load_branch_intent(Path("intent/branches/branch-01.yaml"))

    assert str(intent.routing.neighbor_address) == "10.101.255.2"


@pytest.mark.parametrize(
    "neighbor_address",
    [
        pytest.param("10.101.255.0", id="network-address"),
        pytest.param("10.101.255.3", id="broadcast-address"),
    ],
)
def test_ospf_neighbor_must_be_usable_wan_endpoint(
    neighbor_address: str,
) -> None:
    raw_intent = load_raw_branch_intent()
    raw_intent["routing"]["neighbor_address"] = neighbor_address

    with pytest.raises(
        ValidationError,
        match="OSPF neighbor address.*is not a usable endpoint",
    ):
        BranchIntent.model_validate(raw_intent)


def test_wan_transit_network_allows_both_31_endpoints() -> None:
    raw_intent = load_raw_branch_intent()
    raw_intent["wan"]["transit_prefix"] = "10.101.255.0/31"
    raw_intent["routing"]["neighbor_address"] = "10.101.255.0"

    intent = BranchIntent.model_validate(raw_intent)

    assert str(intent.routing.neighbor_address) == "10.101.255.0"


def test_ospf_neighbor_outside_wan_transit_network_is_rejected() -> None:
    raw_intent = load_raw_branch_intent()
    raw_intent["routing"]["neighbor_address"] = "10.102.255.2"

    with pytest.raises(
        ValidationError,
        match="OSPF neighbor address.*is not within WAN transit network",
    ):
        BranchIntent.model_validate(raw_intent)


def test_ospf_neighbor_cannot_be_router_wan_address() -> None:
    raw_intent = load_raw_branch_intent()
    raw_intent["routing"]["neighbor_address"] = "10.101.255.1"

    with pytest.raises(
        ValidationError,
        match="cannot be the branch router WAN address",
    ):
        BranchIntent.model_validate(raw_intent)


def test_wan_transit_network_requires_distinct_endpoints() -> None:
    raw_intent = load_raw_branch_intent()
    raw_intent["wan"]["transit_prefix"] = "10.101.255.1/32"
    raw_intent["routing"]["neighbor_address"] = "10.101.255.1"

    with pytest.raises(
        ValidationError,
        match="cannot provide distinct branch-router and OSPF neighbor",
    ):
        BranchIntent.model_validate(raw_intent)


def test_vlan_id_above_valid_range_is_rejected() -> None:
    raw_intent = load_raw_branch_intent()
    raw_intent["networks"]["users"]["vlan_id"] = 5000

    with pytest.raises(ValidationError):
        BranchIntent.model_validate(raw_intent)


def test_invalid_routing_protocol_is_rejected() -> None:
    raw_intent = load_raw_branch_intent()
    raw_intent["routing"]["protocol"] = "rip"

    with pytest.raises(ValidationError):
        BranchIntent.model_validate(raw_intent)


def test_management_ip_outside_management_network_is_rejected() -> None:
    raw_intent = load_raw_branch_intent()
    raw_intent["device_roles"]["router"]["management_ip"] = "10.200.1.10"

    with pytest.raises(
        ValidationError,
        match="management IP.*is not within",
    ):
        BranchIntent.model_validate(raw_intent)
