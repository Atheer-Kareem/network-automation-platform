# Company Context

## Overview

The Network Automation Platform models a growing mid-sized financial-services organisation with a distributed enterprise network.

The organisation operates:

- a Melbourne headquarters;
- a primary data-centre environment;
- a disaster-recovery capability;
- multiple branch offices;
- internet and cloud connectivity; and
- a predominantly Cisco network with future multi-vendor requirements.

The network has grown faster than the operating model used to manage it.

As the environment expands, manual device administration creates increasing operational risk and makes consistent network change difficult to scale.

## Current Operational Model

Network operations rely heavily on manual, device-by-device administration.

Common activities include:

- manual CLI configuration;
- spreadsheet-based inventory and IP address management;
- manual configuration backups;
- repetitive branch provisioning;
- manual pre-change and post-change verification;
- inconsistent configuration standards;
- limited configuration-drift detection;
- limited automated compliance checking;
- fragmented operational evidence; and
- operational knowledge concentrated among individual engineers.

Automation exists only in isolated tasks rather than as part of a consistent network delivery lifecycle.

## Business Risks

The existing operating model creates several risks:

- configuration inconsistency;
- human error during repetitive changes;
- slow branch deployment;
- weak auditability;
- configuration drift;
- difficult rollback and recovery;
- inconsistent compliance enforcement;
- limited visibility into intended versus actual network state;
- inconsistent change validation;
- operational dependence on individual engineers; and
- limited scalability as the network grows.

These risks are particularly important in a financial-services environment where availability, security, change control, traceability, and auditability are critical.

## Transformation Goal

The organisation wants to move from traditional manual network operations toward a controlled NetDevOps operating model.

The goal is not simply to replace CLI commands with scripts.

The target operating model should provide a repeatable engineering lifecycle around network changes:

```text
authoritative intent
        ↓
automated validation
        ↓
planned change
        ↓
controlled execution
        ↓
independent verification
        ↓
operational evidence
```

Automation should be introduced incrementally.

The organisation does not want unrestricted or autonomous configuration changes before deterministic validation, safety controls, operational evidence, and human governance have been established.

## Transformation Principles

### Intent before implementation

Network requirements should be represented independently from device-specific configuration wherever practical.

Automation should consume authoritative intent rather than relying on engineers to manually reproduce standards on individual devices.

### Validate before and after change

A successfully executed command does not prove that a network change achieved the intended result.

The operating model should validate both:

- whether the network is safe to change; and
- whether the resulting network state satisfies the intended outcome.

### Small and controlled change scope

Automation should prefer narrowly scoped, explainable changes over unnecessary full-device configuration replacement.

Unsupported or unsafe drift should fail closed rather than trigger speculative remediation.

### Human control at high-risk boundaries

The organisation wants to reduce repetitive manual work without removing accountability.

Configuration writes should remain subject to explicit controls appropriate to the risk of the operation.

### Infrastructure and network changes as software delivery

Network automation should increasingly adopt established software-engineering and DevOps practices including:

- version control;
- peer review;
- automated testing;
- CI/CD;
- reusable environments;
- structured artifacts;
- repeatable releases; and
- auditable execution.

### Operational outcomes over tool success

The organisation is interested in network outcomes rather than merely successful automation jobs.

Routing, reachability, protocol state, service health, and policy compliance should increasingly become part of change validation.

### Security by design

Automation introduces additional access, credential, API, and execution risks.

Secrets, permissions, transport trust, identity validation, and execution boundaries must therefore be designed into the operating model rather than added later.

## Target Progression

The transformation is intentionally incremental.

### Phase 1 — Visibility and Standardisation

1. establish device inventory;
2. collect operational state;
3. standardise branch design;
4. define authoritative network intent;
5. generate deterministic configuration; and
6. introduce automated desired-versus-actual validation.

### Phase 2 — Controlled Automation

7. detect and classify configuration drift;
8. generate narrowly scoped remediation;
9. perform pre-change safety validation;
10. require appropriate operator approval;
11. execute controlled changes;
12. collect fresh post-change state; and
13. validate the resulting network state.

This phase establishes the safe automation foundation before broader automation is introduced.

### Phase 3 — Model-Driven and Framework-Based Automation

14. introduce standards-based device automation using YANG, NETCONF, and RESTCONF;
15. use established automation frameworks where appropriate;
16. strengthen independent automated testing and validation;
17. expand Day-0 and device lifecycle automation; and
18. introduce model-driven telemetry.

The objective is to support multiple automation mechanisms without coupling the organisation to a single tool or protocol.

### Phase 4 — NetDevOps Delivery

19. integrate network automation into CI/CD workflows;
20. introduce programmable digital-twin environments for pre-change testing;
21. strengthen source-of-truth integration;
22. use reproducible containerised automation environments where useful;
23. publish structured change and validation evidence; and
24. improve automated failure diagnosis.

At this stage, network changes increasingly follow the same disciplined delivery practices used for software and infrastructure.

### Phase 5 — Enterprise Platform Automation

25. integrate controller-based network platforms;
26. automate enterprise policy and lifecycle operations;
27. consume network-health and assurance APIs;
28. introduce webhook and event-driven operational workflows; and
29. expand automation across additional network domains and vendors where justified.

Device-level automation remains available, but higher-level platforms are used where they provide stronger abstraction or operational value.

### Phase 6 — Intelligent Operations

30. use AI-assisted tooling to improve engineering productivity and operational analysis;
31. expose constrained network information through structured AI-accessible interfaces;
32. evaluate AI-generated recommendations against deterministic network evidence;
33. use conversational interfaces where they improve operator experience; and
34. consider increasingly automated remediation only where mature safety, validation, governance, and rollback mechanisms exist.

AI is treated as an additional decision-support and automation interface, not as a replacement for deterministic engineering controls.

## Target Operating Model

The long-term operating model is:

```text
Source of Truth / Intent
        ↓
Automation and Policy
        ↓
Simulation / Testing
        ↓
Pre-Change Validation
        ↓
Approval
        ↓
Controlled Deployment
        ↓
Fresh State Collection
        ↓
Post-Change Validation
        ↓
Telemetry / Operational Evidence
        ↓
Compliance and Continuous Improvement
```

Controller APIs, model-driven interfaces, CI/CD systems, and AI-assisted tooling can participate in this lifecycle without bypassing the core safety and validation boundaries.

## Expected Business Outcomes

The transformation should provide:

- faster and more consistent branch deployment;
- reduced repetitive manual configuration;
- improved configuration standardisation;
- earlier detection of drift and non-compliance;
- safer network changes;
- stronger auditability;
- repeatable pre-change and post-change evidence;
- reduced dependence on individual operational knowledge;
- improved troubleshooting information;
- scalable network operations;
- a clearer path toward multi-vendor automation; and
- a controlled foundation for future intelligent operations.

The objective is a network operating model that becomes safer and more repeatable as automation increases, rather than simply becoming faster.
