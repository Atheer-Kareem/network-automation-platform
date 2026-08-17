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

The currently supported targeted interface remediation types are:

```text
missing managed interface / SVI
description mismatch
IPv4 address mismatch
IPv4 prefix-length mismatch
administrative-state mismatch
```

Interface mismatches carry machine-readable `mismatched_fields` metadata so remediation policy does not depend on parsing human-readable validation messages.

Targeted VLAN remediation currently supports:

```text
missing managed VLAN
VLAN name mismatch
```

VLAN failures use the same structured validation metadata as interface failures. Missing VLANs are classified with `reason="missing"`, while existing VLAN configuration drift uses `reason="mismatch"` with machine-readable `mismatched_fields`.

VLAN name mismatch is eligible for automatic remediation. VLAN status mismatch is treated as operational drift and is intentionally excluded from automatic remediation.

A validation check containing both configurable VLAN name drift and operational VLAN status drift is blocked rather than partially remediated.

Targeted switchport remediation supports administrative-mode mismatch, access-VLAN mismatch, and trunk allowed-VLAN mismatch. Narrow VLAN-only drift is remediated without reapplying mode when the desired administrative mode already matches.

Administrative-mode changes are complete desired switchport configuration units. Desired access mode renders `switchport mode access` and the desired access VLAN. Desired trunk mode renders any platform-profile-required encapsulation before `switchport mode trunk`, followed by the complete desired allowed-VLAN list. Encapsulation remains vendor-specific Cisco IOS rendering context rather than part of the vendor-neutral remediation model.

Missing switchport state, `switchport_enabled` mismatch, native-VLAN mismatch, and mixed supported/unsupported switchport checks fail closed. `operational_mode` is collected but is not part of current desired-state validation. Empty desired allowed-VLAN semantics are not represented. IOS voice-VLAN semantics are not implemented; `voice_access` is an ordinary access port assigned wholly to the voice VLAN.

IPv4 address and prefix-length mismatches are treated as one Cisco IOS configuration unit and therefore render the complete desired address and subnet mask.

Operational interface status and protocol mismatches are intentionally excluded from automatic remediation.

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

## V1 Target Scope

V1 establishes the safe automation platform foundation.

The target V1 scope includes:

- representative branch network model;
- structured network intent;
- device inventory;
- inventory-driven environment configuration;
- read-only capability-aware state collection;
- complete desired configuration generation;
- branch-level validation;
- branch-level planning;
- structured drift classification;
- targeted remediation planning;
- Cisco IOS remediation rendering;
- explicit operator approval;
- pre-change safety validation;
- controlled deployment;
- fresh post-change state collection;
- full post-change validation;
- explicit deployment result modelling;
- Cisco IOS deployment execution;
- generated SSH configuration;
- strict SSH host-key verification;
- branch-wide deployment preflight before the first write;
- targeted interface remediation for supported configuration mismatches;
- targeted VLAN remediation;
- targeted switchport remediation;
- routing and OSPF operational validation;
- structured deployment evidence and reporting;
- systematic failure-path validation;
- representative CML acceptance testing;
- automated testing;
- CI quality gates; and
- architecture and operational documentation.

Some of these capabilities remain under development.

The detailed implementation sequence and completion criteria are maintained in the
[Platform Roadmap](../roadmap/platform-roadmap.md).

## Current V1 Deployment Limitations

Controlled deployment currently has the following limitations:

- Cisco IOS / IOS XE CLI-oriented execution path;
- targeted interface remediation is limited to missing interfaces/SVIs, description drift, IPv4 address/prefix drift, and administrative-state drift;
- single-device synchronous execution remains the write-boundary model;
- no automatic rollback;
- no automatic persistence of running configuration to startup configuration;
- remediation is executed as CLI command sequences;
- multi-device transaction semantics are not implemented;
- unsupported drift blocks deployment rather than being partially remediated;
- OSPF neighbor state is collected but OSPF adjacency expectations are not yet modelled in desired-state validation;
- operational interface status/protocol drift, VLAN status drift, missing switchport state, `switchport_enabled` drift, native-VLAN drift, and mixed supported/unsupported switchport drift are not enabled for automatic remediation;
- structured deployment audit/report artifacts are not yet complete; and
- systematic failure-path acceptance coverage is still being expanded.

These constraints are intentional at the current stage of V1.

The remaining V1 work focuses on routing and OSPF operational validation, improving deployment evidence, and proving important failure paths before declaring V1 complete.

## Out of Scope for V1

The following capabilities are deliberately deferred beyond the V1 foundation:

### V1.5

- YANG-driven automation;
- NETCONF device workflows;
- RESTCONF device workflows;
- `ncclient`;
- Netmiko practice and comparison;
- Ansible network automation;
- advanced Jinja2;
- pyATS integration;
- IOS XE Day-0 and on-box automation; and
- model-driven telemetry foundations.

### V2 and Later

- Terraform-based automation;
- GitLab CI/CD network pipelines;
- programmable CML digital-twin lifecycle;
- broader source-of-truth integration;
- containerised automation environments;
- enterprise controller integration;
- broader telemetry, logging, and webhook workflows;
- advanced automation security and TLS workflows;
- AI/MCP integration;
- closed-loop autonomous remediation;
- automatic rollback;
- automatic configuration persistence;
- multi-device transactional deployment;
- full observability platform;
- Kubernetes;
- complex microservice architecture;
- large-scale cloud networking;
- full multi-vendor remediation; and
- production web interface.

Deferring these capabilities prevents V1 from expanding beyond its primary objective: proving a safe, deterministic, testable network automation lifecycle.

## Future Development

This document describes the implemented and intended architecture of V1.

Development beyond the V1 architecture is tracked separately so future technologies do not become requirements of the current platform design.

The planned progression is:

```text
V1
Safe automation platform foundation
    ↓
V1.5
Model-driven and device-automation bridge
    ↓
V2
Broader NetDevOps automation ecosystem
```

Future development includes areas such as model-driven device automation, automation frameworks, CI/CD, programmable CML environments, enterprise controller automation, telemetry, security hardening, and AI/MCP integration.

These capabilities are introduced only where they provide justified engineering value and must preserve the platform's existing validation, safety, and execution boundaries.

See:

- [Platform Roadmap](../roadmap/platform-roadmap.md)
- [CCNP Automation Coverage](../roadmap/ccnp-automation-coverage.md)
