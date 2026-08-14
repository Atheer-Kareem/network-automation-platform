from ipaddress import IPv4Interface, IPv4Network

from network_automation_platform.desired_state import (
    BranchDesiredState,
    DeviceDesiredState,
    InterfaceDesiredState,
    OspfDesiredState,
    VlanDesiredState,
)
from network_automation_platform.models import BranchIntent


def _gateway_interface(prefix: IPv4Network) -> IPv4Interface:
    gateway_ip = prefix.network_address + 1
    return IPv4Interface(f"{gateway_ip}/{prefix.prefixlen}")


def build_branch_desired_state(intent: BranchIntent) -> BranchDesiredState:
    router = DeviceDesiredState(
        hostname=intent.device_roles.router.hostname,
        role="branch_router",
        platform=intent.device_roles.router.platform,
        interfaces=[
            InterfaceDesiredState(
                name="wan",
                description="WAN transit",
                ipv4=_gateway_interface(intent.wan.transit_prefix),
            ),
            InterfaceDesiredState(
                name="lan",
                description="Branch LAN trunk",
            ),
            InterfaceDesiredState(
                name="users",
                description="User VLAN gateway",
                parent="lan",
                vlan_id=intent.networks.users.vlan_id,
                ipv4=_gateway_interface(intent.networks.users.prefix),
            ),
            InterfaceDesiredState(
                name="voice",
                description="Voice VLAN gateway",
                parent="lan",
                vlan_id=intent.networks.voice.vlan_id,
                ipv4=_gateway_interface(intent.networks.voice.prefix),
            ),
            InterfaceDesiredState(
                name="management",
                description="Management VLAN gateway",
                parent="lan",
                vlan_id=intent.networks.management.vlan_id,
                ipv4=_gateway_interface(intent.networks.management.prefix),
            ),
        ],
        ospf=OspfDesiredState(
            area=intent.routing.area,
            networks=[
                intent.networks.users.prefix,
                intent.networks.voice.prefix,
                intent.networks.management.prefix,
                intent.wan.transit_prefix,
            ],
        ),
    )

    switch = DeviceDesiredState(
        hostname=intent.device_roles.switch.hostname,
        role="branch_switch",
        platform=intent.device_roles.switch.platform,
        vlans=[
            VlanDesiredState(
                vlan_id=intent.networks.users.vlan_id,
                name="USERS",
            ),
            VlanDesiredState(
                vlan_id=intent.networks.voice.vlan_id,
                name="VOICE",
            ),
            VlanDesiredState(
                vlan_id=intent.networks.management.vlan_id,
                name="MANAGEMENT",
            ),
        ],
        interfaces=[
            InterfaceDesiredState(
                name="uplink",
                description="Uplink to branch router",
                mode="trunk",
                allowed_vlans=[
                    intent.networks.users.vlan_id,
                    intent.networks.voice.vlan_id,
                    intent.networks.management.vlan_id,
                ],
            ),
            InterfaceDesiredState(
                name="users_access",
                description="User access port",
                mode="access",
                access_vlan=intent.networks.users.vlan_id,
            ),
            InterfaceDesiredState(
                name="voice_access",
                description="Voice access port",
                mode="access",
                access_vlan=intent.networks.voice.vlan_id,
            ),
            InterfaceDesiredState(
                name="management_svi",
                description="Switch management SVI",
                vlan_id=intent.networks.management.vlan_id,
                ipv4=IPv4Interface(
                    f"{intent.device_roles.switch.management_ip}/"
                    f"{intent.networks.management.prefix.prefixlen}"
                ),
            ),
        ],
        default_gateway=str(
            intent.networks.management.prefix.network_address + 1
        ),
    )

    return BranchDesiredState(
        branch_id=intent.site.id,
        devices=[router, switch],
    )