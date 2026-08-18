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

The project will use a modular single canonical repository by default.

Components will maintain clear internal boundaries so they can be extracted into independent repositories later if ownership, deployment, security, or release requirements justify separation.

Repository boundaries will follow domain ownership and lifecycle boundaries rather than programming language or tool choice.

## Scope Clarification

This decision applies to production platform components, topology and environment assets, maintained integrations, documentation, and related practical learning work.

Practical work does not become part of the production Python package merely because it shares the repository. Production and learning areas must preserve explicit ownership, dependency, CI, secret/trust-state, support, and device-write boundaries.

A separate repository is justified only by a genuine independent ownership, deployment, security, access-control, lifecycle, licensing, or release-cadence boundary. Technology comparison, certification alignment, or use of a different tool is not sufficient by itself.

## Consequences

### Positive

- faster initial development
- simpler CI/CD
- easier refactoring while architecture evolves
- easier end-to-end testing
- less repository-management overhead
- one discoverable home for production and related practical evidence

### Negative

- repository responsibilities may broaden over time
- access-control boundaries are less granular
- dependency and CI isolation must be maintained deliberately
- future extraction may require migration work

## Future Review

This decision should be revisited when a component develops a genuinely independent:

- deployment lifecycle
- release cadence
- ownership model
- security boundary
- access-control requirement
- licensing constraint
