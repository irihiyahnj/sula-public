---
id: 2026-05-06T00-00-00Z--decision-document-local-executor-wrapper-contract
time: 2026-05-06T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-06-document-local-executor-wrapper-contract.md
---
# 2026-05-06 - Document Local Executor Wrapper Contract

## Metadata

- Date: 2026-05-06
- Executor: Codex
- Branch: main
- Related commits: pending
- Status: implemented

## Background

Sula Core now emits a bounded executor contract and minimal execution packet, but
the actual provider call remains project-local by design. Other adopted projects
need a durable reference that tells local wrapper maintainers what to consume and
what JSON to return.

## Analysis

The wrapper contract should be reusable documentation, not a centrally enforced
script. Each project may use Claude Code, Hermes, DeepSeek, or a custom runner,
and provider credentials must remain local.

## Chosen Plan

- Add a reference document for the local executor wrapper contract.
- Link it from the documentation map and README agent-routing section.
- Keep the actual `.sula/local/` wrapper implementation project-local and
  uncommitted.

## Execution

- Added `docs/reference/local-executor-wrapper-contract.md`.
- Documented required environment variables, executor contract JSON, execution
  packet JSON, expected behavior, output schema, and open-cost semantics.
- Updated README and docs map so future agents can discover the wrapper
  contract after syncing.

## Verification

- Local wrapper smoke-tested with a fake `claude` command to verify it converts
  a Claude-style result envelope into Sula runner JSON with metrics.
- `python3 -m json.tool site/sula.json >/dev/null`
- `python3 -m py_compile scripts/sula.py tests/test_sula.py site/launch/bootstrap.py`

## Rollback

Remove the local executor wrapper contract reference and revert version metadata
to the prior release. Projects would still have the Sula Core environment
variables, but less guidance for adapting local runners.

## Data Side-effects

The current Sula repository's `.sula/local/deepseek-flash-executor.sh` was
updated locally to consume the contract, but `.sula/local/` remains ignored and
is not part of release truth.

## Follow-up

- Consider adding a scaffold command for generating a starter wrapper only after
  repeated projects confirm the stable wrapper shape.

## Architecture Boundary Check

- Highest rule impact: preserved. The docs describe a reusable operating-system
  boundary without storing local provider credentials or project-specific
  business truth.
- Sync impact: adopted projects receive discoverable guidance for local wrapper
  updates.
