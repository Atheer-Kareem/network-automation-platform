# V1 Architecture Overview

## Objective

V1 of the Network Automation Platform demonstrates a production-style workflow for repeatable, validated, and auditable network operations.

The initial business use case is repeatable branch deployment.

The current V1 implementation now supports the complete operational path from intent and live-state validation through targeted remediation, explicit operator approval, controlled deployment, fresh post-change collection, and final desired-state validation.

## V1 Workflow

A branch definition progresses through the following lifecycle:

1. Define branch intent
2. Validate the input data
3. Build vendor-neutral desired state
4. Render the complete intended configuration
5. Collect current device state
6. Validate current state against desired state
7. Detect configuration drift
8. Build targeted remediation for explicitly supported drift
9. Render vendor-specific remediation commands
10. Review the exact proposed remediation
11. Obtain explicit operator approval
12. Run pre-change safety validation
13. Deploy the targeted change
14. Collect fresh post-change device state
15. Run full post-change desired-state validation
16. Report the deployment result

The runtime deployment path is therefore:

```text
current state
    ↓
validation
    ↓
drift detection
    ↓
targeted remediation planning
    ↓
vendor-specific remediation rendering
    ↓
operator approval
    ↓
pre-change safety validation
    ↓
configuration execution
    ↓
fresh state collection
    ↓
post-change validation
    ↓
deployment result
```

The complete rendered desired configuration and targeted remediation are deliberately treated as separate concepts.

```text
complete desired configuration
    = full representation of intended device state

targeted remediation
    = narrowly scoped commands for explicitly supported drift
```

The controlled deployment path uses targeted remediation rather than blindly applying the complete rendered desired configuration.

## Design Principles

### Intent separated from implementation

Business and network intent should not be hard-coded into device-specific automation logic.

Intent is converted into vendor-neutral desired state before platform-specific rendering or execution occurs.

### Vendor implementation behind clear interfaces

Device-specific behaviour should be isolated so additional platforms can be introduced without redesigning the entire application.

Vendor-specific responsibilities include:

- Full configuration rendering
- Targeted remediation rendering
- Device state collection
- Configuration execution

Core planning, validation, remediation policy, and deployment orchestration remain separate from those implementation details.

### Validate before and after change

Successful command execution is not sufficient evidence that a network change succeeded.

Pre-change validation determines whether the current device state is acceptable and whether required safety prerequisites remain available before a write occurs.

Post-change validation determines whether the resulting fresh device state satisfies the complete required desired state.

### Targeted change over unnecessary full replacement

V1 does not deploy the complete rendered desired configuration merely because drift exists.

Supported drift is converted into structured remediation actions and then into vendor-specific targeted commands.

This reduces the execution surface and avoids changing unrelated configuration during a narrow remediation.

### Explicit operator approval

A supported remediation is displayed before the write boundary.

The operator must explicitly approve the exact targeted command sequence before deployment continues.

A declined change is skipped and no configuration execution occurs.

### Safe automation

Automation should fail predictably, provide useful diagnostics, and avoid uncontrolled partial deployment.

A deployment must not proceed when:

- unsupported drift is present;
- no supported remediation can be generated;
- operator approval is declined;
- required pre-change checks fail; or
- device identity is inconsistent.

### Testable components

Core business logic should be testable without requiring access to live network devices.

External device interaction remains behind platform-owned interfaces so planning, validation, remediation, orchestration, and deployment behaviour can be tested independently.

### Environment independence

The automation platform should not depend directly on any specific lab or execution environment, including CML, EVE-NG, development sandboxes, or physical hardware.

These environments provide network targets, not application architecture.

Environment-specific addressing and SSH information are supplied through inventory rather than embedded in application logic.

## Validation and Planning

V1 supports branch-level validation and planning as read-only workflows.

`nap validate` compares fresh live device state against the desired-state expectation and reports whether the branch is compliant.

`nap plan` performs the same live-state evaluation and additionally displays:

- detected drift;
- targeted remediation for supported drift; and
- the complete rendered desired configuration.

Targeted remediation and the complete rendered desired configuration are intentionally shown separately so operators can distinguish between the complete desired state and the exact commands that would be eligible for deployment.

No configuration writes occur during validation or planning.

## Structured Remediation

Remediation planning is separate from vendor-specific command generation.

The remediation path is:

```text
ValidationExpectation
        +
ValidationReport
        ↓
remediation planner
        ↓
structured remediation action
        ↓
vendor-specific remediation renderer
        ↓
targeted CLI commands
```

Validation failures include machine-readable metadata where required for remediation decisions.

The first supported remediation type is:

```text
missing interface / SVI
```

The remediation planner resolves the failed validation target against the already platform-resolved validation expectation rather than repeating logical-to-physical interface mapping.

This preserves a single mapping boundary and keeps the remediation planner independent from Cisco interface naming rules.

## Controlled Deployment

V1 performs device changes through a controlled deployment workflow.

A configuration change is only attempted when:

1. live drift is present;
2. all failed checks are supported by the current remediation policy;
3. targeted remediation commands are successfully produced;
4. the operator explicitly approves those exact commands; and
5. pre-change safety validation passes.

After configuration execution, the platform collects fresh device state rather than validating against state captured before the change.

The deployment is only considered successful when post-change validation confirms that the resulting device state satisfies the full required desired state.

### Device-Level Deployment Decisions

At the branch orchestration layer:

```text
COMPLIANT
    → SKIPPED

DRIFT + supported remediation
    → eligible for approval and deployment

DRIFT + any unsupported failure
    → BLOCKED

SUPPORTED DRIFT + no rendered remediation
    → BLOCKED

OPERATOR DECLINES
    → SKIPPED
```

This prevents partial remediation of a device when unsupported drift is also present.

### Deployment Outcomes

The underlying deployment workflow reports explicit outcomes:

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

The current V1 implementation provides Cisco IOS adapters using the existing device connection and state collection layers.

Targeted remediation rendering is also isolated from the generic remediation planner.

This keeps deployment orchestration and remediation policy independent from Cisco-specific command syntax and the underlying Scrapli implementation.

The CLI does not write directly to devices.

All writes continue through the deployment runtime, deployment service, and vendor-specific executor.

## Pre-Change Safety Validation

Pre-change safety requirements are constructed separately from the remediation itself.

For the current representative environment, the platform derives the OOB management path from:

- the inventory management address;
- the configured OOB network; and
- fresh collected interface and route state.

The builder identifies the interface currently carrying the inventory management IP and requires that management interface to remain:

- present;
- administratively enabled;
- operationally up; and
- protocol up.

Where a matching connected OOB route is visible in collected state, that route is also included as a prerequisite.

The interface being remediated is not automatically used as a safety prerequisite.

For example, a missing `Vlan99` can be repaired because the deployment safety boundary is the independent OOB management path rather than the missing SVI itself.

## Capability-Aware State Collection

Device state collection is capability-aware.

Inventory declares which state features are supported and required for each device. The collector always gathers common interface state and only executes additional commands for explicitly enabled capabilities.

Current state features include:

- `routes`
- `ospf`
- `vlans`
- `switchports`

This prevents the platform from issuing unsupported or irrelevant commands to devices that do not provide those capabilities.

Collected state currently includes:

- Interface state
- Route state
- OSPF neighbor state
- VLAN state
- Switchport state

Capability selection is an inventory concern rather than a dependency on a specific lab environment.

## Device Identity Safety

Before configuration execution, the deployment workflow verifies that the deployment target, current device state, and desired state refer to the same device.

Concrete execution and state-collection adapters also validate their target before interacting with a device.

Identity mismatches fail before configuration is written.

Strict SSH host-key verification is also maintained so transport trust is separate from application-level hostname checks.

## Interface Administrative State

V1 distinguishes administrative interface state from operational link state.

`enabled=True` in desired state means that the interface should be administratively enabled.

It does not imply that the interface must be operationally `up`.

Collected interface state therefore includes an explicit `admin_enabled` property that can be validated independently from interface and protocol operational status.

This allows the platform to validate configuration intent without incorrectly treating lack of physical connectivity as a deployment failure.

## Representative Drift Remediation

The V1 controlled deployment workflow has been validated against the live representative CML branch environment.

The test intentionally removed the management SVI from `br01-sw01` while preserving the independent OOB management path.

The platform detected:

```text
Interface Vlan99 is missing
```

The validation failure was classified as a supported missing-interface remediation.

The platform then generated the following targeted remediation:

```text
interface Vlan99
description Switch management SVI
ip address 10.101.99.21 255.255.255.0
no shutdown
```

The complete desired switch configuration remained available separately through the planning workflow and was not used as the deployment payload.

The controlled workflow then:

1. collected fresh router and switch state;
2. skipped the already-compliant branch router;
3. detected the missing management SVI on the switch;
4. converted the structured validation failure into targeted remediation;
5. displayed the exact command sequence to the operator;
6. required explicit approval;
7. verified the independent OOB management path;
8. passed only the targeted commands to the deployment runtime;
9. applied the configuration through the Cisco IOS deployment executor;
10. collected fresh post-change state;
11. re-ran full desired-state validation; and
12. reported the deployment as successful only after validation passed.

Subsequent branch validation and planning reported no remaining drift.

This demonstrates that V1 can detect, plan, approve, apply, and verify a specific configuration drift condition without requiring full-device configuration replacement.

## Configuration Persistence

Configuration execution and configuration persistence are separate concerns in V1.

A successful deployment changes the device running configuration.

The deployment workflow does not automatically save the running configuration to startup configuration.

Persistence must be performed explicitly when required.

This keeps deployment behaviour controlled and prevents a successful runtime test or temporary change from being silently persisted.

## Inventory and Environment Configuration

Environment-specific lab configuration is separated from application code.

The authoritative lab source is:

```text
inventory/lab.yaml
```

It owns environment data including:

- OOB network
- Management addresses
- SSH compatibility settings
- Device state capabilities

OpenSSH configuration is generated from inventory rather than manually maintained.

SSH host keys remain separate local runtime trust state and are not treated as desired inventory configuration.

This separation was validated by changing the representative lab OOB network without requiring application-code changes or coupling ordinary unit tests to the live environment.

## V1 Scope

V1 includes:

- Representative branch network model
- Structured network intent
- Device inventory
- Inventory-driven environment configuration
- Read-only capability-aware state collection
- Full desired configuration generation
- Branch-level validation
- Branch-level planning
- Structured drift classification
- Targeted remediation planning
- Cisco IOS remediation rendering
- Explicit operator approval
- Pre-change safety validation
- Controlled deployment
- Post-change fresh state collection
- Full post-change validation
- Explicit deployment result modelling
- Cisco IOS deployment execution
- Generated SSH configuration
- Strict SSH host-key verification
- Automated testing
- CI quality gates
- Architecture and operational documentation

## Current V1 Deployment Limitations

Controlled deployment currently has the following limitations:

- Cisco IOS / IOS XE CLI-oriented execution path
- Targeted remediation currently supports missing interface / SVI drift only
- Single-device synchronous execution at the write boundary
- No automatic rollback
- No automatic persistence of running configuration to startup configuration
- Remediation is executed as CLI command sequences
- Multi-device transaction semantics are not implemented
- Unsupported drift blocks deployment rather than being partially remediated
- OSPF neighbor state is collected but OSPF adjacency expectations are not yet modelled in desired-state validation
- Additional interface, VLAN, and switchport remediation types are not yet enabled for deployment

These constraints are intentional for V1 and keep the execution model small enough to validate safely before expanding platform scope.

## Out of Scope for V1

The following are planned extensions rather than V1 requirements:

- AI-assisted remediation
- Closed-loop autonomous remediation
- Automatic rollback
- Automatic configuration persistence
- Multi-device transactional deployment
- Full observability platform
- Kubernetes
- Complex microservice architecture
- Multiple CI platforms
- Large-scale cloud networking
- Full multi-vendor remediation
- NETCONF / RESTCONF deployment workflows
- Controller integration
- Production web interface
