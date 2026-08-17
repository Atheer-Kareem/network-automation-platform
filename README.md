# Network Automation Platform

A production-style network automation and NetDevOps platform focused on repeatable, validated, and auditable network operations.

The project is designed around a clear separation between network intent, desired state, vendor-specific implementation, live state collection, validation, planning, targeted remediation, controlled deployment, and post-change verification.

## Status

V1 is under active development.

The platform has reached a major V1 milestone: the core end-to-end automation lifecycle has been proven against a representative Cisco branch environment.

The current implementation supports:

```text
intent
  ↓
desired state
  ↓
live state collection
  ↓
validation
  ↓
drift detection
  ↓
targeted remediation
  ↓
operator approval
  ↓
pre-change safety validation
  ↓
controlled deployment
  ↓
fresh state collection
  ↓
post-change validation
  ↓
deployment outcome
```

The controlled deployment workflow has been validated against real lab drift from detection through targeted repair and final desired-state compliance.

V1 is not yet complete.

Remaining V1 work focuses on deployment-report acceptance, systematically exercising failure paths, and final representative acceptance.

Future development is tracked through a defined V1 → V1.5 → V2 roadmap.

## Current Capabilities

- Intent-driven branch configuration
- Vendor-neutral desired-state models
- Cisco IOS / IOS XE configuration rendering
- Live device-state collection with Scrapli
- Capability-aware state collection
- Interface validation
- Route validation
- Expected OSPF adjacency validation
- Required OSPF-learned route outcome validation
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
- Optional schema-versioned deployment evidence JSON
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

Optionally write schema-versioned deployment evidence after any completed workflow outcome:

```bash
uv run nap deploy branch-01 \
  --report-json /tmp/branch-01-deployment-report.json
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
│   ├── adr/
│   ├── architecture/
│   └── roadmap/
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
- `docs/architecture/` — architecture, network model, business context, and operational design
- `docs/adr/` — architectural decision records
- `docs/roadmap/` — platform evolution and competency coverage
- `tests/` — unit, service, orchestration, and safety tests

## Architecture

The current V1 workflow follows this lifecycle:

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

V1 currently supports targeted interface remediation for:

- a missing managed interface or SVI;
- interface description mismatch;
- IPv4 address mismatch;
- IPv4 prefix-length mismatch; and
- administrative-state mismatch.

IPv4 address and prefix-length drift are remediated as a single Cisco IOS configuration unit by applying the complete desired `ip address <address> <mask>` command.

Operational interface status and protocol mismatches may be detected when explicitly modelled by validation, but they are not eligible for automatic remediation.

Additional remediation types are introduced only after their validation semantics, structured remediation, vendor-specific rendering, safety behavior, and tests have been implemented.

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

This provides the first complete V1 proof that the platform can detect, plan, approve, apply, and verify a narrowly scoped network change without replacing the complete device configuration.

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

## Engineering Principles

The project is being developed with production-oriented practices from the beginning:

- Clear separation of concerns
- Explicit domain models
- Vendor-specific behavior behind defined boundaries
- Intent separated from implementation
- Safe automation
- Unsupported automation fails closed
- Targeted changes instead of unnecessary full-configuration writes
- Validation before and after deployment
- Fresh post-change state collection
- Explicit operator approval at the write boundary
- Strict device identity and SSH host-key verification
- Network outcomes over command success
- Testable components
- Environment-independent application logic
- Feature branches and pull requests
- Automated linting and tests
- Documentation maintained alongside implementation
- Engineering value before technology collection

## Roadmap

The platform roadmap is divided into three capability stages.

### V1 — Safe Automation Platform Foundation

V1 proves the core network automation architecture and controlled execution model.

Remaining V1 work includes:

```text
Deployment-report live acceptance
        ↓
Failure-path hardening
        ↓
Final CML acceptance
        ↓
V1 release
```

V1 is complete when supported automation works across multiple drift categories, unsafe or unsupported changes fail closed, important operational outcomes are validated, major failure paths are proven, and the representative acceptance scenarios pass.

### V1.5 — Model-Driven and Device-Automation Bridge

V1.5 expands the project beyond CLI-centric automation into standards-based and commonly used enterprise automation mechanisms.

Primary areas include:

```text
YANG
NETCONF
RESTCONF
ncclient
Netmiko
Ansible
Jinja2
pyATS
IOS XE Day-0 / on-box automation
model-driven telemetry foundations
```

V1.5 does not replace the V1 architecture.

Instead, it introduces additional device-management and automation mechanisms behind appropriate boundaries and through companion labs where integration into the flagship platform would not provide architectural value.

### V2 — NetDevOps Automation Ecosystem

V2 expands from device automation into broader automation-system engineering.

Primary areas include:

```text
Terraform
GitLab CI/CD
programmable CML digital twins
Docker / Docker Compose
stronger source-of-truth integration
telemetry and operational evidence
logging and webhooks
automation security and TLS
enterprise controller automation
AI / MCP integration
```

The intended V2 direction is an end-to-end delivery system:

```text
source change
    ↓
automated quality gates
    ↓
digital-twin validation
    ↓
change planning
    ↓
approval
    ↓
controlled deployment
    ↓
post-change validation
    ↓
published evidence
```

The detailed sequence, completion criteria, and version boundaries are maintained in the [Platform Roadmap](docs/roadmap/platform-roadmap.md).

## Certification and Competency Alignment

The engineering roadmap is intentionally compatible with the skills required for modern enterprise network automation, including the CCNP Automation technology domains.

Certification requirements are used as an external competency framework, not as an architecture specification.

The flagship platform remains engineering-led.

A technology is added to the platform only when it provides justified architectural or operational value.

Technologies that are important for practical breadth but do not belong naturally in the flagship architecture can be implemented through focused companion labs.

Coverage is tracked against a mastery cycle:

```text
UNDERSTAND
    ↓
BUILD
    ↓
BREAK
    ↓
TROUBLESHOOT
    ↓
VALIDATE
    ↓
DOCUMENT
    ↓
EXPLAIN
```

Specific technologies are practiced directly rather than being considered complete merely because a similar technology is already used.

For example:

```text
Scrapli experience
    ≠
Netmiko completed

custom validation
    ≠
pyATS completed

GitHub workflow
    ≠
GitLab CI/CD completed

YAML experience
    ≠
YANG-derived automation completed
```

The detailed mapping is maintained in [CCNP Automation Coverage](docs/roadmap/ccnp-automation-coverage.md).

## Repository and CI/CD Strategy

GitHub remains the canonical public repository for the Network Automation Platform.

It continues to provide:

- source history;
- feature branches;
- pull requests;
- code review;
- project documentation; and
- public portfolio evidence.

GitLab will be introduced during V2 as an additional CI/CD execution environment rather than replacing GitHub.

The intended boundary is:

```text
GitHub
canonical source repository
        ↓
GitLab
CI/CD orchestration
        ↓
GitLab Runner
        ↓
Network Automation Platform
        ↓
CML / network targets
```

CI/CD must orchestrate platform-owned validation and deployment workflows rather than bypassing them with unrelated device-write logic.

See [ADR-0004: Keep GitHub Canonical and Use GitLab for CI/CD Automation](docs/adr/0004-github-canonical-gitlab-cicd.md).

## Current Remediation Scope

The currently supported targeted remediation types are:

### Interfaces

```text
Missing managed interface / SVI
Description mismatch
IPv4 address mismatch
IPv4 prefix-length mismatch
Administrative-state mismatch
```

### VLANs

```text
Missing managed VLAN
VLAN name mismatch
```

### Switchports

```text
Administrative mode mismatch
Access VLAN mismatch
Trunk allowed-VLAN mismatch
```

Administrative mode changes are rendered as complete desired switchport configuration units. Desired access mode renders `switchport mode access` followed by the desired access VLAN. Desired trunk mode renders any profile-required trunk encapsulation, `switchport mode trunk`, and the complete desired allowed-VLAN list. Narrow VLAN-only drift remains narrowly remediated when the administrative mode already matches.

Missing switchport state, `switchport_enabled` mismatch, native-VLAN mismatch, and mixed supported/unsupported switchport drift remain blocked. `operational_mode` is collected but is not part of current desired-state validation. Empty desired allowed-VLAN semantics and IOS `switchport voice vlan` behavior are not implemented; the current `voice_access` port is an ordinary access port assigned wholly to the voice VLAN.

Platform-specific trunk encapsulation remains inside the Cisco IOS rendering boundary and is not stored in the vendor-neutral remediation model.

For IPv4 address or prefix-length drift, the platform renders the complete desired Cisco IOS `ip address <address> <mask>` configuration unit.

Operational interface status/protocol mismatches and VLAN status mismatches may be detected by validation, but they are not eligible for automatic remediation.

The remediation architecture is designed so additional types can be introduced without moving vendor-specific command generation into the core planning layer.

Expected OSPF adjacency is validated by explicit neighbor address, mapped WAN interface, and normalized `FULL` state. Branch intent also declares required learned prefixes inside the OSPF routing context. For the representative branch, `10.200.0.1/32` must be learned with IOS protocol `O`, the expected peer as next hop, and the platform-mapped WAN interface. The next hop and physical interface are derived rather than duplicated in intent.

Additional routes remain permitted. Administrative distance, metric, route subtype, and ECMP cardinality are not validated. OSPF adjacency and learned-route failures are not remediable and therefore block deployment rather than producing configuration commands. Live CML acceptance of both OSPF adjacency and learned-route outcome validation is complete.

Completed branch deployment workflows can be transformed into machine-readable schema-version `1` evidence. Each device record contains detected drift, targeted remediation commands, explicit approval status, pre-change validation, execution, post-change validation, final outcome, and message. `nap deploy --report-json PATH` writes this evidence for compliant, blocked, declined, successful, and failed outcomes without changing deployment authorization or execution semantics. Reports intentionally exclude credentials, SSH settings, and connection objects. Reporting adds neither rollback nor transaction semantics.

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

V1 development strengthens these boundaries before broader automation mechanisms are introduced.

## Documentation

Start with:

- [Company Context](docs/architecture/company-context.md)
- [Architecture Overview](docs/architecture/v1-overview.md)
- [Network Model](docs/architecture/network-model.md)
- [Branch Standard](docs/architecture/branch-standard.md)
- [Platform Roadmap](docs/roadmap/platform-roadmap.md)
- [CCNP Automation Coverage](docs/roadmap/ccnp-automation-coverage.md)
- [SSH Runtime Files](inventory/ssh/README.md)

Architectural decisions are recorded under [`docs/adr/`](docs/adr/).

Current ADRs include:

- [ADR-0001: Start with a Modular Single Repository](docs/adr/0001-platform-scope.md)
- [ADR-0002: Use a Minimal Standard Branch Topology for V1](docs/adr/0002-branch-network-design.md)
- [ADR-0003: Use Scrapli for V1 Network Device CLI Access](docs/adr/0003-network-device-cli-library.md)
- [ADR-0004: Keep GitHub Canonical and Use GitLab for CI/CD Automation](docs/adr/0004-github-canonical-gitlab-cicd.md)
