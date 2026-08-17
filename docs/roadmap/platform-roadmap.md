# Platform Roadmap

## Purpose

This roadmap defines the planned evolution of the Network Automation Platform from the current V1 foundation through V1.5 and V2.

The roadmap is engineering-led.

Certification objectives, including CCNP Automation, are used to identify useful technologies and practical competencies, but they do not determine the architecture of the flagship platform.

A technology is incorporated into the Network Automation Platform only when it strengthens the platform design or provides a justified implementation capability.

Broader technology practice that does not belong naturally in the flagship architecture may be implemented in separate companion labs.

## Current Position

The platform has reached a significant V1 milestone.

The current implementation supports an end-to-end controlled network automation workflow:

```text
Intent
  ↓
Validated desired state
  ↓
Live state collection
  ↓
Desired-vs-actual validation
  ↓
Drift classification
  ↓
Structured targeted remediation
  ↓
Vendor-specific remediation rendering
  ↓
Operator review
  ↓
Explicit approval
  ↓
Pre-change safety validation
  ↓
Controlled deployment
  ↓
Fresh post-change collection
  ↓
Full post-change validation
  ↓
Explicit deployment outcome
```

This workflow has been validated against the representative CML branch environment using real configuration drift.

V1 is not complete, but the core architecture and write boundary have been proven.

## Roadmap Principles

The roadmap follows several constraints.

### Engineering value before technology collection

Technologies are not added to the flagship platform merely to demonstrate familiarity with a tool.

Each platform capability must have a clear architectural or operational purpose.

### Depth and breadth are separated deliberately

The flagship repository provides engineering depth:

```text
network-automation-platform
    ↓
architecture
domain modelling
state collection
validation
drift detection
safe remediation
deployment
testing
failure handling
auditability
```

Broader automation technologies may be exercised in a companion environment:

```text
enterprise-network-automation-lab
    ↓
alternative frameworks
model-driven protocols
controller APIs
CI/CD exercises
technology-specific labs
certification coverage
```

The companion environment does not replace or fragment the flagship platform.

### Unsafe automation fails closed

A detected difference between desired and actual state does not automatically become deployable remediation.

A write capability is enabled only after the relevant drift type has:

1. structured validation semantics;
2. structured remediation modelling;
3. vendor-specific rendering;
4. automated tests;
5. safety checks;
6. failure-path coverage; and
7. representative lab validation.

Unsupported drift remains blocked.

### Network outcome matters more than command success

Successful command execution is not sufficient evidence of successful automation.

The platform should increasingly validate operational network outcomes, including routing and protocol state, rather than only configuration presence.

### Version boundaries represent capability maturity

V1, V1.5, and V2 are not arbitrary feature collections.

Each version represents a distinct maturity stage:

```text
V1
Safe automation platform foundation

V1.5
Model-driven and multi-interface automation bridge

V2
Broader NetDevOps automation ecosystem
```

## V1 — Safe Automation Platform Foundation

### Objective

Complete a production-style network automation foundation that can safely observe, plan, remediate, deploy, verify, and report changes in the representative branch environment.

V1 primarily proves architecture, safety, validation, and execution discipline.

### Already Implemented

Current V1 capabilities include:

- structured branch intent;
- vendor-neutral desired-state models;
- Cisco IOS / IOS XE configuration rendering;
- inventory-driven environment configuration;
- generated OpenSSH configuration;
- strict SSH host-key verification;
- capability-aware live-state collection;
- interface validation;
- route validation;
- VLAN validation;
- switchport validation;
- branch-level validation;
- branch-level planning;
- structured drift classification;
- targeted remediation planning;
- Cisco IOS targeted remediation rendering;
- operator-approved controlled deployment;
- unsupported-drift blocking;
- pre-change OOB safety validation;
- device identity checks;
- fresh post-change state collection;
- full post-change desired-state validation; and
- explicit deployment outcomes.

Targeted interface remediation now supports missing managed interfaces/SVIs, description mismatch, IPv4 address or prefix-length mismatch, and administrative-state mismatch.

Targeted VLAN remediation now supports missing managed VLANs and VLAN name mismatch.

Targeted switchport remediation now supports administrative-mode mismatch, access-VLAN mismatch, and trunk allowed-VLAN mismatch.

### Remaining V1 Work

#### 1. Branch-wide deployment preflight [Completed]

Perform complete branch analysis before the first device write.

The preflight should:

```text
collect all relevant devices
        ↓
validate all devices
        ↓
classify all drift
        ↓
derive eligible remediation
        ↓
evaluate branch-wide safety
        ↓
only then allow writes
```

This does not introduce multi-device transaction semantics.

It prevents avoidable partial execution where a later device contains known unsupported or unsafe drift.

#### 2. Interface remediation expansion [Completed]

Targeted interface remediation now covers description, IPv4 address or prefix-length, and administrative-state mismatches in addition to missing interfaces.

Completed capabilities include:

- description mismatch;
- IPv4 address or prefix mismatch; and
- administrative-state mismatch.

Each capability must preserve the existing structured validation-to-remediation boundary.

#### 3. VLAN remediation [Completed]

Targeted VLAN remediation now supports carefully scoped configuration drift:

- missing managed VLAN; and
- VLAN name mismatch.

VLAN status mismatch remains validation-only operational drift and is not eligible for automatic remediation.

Mixed configurable and operational VLAN drift is blocked rather than partially remediated.

#### 4. Switchport remediation [Completed]

Controlled switchport remediation now supports:

- administrative-mode mismatch;
- access VLAN mismatch;
- trunk allowed-VLAN mismatch.

Administrative-mode changes are rendered as complete desired switchport configuration units. Access mode includes the desired access VLAN; trunk mode includes profile-required encapsulation and the complete non-empty desired allowed-VLAN list. Narrow VLAN-only drift remains narrow when mode already matches.

Missing switchport state, `switchport_enabled` mismatch, native-VLAN mismatch, and mixed supported/unsupported drift remain blocked. Operational mode is collected but not currently desired-state validated. IOS voice-VLAN and empty allowed-VLAN semantics are not implemented.

#### 5. Routing and OSPF validation [Next]

Extend validation beyond configuration presence toward network behavior.

Planned work includes modelling expected OSPF adjacency and relevant routing outcomes.

Routing-protocol remediation is not required for V1.

#### 6. Deployment evidence and reporting

Improve structured evidence of each deployment.

A deployment record should be able to represent:

```text
branch
device
detected drift
approved remediation
pre-change result
execution result
post-change result
final outcome
```

Machine-readable output or report artifacts may be introduced where useful.

#### 7. Failure-path hardening

Systematically exercise important failure conditions, including:

- unreachable device;
- authentication failure;
- SSH host-key failure;
- identity mismatch;
- unavailable OOB prerequisite;
- unsupported drift;
- operator rejection;
- configuration execution failure;
- post-change collection failure;
- post-change validation failure; and
- already-compliant state.

#### 8. V1 acceptance and release

V1 is complete when:

- supported remediation works across multiple drift categories;
- unsupported or unsafe changes fail closed;
- branch-wide preflight occurs before writes;
- routing validation proves meaningful operational state;
- major failure paths are tested;
- operator documentation is complete;
- representative CML acceptance scenarios pass; and
- architecture documentation accurately describes the implemented system.

At that point V1 should be tagged as a stable project milestone.

## V1.5 — Model-Driven and Device-Automation Bridge

### Objective

Expand the platform and associated lab work beyond CLI-centric automation into model-driven network management and commonly used network automation frameworks.

V1.5 bridges the custom platform architecture built in V1 with standards-based and ecosystem automation methods.

### YANG and Data Models

Develop practical competence with:

- YANG fundamentals;
- YANG trees;
- native Cisco models;
- IETF models;
- OpenConfig models;
- JSON and XML representations; and
- model discovery and inspection.

Where practical, use Cisco YANG tooling to inspect and validate models.

### NETCONF

Implement and troubleshoot NETCONF workflows including:

- capability discovery;
- datastore operations;
- filters;
- RPCs;
- configuration retrieval;
- configuration modification;
- XML payloads;
- error handling; and
- device capability differences.

Use `ncclient` for practical Python automation.

### RESTCONF

Implement RESTCONF device automation including:

- authentication;
- resource paths;
- GET operations;
- configuration changes;
- JSON payloads;
- YANG-derived resource structures;
- HTTP status handling;
- error responses; and
- idempotent automation patterns.

Where architecturally justified, introduce a RESTCONF execution or state-collection adapter to the flagship platform rather than replacing the existing CLI implementation.

### Alternative Python Device Automation

Exercise Netmiko as an additional network-device automation library.

This does not replace Scrapli in the flagship platform.

The purpose is to understand implementation differences, operational behavior, failure handling, and common enterprise tooling.

### Ansible

Develop practical network automation using Ansible for:

- inventory;
- variables;
- playbooks;
- network modules;
- configuration management;
- compliance;
- idempotency;
- templates;
- failure handling; and
- repeatable branch operations.

The same branch problems used by the flagship platform should be reimplemented selectively with Ansible to compare approaches.

### Jinja2

Develop advanced templating competence including:

- variables;
- conditionals;
- loops;
- filters;
- reusable templates; and
- deterministic configuration rendering.

### pyATS

Introduce pyATS as an independent validation framework.

Use it for:

- operational checks;
- pre-change validation;
- post-change validation;
- snapshots;
- comparison;
- topology-aware testing; and
- later CI/CD integration.

The existing platform validation engine remains valuable and is not replaced merely to use pyATS.

### IOS XE On-Box and Day-0 Automation

Practice enterprise device automation capabilities where suitable, including:

- EEM;
- Guest Shell;
- on-box Python; and
- Day-0 / ZTP concepts and implementation.

These capabilities may live primarily in companion labs unless a clear flagship-platform requirement emerges.

### Telemetry Foundations

Establish model-driven telemetry foundations, including:

- subscriptions;
- telemetry models;
- data transport;
- collection;
- interpretation; and
- operational use cases.

V1.5 focuses on understanding and producing telemetry.

Broader operational integration belongs in V2.

### V1.5 Completion Criteria

V1.5 is complete when the project and companion labs demonstrate practical working knowledge of:

```text
YANG
NETCONF
RESTCONF
ncclient
Netmiko
Ansible
Jinja2
pyATS
IOS XE model-driven automation
Day-0 / on-box automation
telemetry foundations
```

Completion requires more than successful happy-path labs.

Important technologies should also be deliberately broken, diagnosed, and recovered.

## V2 — NetDevOps Automation Ecosystem

### Objective

Extend the project from device and protocol automation into the broader delivery, infrastructure, operational, controller, security, and AI ecosystem expected of a modern NetDevOps platform.

V2 emphasizes automation systems rather than individual automation scripts.

## Infrastructure as Code

### Terraform

Develop practical Terraform automation including:

- providers;
- resources;
- variables;
- outputs;
- state;
- plans;
- idempotency;
- drift;
- dependency handling; and
- appropriate network automation use cases.

Terraform should be used where declarative infrastructure management provides a meaningful advantage rather than being inserted into the flagship project unnecessarily.

### Source of Truth

Expand source-of-truth concepts beyond the current inventory and intent files.

Evaluate and implement a more complete source-of-truth integration when it improves the architecture.

The source of truth should remain authoritative rather than becoming a second copy of device state.

## CI/CD and GitOps

Introduce a complete network automation delivery pipeline using GitLab CI/CD.

The target lifecycle is:

```text
commit / merge request
        ↓
lint
        ↓
automated tests
        ↓
build / package
        ↓
digital-twin preparation
        ↓
pre-change validation
        ↓
plan
        ↓
manual approval
        ↓
deployment
        ↓
post-change validation
        ↓
published evidence
```

GitHub remains the canonical public repository and portfolio.

GitLab is introduced as an additional CI/CD execution and learning environment rather than replacing GitHub.

## CML Digital-Twin Automation

Expand CML usage from manually operated lab infrastructure into programmable test infrastructure.

Planned capabilities include:

- topology lifecycle automation;
- API-driven startup and teardown;
- reusable test environments;
- CI integration;
- pre-change simulations; and
- automated validation against representative network state.

## Containers and Runtime Environment

Use Docker and Docker Compose where they improve reproducibility of the automation environment.

Potential components include:

- automation services;
- validation tooling;
- telemetry collectors;
- GitLab runners;
- supporting APIs; and
- development dependencies.

Containers should support the architecture rather than force a microservice design.

## Operations and Observability

Expand operational capabilities around:

- model-driven telemetry;
- structured logging;
- syslog;
- webhooks;
- troubleshooting evidence;
- health checks;
- automation execution records; and
- failure diagnostics.

A full observability platform is not required.

## Security

Strengthen automation security practices including:

- secret management;
- environment isolation;
- input validation;
- authentication;
- authorization;
- TLS;
- certificate handling;
- least privilege;
- secure CI/CD variables; and
- safe handling of automation outputs.

Secrets must not be committed to source control.

## Enterprise Controller Automation

Develop practical controller-based automation using appropriate Cisco environments and sandboxes.

Target technologies include, where relevant to the current certification and engineering objectives:

- Catalyst Center;
- SD-WAN Manager;
- Meraki;
- ISE; and
- ThousandEyes.

Controller-specific exercises do not need to be forced into the flagship platform.

They may be implemented in the companion enterprise automation lab when that produces a cleaner design.

## AI-Assisted Network Automation

Introduce AI only after deterministic automation and safety boundaries are established.

Potential V2 work includes:

- AI-assisted development;
- evaluating AI-generated network recommendations;
- constrained read-only network tools;
- FastMCP;
- MCP servers;
- conversational automation interfaces; and
- guarded integration with structured platform APIs.

The intended architecture is:

```text
AI / agent
    ↓
query / propose / explain
    ↓
structured platform interfaces
    ↓
existing validation and safety controls
    ↓
operator approval where required
    ↓
controlled execution
```

Direct unrestricted LLM-to-device configuration is not an intended platform design.

## V2 Completion Criteria

V2 is complete when the combined platform and companion automation environment demonstrate:

- declarative infrastructure automation;
- GitLab-based network CI/CD;
- programmable CML test infrastructure;
- reproducible containerized tooling;
- stronger source-of-truth integration;
- operational telemetry and evidence;
- secure automation practices;
- enterprise controller/API automation;
- AI/MCP integration behind explicit safety boundaries; and
- end-to-end automation workflows that can be explained, tested, and reproduced.

## Companion Automation Environment

Not every technology belongs in the Network Automation Platform repository.

A separate companion project may be maintained for automation technologies whose primary purpose is breadth, comparison, controller experimentation, or certification-aligned practice.

A suitable structure is:

```text
network-automation-platform
    ↓
flagship engineering system
production-style architecture
safe deployment
validation
deep implementation

enterprise-network-automation-lab
    ↓
technology breadth
framework comparison
controller APIs
protocol labs
CI/CD exercises
certification evidence
```

This is not a decomposition of the flagship platform into multiple services.

The two repositories have different responsibilities.

The flagship platform remains cohesive.

## Certification Alignment

CCNP Automation provides a useful external competency framework for the roadmap.

The certification blueprint influences the technologies and practical exercises used during V1.5 and V2, but certification coverage does not override platform architecture.

A separate coverage document maps certification objectives to:

- platform functionality;
- companion labs;
- theory;
- troubleshooting exercises;
- Cisco-hosted environments;
- portfolio evidence; and
- interview competencies.

See [CCNP Automation Coverage](ccnp-automation-coverage.md).

## Job and Portfolio Objective

The roadmap is also designed to produce defensible engineering evidence.

By completion, the portfolio should demonstrate the ability to:

- model intent and desired state;
- collect and normalize network state;
- detect and classify drift;
- design targeted remediation;
- automate safely through multiple mechanisms;
- work with CLI and model-driven interfaces;
- validate before and after change;
- build CI/CD around network operations;
- automate enterprise controllers;
- work with telemetry and operational feedback;
- design for failure;
- secure automation workflows; and
- use AI-assisted automation without bypassing deterministic safety controls.

The objective is not merely to accumulate technologies.

Each major capability should be understandable, reproducible, testable, and explainable.
