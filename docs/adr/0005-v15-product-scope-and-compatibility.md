# ADR-0005: Bound V1.5 to One Compatible Model-Driven Path

## Status

Accepted

## Context

V1.0.0 proved and published a deterministic Cisco IOS/Scrapli branch lifecycle with intent, normalized state, validation, targeted remediation, branch-wide preflight, approval, pre-change safety, controlled execution, fresh post-change collection, full validation, and schema-versioned evidence.

The earlier V1.5 roadmap grouped model-driven protocols, alternative automation libraries, external validation, on-box automation, Day-0, and telemetry into one release gate. A bottom-up repository audit found that the immediate engineering constraints are narrower: branch workflows compose Cisco implementations directly, inventory and settings represent one CLI access method, pre-write safety uses the original preflight snapshot, and execution/evidence are CLI-text shaped.

Making every automation technology a package release requirement would mix platform evolution with learning breadth and encourage abstractions before a second real implementation establishes their requirements.

## Decision

V1.5 will preserve the released V1 path and add one production Cisco IOS XE NETCONF read/write path.

The production scope includes:

- backward-compatible access and inventory evolution;
- explicit composition shared by validate, plan, and deploy;
- normalized NETCONF interface-state collection;
- fresh management-safety evidence and approved-plan equivalence immediately before writes;
- one harmless controlled NETCONF remediation; and
- typed non-CLI execution and versioned evidence only when required by that write.

Branch-01 remains unchanged as the V1 regression/reference environment. Existing intent, inventory input, CLI behavior, Cisco IOS/Scrapli operation, targeted remediation, safety guarantees, and deployment-report schema version `1` remain compatible through additive migration.

NETCONF is the only required production model-driven write protocol for `v1.5.0`. RESTCONF, Ansible, Netmiko, Jinja2, pyATS, telemetry, Day-0/ZTP, Guest Shell, EEM, and related work may remain in the same repository as future engineering or practical learning, but they are not production-package release gates.

One canonical repository remains the default. Production runtime and practical work must retain separate ownership, dependencies, CI, secrets, and support boundaries. Repository separation requires a concrete ownership, security, deployment, access-control, lifecycle, licensing, or release-cadence reason.

## Rationale

One real second adapter is sufficient to test whether the V1 domain boundaries can support model-driven automation. It exposes composition, capability, trust, state normalization, execution, approval, and evidence requirements without duplicating those costs across two write protocols.

Backward compatibility keeps the published V1 evidence meaningful and enables incremental, reversible implementation. Deferring the final executor and report-schema shape until the first concrete NETCONF write avoids designing a universal transaction model from hypothetical requirements.

Separating product acceptance from learning breadth keeps engineering value ahead of technology collection while retaining one repository for related practical work.

## Consequences

### Positive

- V1 remains a continuously tested regression baseline;
- V1.5 has measurable production completion criteria;
- the first real model-driven adapter drives only necessary abstractions;
- broader practical work can proceed without delaying the package release;
- schema version `1` consumers remain supported; and
- repository structure can evolve from concrete dependency and ownership needs.

### Negative

- V1.5 does not provide production RESTCONF write parity;
- model-driven state coverage begins narrowly with interfaces;
- compatibility layers may temporarily preserve both old and new internal representations; and
- later protocols may expose requirements not covered by the first NETCONF implementation.

## Decisions Deferred

This ADR does not decide:

- the exact inventory normalization model;
- the exact second-branch topology or addressing;
- the detailed routed management-path safety model;
- the NETCONF YANG model and path;
- the typed execution artifact structure;
- schema-version `2` fields;
- whether pyATS becomes a formal release acceptance dependency; or
- the final top-level directory structure for practical work.

These decisions require environment or implementation evidence and should be recorded separately only when durable.

## Compatibility Exit

Any future proposal to remove the V1 input, CLI, Scrapli, safety, or schema-version `1` compatibility contract requires an explicit architectural decision and migration plan. It is not an incidental consequence of implementing NETCONF.
