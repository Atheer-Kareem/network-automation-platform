# Platform Roadmap

## Purpose

This roadmap defines the planned evolution of the Network Automation Platform from the current V1 foundation through V1.5 and V2.

The roadmap is engineering-led.

Certification objectives, including CCNP Automation, are used to identify useful technologies and practical competencies, but they do not determine the architecture of the flagship platform.

A technology is incorporated into the Network Automation Platform only when it strengthens the platform design or provides a justified implementation capability.

Broader technology practice that does not belong naturally in the flagship runtime may be implemented as isolated practical work in this repository. It does not become a production-package release gate merely because it shares the repository.

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

V1 is complete against its defined engineering acceptance criteria. Version `1.0.0` is tagged and published as the V1.0.0 GitHub release. No V1 implementation or release work remains.

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

Broader automation technologies may be exercised in isolated in-repository practical tracks:

```text
network-automation-platform
    ↓
alternative frameworks
model-driven protocols
controller APIs
CI/CD exercises
technology-specific labs
certification coverage
```

Production runtime and practical tracks must remain separate in ownership, dependency sets, CI gates, credentials/trust state, and support level. A second repository is considered only when an independent ownership, security, deployment, access-control, lifecycle, licensing, or release-cadence boundary exists.

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
- required OSPF-learned route outcome validation;
- VLAN validation;
- switchport validation;
- expected OSPF adjacency validation;
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
- full post-change desired-state validation;
- explicit deployment outcomes; and
- schema-versioned deployment evidence JSON.

Targeted interface remediation now supports missing managed interfaces/SVIs, description mismatch, IPv4 address or prefix-length mismatch, and administrative-state mismatch.

Targeted VLAN remediation now supports missing managed VLANs and VLAN name mismatch.

Targeted switchport remediation now supports administrative-mode mismatch, access-VLAN mismatch, and trunk allowed-VLAN mismatch.

### V1 Completion Record

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

#### 5. Routing and OSPF validation [Completed]

Extend validation beyond configuration presence toward network behavior.

Expected OSPF adjacency validation is complete. The peer address is explicit branch intent and generic validation checks the mapped WAN interface and normalized `FULL` state. IOS adjacency-role suffixes are normalized at the collector boundary.

OSPF-learned route outcome implementation is complete. Branch intent explicitly requires `10.200.0.1/32` within the OSPF context. Validation derives the next hop from the expected peer and the outgoing interface from the mapped `wan` role, then checks the prefix, IOS OSPF protocol, next hop, and interface. Additional routes remain permitted; administrative distance, metric, route subtype, and ECMP cardinality are not validated.

OSPF adjacency and learned-route failures remain unsupported for remediation and block branch deployment before writes. Live CML acceptance of adjacency and learned-route outcome validation is complete.

#### 6. Deployment evidence and reporting [Completed]

Completed branch deployment results can be transformed into durable, machine-readable schema-version `1` evidence containing:

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

The optional `nap deploy --report-json PATH` interface writes readable UTF-8 JSON for compliant, blocked, declined, successful, and failed workflow outcomes. Reports intentionally exclude credentials, SSH settings, secrets, and connection objects.

Reporting remains separate from orchestration and device execution. It never authorizes writes, never retries deployment, and adds no rollback or multi-device transaction semantics. Broader retention and external audit-system integration remain future work.

Implementation, automated coverage, and live acceptance of schema-version `1` JSON evidence are complete.

#### 7. Failure-path hardening [Completed]

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

The automated coverage audit and current evidence are recorded in the [V1 failure-path matrix](../acceptance/v1-failure-path-matrix.md). All eleven paths have deterministic automated evidence, and the selected safe live subset for unreachable, authentication, and host-key failures completed successfully. Destructive or unsafe post-write failure injection is intentionally excluded. Failure-path hardening is complete for V1.

#### 8. V1 acceptance and release [Completed]

Release-gate evidence and the completed final representative scenario are recorded in the [V1 acceptance report](../acceptance/v1-acceptance-report.md).

V1 is complete when:

- supported remediation works across multiple drift categories;
- unsupported or unsafe changes fail closed;
- branch-wide preflight occurs before writes;
- routing validation proves meaningful operational state;
- major failure paths are tested;
- operator documentation is complete;
- representative CML acceptance scenarios pass; and
- architecture documentation accurately describes the implemented system.

All defined V1 capability and release criteria are satisfied. Engineering acceptance, the `v1.0.0` tag, and GitHub release publication are complete.

## V1.5 — Model-Driven and Device-Automation Bridge

### Objective

Preserve the released V1 deterministic lifecycle and branch-01 compatibility while adding one production Cisco IOS XE NETCONF read/write path.

The authoritative architecture and completion contract are defined in the [V1.5 architecture overview](../architecture/v1.5-overview.md) and [ADR-0005](../adr/0005-v15-product-scope-and-compatibility.md).

### Production Capability Sequence

The expected engineering sequence is:

1. establish this architecture and documentation baseline;
2. verify a minimal Cisco Catalyst 8000V IOS XE 17.15.01a scenario in CML 2.10, including the preferred routed management-loopback direction;
3. normalize access and inventory backward-compatibly while retaining current `inventory/lab.yaml` behavior;
4. introduce one explicit application composition boundary shared by validate, plan, and deploy;
5. inspect trusted IOS XE capabilities/models and normalize a narrow NETCONF interface-state read meaningfully with CLI state;
6. rebuild and validate fresh management-safety evidence immediately before writes;
7. recompute the required remediation and fail closed unless it is equivalent to the exact approved immutable change;
8. introduce the smallest typed NETCONF execution artifact and approval binding required by the first real write;
9. execute one harmless description-only NETCONF remediation on a non-management, non-routing-critical interface and introduce schema-version `2` evidence without changing schema version `1`;
10. harden adapter security and failure paths, run branch-01 regression, and complete final cross-path CML acceptance; and
11. release `v1.5.0` only after the measurable completion contract passes.

The sequence describes dependencies, not fixed PR numbering. Safety, compatibility, automated evidence, and focused live acceptance accompany the increments they affect rather than being deferred entirely to the end.

### Concrete Model-Driven Scenario

Branch-01 remains unchanged as the V1 regression/reference environment. The preferred new scenario is a second representative branch using the current branch shape initially, with a Cisco Catalyst 8000V router as the model-driven target. Exact topology, addressing, interface mappings, bootstrap, routing, and YANG paths remain subject to local feasibility evidence.

The first read capability is interface state. Full NETCONF parity with routes, OSPF, VLANs, and switchports is not required. The first write is a description-only change on a non-management, non-routing-critical interface. Existing CLI collection may provide complete post-change observation for that first NETCONF write.

### Compatibility and Safety Gates

V1.5 preserves:

- branch-01 intent and current inventory compatibility;
- existing validate, plan, and deploy behavior;
- Cisco IOS/Scrapli collection and execution;
- targeted remediation and all V1 fail-closed guarantees; and
- deployment-report schema version `1`.

Immediately before every eventual V1.5 write, trusted target access and identity, a freshly rebuilt management-safety expectation, fresh required state, and approved-plan equivalence must pass. The exact approved artifact is then executed, followed by fresh complete post-change collection and validation. This reduces but does not eliminate TOCTOU risk.

### Composition and Evidence Gates

Validate, plan, and deploy share an explicit application composition root or factory. Read, render, execute, discovery, and safety responsibilities remain separate. Declared/allowed capabilities constrain live discovery; discovery never silently authorizes or selects an unapproved mechanism. Unsupported combinations fail closed. A dynamic plugin framework is not required.

Read-only NETCONF precedes final write-artifact design. The first stable NETCONF write drives the smallest immutable typed execution artifact. Approval preview and machine payload derive from that artifact. Schema version `1` remains unchanged; schema version `2` begins only when durable model-driven execution evidence exists.

### Parallel Learning and Portfolio Track

The following remain important engineering or certification-aligned practical areas in this repository, isolated from production runtime dependencies and package release gates:

- RESTCONF and YANG exploration beyond the selected NETCONF implementation;
- Ansible network automation;
- Netmiko comparison;
- Jinja2 where a real templating problem exists;
- pyATS/Genie independent acceptance evidence;
- model-driven telemetry with a selected consumer;
- Day-0/ZTP;
- Guest Shell and on-box Python; and
- EEM.

pyATS may provide a small independent final-acceptance cross-check. It does not replace NAP validation and is not a production deployment-service dependency by default. Production RESTCONF write parity is not a `v1.5.0` requirement unless a later ADR establishes a distinct need.

### V1.5 Completion Criteria

V1.5 is complete when measurable evidence proves:

- the released branch-01 path remains compatible;
- one reproducible IOS XE model-driven scenario exists;
- access/composition distinguishes platform, endpoint, and selected access method without transport policy entering domain logic;
- CLI and NETCONF normalize interface state meaningfully;
- validate, plan, and deploy share one explicit composition boundary;
- immediate pre-write safety uses fresh evidence and stale approved plans fail closed;
- one harmless NETCONF remediation passes the V1 controlled lifecycle;
- non-CLI evidence is explicitly versioned without breaking schema version `1`;
- adapter trust, authentication, identity, capability, error-redaction, execution, and post-check failures are tested;
- final CML acceptance proves branch-01 regression and the selected IOS XE scenario; and
- documentation and ADRs accurately describe behavior and limitations.

Learning exercises are not production-package completion criteria.

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

They may be implemented as isolated in-repository practical work when that produces a cleaner design.

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

V2 is complete when the combined platform and isolated practical environments demonstrate:

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

## Single-Repository Production and Practical Tracks

The Network Automation Platform remains the single canonical repository by default:

```text
network-automation-platform
    ↓
production package and maintained integrations
intent, inventory, topology, and evidence
isolated practical protocol/framework work
documentation and certification coverage
```

Same repository does not mean one Python package, dependency group, CI gate, credential boundary, or support level. Practical work must not become an alternate uncontrolled device-write path or a production runtime dependency by accident. Exact directories are introduced only with concrete assets.

Repository separation remains possible only when independent ownership, deployment, security, access control, lifecycle, licensing, or release cadence justifies it.

## Certification Alignment

CCNP Automation provides a useful external competency framework for the roadmap.

The certification blueprint influences the technologies and practical exercises used during V1.5 and V2, but certification coverage does not override platform architecture.

A separate coverage document maps certification objectives to:

- platform functionality;
- in-repository practical work;
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
