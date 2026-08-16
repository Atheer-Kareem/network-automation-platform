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

## Scope Clarification

This decision applies to components that form part of the Network Automation Platform itself.

A separate companion repository may be used for technology comparison, controller-specific exercises, certification-aligned labs, or other practical work that does not naturally belong to the flagship platform architecture.

For example:

network-automation-platform = production-style platform implementation

enterprise-network-automation-lab = broader automation practice and technology-specific labs Creating such a companion repository does not represent decomposition of the platform into multiple repositories.

Platform components should still remain within the modular single repository unless independent ownership, lifecycle, security, or deployment requirements justify extraction.

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
