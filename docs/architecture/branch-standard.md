# Branch Network Standard

## Purpose

This document defines the standard network design for branch locations managed by the Network Automation Platform.

The design provides a repeatable baseline that can be instantiated across multiple branch sites while allowing site-specific addressing and device metadata to be supplied through structured intent data.

## Design Goals

The branch standard should:

- provide consistent network segmentation
- support repeatable branch deployment
- minimize device-specific configuration logic
- support automated validation
- support future multi-vendor implementations
- separate business intent from platform-specific configuration
- provide a clear path for future redundancy and security enhancements

## Initial Branch Topology

The initial representative branch uses:

```text
                        WAN / Core
                           |
                     Branch Router
                           |
                    802.1Q Trunk
                           |
                     Branch Switch
                    /       |       \
                 Users    Voice   Management
                VLAN 10  VLAN 20    VLAN 99
```

### V1 Addressing Convention

V1 uses a human-readable site addressing convention to simplify troubleshooting, validation, and early automation development.

Each branch receives a dedicated `/16` block derived from its site identifier.

Examples:

| Site      | Site Prefix     |
| --------- | --------------- |
| Branch 01 | `10.101.0.0/16` |
| Branch 02 | `10.102.0.0/16` |
| Branch 03 | `10.103.0.0/16` |

Standard branch subnets are derived consistently:

| Purpose       | Pattern           |
| ------------- | ----------------- |
| Users         | `10.10X.10.0/24`  |
| Voice         | `10.10X.20.0/24`  |
| Management    | `10.10X.99.0/24`  |
| WAN / Transit | `10.10X.255.0/30` |

This convention is intentionally simple for V1.

The addressing model must not be hard-coded into platform business logic. A future source-of-truth implementation, such as an IPAM or network source-of-truth platform, may replace deterministic local allocation with centrally managed prefix allocation when that provides sufficient architectural and operational value.

## Standard VLAN Roles

V1 defines three standard branch VLANs:

| VLAN | Purpose    | Standard Subnet Pattern |
| ---- | ---------- | ----------------------- |
| 10   | Users      | `10.10X.10.0/24`        |
| 20   | Voice      | `10.10X.20.0/24`        |
| 99   | Management | `10.10X.99.0/24`        |

The branch router provides the default gateway for each VLAN using router-on-a-stick subinterfaces.

The branch switch provides Layer 2 access and carries all branch VLANs toward the router over an 802.1Q trunk.

## Standard Branch Interface Roles

Logical interface roles are defined independently from platform-specific interface names.

The branch router uses:

- `wan` — WAN or upstream transit
- `lan` — parent interface for the branch VLAN trunk
- user VLAN subinterface
- voice VLAN subinterface
- management VLAN subinterface

The branch switch uses:

- `uplink` — router-facing trunk
- `users_access` — user access port
- `voice_access` — voice access port
- `management_svi` — in-band switch management interface

Platform profiles map these logical roles to the physical or virtual interface names exposed by a specific device platform.

## Branch Switch Standard

The V1 branch switch baseline includes:

- VLAN 10 for users
- VLAN 20 for voice
- VLAN 99 for management
- an 802.1Q uplink trunk carrying VLANs 10, 20, and 99
- a user access port assigned to VLAN 10
- a voice access port assigned to VLAN 20
- a management SVI in VLAN 99
- a default gateway pointing to the branch router management VLAN gateway

For Branch 01, the management SVI is:

`10.101.99.21/24`

and the management default gateway is:

`10.101.99.1`

## Branch Routing Standard

The representative V1 branch uses OSPF for dynamic routing toward upstream infrastructure.

The branch router advertises the branch networks and forms an adjacency across the WAN transit network.

Branch intent explicitly identifies the expected upstream peer by neighbor address. For branch 01 this is `10.101.255.2`; it must belong to the configured WAN transit network and must not be the branch router's derived WAN address.

The vendor-neutral desired state and validation expectation carry that address, the WAN role's mapped physical interface, and the protocol state `FULL`. Peer identity is not inferred from a hard-coded addressing rule.

OSPF adjacency is operational validation only. OSPF router ID is not validated, unexpected additional neighbors are not rejected, and OSPF failures cannot produce remediation. OSPF-learned route outcome validation remains a subsequent V1 increment.

## Management Plane Separation

The branch management VLAN and the automation out-of-band management network serve different purposes.

The branch management VLAN is part of branch intent and carries in-band management traffic within the branch design.

The out-of-band management network is an execution-environment concern used to provide a stable automation control path to lab devices.

Out-of-band addressing must therefore not be derived from branch intent or rendered into branch desired configuration or remediation.

This separation prevents branch configuration changes from unnecessarily modifying the management path used by the automation platform.
