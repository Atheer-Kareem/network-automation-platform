import os
from pathlib import Path

from pydantic import BaseModel, SecretStr


class ConnectionSettings(BaseModel):
    username: str
    password: SecretStr
    ssh_config_file: Path
    ssh_known_hosts_file: Path
    strict_host_key_checking: bool = True

class ConnectionSettingsError(ValueError):
    pass

def load_connection_settings() -> ConnectionSettings:
    username = os.getenv("NAP_DEVICE_USERNAME")
    password = os.getenv("NAP_DEVICE_PASSWORD")
    ssh_config_file = os.getenv("NAP_SSH_CONFIG_FILE")
    ssh_known_hosts_file = os.getenv("NAP_SSH_KNOWN_HOSTS_FILE")

    missing = [
        name
        for name, value in (
            ("NAP_DEVICE_USERNAME", username),
            ("NAP_DEVICE_PASSWORD", password),
            ("NAP_SSH_CONFIG_FILE", ssh_config_file),
            ("NAP_SSH_KNOWN_HOSTS_FILE", ssh_known_hosts_file),
        )
        if not value
    ]

    if missing:
        raise ConnectionSettingsError(
            "Missing required connection settings: "
            + ", ".join(missing)
        )

    return ConnectionSettings(
        username=username,
        password=SecretStr(password),
        ssh_config_file=Path(ssh_config_file),
        ssh_known_hosts_file=Path(ssh_known_hosts_file),
    )
