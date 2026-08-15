# Network Automation Platform

A production-style network automation and NetDevOps platform focused on repeatable, validated, and auditable network operations.

The project is designed around a clear separation between network intent, desired state, vendor-specific implementation, live state collection, validation, planning, and controlled deployment.

## Status

V1 is under active development.

The platform currently supports a representative Cisco branch environment and includes working validation and planning workflows against live devices.

The next major capability is the operator-facing controlled deployment CLI.

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
- Controlled deployment orchestration engine
- Pre-change safety validation
- Fresh post-change state collection
- Post-change validation
- Inventory-driven lab configuration
- Generated OpenSSH configuration
- Strict SSH host-key verification
- Production-style testing and development workflow

## Operational CLI

Validate the live branch state against desired state:

```bash
uv run nap validate branch-01
```

Plan the branch and show drift plus the rendered desired configuration:

```bash
uv run nap plan branch-01
```

Generate the lab SSH configuration from inventory:

```bash
uv run nap inventory render-ssh-config
```

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
- `inventory/ssh/` — generated SSH configuration and local SSH runtime files
- `docs/architecture/` — architecture, network model, and engineering decisions
- `tests/` — unit and service-level tests

## Architecture

The V1 workflow follows this lifecycle:

```text
Intent
  ↓
Input validation
  ↓
Desired state
  ↓
Configuration rendering
  ↓
Current-state collection
  ↓
Validation
  ↓
Planning
  ↓
Pre-change safety validation
  ↓
Controlled deployment
  ↓
Fresh state collection
  ↓
Post-change validation
  ↓
Result
```

The core platform is intended to remain independent from a specific lab implementation or device transport wherever practical.

Vendor-specific behavior is kept behind dedicated rendering, collection, and execution boundaries.

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

This file represents local runtime trust state rather than desired configuration.

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
- Vendor boundaries
- Safe automation
- Validation before and after change
- Testable components
- Environment-independent application logic
- Feature branches and pull requests
- Automated linting and tests
- Documentation kept alongside implementation

## V1 Scope

The current V1 scope focuses on:

```text
Cisco IOS / IOS XE
Single-device synchronous operations
Branch validation
Branch planning
Controlled configuration deployment
Interface state
Route state
VLAN state
Switchport state
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
```

## Next Major Milestone

The next major development step is the controlled deployment CLI.

The goal is to expose the existing deployment engine through an operator-facing workflow that includes:

```text
Drift detection
  ↓
Targeted remediation planning
  ↓
Safety validation
  ↓
Explicit operator approval
  ↓
Deployment
  ↓
Fresh state collection
  ↓
Post-change validation
```

The deployment workflow will prioritize explicit change scope and safety rather than blindly applying the full rendered desired configuration.
