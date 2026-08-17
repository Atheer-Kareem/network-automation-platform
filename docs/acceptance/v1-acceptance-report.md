# V1 Acceptance Report

## Scope

This document is the release gate for the bounded V1 safe automation platform. It audits the implemented system against the eight roadmap completion criteria and consolidates existing implementation, automated, documentation, and live evidence. It does not declare V1 complete: the final representative CML acceptance run remains pending and must be operator approved.

## Release criteria

| Criterion | Status | Evidence and remaining gate |
| --- | --- | --- |
| Supported remediation works across multiple drift categories | PASS | Interface, VLAN, and switchport remediation are implemented with structured validation, planning, IOS rendering, and focused tests. Existing live deployment evidence proves targeted VLAN/SVI repair. |
| Unsupported or unsafe changes fail closed | PASS | Unsupported and mixed drift block deployment; OSPF operational failures remain validation-only; pre-change safety failure prevents execution. |
| Branch-wide preflight occurs before writes | PASS | All devices are collected, validated, and classified before approval or execution; all approvals are collected before the first write. |
| Routing validation proves meaningful operational state | PASS | The representative branch requires OSPF neighbor `10.101.255.2` in `FULL` state and learned route `10.200.0.1/32` through that peer and the mapped WAN interface. Both outcomes and their fail-closed behavior are live accepted. |
| Major failure paths are tested | PASS | All 11 V1 failure paths have deterministic automated evidence; unreachable, authentication, and strict host-key failures also have safe live evidence. |
| Operator documentation is complete | PASS | README and architecture documentation cover prerequisites, connection inputs, inventory and SSH trust, validate/plan/deploy, approvals, JSON reporting, exit/error behavior, safety boundaries, and limitations. |
| Representative CML acceptance scenarios pass | PENDING FINAL ACCEPTANCE | Historical focused CML scenarios pass. One final multi-device, multi-category end-to-end run remains to consolidate the complete V1 workflow. |
| Architecture documentation accurately describes the implemented system | PASS | The V1 overview, roadmap, branch/network documents, failure-path matrix, and this report agree with current code and explicit limitations. |

Seven of eight criteria pass before the final live run. No unaddressed implementation gap was found.

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
- missing adjacency and missing learned-route outcomes blocking deployment with zero writes; and
- safe live connection failures for an unused endpoint, disposable invalid authentication, and strict temporary host-key trust, with no device commands, persistent trust/inventory changes, or credential exposure.

Unsafe post-write failures remain deterministic automated evidence rather than deliberate live disruption.

## Final representative acceptance plan

This plan is for a future operator-approved CML run. Do not persist the temporary drift to startup configuration.

### 1. Confirm baseline

Run:

```bash
uv run nap validate branch-01
uv run nap plan branch-01
```

Require `RESULT: COMPLIANT` and `RESULT: NO DRIFT` before continuing.

### 2. Inject two harmless supported differences

On `br01-rtr01`, change only the cosmetic LAN-trunk description. Intended value: `Branch LAN trunk`. Temporary value: `V1 ACCEPTANCE TEMPORARY DRIFT`.

Future operator-approved commands:

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

On `br01-sw01`, change only the cosmetic name of user VLAN 10. Intended value: `USERS`. Temporary value: `USERS_TEMP`.

Future operator-approved commands:

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

### 3. Validate, plan, and review

Run `uv run nap validate branch-01` and require only the two expected failed checks. Run `uv run nap plan branch-01` and require only the exact targeted commands above. Any additional or unsupported drift is a stop condition.

### 4. Deploy and capture evidence

Run:

```bash
uv run nap deploy branch-01 \
  --report-json /tmp/nap-v1-final-acceptance.json
```

The operator must approve the exact remediation for both devices. Confirm that both approvals occur before the first write, only the displayed commands are sent, immediate OOB pre-change validation passes, execution succeeds, fresh state is collected, and complete post-change validation passes.

Inspect the JSON artifact and require `schema_version` `1`, branch `branch-01`, both original drift checks, exact remediation commands, `approved` status, successful execution and post-change evidence, final outcome `succeeded`, and no credential, SSH setting, or connection material.

### 5. Confirm final state and restoration

Run `uv run nap validate branch-01` and `uv run nap plan branch-01`; require `COMPLIANT` and `NO DRIFT`.

If controlled deployment cannot restore either cosmetic value, stop and use only these explicit operator-approved restoration commands:

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

Re-run validation and planning after restoration. Do not save the temporary drift. Any loss of management, adjacency, learned-route, or trunk state is an immediate stop condition.

## Known V1 limitations

V1 intentionally does not provide automatic rollback, startup-configuration persistence, multi-device transaction semantics, automatic retry, unsupported-drift remediation, or unrestricted AI-to-device writes. V1.5/V2 technologies—including model-driven protocols, external automation frameworks, programmable digital-twin lifecycle, broader source-of-truth integration, and autonomous remediation—remain outside this release boundary. These are explicit scope decisions, not V1 release blockers.

Initial connection failures occur before a branch deployment result exists and therefore return CLI exit 2 without a JSON deployment report. Deployment changes affect running configuration only.

## Release decision

**PENDING FINAL ACCEPTANCE.** The implementation and seven release criteria are supported by existing evidence. V1 must not be declared complete until the final representative scenario above passes and its evidence is recorded.

The proposed release sequence is:

```text
final representative acceptance passes
    ↓
update release documentation and project version to 1.0.0
    ↓
merge the release PR
    ↓
tag merged main as v1.0.0
    ↓
create the GitHub release
```

The current project version remains `0.1.0`; no tag or GitHub release is created in this phase.
