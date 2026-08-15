import argparse
import sys
from pathlib import Path

from network_automation_platform.branch_deployment import (
    BranchDeviceDeploymentStatus,
    deploy_branch,
)
from network_automation_platform.branch_plan import plan_branch
from network_automation_platform.branch_validation import (
    validate_branch,
)
from network_automation_platform.collectors.cisco_ios import (
    StateCollectionError,
)
from network_automation_platform.connection_settings import (
    ConnectionSettingsError,
    load_connection_settings,
)
from network_automation_platform.deployment import DeploymentStatus
from network_automation_platform.device_resolution import (
    DeviceResolutionError,
)
from network_automation_platform.inventory import load_device_inventory
from network_automation_platform.ssh_config import SshConfigError
from network_automation_platform.ssh_config_writer import (
    write_ssh_config,
)
from network_automation_platform.validation import ValidationStatus
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

    plan_parser = subparsers.add_parser(
        "plan",
        help="Show branch drift and desired candidate configuration",
    )
    plan_parser.add_argument(
        "branch",
        help="Branch identifier, for example branch-01",
    )

    inventory_parser = subparsers.add_parser(
        "inventory",
        help="Manage inventory-derived artifacts",
    )

    inventory_subparsers = inventory_parser.add_subparsers(
        dest="inventory_command",
        required=True,
    )

    inventory_subparsers.add_parser(
        "render-ssh-config",
        help="Render SSH configuration from lab inventory",
    )

    deploy_parser = subparsers.add_parser(
        "deploy",
        help="Apply supported targeted branch remediation",
    )

    deploy_parser.add_argument(
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
        ConnectionSettingsError,
        StateCollectionError,
        DeviceResolutionError,
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

def run_plan(branch_id: str) -> int:
    intent_path = Path("intent/branches") / f"{branch_id}.yaml"
    inventory_path = Path("inventory/lab.yaml")

    try:
        inventory = load_device_inventory(inventory_path)
        settings = load_connection_settings()

        result = plan_branch(
            branch_id,
            intent_path=intent_path,
            inventory=inventory,
            settings=settings,
        )
    except (
        FileNotFoundError,
        DeviceResolutionError,
        ConnectionSettingsError,
        StateCollectionError,
        ValidationExpectationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Branch: {result.branch_id}")
    print()

    for device in result.devices:
        status = (
            "DRIFT"
            if not device.validation.passed
            else "COMPLIANT"
        )

        print(f"{device.hostname}: {status}")

        failed_checks = [
            check
            for check in device.validation.checks
            if check.status == ValidationStatus.FAIL
        ]

        if failed_checks:
            print()
            print("Drift:")
            for check in failed_checks:
                print(f"  - {check.message}")

        if not device.validation.passed:
            print()
            print("Targeted remediation:")

            if device.remediation_commands:
                for command in device.remediation_commands:
                    print(f"  {command}")
            else:
                print(
                    "  No supported targeted remediation available."
                )

        print()
        print("Candidate configuration:")
        print("------------------------")
        print(device.candidate_config)
        print("------------------------")
        print()

    if result.has_drift:
        print("RESULT: DRIFT DETECTED")
        return 1

    print("RESULT: NO DRIFT")
    return 0

def run_render_ssh_config() -> int:
    inventory_path = Path("inventory/lab.yaml")
    output_path = Path("inventory/ssh/lab_config")

    try:
        write_ssh_config(
            inventory_path,
            output_path,
        )
    except (
        FileNotFoundError,
        SshConfigError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Generated: {output_path}")
    return 0

def confirm_deployment(
    hostname: str,
    commands: list[str],
) -> bool:
    print()
    print(f"Device: {hostname}")
    print("Targeted remediation:")
    print("---------------------")

    for command in commands:
        print(f"  {command}")

    print("---------------------")

    response = input(
        "Apply this change? [y/N]: "
    ).strip().lower()

    return response in {"y", "yes"}

def run_deploy(branch_id: str) -> int:
    intent_path = Path("intent/branches") / f"{branch_id}.yaml"
    inventory_path = Path("inventory/lab.yaml")

    try:
        inventory = load_device_inventory(
            inventory_path
        )
        settings = load_connection_settings()

        result = deploy_branch(
            branch_id,
            intent_path=intent_path,
            inventory=inventory,
            settings=settings,
            approve=confirm_deployment,
        )
    except (
        FileNotFoundError,
        DeviceResolutionError,
        ConnectionSettingsError,
        StateCollectionError,
        ValidationExpectationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print()
    print(f"Branch: {result.branch_id}")
    print()

    failed = False

    for device in result.devices:
        print(
            f"{device.hostname}: "
            f"{device.status.value.upper()}"
        )

        print(f"  {device.message}")

        if device.deployment is not None:
            print(
                "  Deployment status: "
                f"{device.deployment.status.value.upper()}"
            )

            if (
                device.deployment.status
                != DeploymentStatus.SUCCEEDED
            ):
                failed = True

        if (
            device.status
            == BranchDeviceDeploymentStatus.BLOCKED
        ):
            failed = True

    if failed:
        print()
        print("RESULT: DEPLOYMENT NOT COMPLETED")
        return 1

    print()
    print("RESULT: DEPLOYMENT WORKFLOW COMPLETED")
    return 0

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "validate":
        raise SystemExit(run_validate(args.branch))

    if args.command == "plan":
        raise SystemExit(run_plan(args.branch))

    if (
        args.command == "inventory"
        and args.inventory_command == "render-ssh-config"
    ):
        raise SystemExit(run_render_ssh_config())
    if args.command == "deploy":
        raise SystemExit(
            run_deploy(args.branch)
        )

