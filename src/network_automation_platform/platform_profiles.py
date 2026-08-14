from dataclasses import dataclass


@dataclass(frozen=True)
class RouterPlatformProfile:
    interface_map: dict[str, str]


@dataclass(frozen=True)
class SwitchPlatformProfile:
    interface_map: dict[str, str]
    trunk_encapsulation: str | None = None
    disable_ip_routing: bool = False


ROUTER_PLATFORM_PROFILES = {
    "cisco_ios_c7200": RouterPlatformProfile(
        interface_map={
            "wan": "FastEthernet1/0",
            "lan": "FastEthernet1/1",
        }
    ),
    "cisco_iosv": RouterPlatformProfile(
        interface_map={
            "wan": "GigabitEthernet0/1",
            "lan": "GigabitEthernet0/2",
        }
    ),
}


SWITCH_PLATFORM_PROFILES = {
    "cisco_iosv_l2": SwitchPlatformProfile(
        interface_map={
            "uplink": "GigabitEthernet0/1",
            "users_access": "GigabitEthernet0/2",
            "voice_access": "GigabitEthernet0/3",
        },
        trunk_encapsulation="dot1q",
        disable_ip_routing=True,
    ),
}