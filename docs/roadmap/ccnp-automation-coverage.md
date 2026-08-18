# CCNP Automation Coverage

## Purpose

This document maps the current CCNP Automation certification objectives to the engineering roadmap for the Network Automation Platform and related practical work in the same canonical repository.

The certification is used as an external competency framework.

It does not define the architecture of the flagship platform.

The objective is not merely to prepare for two exams.

The objective is to develop practical, demonstrable competence across the technologies and engineering behaviors represented by the certification while producing portfolio evidence that is useful independently of the certification.

Phase labels in this document describe learning and evidence timing. They do not make every listed technology a production-package release criterion. The authoritative `v1.5.0` product contract is the narrower NETCONF path defined in the [V1.5 architecture overview](../architecture/v1.5-overview.md); other V1.5-labelled objectives may proceed as parallel, isolated practical work.

## Blueprint Baseline

This coverage plan was reviewed against the Cisco exam topics current as of August 2026.

The selected certification path is:

```text
350-901 AUTOCOR v2.0
Designing, Deploying and Managing Network Automation Systems

        +

300-435 ENAUTO v2.0
Automating Cisco Enterprise Solutions

        ↓

CCNP Automation
```

AUTOCOR is the core automation exam.

ENAUTO is the selected enterprise concentration because the current project and career direction focus on enterprise network automation.

Cisco may revise exam topics over time.

The official exam topics remain authoritative, and this document should be reviewed whenever Cisco publishes a blueprint revision.

## Coverage Philosophy

Certification objectives are mapped to one or more forms of evidence:

```text
flagship platform implementation
in-repository practical lab
CML exercise
Cisco-hosted sandbox
troubleshooting exercise
design / theory exercise
CI/CD implementation
portfolio documentation
interview explanation
```

A technology is not forced into the flagship platform solely because it appears on an exam blueprint.

The placement rule is:

```text
Does the capability improve the Network Automation Platform architecture?
        │
        ├── Yes
        │     ↓
        │   integrate it where appropriate
        │
        └── No
              ↓
            implement it in an isolated in-repository lab
            or focused practical exercise
```

This preserves both:

```text
engineering depth
        +
certification breadth
```

## Mastery Standard

A topic is not considered mastered merely because a lab executed successfully or a course section was completed.

The target learning cycle is:

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

### Understand

Be able to explain:

- what the technology does;
- why it exists;
- where it belongs architecturally;
- its important protocol or data-model behavior;
- alternatives;
- trade-offs; and
- common limitations.

### Build

When the blueprint requires implementation, construction, configuration, or automation, produce a working solution rather than relying only on theoretical study.

### Break

Deliberately introduce realistic failures where appropriate.

Examples include:

- incorrect credentials;
- invalid YANG paths;
- malformed payloads;
- unreachable devices;
- failed CI jobs;
- broken dependencies;
- invalid configuration;
- certificate problems;
- API errors; and
- incorrect automation assumptions.

### Troubleshoot

Diagnose failures from:

- logs;
- error responses;
- device state;
- pipeline output;
- protocol messages; and
- automation behavior.

Do not treat looking up the final answer immediately as troubleshooting practice.

### Validate

Prove the network or system outcome independently from the automation request itself.

Successful command, RPC, API, or pipeline execution is not sufficient evidence of the intended network result.

### Document

Record useful evidence such as:

- architecture;
- implementation decisions;
- commands;
- code;
- tests;
- failures;
- troubleshooting findings;
- validation results; and
- limitations.

### Explain

Be able to discuss the technology without relying on a memorized script.

An interview-quality explanation should include:

```text
what was built
why it was built
how it works
why that approach was selected
what failed
how it was diagnosed
what alternatives exist
what would change in production
```

## Status Definitions

This document uses the following coverage states:

| Status       | Meaning                                                                                                      |
| ------------ | ------------------------------------------------------------------------------------------------------------ |
| `FOUNDATION` | Existing work provides relevant experience, but the blueprint objective has not yet been completed directly  |
| `PARTIAL`    | Some required practical or theoretical work has been completed                                               |
| `PLANNED`    | Explicitly mapped to future roadmap work                                                                     |
| `MASTERED`   | Required practical, troubleshooting, validation, documentation, and explanation criteria have been completed |

`MASTERED` should be used conservatively.

Exam familiarity alone is not sufficient.

---

# AUTOCOR 350-901 v2.0

## Domain 1 — Network Automation — 30%

### 1.1 Ansible Network Automation

**Objective**

Construct network automation solutions with Ansible for configurations such as:

- VLANs;
- OSPF;
- asset management;
- interfaces; and
- ACLs.

**Roadmap**

```text
V1.5
```

**Primary evidence**

- isolated in-repository enterprise automation lab;
- same representative branch problems used by the flagship platform;
- Ansible inventory and variables;
- network collections/modules;
- idempotent configuration;
- compliance exercises;
- failure handling; and
- comparison with custom Python automation.

**Current status**

`PLANNED`

---

### 1.2 Terraform Network Automation

**Objective**

Construct network automation solutions with Terraform for configuration and infrastructure-management use cases.

**Roadmap**

```text
V2
```

**Primary evidence**

- Terraform configuration;
- providers/resources;
- variables and outputs;
- plan/apply lifecycle;
- Terraform state;
- idempotency;
- drift behavior;
- dependency handling;
- intentionally broken plan/apply scenarios; and
- comparison with imperative automation.

**Current status**

`PLANNED`

---

### 1.3 RESTCONF and YANG Automation

**Objective**

Construct network automation using RESTCONF given a YANG model.

**Roadmap**

```text
V1.5
```

**Primary evidence**

- IOS XE RESTCONF lab;
- YANG model inspection;
- resource-path construction;
- GET and configuration operations;
- JSON payload generation;
- HTTP error handling;
- authentication failures;
- idempotency testing; and
- possible RESTCONF adapter within the flagship platform where architecturally justified.

**Current status**

`PLANNED`

---

### 1.4 Python Network Automation

**Objective**

Construct Python automation for network configuration and operational use cases.

**Roadmap**

```text
V1
→ V1.5
→ V2
```

**Existing evidence**

The flagship platform already includes substantial Python automation for:

- structured intent;
- desired-state modelling;
- configuration rendering;
- Scrapli-based state collection;
- validation;
- drift classification;
- remediation planning;
- controlled deployment;
- failure modelling; and
- automated testing.

**Remaining work**

Use additional interfaces and libraries where the blueprint requires them rather than treating the existing Scrapli implementation as universal coverage.

**Current status**

`PARTIAL`

---

### 1.5 Selecting an Automation Approach

**Objective**

Select an appropriate automation method based on technical and business requirements.

Approaches include:

- Infrastructure as Code;
- low-code / no-code;
- custom applications; and
- automation frameworks.

**Roadmap**

```text
V1
→ V1.5
→ V2
```

**Primary evidence**

Compare real implementations of similar network problems using:

```text
custom Python
Ansible
Terraform
RESTCONF
controller APIs
```

Document when each approach is appropriate and when it is not.

**Current status**

`FOUNDATION`

---

### 1.6 Advanced REST API Consumption

**Objective**

Construct automation that handles production REST API behavior such as:

- advanced authentication;
- persistent authentication;
- pagination;
- rate limiting;
- error handling; and
- more complex API workflows.

**Roadmap**

```text
V1.5
→ V2
```

**Primary evidence**

- reusable Python API client patterns;
- controller APIs;
- authentication lifecycle;
- pagination;
- retry/backoff behavior where appropriate;
- structured errors;
- deliberately failed API calls; and
- controller-specific labs.

**Current status**

`PLANNED`

---

## Domain 2 — Infrastructure as Code — 30%

### 2.1 Git Operations

**Objective**

Use Git operations including:

- branch merging;
- squash;
- conflict resolution;
- `cherry-pick`;
- `reset`;
- `checkout`; and
- `revert`.

**Roadmap**

```text
V1
→ ongoing
```

**Existing evidence**

The flagship project already uses:

- Git;
- feature branches;
- GitHub pull requests;
- structured commits;
- code review;
- documentation review; and
- regular integration into `main`.

**Remaining work**

Deliberately exercise operations not encountered naturally, particularly:

- conflict resolution;
- cherry-pick;
- reset behavior;
- safe revert workflows; and
- squash behavior.

**Current status**

`PARTIAL`

---

### 2.2 Diagnose GitLab CE CI/CD Failures

**Objective**

Troubleshoot pipeline failures such as:

- missing dependencies;
- incompatible component versions; and
- failed tests.

**Roadmap**

```text
V2
```

**Primary evidence**

Self-managed or otherwise suitable GitLab CI/CD environment with deliberately broken jobs.

Troubleshooting should use:

- runner output;
- job logs;
- artifacts;
- dependency information; and
- pipeline status.

**Current status**

`PLANNED`

---

### 2.3 Construct a GitLab CE Network CI/CD Pipeline

**Objective**

Build a pipeline containing:

```text
build
  ↓
prevalidation
  ↓
deploy
  ↓
post-validation
```

**Roadmap**

```text
V2
```

**Target implementation**

```text
GitHub
canonical public repository
        ↓
GitLab CI/CD environment
        ↓
runner
        ↓
lint / tests
        ↓
build
        ↓
CML preparation
        ↓
prevalidation
        ↓
manual approval
        ↓
deployment
        ↓
post-validation
        ↓
published evidence
```

GitLab does not replace GitHub as the canonical portfolio repository.

**Current status**

`PLANNED`

---

### 2.4 Cisco Modeling Labs

**Objective**

Construct network simulations with CML for automation testing.

**Roadmap**

```text
V1
→ V2
```

**Existing evidence**

The representative V1 network already runs in CML and has been used for:

- routing;
- switching;
- real state collection;
- deliberate drift;
- controlled remediation; and
- post-change validation.

**Remaining work**

V2 introduces programmable CML lifecycle management and CI/CD integration.

**Current status**

`PARTIAL`

---

### 2.5 Docker Compose

**Objective**

Interpret Docker Compose concepts including:

- services;
- networks;
- volumes; and
- relationships between services.

**Roadmap**

```text
V2
```

**Primary evidence**

Use Docker Compose to build a reproducible automation environment containing selected components such as:

- automation tooling;
- telemetry services;
- validation dependencies;
- APIs; and
- CI supporting services.

**Current status**

`PLANNED`

---

### 2.6 Source-of-Truth Integration

**Objective**

Integrate an authoritative source of truth into a network automation solution.

**Roadmap**

```text
V1 foundation
→ V2 expansion
```

**Existing evidence**

The project already distinguishes authoritative sources for:

- branch intent;
- inventory;
- OOB addressing;
- device capabilities; and
- generated SSH configuration.

The inventory refactor already proved that environment data can change without embedding lab-specific values in application code.

**Remaining work**

Evaluate and integrate a richer source-of-truth implementation when it provides architectural value.

**Current status**

`PARTIAL`

---

### 2.7 YAML / JSON from YANG-Based Data Models

**Objective**

Construct structured network configuration representations from a YANG-based model.

**Roadmap**

```text
V1.5
```

**Existing foundation**

The platform already uses structured YAML and Python domain models.

**Remaining work**

Explicitly derive JSON/YAML payloads and configuration structures from YANG models rather than treating existing YAML experience as equivalent.

**Current status**

`FOUNDATION`

---

## Domain 3 — Operations — 20%

### 3.1 Model-Driven Telemetry Architecture

**Roadmap**

```text
V1.5
→ V2
```

**Primary evidence**

Understand and implement:

- telemetry components;
- subscriptions;
- models;
- transport;
- collectors;
- data consumers; and
- operational use cases.

**Current status**

`PLANNED`

---

### 3.2 Logging Strategy

**Roadmap**

```text
V2
```

**Primary evidence**

Implement structured automation logging with appropriate destinations such as:

- local structured logs;
- syslog; and
- webhooks.

Logging should support troubleshooting and deployment evidence rather than simply generate output.

**Current status**

`PLANNED`

---

### 3.3 Diagnose Automation Problems from Logs and Output

**Roadmap**

```text
V1 foundation
→ V2 systematic coverage
```

**Existing evidence**

The current development process already includes diagnosis of:

- SSH errors;
- host-key problems;
- device collection failures;
- Pydantic validation failures;
- configuration validation failures; and
- automation test failures.

**Remaining work**

Create deliberate operational scenarios where logs are the primary evidence source.

**Current status**

`FOUNDATION`

---

### 3.4 Change Validation with pyATS

**Roadmap**

```text
V1.5
→ V2 CI/CD
```

**Primary evidence**

Use pyATS independently from the custom validation engine for:

- pre-change state;
- post-change state;
- operational checks;
- snapshots;
- comparison;
- topology-aware validation; and
- CI/CD quality gates.

The platform's custom validation system remains in place.

**Current status**

`PLANNED`

---

### 3.5 CA-Signed TLS Certificates

**Roadmap**

```text
V2
```

**Primary evidence**

Understand and practice:

- certificate signing requests;
- certificate authorities;
- certificate chains;
- trust stores;
- certificate deployment;
- validation; and
- common TLS failures.

**Current status**

`PLANNED`

---

### 3.6 Secure Coding for Network Automation

**Roadmap**

```text
V1 foundation
→ V2 hardening
```

**Existing evidence**

Current platform design already includes:

- strict data validation;
- explicit failure paths;
- Pydantic models;
- secrets separated from inventory;
- strict SSH host-key verification;
- device identity checks;
- controlled write boundaries; and
- explicit operator approval.

**Remaining work**

Expand coverage around:

- secret management;
- authentication;
- authorization;
- least privilege;
- TLS;
- secure CI variables;
- API credentials; and
- input attack scenarios.

**Current status**

`PARTIAL`

---

## Domain 4 — AI in Automation — 20%

### 4.1 AI-Assisted Code Development

**Roadmap**

```text
V2
```

Cover benefits and risks including:

- productivity;
- incorrect output;
- data privacy;
- intellectual-property concerns;
- code validation; and
- over-reliance on generated solutions.

**Current status**

`PLANNED`

---

### 4.2 AI Security Risks

**Roadmap**

```text
V2
```

Study and exercise risks such as:

- sensitive-data disclosure;
- untrusted output;
- excessive permissions;
- unsafe tool access;
- prompt-driven misuse;
- hallucinated network recommendations; and
- loss of deterministic control.

**Current status**

`PLANNED`

---

### 4.3 FastMCP Network MCP Server

**Roadmap**

```text
V2
```

**Target architecture**

```text
AI agent
    ↓
FastMCP server
    ↓
structured read-only network tools
    ↓
platform interfaces / network APIs
```

Write operations, if ever exposed, must remain behind deterministic safety and approval controls.

**Current status**

`PLANNED`

---

### 4.4 Conversational LLM Automation Agent

**Roadmap**

```text
V2
```

Construct a constrained conversational automation interface that can:

- query network information;
- explain state;
- consume MCP tools;
- reason over structured results; and
- propose actions without bypassing platform controls.

**Current status**

`PLANNED`

---

### 4.5 Evaluate AI Recommendations

**Roadmap**

```text
V2
```

Provide deliberately correct, incomplete, unsafe, and hallucinated automation recommendations and evaluate them using networking and automation knowledge.

The engineer remains responsible for determining whether an AI recommendation is technically valid.

**Current status**

`PLANNED`

---

# ENAUTO 300-435 v2.0

## Domain 1 — Network Automation Foundation — 10%

### 1.1 OpenConfig, IETF, and Native YANG Models

**Roadmap**

```text
V1.5
```

Compare:

- native Cisco YANG models;
- IETF models; and
- OpenConfig models.

Understand namespace, portability, platform-specific capability, and practical selection trade-offs.

**Current status**

`PLANNED`

---

### 1.2 NETCONF and RESTCONF

**Roadmap**

```text
V1.5
```

Understand protocol architecture and practical differences including:

- transports;
- data representation;
- operations;
- datastores;
- HTTP behavior;
- capabilities;
- error handling; and
- model dependency.

**Current status**

`PLANNED`

---

### 1.3 JSON Payload from a YANG Model

**Roadmap**

```text
V1.5
```

Use tools such as YANG Suite and `pyang` to inspect models and construct valid JSON.

**Current status**

`PLANNED`

---

### 1.4 XML Payload from a YANG Model

**Roadmap**

```text
V1.5
```

Construct and validate XML payloads from YANG models for NETCONF use.

**Current status**

`PLANNED`

---

### 1.5 Interpret a YANG Module Tree

**Roadmap**

```text
V1.5
```

Be able to read a YANG tree and determine:

- hierarchy;
- containers;
- lists;
- leaves;
- keys;
- configuration versus operational data; and
- paths required by NETCONF/RESTCONF automation.

**Current status**

`PLANNED`

---

## Domain 2 — Device-Level Network Automation — 25%

### 2.1 Python with Netmiko

**Roadmap**

```text
V1.5
```

Implement real IOS XE collection and configuration workflows with Netmiko.

Compare behavior with the flagship Scrapli implementation.

**Current status**

`PLANNED`

---

### 2.2 Python with ncclient

**Roadmap**

```text
V1.5
```

Use `ncclient` for:

- capability discovery;
- configuration retrieval;
- filtered retrieval;
- edit-config operations;
- XML payloads;
- errors; and
- NETCONF troubleshooting.

**Current status**

`PLANNED`

---

### 2.3 Python with RESTCONF

**Roadmap**

```text
V1.5
```

Build Python RESTCONF automation for configuration and monitoring.

**Current status**

`PLANNED`

---

### 2.4 Ansible Device Configuration Management

**Roadmap**

```text
V1.5
```

Use Ansible against the representative enterprise environment for configuration and compliance.

**Current status**

`PLANNED`

---

### 2.5 Day-0 Provisioning

**Roadmap**

```text
V1.5
```

Build and understand a repeatable Day-0 provisioning workflow.

The implementation may remain isolated practical work if it does not naturally belong in the flagship platform.

**Current status**

`PLANNED`

---

### 2.6 Troubleshoot RESTCONF, NETCONF, and YANG

**Roadmap**

```text
V1.5
```

Deliberately diagnose:

- wrong resource paths;
- unsupported models;
- namespace problems;
- malformed JSON;
- malformed XML;
- authentication errors;
- capability mismatches;
- RPC errors; and
- device-side configuration rejection.

**Current status**

`PLANNED`

---

### 2.7 EEM, Guest Shell, and On-Box Python

**Roadmap**

```text
V1.5
```

Develop practical exercises around:

- EEM;
- IOS XE Guest Shell; and
- on-box Python.

These are primarily isolated practical capabilities unless a justified flagship use case emerges.

**Current status**

`PLANNED`

---

## Domain 3 — Controller-Based Network Automation — 30%

Controller automation provides the largest ENAUTO domain and is intentionally treated as a major V2 workstream.

Target platforms include appropriate combinations of:

```text
Catalyst Center
Cisco SD-WAN
Meraki
ISE
ThousandEyes
```

Cisco-hosted sandbox environments should be used where local deployment is impractical.

---

### 3.1 Controller-Based Day-0 Provisioning

**Roadmap**

```text
V2
```

Build controller-driven onboarding / provisioning workflows.

**Current status**

`PLANNED`

---

### 3.2 Controller Automation with Python

**Roadmap**

```text
V2
```

Use Python and controller APIs to manage and monitor enterprise network configuration and state.

**Current status**

`PLANNED`

---

### 3.3 Advanced Jinja2 Templates

**Roadmap**

```text
V1.5 foundation
→ V2 controller use
```

Exercise:

- loops;
- conditionals;
- filters;
- output modification;
- reusable structures; and
- complex configuration generation.

**Current status**

`PLANNED`

---

### 3.4 Controller Automation with Ansible

**Roadmap**

```text
V2
```

Implement controller-based Ansible workflows where supported and useful.

**Current status**

`PLANNED`

---

### 3.5 Security Automation

**Roadmap**

```text
V2
```

Exercise automation scenarios involving:

- policy enforcement;
- compliance;
- segmentation; and
- security-controller APIs.

ISE is a likely isolated practical environment for this work.

**Current status**

`PLANNED`

---

### 3.6 Troubleshoot Controller REST APIs

**Roadmap**

```text
V2
```

Deliberately introduce and diagnose:

- authentication failures;
- authorization failures;
- invalid endpoints;
- invalid payloads;
- asynchronous task failures;
- rate limits;
- API version differences; and
- controller-specific error behavior.

**Current status**

`PLANNED`

---

## Domain 4 — Operations — 20%

### 4.1 Cisco Platform APIs for Testing and Validation

**Roadmap**

```text
V2
```

Use controller/platform APIs as independent evidence during automation validation.

**Current status**

`PLANNED`

---

### 4.2 Network Topology Simulation

**Roadmap**

```text
V1 foundation
→ V2 automation
```

The current CML environment already provides representative simulation.

V2 extends this into programmable digital-twin workflows and CI/CD.

**Current status**

`PARTIAL`

---

### 4.3 Controller-Based Software Management

**Roadmap**

```text
V2
```

Construct controller workflows for software-image or version management using suitable Cisco platforms.

**Current status**

`PLANNED`

---

### 4.4 Controller-Based Network Health Monitoring

**Roadmap**

```text
V2
```

Use controller APIs to collect, analyze, and validate network health.

**Current status**

`PLANNED`

---

### 4.5 IOS XE Model-Driven Telemetry Subscription

**Roadmap**

```text
V1.5
```

Configure and validate model-driven telemetry through methods including:

- CLI;
- NETCONF; and
- RESTCONF.

**Current status**

`PLANNED`

---

### 4.6 Controller Webhook Monitoring

**Roadmap**

```text
V2
```

Implement webhook-driven monitoring and event handling.

Validate:

- event delivery;
- payload parsing;
- authentication where relevant;
- failure handling; and
- idempotent processing.

**Current status**

`PLANNED`

---

## Domain 5 — AI in Automation — 15%

### 5.1 AI in Controller-Based Platforms

**Roadmap**

```text
V2
```

Understand how AI capabilities are exposed through enterprise networking platforms and where they provide operational value.

**Current status**

`PLANNED`

---

### 5.2 AI-Assisted Automation Development

**Roadmap**

```text
V2
```

Evaluate AI-assisted development as an engineering tool rather than an authority.

**Current status**

`PLANNED`

---

### 5.3 AI Security Risks

**Roadmap**

```text
V2
```

Shared with AUTOCOR AI-security work but evaluated in enterprise controller and network-automation contexts.

**Current status**

`PLANNED`

---

### 5.4 FastMCP Network MCP Server

**Roadmap**

```text
V2
```

This overlaps directly with AUTOCOR and should be satisfied through one well-designed implementation rather than duplicated solely for exam coverage.

**Current status**

`PLANNED`

---

# Shared Competency Map

Many AUTOCOR and ENAUTO objectives overlap.

They should be implemented once at sufficient depth rather than duplicated artificially.

| Competency             | AUTOCOR            | ENAUTO                         | Primary Roadmap |
| ---------------------- | ------------------ | ------------------------------ | --------------- |
| Python automation      | Yes                | Yes                            | V1 → V1.5       |
| Ansible                | Yes                | Yes                            | V1.5            |
| RESTCONF               | Yes                | Yes                            | V1.5            |
| YANG                   | Yes                | Yes                            | V1.5            |
| CML                    | Yes                | Yes                            | V1 → V2         |
| Git                    | Yes                | Supporting skill               | V1              |
| GitLab CI/CD           | Yes                | Supporting skill               | V2              |
| Terraform              | Yes                | Supporting skill               | V2              |
| pyATS / validation     | Yes                | Related operational validation | V1.5 → V2       |
| Telemetry              | Yes                | Yes                            | V1.5 → V2       |
| REST APIs              | Yes                | Yes                            | V1.5 → V2       |
| Controller automation  | Platform awareness | Major domain                   | V2              |
| Secure automation      | Yes                | Yes                            | V1 → V2         |
| FastMCP                | Yes                | Yes                            | V2              |
| AI-assisted automation | Yes                | Yes                            | V2              |

## Flagship Platform Evidence

The flagship `network-automation-platform` should provide deep evidence in areas such as:

```text
Python engineering
intent modelling
desired state
inventory
source-of-truth principles
configuration rendering
state collection
validation
drift classification
targeted remediation
safe deployment
identity safety
failure handling
CML testing
Git engineering workflow
model-driven adapters where justified
pyATS integration where useful
CI/CD integration
telemetry integration
secure automation boundaries
AI/MCP integration behind safety controls
```

## In-Repository Practical Evidence

Isolated practical work can provide breadth without distorting the flagship architecture or production dependency set.

Likely areas include:

```text
Netmiko
ncclient
standalone RESTCONF exercises
Ansible comparison labs
Terraform
YANG Suite
EEM
Guest Shell
ZTP / Day-0
Catalyst Center
SD-WAN
Meraki
ISE
ThousandEyes
controller-specific Ansible
controller APIs
software-management exercises
security automation
webhooks
```

The exact directory structure is intentionally undecided until the first concrete asset establishes its ownership and dependency needs. Practical work must still use professional engineering practices rather than becoming an unstructured collection of certification scripts. It must not import secrets or trust state, enter the production package accidentally, or create an alternate uncontrolled write path.

## Portfolio Evidence Standard

A completed technology should ideally leave visible evidence such as:

```text
README / architecture explanation
source code
structured configuration
automated tests
sample failure scenarios
troubleshooting notes
validation results
CI evidence
lab topology
design decisions
limitations
```

The portfolio should demonstrate both:

```text
depth
    ↓
how a production-style automation platform is engineered

breadth
    ↓
how common enterprise automation technologies are applied
```

## Interview Readiness

The certification roadmap and interview roadmap intentionally reinforce each other.

For each major technology, be prepared to answer:

```text
What problem does it solve?

How did you use it?

Why did you choose that implementation?

What alternatives did you consider?

What happens when it fails?

How did you validate the result?

How would the design change at larger scale?

What security concerns exist?

Where does it fit into an end-to-end NetDevOps workflow?
```

The ability to explain these decisions is considered part of completion.

## Exam Readiness

Exam preparation occurs after practical coverage, not instead of it.

The intended sequence is:

```text
engineering implementation
        ↓
practical labs
        ↓
failure and troubleshooting
        ↓
documentation
        ↓
blueprint audit
        ↓
targeted theory revision
        ↓
practice questions
        ↓
remaining gap remediation
        ↓
exam
```

The exam should validate an existing body of practical competence rather than become the primary evidence of that competence.

## Final Coverage Audit

Before scheduling the certification exams, review the official Cisco blueprints line by line.

Each objective should have an explicit disposition:

```text
MASTERED
or
GAP IDENTIFIED
```

No objective should be marked complete merely because another technology appears conceptually similar.

Examples:

```text
Scrapli experience
    ≠
Netmiko objective completed

custom validation engine
    ≠
pyATS objective completed

GitHub Actions knowledge
    ≠
GitLab CE objective completed

YAML experience
    ≠
YANG-derived payload construction completed
```

Where Cisco names a specific implementation technology, that technology should be practiced directly.

## Review Policy

Review this document when:

- Cisco publishes a new AUTOCOR blueprint;
- Cisco publishes a new ENAUTO blueprint;
- a roadmap phase is completed;
- a major platform capability is added;
- an in-repository practical lab is completed; or
- exam preparation begins.

The official Cisco exam topics always take precedence over this internal mapping.

The goal is complete coverage without allowing certification requirements to weaken the engineering architecture.
