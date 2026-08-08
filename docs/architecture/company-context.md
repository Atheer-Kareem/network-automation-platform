# Company Context

## Overview

The Network Automation Platform models a growing mid-sized financial-services organisation with a distributed branch network.

The organisation operates:

- a Melbourne headquarters
- a primary data-centre environment
- a disaster-recovery capability
- multiple branch offices
- internet and cloud connectivity
- a predominantly Cisco network with future multi-vendor requirements

The network has grown faster than the operating model used to manage it.

## Current Operational Model

Network operations rely heavily on manual, device-by-device administration.

Common activities include:

- manual CLI configuration
- spreadsheet-based inventory and IP address management
- manual configuration backups
- repetitive branch provisioning
- manual pre-change and post-change verification
- inconsistent configuration standards
- limited configuration-drift detection
- operational knowledge concentrated among individual engineers

## Business Risks

The existing operating model creates several risks:

- configuration inconsistency
- human error during repetitive changes
- slow branch deployment
- weak auditability
- configuration drift
- difficult rollback
- inconsistent compliance enforcement
- limited scalability as the network grows

These risks are particularly important in a financial-services environment where availability, security, change control, and auditability are critical.

## Transformation Goal

The organisation wants to move from traditional manual network operations toward a controlled NetDevOps operating model.

The transformation should introduce automation incrementally rather than immediately allowing unrestricted configuration changes.

The target progression is:

1. visibility and inventory
2. state collection and configuration backup
3. source-of-truth-driven network intent
4. automated configuration generation
5. pre-change validation
6. controlled deployment
7. post-change validation
8. configuration compliance and drift detection
9. broader observability and closed-loop capabilities
10. AI-assisted operations with appropriate guardrails
