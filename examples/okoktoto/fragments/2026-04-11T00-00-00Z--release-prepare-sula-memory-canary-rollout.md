---
id: 2026-04-11T00-00-00Z--release-prepare-sula-memory-canary-rollout
time: 2026-04-11T00:00:00Z
kind: release
tags: [migrated-from-sula, release]
source_path: docs/releases/2026-04-11-prepare-sula-memory-canary-rollout.md
---
# Prepare Sula memory canary rollout

## Metadata

- date: 2026-04-11
- executor: Codex
- branch: codex/bootstrap-sula
- status: completed

## Scope

Prepared the example project for memory-aware release verification.

## Risks

- memory scaffolds could drift from doctor expectations
- strict validation could become too noisy for real projects if the canary is not maintained

## Verification

- generated the latest canary files
- confirmed the example has release, incident, and change-record sources for the memory digest
- verified strict doctor after adding minimal path stubs

## Rollback

- stop using the example as a canary and remove the committed generated memory outputs
- keep the underlying Sula Core features if they remain valid elsewhere

## Follow-up

- review the canary on every minor Sula release
- expand to a real adopted repository when available
