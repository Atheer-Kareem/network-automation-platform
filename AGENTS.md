# Codex Repository Guide

## Project purpose

This repository implements a production-style network automation platform for intent-driven, validated, auditable branch operations. V1 targets Cisco IOS/IOS XE through a controlled CLI workflow while keeping core policy independent of vendor transport and syntax.

## Repository map

- `src/network_automation_platform/`: application models, planning, validation, remediation, orchestration, and platform adapters.
- `intent/`: declarative branch inputs.
- `inventory/`: device inventory, capabilities, environment configuration, and SSH-related configuration.
- `inventory/ssh/`: generated SSH configuration documentation and local SSH runtime/trust state; `known_hosts` is not version controlled.
- `tests/`: unit, service, orchestration, rendering, and safety coverage.
- `docs/architecture/`: current design and operational boundaries.
- `docs/adr/`: accepted architectural decisions.
- `docs/roadmap/`: completed and planned platform capabilities.

## Authoritative context

Start with `README.md`, `docs/architecture/v1-overview.md`, and `docs/roadmap/platform-roadmap.md`. Use `docs/adr/` for durable decisions and `docs/architecture/branch-standard.md` plus `network-model.md` for branch/network conventions. Prefer current production code and tests when prose is stale or ambiguous.

## Architecture boundaries

- Keep intent separate from desired state and vendor implementation.
- Keep validation and remediation policy separate from vendor-specific rendering.
- Treat complete desired configuration and targeted remediation as distinct artifacts.
- Keep Cisco/platform behavior behind collectors, renderers, executors, state providers, profiles, or other vendor boundaries.
- Fail closed for unsupported or ambiguous automation. Never partially remediate mixed supported/unsupported drift.
- Route every device write through the controlled deployment path; the CLI is an operator interface, not an independent write path.

## Safety boundaries

Do not weaken explicit operator approval, branch-wide preflight, pre-change safety validation, device identity checks, SSH host-key verification, fresh post-change collection, or full post-change validation. Preserve unsupported-drift blocking and avoid broadening write scope implicitly.

## Implementation discipline

Inspect the working tree and relevant tests before editing. Make the smallest coherent change, preserve unrelated work, keep domain models vendor-neutral, and add or update tests at the closest appropriate layer. Do not introduce capabilities outside the requested scope.

## Testing and quality

Run focused tests while iterating, then the normal gates:

```bash
uv run ruff check .
uv run pytest
git diff --check
```

Review `git status --short --branch` and the final diff for unintended changes.

## Git safety

Do not commit, push, merge, rebase, force-push, delete branches, or rewrite history unless explicitly requested. Never use plain `git push --force`; prefer `--force-with-lease` only when history rewriting is explicitly required. Do not modify unrelated files.

## Documentation expectations

Update documentation when behavior, scope, safety boundaries, or roadmap status changes. Keep README concise, architecture documents authoritative, roadmap status accurate, and ADRs reserved for durable decisions. Do not claim acceptance evidence that was not established.

## Codex working method

Investigate first, state material assumptions, implement narrowly, run proportionate focused checks followed by repository gates, and report concrete evidence. Stop for direction before expanding scope or taking externally consequential action.

## Final report format

Report:

- Summary
- Files changed
- Architecture decisions or preserved boundaries
- Tests added or changed
- Quality-gate results
- Known limitations / follow-up items
- Git status
