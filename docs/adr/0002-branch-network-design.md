# ADR-0002: Use a Minimal Standard Branch Topology for V1

## Status

Accepted

## Context

The long-term platform must support realistic enterprise branch environments.

Introducing redundancy, multiple WAN providers, firewalls, SD-WAN, advanced security controls, and multiple vendors in the first implementation would significantly increase lab and automation complexity before the core workflow has been validated.

## Decision

V1 will use a minimal standard branch containing:

- one branch router
- one branch switch
- user VLAN
- voice VLAN
- management VLAN
- upstream connectivity
- OSPF routing

The branch model will remain data-driven so later enhancements can be introduced without replacing the underlying automation architecture.

## Rationale

The initial topology is sufficiently realistic to demonstrate:

- device inventory
- network intent
- configuration generation
- routing
- switching
- validation
- controlled deployment
- multi-device automation

while keeping the first implementation small enough to test repeatedly.

## Consequences

### Positive

- fast feedback during development
- lower lab resource requirements
- simpler failure analysis
- easier automation testing
- clear baseline for later expansion

### Negative

- V1 does not demonstrate branch redundancy
- WAN resiliency is limited
- advanced security controls are deferred

## Future Review

The branch topology should be expanded after the initial deployment workflow is stable and testable.
