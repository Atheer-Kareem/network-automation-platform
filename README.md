# Network Automation Platform

A production-style network automation and NetDevOps platform focused on repeatable, validated, and auditable network operations.

The project is designed around a clear separation between network intent, desired state, vendor-specific implementation, live state collection, validation, planning, targeted remediation, controlled deployment, and post-change verification.

## Status

V1 is under active development.

The platform currently supports a representative Cisco branch environment with working end-to-end validation, planning, targeted remediation, and operator-approved controlled deployment against live devices.

The controlled deployment workflow has been validated in the lab from real drift detection through targeted remediation, pre-change safety checks, configuration deployment, fresh state collection, and post-change validation.

## Current Capabilities

- Intent-driven branch configuration
- Vendor-neutral desired-state models
- Cisco IOS / IOS XE configuration rendering
- Live device-state collection with Scrapli
- Capability-aware state collection
- Interface validation
- Route validation
- VLAN validation
- Switchport validation
- Branch-level validation workflow
- Branch-level planning workflow
- Targeted remediation planning
- Vendor-specific targeted remediation rendering
- Operator-approved controlled deployment
- Unsupported-drift blocking
- Pre-change OOB management safety validation
- Device identity validation
- Fresh post-change state collection
- Post-change desired-state validation
- Explicit deployment outcome reporting
- Inventory-driven lab configuration
- Generated OpenSSH configuration
- Strict SSH host-key verification
- Production-style testing and development workflow

## Operational CLI

Validate live branch state against desired state:

```bash
uv run nap validate branch-01
```

Plan the branch, show detected drift, targeted remediation where supported, and the complete rendered desired configuration:

```bash
uv run nap plan branch-01
```

Deploy supported targeted remediation with explicit operator approval:

```bash
uv run nap deploy branch-01
```

Generate the lab SSH configuration from inventory:

```bash
uv run nap inventory render-ssh-config
```

### Deployment Behavior

The deployment workflow is intentionally conservative.

A compliant device is skipped.

A device with unsupported drift is blocked from deployment.

A supported remediation is displayed to the operator before any write occurs.

The operator must explicitly approve the exact targeted commands before deployment continues.

Configuration changes are applied to running configuration only. Automatic persistence to startup configuration is intentionally outside the current V1 scope.

## Development

Install or synchronize dependencies:

```bash
uv sync
```

Run linting:

```bash
uv run ruff check .
```

Run the full test suite:

```bash
uv run pytest
```

## Repository Structure

```text
network-automation-platform/
├── docs/
│   └── architecture/
├── intent/
├── inventory/
│   └── ssh/
├── src/
│   └── network_automation_platform/
├── tests/
├── pyproject.toml
└── README.md
```

Key areas:

- `src/network_automation_platform/` — application and platform code
- `intent/` — desired branch intent
- `inventory/` — device inventory and lab environment configuration
- `inventory/ssh/` — generated SSH configuration and local SSH runtime state
- `docs/architecture/` — architecture, network model, and engineering decisions
- `tests/` — unit, service, and orchestration tests

## Architecture

The V1 workflow follows this lifecycle:

```text
Intent
  ↓
Input validation
  ↓
Desired state
  ↓
Current-state collection
  ↓
Validation
  ↓
Drift detection
  ↓
Targeted remediation planning
  ↓
Vendor-specific remediation rendering
  ↓
Operator review and approval
  ↓
Pre-change safety validation
  ↓
Controlled deployment
  ↓
Fresh state collection
  ↓
Post-change validation
  ↓
Deployment result
```

The core platform is intended to remain independent from a specific lab implementation or device transport wherever practical.

Vendor-specific behavior is kept behind dedicated rendering, collection, remediation, execution, and state-provider boundaries.

The complete rendered desired configuration and targeted remediation are deliberately treated as different concepts:

```text
Complete desired configuration
    = full representation of the intended device state

Targeted remediation
    = narrowly scoped commands for explicitly supported drift
```

Controlled deployment uses the targeted remediation path rather than blindly applying the complete rendered desired configuration.

## Controlled Deployment

Supported drift can be converted into structured remediation actions and then rendered into vendor-specific commands.

The current controlled deployment workflow is:

```text
Live state
  ↓
Validation
  ↓
Supported drift detection
  ↓
Targeted remediation planning
  ↓
Exact command preview
  ↓
Explicit operator approval
  ↓
Pre-change safety validation
  ↓
Configuration deployment
  ↓
Fresh state collection
  ↓
Post-change validation
  ↓
Deployment outcome
```

A deployment is not attempted when:

- the device is already compliant;
- unsupported drift is present;
- no targeted remediation commands can be produced;
- the operator declines the change; or
- pre-change safety requirements are not satisfied.

Current deployment outcomes include:

```text
BLOCKED
FAILED
POST_CHECK_FAILED
POST_VALIDATION_FAILED
SUCCEEDED
```

V1 currently supports targeted remediation for a missing interface or SVI.

Additional remediation types can be added independently as the remediation model expands.

## Representative Deployment Validation

The controlled deployment workflow has been validated against the representative CML branch environment.

A missing `Vlan99` management SVI on `br01-sw01` was detected from live device state.

The platform generated only the targeted remediation:

```text
interface Vlan99
description Switch management SVI
ip address 10.101.99.21 255.255.255.0
no shutdown
```

The workflow then:

1. detected the live drift;
2. displayed the targeted remediation separately from the complete desired configuration;
3. required explicit operator approval;
4. validated the OOB management path before deployment;
5. applied only the targeted commands;
6. collected fresh device state after the change; and
7. confirmed full desired-state compliance.

The already-compliant branch router was skipped rather than unnecessarily modified.

## Lab Configuration

The authoritative source for the current lab environment is:

```text
inventory/lab.yaml
```

It contains environment-level data such as:

- OOB network
- Device management addresses
- SSH compatibility settings
- Device collection capabilities

The generated OpenSSH configuration is written to:

```text
inventory/ssh/lab_config
```

Generate or refresh it with:

```bash
uv run nap inventory render-ssh-config
```

Do not edit the generated file manually.

SSH host keys are maintained separately in:

```text
inventory/ssh/known_hosts
```

This file represents local runtime trust state rather than desired configuration and is intentionally not treated as an inventory source of truth.

When device addresses or device identities change, local SSH trust state may need to be refreshed.

## Documentation

Start with:

- [Architecture Overview](docs/architecture/v1-overview.md)
- [Network Model](docs/architecture/network-model.md)
- [Branch Standard](docs/architecture/branch-standard.md)
- [SSH Runtime Files](inventory/ssh/README.md)

## Engineering Principles

The project is being developed with production-oriented practices from the beginning:

- Clear separation of concerns
- Explicit domain models
- Vendor-specific behavior behind defined boundaries
- Intent separated from implementation
- Safe automation
- Targeted changes instead of unnecessary full-configuration writes
- Validation before and after deployment
- Fresh post-change state collection
- Explicit operator approval at the write boundary
- Strict device identity and SSH host-key verification
- Testable components
- Environment-independent application logic
- Feature branches and pull requests
- Automated linting and tests
- Documentation maintained alongside implementation

## V1 Scope

The current V1 scope focuses on:

```text
Cisco IOS / IOS XE
Synchronous single-device execution
Branch-level validation
Branch-level planning
Targeted remediation planning
Operator-approved controlled deployment
Interface state
Route state
VLAN state
Switchport state
Pre-change safety validation
Post-change validation
Representative branch topology
```

V1 intentionally does not yet include:

```text
Automatic rollback
Automatic configuration persistence
Multi-device transactional deployment
Full multi-vendor support
NETCONF / RESTCONF workflows
Controller integration
Automatic remediation of every drift type
```

## Current Remediation Scope

The first supported targeted remediation type is:

```text
Missing interface / SVI
```

The remediation architecture is designed so that additional types can be introduced without moving vendor-specific command generation into the core planning layer.

Potential later additions include:

```text
Interface IP mismatch
Administrative state mismatch
Missing VLAN
VLAN name mismatch
Switchport mode mismatch
Access VLAN mismatch
Trunk allowed-VLAN mismatch
```

These are not considered supported deployment actions until explicitly implemented and tested.

## V1 Safety Boundaries

The current deployment design intentionally maintains the following boundaries:

```text
No unsupported drift deployment
No write without operator approval
No automatic startup-config persistence
No automatic rollback
No multi-device transaction semantics
No direct CLI-to-device write path
```

All device writes continue through the deployment service and vendor-specific deployment executor.

The CLI remains an operator interface rather than an independent execution path.
