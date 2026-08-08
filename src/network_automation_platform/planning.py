from ipaddress import IPv4Interface

from network_automation_platform.desired_state import (
    BranchDesiredState,
    DeviceDesiredState,
    InterfaceDesiredState,
    OspfDesiredState,
    VlanDesiredState,
)
from network_automation_platform.models import BranchIntent


def build_branch_desired_state(intent: BranchIntent) -> BranchDesiredState:
    router = DeviceDesiredState(
        hostname=intent.device_roles.router.hostname,
        role="branch_router",
        platform=intent.device_roles.router.platform,
        interfaces=[
            InterfaceDesiredState(
                name="lan",
                description="Branch LAN trunk",
            ),
            InterfaceDesiredState(
                name="wan",
                description="WAN transit",
                ipv4=IPv4Interface(
                    f"{intent.wan.transit_prefix.network_address + 1}/"
                    f"{intent.wan.transit_prefix.prefixlen}"
                ),
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
    )

    return BranchDesiredState(
        branch_id=intent.site.id,
        devices=[router, switch],
    )