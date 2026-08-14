import argparse
import sys
from pathlib import Path

from network_automation_platform.branch_validation import (
    BranchValidationError,
    validate_branch,
)
from network_automation_platform.collectors.cisco_ios import (
    StateCollectionError,
)
from network_automation_platform.connection_settings import (
    ConnectionSettingsError,
    load_connection_settings,
)
from network_automation_platform.inventory import load_device_inventory
from network_automation_platform.validation_expectations import (
    ValidationExpectationError,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nap",
        description="Network Automation Platform",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate live branch state against desired state",
    )
    validate_parser.add_argument(
        "branch",
        help="Branch identifier, for example branch-01",
    )

    return parser


def run_validate(branch_id: str) -> int:
    intent_path = Path("intent/branches") / f"{branch_id}.yaml"
    inventory_path = Path("inventory/lab.yaml")

    try:
        inventory = load_device_inventory(inventory_path)
        settings = load_connection_settings()

        result = validate_branch(
            branch_id,
            intent_path=intent_path,
            inventory=inventory,
            settings=settings,
        )
    except (
        FileNotFoundError,
        BranchValidationError,
        ConnectionSettingsError,
        StateCollectionError,
        ValidationExpectationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Branch: {result.branch_id}")
    print()

    for device in result.devices:
        status = "PASS" if device.report.passed else "FAIL"

        print(f"{device.hostname}: {status}")

        for check in device.report.checks:
            print(
                f"  [{check.status.value.upper()}] "
                f"{check.name}: {check.message}"
            )

        print()

    if result.passed:
        print("RESULT: COMPLIANT")
        return 0

    print("RESULT: DRIFT DETECTED")
    return 1


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "validate":
        raise SystemExit(run_validate(args.branch))