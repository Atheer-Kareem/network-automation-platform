# V1 Architecture Overview

## Objective

V1 of the Network Automation Platform demonstrates a production-style workflow for repeatable and validated network operations.

The initial business use case is repeatable branch deployment.

## V1 Workflow

A branch definition should progress through the following lifecycle:

1. define branch intent
2. validate the input data
3. generate intended network configuration
4. perform automated quality checks
5. review the proposed change
6. run pre-change validation
7. deploy the change
8. run post-change validation
9. report the deployment result

## Design Principles

### Intent separated from implementation

Business and network intent should not be hard-coded into device-specific automation logic.

### Vendor implementation behind clear interfaces

Device-specific behaviour should be isolated so additional platforms can be introduced without redesigning the entire application.

### Validate before and after change

Successful command execution is not sufficient evidence that a network change succeeded.

### Safe automation

Automation should fail predictably, provide useful diagnostics, and avoid uncontrolled partial deployment.

### Testable components

Core business logic should be testable without requiring access to live network devices.

### Environment independence

The automation platform should not depend directly on GNS3, EVE-NG, CML, or physical hardware.

These environments provide network targets, not application architecture.

## V1 Scope

V1 includes:

- representative branch network model
- structured network intent
- device inventory
- read-only state collection
- configuration generation
- pre-change validation
- controlled deployment
- post-change validation
- automated testing
- CI quality gates
- architecture and operational documentation

## Out of Scope for V1

The following are planned extensions rather than V1 requirements:

- AI-assisted remediation
- full observability platform
- Kubernetes
- complex microservice architecture
- multiple CI platforms
- large-scale cloud networking
- closed-loop autonomous remediation
- support for every network vendor
- production web interface
