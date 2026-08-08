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
                  WAN / HQ
                     |
               Branch Router
                     |
               Branch Switch
               /     |      \
            Users  Voice   Management
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

The addressing model must not be hard-coded into platform business logic. A future source-of-truth implementation, such as NetBox IPAM, will replace deterministic local allocation with centrally managed prefix allocation.
