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
    load_branch_intent(Path("intent/branches/branch-01.yaml"))

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
   