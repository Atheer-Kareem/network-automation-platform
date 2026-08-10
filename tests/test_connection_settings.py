from pathlib import Path

import pytest

from network_automation_platform.connection_settings import (
    ConnectionSettingsError,
    load_connection_settings,
)


def test_load_connection_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NAP_DEVICE_USERNAME", "netdevops")
    monkeypatch.setenv("NAP_DEVICE_PASSWORD", "test-password")
    monkeypatch.setenv(
    "NAP_SSH_CONFIG_FILE",
    "inventory/ssh/lab_config",
)
    monkeypatch.setenv(
    "NAP_SSH_KNOWN_HOSTS_FILE",
    "inventory/ssh/known_hosts",
    )

    settings = load_connection_settings()

    assert settings.username == "netdevops"
    assert settings.password.get_secret_value() == "test-password"
    assert settings.ssh_config_file == Path(
        "inventory/ssh/lab_config"
    )
    assert settings.ssh_known_hosts_file == Path(
        "inventory/ssh/known_hosts"
    )
    assert settings.strict_host_key_checking is True


def test_load_connection_settings_rejects_missing_ssh_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NAP_DEVICE_USERNAME", "netdevops")
    monkeypatch.setenv("NAP_DEVICE_PASSWORD", "test-password")
    monkeypatch.delenv("NAP_SSH_CONFIG_FILE", raising=False)
    monkeypatch.delenv(
        "NAP_SSH_KNOWN_HOSTS_FILE",
        raising=False,
    )

    with pytest.raises(
        ConnectionSettingsError,
        match="NAP_SSH_CONFIG_FILE, NAP_SSH_KNOWN_HOSTS_FILE",
    ):
        load_connection_settings()

def test_load_connection_settings_rejects_missing_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NAP_DEVICE_USERNAME", raising=False)
    monkeypatch.delenv("NAP_DEVICE_PASSWORD", raising=False)

    with pytest.raises(
        ConnectionSettingsError,
        match="NAP_DEVICE_USERNAME, NAP_DEVICE_PASSWORD",
    ):
        load_connection_settings()
