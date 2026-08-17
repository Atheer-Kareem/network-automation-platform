# Network Model

## Logical Enterprise Model

The platform represents a financial-services organisation with:

- headquarters
- primary data centre
- disaster-recovery capability
- multiple branch locations
- internet connectivity
- cloud connectivity

The logical production estate may contain substantially more devices than are instantiated in a development lab.

## Representative Lab Model

Development and integration environments use representative subsets of the production network.

The automation platform treats the execution environment as an implementation detail rather than an architectural dependency.

Potential execution environments include:

- Cisco Modeling Labs (CML)
- EVE-NG
- Cisco development sandboxes
- physical lab equipment
- cloud-hosted virtual appliances

GNS3 is not used as the representative V1 environment because the required IOSv/IOSvL2 and virtualization characteristics are not a good fit for the current Apple Silicon development environment.

The current representative lab is implemented in Cisco Modeling Labs.

It contains:

- `core01` — IOSv core router
- `br01-rtr01` — IOSv branch router
- `br01-sw01` — IOSvL2 branch switch
- `user01` — user endpoint
- `voice01` — voice endpoint
- a dedicated unmanaged out-of-band management segment
- a CML external connector providing access from the development workstation

The lab topology is representative of the logical production design but is not part of the platform architecture itself.

## Management and Data-Plane Separation

The representative lab separates out-of-band management from branch production traffic.
The authoritative source for lab OOB addressing is `inventory/lab.yaml`.

This document describes the current representative topology but is not a runtime configuration source. Generated SSH configuration is derived from the inventory.
SSH host keys are maintained separately in `inventory/ssh/known_hosts`.
This file represents learned runtime trust state and is not generated from inventory.
It may require refresh when device addresses or device identities change.

The dedicated OOB management network is:

`192.168.4.0/24`

Current OOB addresses are:

- `core01` — `192.168.4.10`
- `br01-rtr01` — `192.168.4.11`
- `br01-sw01` — `192.168.4.12`

On the IOSv and IOSvL2 devices, `GigabitEthernet0/0` is reserved for out-of-band management.

The OOB interface is intentionally excluded from branch desired-state configuration.

This separation allows the platform to validate and modify branch network state without using the same interfaces that carry the automation control connection.

## Representative Branch Pattern

The representative branch contains:

- WAN connectivity
- branch routing
- LAN switching
- user network
- voice network
- management network
- dynamic routing toward core services
- dedicated out-of-band management

The branch data-plane design is:

- WAN transit: `10.101.255.0/30`
- User VLAN 10: `10.101.10.0/24`
- Voice VLAN 20: `10.101.20.0/24`
- Management VLAN 99: `10.101.99.0/24`

`br01-rtr01` provides inter-VLAN routing using router-on-a-stick subinterfaces.

The current IOSv interface mapping is:

- `GigabitEthernet0/0` — OOB management
- `GigabitEthernet0/1` — WAN transit
- `GigabitEthernet0/2` — branch LAN trunk
- `GigabitEthernet0/2.10` — user VLAN gateway
- `GigabitEthernet0/2.20` — voice VLAN gateway
- `GigabitEthernet0/2.99` — management VLAN gateway

The current IOSvL2 switch interface mapping is:

- `GigabitEthernet0/0` — OOB management
- `GigabitEthernet0/1` — router-facing 802.1Q trunk
- `GigabitEthernet0/2` — user access port, VLAN 10
- `GigabitEthernet0/3` — voice access port, VLAN 20
- `Vlan99` — in-band switch management SVI

The router-facing trunk carries VLANs 10, 20, and 99.

The switch management SVI uses:

`10.101.99.21/24`

with the branch router providing the VLAN 99 gateway at:

`10.101.99.1`

## Representative Routing

The branch router forms an OSPF adjacency with `core01` across the WAN transit network.

The representative lab uses OSPF to prove that the branch can exchange routes with upstream infrastructure.

OSPF neighbor state is collected by the platform when the `ospf` state capability is enabled for a device.

The expected peer address is explicit branch intent and is propagated through vendor-neutral desired state. For branch 01 the expected neighbor is `10.101.255.2` on the physical interface mapped from the logical `wan` role, with expected protocol state `FULL`.

Cisco IOS adjacency-role suffixes such as `FULL/DR`, `FULL/BDR`, and `FULL/-` are normalized to `FULL` at the collector boundary, along with IOS interface-name normalization. Generic validation matches the expected neighbor by address and compares its interface and state. It does not validate router ID or reject unexpected additional neighbors in this increment.

Branch intent explicitly requires the upstream prefix `10.200.0.1/32` inside the OSPF routing context. `core01` intentionally originates this representative service route from Loopback0. The protocol is inherited from the parent context, while the expected next hop is derived from the declared neighbor and the outgoing interface from the platform mapping for logical role `wan`.

Validation requires the prefix through OSPF from `10.101.255.2` on `GigabitEthernet0/1`. Additional routes remain permitted, and administrative distance, metric, route subtype, and ECMP cardinality are not validated.

OSPF adjacency and learned-route failures are validation-only, cannot produce targeted remediation, and block deployment before writes. Adjacency live CML acceptance is complete; learned-route outcome implementation is complete but its live CML acceptance remains pending.

## Environment Portability

The current lab uses IOSv and IOSvL2 because they provide a representative Cisco IOS environment in CML.

The platform retains separate platform profiles, including the existing C7200 profile, so logical intent is not tied to a single virtual appliance or lab implementation.

Changing the execution environment should require inventory and platform-profile changes rather than redesigning intent, orchestration, or validation logic.
