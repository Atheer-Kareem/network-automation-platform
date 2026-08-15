from unittest.mock import MagicMock, patch

from network_automation_platform.branch_plan import (
    BranchPlanResult,
    DevicePlanResult,
)
from network_automation_platform.branch_validation import (
    BranchValidationResult,
    DeviceValidationResult,
)
from network_automation_platform.cli import (
    build_parser,
    confirm_deployment,
    run_plan,
    run_render_ssh_config,
    run_validate,
)
from network_automation_platform.connection_settings import (
    ConnectionSettingsError,
)
from network_automation_platform.validation import (
    ValidationCheck,
    ValidationReport,
    ValidationStatus,
)


def test_build_parser_parses_validate_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "validate",
            "branch-01",
        ]
    )

    assert args.command == "validate"
    assert args.branch == "branch-01"

def test_run_validate_returns_zero_when_branch_is_compliant(
    capsys,
) -> None:
    result = BranchValidationResult(
        branch_id="branch-01",
        devices=[
            DeviceValidationResult(
                hostname="br01-rtr01",
                report=ValidationReport(
                    hostname="br01-rtr01",
                    checks=[
                        ValidationCheck(
                            name="interface:GigabitEthernet0/1",
                            status=ValidationStatus.PASS,
                            message="Interface matches expectation",
                        )
                    ],
                ),
            )
        ],
    )

    with (
        patch(
            "network_automation_platform.cli.load_device_inventory",
            return_value=MagicMock(),
        ),
        patch(
            "network_automation_platform.cli.load_connection_settings",
            return_value=MagicMock(),
        ),
        patch(
            "network_automation_platform.cli.validate_branch",
            return_value=result,
        ),
    ):
        exit_code = run_validate("branch-01")

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "br01-rtr01: PASS" in output
    assert "RESULT: COMPLIANT" in output
    assert "Targeted remediation:" not in output

def test_run_validate_returns_one_when_drift_is_detected(
    capsys,
) -> None:
    result = BranchValidationResult(
        branch_id="branch-01",
        devices=[
            DeviceValidationResult(
                hostname="br01-sw01",
                report=ValidationReport(
                    hostname="br01-sw01",
                    checks=[
                        ValidationCheck(
                            name="interface:Vlan99",
                            status=ValidationStatus.FAIL,
                            message="Interface Vlan99 is missing",
                        )
                    ],
                ),
            )
        ],
    )

    with (
        patch(
            "network_automation_platform.cli.load_device_inventory",
            return_value=MagicMock(),
        ),
        patch(
            "network_automation_platform.cli.load_connection_settings",
            return_value=MagicMock(),
        ),
        patch(
            "network_automation_platform.cli.validate_branch",
            return_value=result,
        ),
    ):
        exit_code = run_validate("branch-01")

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "br01-sw01: FAIL" in output
    assert "Interface Vlan99 is missing" in output
    assert "RESULT: DRIFT DETECTED" in output

def test_run_validate_returns_two_on_application_error(
    capsys,
) -> None:
    with (
        patch(
            "network_automation_platform.cli.load_device_inventory",
            return_value=MagicMock(),
        ),
        patch(
            "network_automation_platform.cli.load_connection_settings",
            side_effect=ConnectionSettingsError(
                "Missing required connection settings: "
                "NAP_DEVICE_USERNAME"
            ),
        ),
    ):
        exit_code = run_validate("branch-01")

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "ERROR: Missing required connection settings: "
        "NAP_DEVICE_USERNAME"
        in captured.err
    )

def test_build_parser_parses_plan_command() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "plan",
            "branch-01",
        ]
    )

    assert args.command == "plan"
    assert args.branch == "branch-01"

def test_run_plan_returns_zero_when_no_drift(
    capsys,
) -> None:
    result = BranchPlanResult(
        branch_id="branch-01",
        devices=[
            DevicePlanResult(
                hostname="br01-rtr01",
                candidate_config="hostname br01-rtr01",
                validation=ValidationReport(
                    hostname="br01-rtr01",
                    checks=[
                        ValidationCheck(
                            name="router-check",
                            status=ValidationStatus.PASS,
                            message="Router matches expectation",
                        )
                    ],
                ),
                remediation_commands=[],
            )
        ],
    )

    with (
        patch(
            "network_automation_platform.cli."
            "load_device_inventory"
        ),
        patch(
            "network_automation_platform.cli."
            "load_connection_settings"
        ),
        patch(
            "network_automation_platform.cli.plan_branch",
            return_value=result,
        ),
    ):
        exit_code = run_plan("branch-01")

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "br01-rtr01: COMPLIANT" in output
    assert "Targeted remediation:" not in output
    assert "Candidate configuration:" in output
    assert "RESULT: NO DRIFT" in output

def test_run_plan_returns_one_when_drift_is_detected(
    capsys,
) -> None:
    result = BranchPlanResult(
        branch_id="branch-01",
        devices=[
            DevicePlanResult(
                hostname="br01-sw01",
                candidate_config="hostname br01-sw01",
                validation=ValidationReport(
                    hostname="br01-sw01",
                    checks=[
                        ValidationCheck(
                            name="interface:Vlan99",
                            status=ValidationStatus.FAIL,
                            message="Interface Vlan99 is missing",
                        )
                    ],
                ),
                remediation_commands=[
                    "interface Vlan99",
                    "description Switch management SVI",
                    "ip address 10.101.99.21 255.255.255.0",
                    "no shutdown",
                ]
            )
        ],
    )

    with (
        patch(
            "network_automation_platform.cli.load_device_inventory",
            return_value=MagicMock(),
        ),
        patch(
            "network_automation_platform.cli.load_connection_settings",
            return_value=MagicMock(),
        ),
        patch(
            "network_automation_platform.cli.plan_branch",
            return_value=result,
        ),
    ):
        exit_code = run_plan("branch-01")

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "br01-sw01: DRIFT" in output
    assert "Interface Vlan99 is missing" in output
    assert "hostname br01-sw01" in output
    assert "RESULT: DRIFT DETECTED" in output
    assert "Targeted remediation:" in output
    assert "interface Vlan99" in output
    assert "description Switch management SVI" in output
    assert (
        "ip address 10.101.99.21 255.255.255.0"
        in output
    )
    assert "no shutdown" in output

def test_run_plan_returns_two_on_application_error(
    capsys,
) -> None:
    with (
        patch(
            "network_automation_platform.cli.load_device_inventory",
            return_value=MagicMock(),
        ),
        patch(
            "network_automation_platform.cli.load_connection_settings",
            side_effect=ConnectionSettingsError(
                "Missing required connection settings: "
                "NAP_DEVICE_USERNAME"
            ),
        ),
    ):
        exit_code = run_plan("branch-01")

    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert (
        "ERROR: Missing required connection settings: "
        "NAP_DEVICE_USERNAME"
        in captured.err
    )

def test_build_parser_parses_inventory_render_ssh_config() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "inventory",
            "render-ssh-config",
        ]
    )

    assert args.command == "inventory"
    assert args.inventory_command == "render-ssh-config"

def test_run_render_ssh_config_returns_zero(
    capsys,
) -> None:
    with patch(
        "network_automation_platform.cli.write_ssh_config"
    ) as write_mock:
        exit_code = run_render_ssh_config()

    output = capsys.readouterr().out

    assert exit_code == 0
    assert write_mock.call_count == 1
    assert "Generated: inventory/ssh/lab_config" in output

def test_run_plan_reports_unsupported_remediation(
    capsys,
) -> None:
    result = BranchPlanResult(
        branch_id="branch-01",
        devices=[
            DevicePlanResult(
                hostname="br01-sw01",
                candidate_config="hostname br01-sw01",
                validation=ValidationReport(
                    hostname="br01-sw01",
                    checks=[
                        ValidationCheck(
                            name="vlan:99",
                            status=ValidationStatus.FAIL,
                            message="VLAN 99 is missing",
                        )
                    ],
                ),
                remediation_commands=[],
            )
        ],
    )

    with (
        patch(
            "network_automation_platform.cli."
            "load_device_inventory"
        ),
        patch(
            "network_automation_platform.cli."
            "load_connection_settings"
        ),
        patch(
            "network_automation_platform.cli.plan_branch",
            return_value=result,
        ),
    ):
        exit_code = run_plan("branch-01")

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "DRIFT" in output
    assert "VLAN 99 is missing" in output
    assert "Targeted remediation:" in output
    assert (
        "No supported targeted remediation available."
        in output
    )

def test_confirm_deployment_accepts_yes() -> None:
    with patch(
        "builtins.input",
        return_value="y",
    ):
        approved = confirm_deployment(
            "br01-sw01",
            ["interface Vlan99"],
        )

    assert approved is True

def test_confirm_deployment_defaults_to_no() -> None:
    with patch(
        "builtins.input",
        return_value="",
    ):
        approved = confirm_deployment(
            "br01-sw01",
            ["interface Vlan99"],
        )

    assert approved is False