# ADR-0001: Start with a Modular Single Repository

## Status

Accepted

## Context

The Network Automation Platform will eventually contain multiple concerns including:

- network automation
- network intent
- lab integration
- infrastructure provisioning
- CI/CD
- observability
- AI-assisted operations

Creating separate repositories for each concern immediately would introduce operational and architectural overhead before stable boundaries and independent lifecycles have emerged.

## Decision

V1 will use a modular single repository.

Components will maintain clear internal boundaries so they can be extracted into independent repositories later if ownership, deployment, security, or release requirements justify separation.

Repository boundaries will follow domain ownership and lifecycle boundaries rather than programming language or tool choice.

## Consequences

### Positive

- faster initial development
- simpler CI/CD
- easier refactoring while architecture evolves
- easier end-to-end testing
- less repository-management overhead

### Negative

- repository responsibilities may broaden over time
- access-control boundaries are less granular
- future extraction may require migration work

## Future Review

This decision should be revisited when a component develops a genuinely independent:

- deployment lifecycle
- release cadence
- ownership model
- security boundary
- access-control requirement
