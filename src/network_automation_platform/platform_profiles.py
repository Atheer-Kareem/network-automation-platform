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
            "wan": "FastEthernet0/0",
            "lan": "FastEthernet1/0",
        }
    ),
}


SWITCH_PLATFORM_PROFILES = {
    "cisco_iosv_l2": SwitchPlatformProfile(
        interface_map={
            "uplink": "GigabitEthernet0/0",
            "users_access": "GigabitEthernet0/1",
        },
        trunk_encapsulation="dot1q",
        disable_ip_routing=True,
    ),
}
