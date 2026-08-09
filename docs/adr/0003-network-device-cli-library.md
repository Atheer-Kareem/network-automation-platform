# ADR-0003: Use Scrapli for V1 Network Device CLI Access

## Status

Accepted

## Context

V1 of the Network Automation Platform requires read-only operational state
collection, pre-change validation, controlled deployment, and post-change
validation against network devices.

The platform requires a network CLI library that can:

- support Cisco IOS-class devices used by the representative V1 lab
- execute operational commands reliably
- support configuration workflows later in V1
- expose useful failure information
- integrate cleanly behind platform-owned interfaces
- remain testable without requiring live devices
- provide a reasonable path toward concurrent device operations later

The application architecture must not depend directly on GNS3 or any other
specific lab environment.

## Decision

V1 will use Scrapli for network device CLI access.

The initial implementation will use Scrapli's synchronous drivers.

Scrapli will be isolated behind platform-owned connection and collection
interfaces. Core domain and validation logic must not depend directly on
Scrapli response objects.

Read-only device state collection will be implemented before configuration
deployment.

Structured operational state will be represented using platform-owned models.

## Rationale

Scrapli provides:

- synchronous network drivers suitable for the initial V1 workflow
- an asynchronous API that provides a future path for concurrent operations
- structured response objects with explicit command success/failure state
- support for structured parsing integrations
- clear separation between transport/session behaviour and application logic

Using synchronous operation initially keeps V1 simple while preserving a path
toward concurrency when scale requires it.

Keeping Scrapli behind platform-owned interfaces prevents the transport
library from becoming part of the domain model.

## Alternatives Considered

### Netmiko

Netmiko is mature, widely adopted, and supports a broad range of network
platforms.

It would also be a valid choice for V1.

Scrapli was selected because its response model and sync/async architecture
fit the platform's planned state-collection and future concurrency model well.

### Direct Paramiko Usage

Rejected because the platform should not implement low-level network CLI
session handling that mature network automation libraries already provide.

## Consequences

### Positive

- clean network CLI abstraction
- straightforward read-only state collection
- explicit command response and failure handling
- future async path without redesigning the platform architecture
- no dependency on a specific lab environment

### Negative

- introduces an external runtime dependency
- platform-specific driver behaviour still requires testing
- structured parsing requires an additional design decision
- developers must understand both the platform abstraction and Scrapli

## Future Review

Revisit this decision if:

- V1 device support expands significantly
- Scrapli lacks required platform capabilities
- concurrency requirements materially change
- API-driven platforms replace CLI-driven workflows
