# V1 Architecture Overview

## Objective

V1 of the Network Automation Platform demonstrates a production-style workflow for repeatable and validated network operations.

The initial business use case is repeatable branch deployment.

## V1 Workflow

A branch definition progresses through the following lifecycle:

1. Define branch intent
2. Validate the input data
3. Generate intended network configuration
4. Perform automated quality checks
5. Review the proposed change
6. Collect current device state
7. Run pre-change validation
8. Deploy the change
9. Collect fresh post-change device state
10. Run post-change validation
11. Report the deployment result

The runtime deployment path is therefore:

```text
current state
    ↓
pre-change validation
    ↓
configuration execution
    ↓
fresh state collection
    ↓
post-change validation
    ↓
deployment result
```

## Design Principles

### Intent separated from implementation

Business and network intent should not be hard-coded into device-specific automation logic.

### Vendor implementation behind clear interfaces

Device-specific behaviour should be isolated so additional platforms can be introduced without redesigning the entire application.

### Validate before and after change

Successful command execution is not sufficient evidence that a network change succeeded.

Pre-change validation determines whether the current device state is acceptable for the proposed change.

Post-change validation determines whether the resulting device state satisfies the required desired state.

### Safe automation

Automation should fail predictably, provide useful diagnostics, and avoid uncontrolled partial deployment.

A deployment must not proceed when required pre-change checks fail.

### Testable components

Core business logic should be testable without requiring access to live network devices.

External device interaction should remain behind platform-owned interfaces so orchestration and validation logic can be tested independently.

### Environment independence

The automation platform should not depend directly on GNS3, EVE-NG, CML, or physical hardware.

These environments provide network targets, not application architecture.

## Controlled Deployment

V1 performs device changes through a controlled deployment workflow.

A configuration change is only attempted when pre-change validation passes.

After configuration execution, the platform collects fresh device state rather than validating against state captured before the change.

The deployment is only considered successful when post-change validation confirms that the resulting device state satisfies the required desired state.

### Deployment Outcomes

The deployment workflow reports explicit outcomes:

- `BLOCKED` — pre-change validation failed and no configuration was attempted.
- `FAILED` — pre-change validation passed, but configuration execution failed.
- `POST_CHECK_FAILED` — configuration was applied, but fresh post-change state could not be collected.
- `POST_VALIDATION_FAILED` — configuration was applied and fresh state was collected, but the resulting state did not satisfy post-change validation.
- `SUCCEEDED` — configuration was applied and the resulting state passed post-change validation.

Configuration execution success is intentionally distinct from overall deployment success.

A successful device write does not by itself mean that the deployment succeeded.

## Execution Boundaries

The core deployment workflow is vendor-independent.

It depends on platform-owned abstractions for:

- Configuration execution
- Device state collection

Vendor-specific implementations remain behind these interfaces.

The initial V1 implementation provides Cisco IOS adapters using the existing device connection and state collection layers.

This keeps deployment orchestration and policy independent from Cisco-specific behaviour and the underlying Scrapli implementation.

## Device Identity Safety

Before configuration execution, the deployment workflow verifies that the deployment target, current device state, and desired state refer to the same device.

Concrete execution and state-collection adapters also validate their target before interacting with a device.

Identity mismatches fail before configuration is written.

## Interface Administrative State

V1 distinguishes administrative interface state from operational link state.

`enabled=True` in desired state means that the interface should be administratively enabled.

It does not imply that the interface must be operationally `up`.

Collected interface state therefore includes an explicit `admin_enabled` property that can be validated independently from interface and protocol operational status.

This allows the platform to validate configuration intent without incorrectly treating lack of physical connectivity as a deployment failure.

## Configuration Persistence

Configuration execution and configuration persistence are separate concerns in V1.

A successful deployment changes the device running configuration.

The deployment workflow does not automatically save the running configuration to startup configuration.

Persistence must be performed explicitly when required.

This keeps deployment behaviour controlled and prevents a successful runtime test or temporary change from being silently persisted.

## V1 Scope

V1 includes:

- Representative branch network model
- Structured network intent
- Device inventory
- Read-only state collection
- Configuration generation
- Pre-change validation
- Controlled deployment
- Post-change state collection
- Post-change validation
- Explicit deployment result modelling
- Cisco IOS deployment execution
- Automated testing
- CI quality gates
- Architecture and operational documentation

## Current V1 Deployment Limitations

Controlled deployment currently has the following limitations:

- Cisco IOS only
- Single-device synchronous execution
- No automatic rollback
- No automatic persistence of running configuration to startup configuration
- Candidate configuration is executed as CLI command sequences
- Multi-device transaction semantics are not implemented

These constraints are intentional for V1 and keep the execution model small enough to validate safely before expanding platform scope.

## Out of Scope for V1

The following are planned extensions rather than V1 requirements:

- AI-assisted remediation
- Full observability platform
- Kubernetes
- Complex microservice architecture
- Multiple CI platforms
- Large-scale cloud networking
- Closed-loop autonomous remediation
- Support for every network vendor
- Production web interface
