---
id: 2026-05-07T00-00-00Z--release-release-sula-0-18-13-fleet-token-cost-status
time: 2026-05-07T00:00:00Z
kind: release
tags: [migrated-from-sula, release]
source_path: docs/releases/2026-05-07-release-sula-0-18-13-fleet-token-cost-status.md
---
# Release Sula 0.18.13 Fleet Token Cost Status

## Metadata

- date: 2026-05-07
- executor: Codex host with local Sula validation
- branch: main
- status: ready

## Scope

Sula 0.18.13 makes fleet autopilot cost visibility visible in the compact status
bar. Executor-reported token and cost metrics are aggregated into
`summary.usage` and rendered as `Tokens` and `Cost`.

## Risks

- Metrics depend on wrapper reporting. Sula displays reported usage and does not
  independently verify provider billing.
- Dry-run or already-current projects correctly show zero usage.

## Verification

- Python compile check passed for `scripts/sula.py` and `tests/test_sula.py`.
- Autopilot executor delegation and missing-executor blocking tests passed.
- Manual dry-run status output showed `Tokens: 0` and `Cost: $0.0000`.

## Rollback

Revert the 0.18.13 commit and tag, then return version metadata to 0.18.12.

## Follow-up

- Use real project fleet runs to compare reported executor cost with supervisor
  token usage and task quality.
