# ADR-0004: Keep GitHub Canonical and Use GitLab for CI/CD Automation

## Status

Accepted

## Context

The Network Automation Platform is currently developed and published through GitHub.

GitHub provides the primary public development history for the project, including:

- feature branches;
- pull requests;
- code review;
- commit history;
- documentation changes; and
- portfolio visibility.

The future V2 roadmap introduces GitLab CI/CD as part of the broader NetDevOps automation environment.

GitLab is required for practical work involving:

- GitLab CI/CD pipelines;
- runners;
- pipeline stages;
- variables and secrets;
- artifacts;
- manual approval gates;
- network pre-validation;
- controlled deployment;
- post-change validation; and
- troubleshooting failed CI/CD jobs.

Moving the canonical project repository from GitHub to GitLab solely to introduce GitLab CI/CD would discard the value of the existing public GitHub workflow and unnecessarily change the project's development model.

At the same time, treating GitLab CI/CD as equivalent to another CI platform without implementing it directly would not provide sufficient practical experience with GitLab-specific workflows.

The platform therefore requires a clear relationship between GitHub and GitLab.

## Decision

GitHub will remain the canonical source repository for the Network Automation Platform.

GitHub will continue to provide:

```text
canonical source history
feature branches
pull requests
code review
public portfolio visibility
primary developer workflow
```

GitLab will be introduced as an additional CI/CD execution and learning environment.

GitLab will provide capabilities such as:

```text
GitLab CI/CD pipelines
GitLab Runner
pipeline stages
variables and secret handling
artifacts
manual approval gates
pre-change validation
deployment orchestration
post-change validation
pipeline troubleshooting
```

The initial target relationship is:

```text
Developer
    ↓
GitHub
canonical repository
    ↓
repository synchronization / integration
    ↓
GitLab
CI/CD execution environment
    ↓
GitLab Runner
    ↓
automated network workflow
```

The GitLab environment must not become an independent source of project truth.

Changes to application code should continue to originate from the normal GitHub development workflow unless a future architectural decision explicitly changes this model.

## Rationale

### Preserve the existing public engineering history

The GitHub repository already demonstrates:

- incremental development;
- feature-branch discipline;
- pull-request review;
- architecture evolution;
- testing practices; and
- documented engineering decisions.

Replacing GitHub with GitLab would provide little architectural value while weakening continuity of the public project history.

### Practice GitLab directly

GitLab CI/CD should be learned through real implementation rather than treated as interchangeable with another CI platform.

Practical experience should include:

- `.gitlab-ci.yml`;
- stages and jobs;
- runners;
- dependencies;
- `needs`;
- rules;
- artifacts;
- variables;
- protected values;
- manual jobs;
- pipeline logs;
- job failures; and
- recovery from broken pipelines.

### Separate source control from execution infrastructure

Git is the underlying version-control system.

GitHub and GitLab are platforms that provide different surrounding capabilities.

The project should therefore distinguish between:

```text
source repository responsibility
        ↓
GitHub

CI/CD execution responsibility
        ↓
GitLab
```

This avoids unnecessarily coupling source ownership to the choice of CI/CD engine.

### Support the V2 network automation lifecycle

The planned V2 CI/CD lifecycle includes:

```text
commit / merge request
        ↓
lint
        ↓
tests
        ↓
build
        ↓
CML digital-twin preparation
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

GitLab will provide the orchestration environment for this workflow while the Network Automation Platform continues to provide the underlying validation, planning, deployment, and verification capabilities.

## Alternatives Considered

### Move the canonical repository entirely to GitLab

Rejected.

Moving the project would disrupt the existing GitHub development and portfolio history without providing a corresponding architectural benefit.

GitLab CI/CD can be introduced without changing the canonical repository.

### Use GitHub only

Rejected for the complete roadmap.

GitHub remains suitable for normal development and portfolio visibility, but the V2 roadmap intentionally includes practical GitLab CI/CD experience.

Treating GitHub CI/CD knowledge as equivalent to GitLab-specific implementation would reduce the intended breadth of the automation lab.

### Maintain GitHub and GitLab as equal canonical repositories

Rejected.

Two independent authoritative repositories would create ambiguity around:

- source ownership;
- merge history;
- branch state;
- release state;
- pull-request versus merge-request workflow; and
- recovery from synchronization differences.

Only one repository should remain authoritative.

### Replace the development workflow with GitLab merge requests

Rejected for the current roadmap.

The existing GitHub pull-request workflow is already functioning well and provides useful public engineering evidence.

GitLab merge requests may still be exercised in isolated labs where useful, but they do not become the primary project workflow under this decision.

## Consequences

### Positive

- preserves the existing GitHub portfolio and engineering history;
- provides direct hands-on GitLab CI/CD experience;
- separates source-of-truth concerns from CI execution;
- allows the same application to be exercised through multiple delivery environments;
- provides practical experience with GitLab Runner;
- supports future CML, pyATS, validation, deployment, and reporting pipelines;
- demonstrates understanding of Git independently from hosting platform; and
- avoids an unnecessary repository migration.

### Negative

- introduces an additional platform to operate;
- repository synchronization must be designed and maintained;
- GitLab CI/CD adds runtime and infrastructure dependencies;
- pipeline failures may occur independently from GitHub development status;
- developers must understand which platform is authoritative;
- credentials and CI/CD variables must be managed securely in both environments where applicable; and
- some workflow duplication is unavoidable.

## Operational Boundaries

The following boundaries apply:

```text
GitHub
    = canonical source repository

GitLab
    = CI/CD execution environment

GitLab Runner
    = execution worker

CML
    = representative network test environment

Network Automation Platform
    = validation, planning, remediation,
      deployment, and verification logic
```

GitLab pipeline jobs must call platform-owned application interfaces or CLI workflows rather than duplicating deployment logic directly inside CI configuration.

For example:

```text
preferred

GitLab job
    ↓
nap validate
nap plan
nap deploy
```

rather than:

```text
not preferred

GitLab job
    ↓
direct ad-hoc SSH configuration logic
    ↓
device
```

CI/CD should orchestrate the platform, not bypass it.

## Security Considerations

GitLab CI/CD introduces additional secret-management responsibilities.

Sensitive values such as:

- device credentials;
- API tokens;
- private keys;
- controller credentials; and
- certificate material

must not be committed to either GitHub or GitLab repositories.

CI/CD secrets should be supplied through appropriate protected runtime mechanisms.

Pipeline logs and artifacts must also be reviewed to ensure sensitive values are not exposed indirectly.

The existing principle that configuration execution remains behind controlled application boundaries continues to apply inside CI/CD.

## Portfolio and Learning Considerations

GitHub remains the primary public portfolio surface.

GitLab exists to demonstrate practical CI/CD implementation rather than to duplicate the entire public project history.

The project should retain evidence of GitLab CI/CD capability through appropriate repository files and documentation, including where useful:

```text
.gitlab-ci.yml
pipeline architecture
runner design
sample pipeline evidence
failure scenarios
troubleshooting notes
CI/CD security decisions
```

The objective is to demonstrate that the same network automation system can participate in a professional delivery pipeline without changing its internal architecture.

## Future Review

Revisit this decision if:

- GitLab becomes the organisation's actual primary source-control platform;
- the GitHub-to-GitLab integration becomes operationally fragile;
- GitLab-specific release or security requirements make dual-platform operation impractical;
- the project develops a reason to standardize on one end-to-end DevOps platform;
- CI/CD requirements materially exceed the planned V2 workflow; or
- repository ownership and deployment lifecycles change substantially.

Any future change to the canonical repository should be treated as a separate architectural decision rather than an incidental tooling change.
