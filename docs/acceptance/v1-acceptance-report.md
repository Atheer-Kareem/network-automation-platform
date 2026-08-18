# V1 Acceptance Report

## Scope

This document records the release gate for the bounded V1 safe automation platform. It audited the implemented system against the eight roadmap completion criteria and consolidated implementation, automated, documentation, and live evidence. All engineering acceptance criteria passed. The reviewed release candidate was subsequently merged, tagged, and published as V1.0.0.

## Release criteria

| Criterion | Status | Evidence and remaining gate |
| --- | --- | --- |
| Supported remediation works across multiple drift categories | PASS | Interface, VLAN, and switchport remediation are implemented with structured validation, planning, IOS rendering, and focused tests. Existing live deployment evidence proves targeted VLAN/SVI repair. |
| Unsupported or unsafe changes fail closed | PASS | Unsupported and mixed drift block deployment; OSPF operational failures remain validation-only; pre-change safety failure prevents execution. |
| Branch-wide preflight occurs before writes | PASS | All devices are collected, validated, and classified before approval or execution; all approvals are collected before the first write. |
| Routing validation proves meaningful operational state | PASS | The representative branch requires OSPF neighbor `10.101.255.2` in `FULL` state and learned route `10.200.0.1/32` through that peer and the mapped WAN interface. Both outcomes and their fail-closed behavior are live accepted. |
| Major failure paths are tested | PASS | All 11 V1 failure paths have deterministic automated evidence; unreachable, authentication, and strict host-key failures also have safe live evidence. |
| Operator documentation is complete | PASS | README and architecture documentation cover prerequisites, connection inputs, inventory and SSH trust, validate/plan/deploy, approvals, JSON reporting, exit/error behavior, safety boundaries, and limitations. |
| Representative CML acceptance scenarios pass | PASS | Historical focused scenarios and the final multi-device, multi-category controlled deployment completed successfully with schema-v1 evidence and restored compliance. |
| Architecture documentation accurately describes the implemented system | PASS | The V1 overview, roadmap, branch/network documents, failure-path matrix, and this report agree with current code and explicit limitations. |

All eight criteria pass. No unaddressed implementation or architecture gap remains inside the defined V1 scope.

## Existing implementation evidence

- `branch_deployment.deploy_branch()` performs branch-wide preflight, blocks unsupported drift, gathers every approval before writes, skips compliant devices, and preserves per-device results.
- Interface remediation supports missing managed interfaces/SVIs plus description, IPv4 address/prefix, and administrative-state mismatch.
- VLAN remediation supports missing VLANs and VLAN name mismatch.
- Switchport remediation supports administrative-mode, access-VLAN, and trunk allowed-VLAN mismatch.
- Validation checks the expected OSPF peer state and representative learned upstream route; neither is automatically remediated.
- The deployment service requires immediate pre-change safety validation, targeted executor success, fresh post-change collection, and complete desired-state post-validation.
- Schema-version `1` reporting records drift, commands, approval, pre-change, execution, post-change, and final outcome without credentials or connection objects.

## Automated evidence

The full suite covers intent and desired-state construction, collection and parsing, validation, remediation eligibility and rendering, branch preflight, approval ordering, execution outcomes, reporting, CLI exit behavior, and identity/OOB safety.

The [V1 failure-path matrix](v1-failure-path-matrix.md) maps deterministic tests to unreachable device, authentication failure, SSH host-key failure, identity mismatch, unavailable OOB prerequisite, unsupported drift, operator rejection, execution failure, post-change collection failure, post-change validation failure, and already-compliant state.

## Existing live acceptance evidence

Existing operator-established CML evidence includes:

- branch-wide validation and planning returning `COMPLIANT` and `NO DRIFT`;
- targeted management SVI/VLAN drift detection, approval, deployment, fresh collection, and restored compliance;
- schema-version `1` JSON evidence for a successful controlled deployment with no secrets;
- expected OSPF adjacency in `FULL` state and required route `10.200.0.1/32` learned through OSPF from `10.101.255.2` on the mapped WAN interface;
- missing adjacency and missing learned-route outcomes blocking deployment with zero writes;
- safe live connection failures for an unused endpoint, disposable invalid authentication, and strict temporary host-key trust, with no device commands, persistent trust/inventory changes, or credential exposure; and
- final multi-device remediation of a router interface-description mismatch and switch VLAN-name mismatch, ending `COMPLIANT` and `NO DRIFT` with verified schema-v1 evidence.

Unsafe post-write failures remain deterministic automated evidence rather than deliberate live disruption.

## Final representative acceptance evidence

The final operator-approved CML run completed successfully. Temporary drift was not persisted to startup configuration, and no manual restoration was required.

### 1. Initial baseline

The initial read-only checks were:

```bash
uv run nap validate branch-01
uv run nap plan branch-01
```

They returned `RESULT: COMPLIANT` and `RESULT: NO DRIFT`.

### 2. Temporary supported differences

On `br01-rtr01`, only the cosmetic LAN-trunk description changed. Intended value: `Branch LAN trunk`. Temporary value: `V1 ACCEPTANCE TEMPORARY DRIFT`.

Operator-approved temporary commands:

```text
configure terminal
interface GigabitEthernet0/2
description V1 ACCEPTANCE TEMPORARY DRIFT
end
```

Expected validation check: `interface:GigabitEthernet0/2`, with only `description` mismatched. Expected targeted remediation:

```text
interface GigabitEthernet0/2
description Branch LAN trunk
```

On `br01-sw01`, only the cosmetic name of user VLAN 10 changed. Intended value: `USERS`. Temporary value: `USERS_TEMP`.

Operator-approved temporary commands:

```text
configure terminal
vlan 10
name USERS_TEMP
end
```

Expected validation check: `vlan:10`, with only `name` mismatched. Expected targeted remediation:

```text
vlan 10
name USERS
```

These differences span both managed devices and two remediation categories while leaving OOB addressing, SSH reachability, WAN state, OSPF, routing, switchport forwarding, trunks, access VLAN assignment, and management SVI connectivity unchanged.

### 3. Validation and planning result

Validation and planning detected only `interface:GigabitEthernet0/2` with `mismatched_fields=["description"]` and `vlan:10` with `mismatched_fields=["name"]`. They produced only the exact targeted commands above. No interface, IP, OSPF, routing, management, trunk, switchport, administrative-state, or unsupported drift appeared.

### 4. Controlled deployment and evidence

Run:

```bash
uv run nap deploy branch-01 \
  --report-json /tmp/nap-v1-final-acceptance.json
```

The operator approved the exact remediation for both devices. Both approvals occurred before writes; only the displayed commands were sent; pre-change validation passed; execution succeeded; fresh state was collected; and complete post-change validation passed.

The `/tmp/nap-v1-final-acceptance.json` artifact was verified programmatically against `BranchDeploymentReport`: `schema_version` is `1`, `branch_id` is `branch-01`, both original drift checks and exact remediation commands are retained, both approvals are `approved`, pre-change and post-change phases passed, both executions were attempted and succeeded with deployment status and final outcome `succeeded`, and credential, username, SSH, trust-file, connection-object, and configured NAP connection values are absent. Verifier result: `RESULT: V1 FINAL EVIDENCE PASS`.

### 5. Final state

Final validation and planning returned `RESULT: COMPLIANT` and `RESULT: NO DRIFT`. No manual restoration was required.

The pre-approved contingency restoration commands were not needed:

```text
br01-rtr01:
  configure terminal
  interface GigabitEthernet0/2
  description Branch LAN trunk
  end

br01-sw01:
  configure terminal
  vlan 10
  name USERS
  end
```

No loss of management, adjacency, learned-route, or trunk state occurred.

## Known V1 limitations

V1 intentionally does not provide automatic rollback, startup-configuration persistence, multi-device transaction semantics, automatic retry, unsupported-drift remediation, or unrestricted AI-to-device writes. V1.5/V2 technologies—including model-driven protocols, external automation frameworks, programmable digital-twin lifecycle, broader source-of-truth integration, and autonomous remediation—remain outside this release boundary. These are explicit scope decisions, not V1 release blockers.

Initial connection failures occur before a branch deployment result exists and therefore return CLI exit 2 without a JSON deployment report. Deployment changes affect running configuration only.

## Release decision

**PASS.** All eight release criteria are supported by implementation, automated, documentation, and live evidence. V1 acceptance is complete against its defined engineering scope. V1.0.0 was subsequently released and published.

The completed release sequence was:

```text
V1 acceptance complete
    ↓
version 1.0.0 prepared in the release PR
    ↓
merge the release PR
    ↓
tag merged main as v1.0.0
    ↓
create the GitHub release
```

The historical acceptance phase itself did not create a tag or GitHub release. Those publication steps are now complete.
