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

The automation platform must treat the execution environment as an implementation detail.

Examples may include:

- GNS3
- EVE-NG
- Cisco development sandboxes
- physical lab equipment
- cloud-hosted virtual appliances

## Initial Branch Pattern

Each branch is expected to contain, conceptually:

- WAN connectivity
- branch routing
- LAN switching
- user network
- voice network
- management network
- routing toward headquarters or data-centre services

The exact implementation will be defined in a later architecture increment.
