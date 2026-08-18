# ADR-0003: Use Scrapli for V1 Network Device CLI Access

## Status

Accepted

## Context

V1 of the Network Automation Platform requires read-only operational state collection, pre-change validation, controlled deployment, and post-change validation against network devices.

The platform requires a network CLI library that can:

- support Cisco IOS-class devices used by the representative V1 lab;
- execute operational commands reliably;
- support controlled configuration workflows;
- expose useful failure information;
- integrate cleanly behind platform-owned interfaces;
- remain testable without requiring live devices; and
- provide a reasonable path toward concurrent device operations later.

The application architecture must not depend directly on CML, GNS3, EVE-NG, or any other specific lab environment.

The V1.5 product direction adds one Cisco IOS XE NETCONF path while retaining broader alternative device-automation technologies as separate engineering or learning work.

These technologies serve different learning and architectural purposes and do not automatically replace the V1 CLI transport decision.

## Decision

V1 will use Scrapli for network device CLI access.

The initial implementation uses Scrapli's synchronous drivers.

Scrapli is isolated behind platform-owned connection, state-collection, and configuration-execution boundaries.

Core domain, validation, remediation, and orchestration logic must not depend directly on Scrapli response objects.

Structured operational state is represented using platform-owned models.

Configuration writes continue through platform-owned deployment interfaces rather than allowing higher-level orchestration or CLI code to interact directly with Scrapli.

The introduction of additional automation mechanisms in V1.5 does not change Scrapli's role as the primary V1 CLI implementation.

## Rationale

Scrapli provides:

- synchronous network drivers suitable for the current V1 workflow;
- an asynchronous API that provides a future path toward concurrent operations;
- structured response objects with explicit command success and failure state;
- support for structured parsing integrations;
- clear separation between transport/session behavior and application logic; and
- a clean fit behind the platform's existing state-provider and deployment-executor abstractions.

Using synchronous operation initially keeps V1 simple while preserving a path toward concurrency when scale requires it.

Keeping Scrapli behind platform-owned interfaces prevents the transport library from becoming part of the domain model.

This separation provides useful adapter seams, although V1 branch workflows still require an explicit shared composition boundary before multiple access mechanisms can be selected consistently.

For example:

```text
platform-owned state / execution interfaces
        │
        ├── Cisco CLI
        │      ↓
        │    Scrapli
        │
        ├── NETCONF
        │      ↓
        │    ncclient
        │
        └── future justified mechanism
```

The exact implementation boundaries may evolve, but the core platform should remain independent from any individual transport library.

## Relationship to the V1.5 Roadmap

V1.5 adds NETCONF as the sole required production model-driven write protocol while broader technologies remain separate engineering or learning work in the same repository.

### Netmiko

Netmiko may be practiced as an alternative network CLI automation library.

This provides experience with another widely adopted implementation and allows comparison of:

- connection handling;
- command execution;
- configuration workflows;
- failure behavior;
- parsing patterns; and
- operational ergonomics.

Netmiko practice does not require replacing Scrapli in the flagship platform.

A replacement would require a separate architectural reason rather than certification or technology exposure alone.

### ncclient

`ncclient` is not a competing CLI library.

It will be used for NETCONF automation and therefore represents a different device-management interface.

Practical work will include:

- capability discovery;
- datastore interaction;
- filtered retrieval;
- configuration retrieval;
- `edit-config`;
- XML payloads;
- RPC handling; and
- NETCONF error diagnosis.

V1.5 will introduce a bounded NETCONF adapter behind platform-owned interfaces. The concrete IOS XE model and execution artifact remain evidence-driven decisions.

### RESTCONF

RESTCONF provides another standards-based device-management interface.

RESTCONF may be used for practical IOS XE automation involving:

- YANG-derived resource paths;
- JSON payloads;
- operational-state retrieval;
- configuration changes;
- authentication;
- HTTP status handling; and
- error processing.

A RESTCONF adapter may be integrated into the flagship platform only when a distinct engineering requirement justifies it.

RESTCONF should not be added merely to duplicate working CLI functionality without architectural purpose.

### YANG

YANG provides the data-model foundation for NETCONF and RESTCONF work.

It is therefore conceptually different from the CLI access decision made by this ADR.

The NETCONF implementation requires focused YANG model inspection. Broader practical work may develop understanding of:

- native Cisco models;
- IETF models;
- OpenConfig models;
- model trees;
- paths;
- configuration versus operational data; and
- JSON/XML payload construction.

## Alternatives Considered

### Netmiko as the Primary V1 CLI Library

Netmiko is mature, widely adopted, and supports a broad range of network platforms.

It would also have been a valid choice for V1.

Scrapli was selected because its response model and synchronous/asynchronous architecture fit the planned state-collection and future concurrency model well.

Netmiko remains valuable as an alternative implementation for V1.5 practical work and comparison.

### Direct Paramiko Usage

Rejected because the platform should not implement low-level network CLI session handling that mature network automation libraries already provide.

### NETCONF as the Initial V1 Device Interface

Deferred rather than rejected.

NETCONF provides structured model-driven configuration and operational-state access, but introducing it as the initial implementation would have increased V1 complexity before the core automation lifecycle was proven.

NETCONF becomes appropriate during V1.5 after the CLI-based platform architecture has been validated.

### RESTCONF as the Initial V1 Device Interface

Deferred rather than rejected.

RESTCONF provides standards-based HTTP access to YANG-modeled data and is useful for IOS XE automation.

Production RESTCONF integration remains deferred unless a later engineering requirement justifies it; practical RESTCONF work may proceed independently.

### Direct Device API or Transport Logic in Core Services

Rejected.

Core planning, validation, remediation, and deployment orchestration should not depend directly on any particular transport implementation.

## Consequences

### Positive

- clean network CLI abstraction;
- straightforward operational-state collection;
- explicit command response and failure handling;
- controlled configuration execution;
- future asynchronous path without redesigning the platform architecture;
- no dependency on a specific lab environment;
- core domain logic remains independent from Scrapli;
- alternative interfaces can be added behind platform-owned boundaries;
- V1.5 can introduce NETCONF without rewriting the V1 CLI path; and
- different automation approaches can be compared using the same network problem domain.

### Negative

- Scrapli remains an external runtime dependency;
- platform-specific driver behavior still requires testing;
- developers must understand both platform abstractions and the underlying implementation;
- introducing additional device-management mechanisms increases testing requirements;
- Netmiko exercises may intentionally duplicate some CLI behavior for learning and comparison; and
- multiple transports may eventually require clearer capability and adapter selection logic.

## Architectural Boundary

The intended dependency direction is:

```text
domain / desired state
        ↓
validation / remediation
        ↓
deployment and state abstractions
        ↓
vendor / transport adapter
        ↓
Scrapli | NETCONF | RESTCONF | future mechanism
        ↓
network device
```

The reverse dependency is not allowed.

Transport-specific objects and behavior must not leak upward into domain models merely for implementation convenience.

## Future Review

Revisit this decision if:

- V1 device support expands significantly;
- Scrapli lacks required CLI capabilities;
- concurrency requirements materially change;
- asynchronous execution becomes necessary;
- NETCONF or RESTCONF becomes the preferred operational interface for a supported platform;
- controller-driven automation replaces direct device interaction for a major workflow;
- supporting multiple transports requires a more explicit capability-selection architecture; or
- operational evidence demonstrates that a different CLI library provides a material platform advantage.

Practicing another library or protocol by itself is not sufficient reason to replace Scrapli.

Any replacement of the primary CLI implementation should be based on platform requirements and recorded as a separate architectural decision.
