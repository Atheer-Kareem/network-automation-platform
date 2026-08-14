from unittest.mock import MagicMock, patch

from network_automation_platform.branch_validation import (
    BranchValidationResult,
    DeviceValidationResult,
)
from network_automation_platform.cli import (
    build_parser,
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