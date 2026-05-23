---
id: 2026-05-06T00-00-00Z--decision-fix-sula-check-automation-self-lock
time: 2026-05-06T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-06-fix-sula-check-automation-self-lock.md
---
# 2026-05-06 - Fix Sula Check Automation Self Lock

## Metadata

- Date: 2026-05-06
- Executor: Codex with DeepSeek Flash executor assistance
- Branch: main
- Related commits: pending
- Status: implemented

## Background

Adopted projects with local orchestration task files could enter a check loop:
`sula check` failed, automation created a `Repair failed Sula check` intent, and
that open automation repair task or its dry-run human-review run then became a
reason for the next `sula check` to fail.

## Analysis

The automation repair intent is useful and should not be disabled globally.
The defect is narrower: Sula's own `sula-check` repair task should not be
counted as project work that blocks `check`. Ordinary project tasks and real
pending runs still need to remain visible and fail the check gate.

## Chosen Plan

- Identify Sula-generated `sula-check` automation repair task ids.
- Exclude those repair tasks from open/eligible task check failures.
- Exclude runs tied to those repair task ids from pending-run check failures.
- Preserve normal failures for non-automation open tasks.

## Execution

- Updated `scripts/sula.py` orchestration check filtering.
- Added regression coverage in `tests/test_sula.py` for the self-lock recovery
  path and the non-automation task failure path.
- Closed the Sula orchestration run after reviewer correction and validation.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_automation_check_failure_creates_intent_without_manual_trigger tests.test_sula.SulaCliTests.test_check_ignores_sula_check_automation_repair_self_lock tests.test_sula.SulaCliTests.test_automation_default_dispatches_low_risk_intent_to_dry_run -v`

## Runner Metrics

- Executor route: `deepseek/deepseek-v4-flash/xhigh`, runner effort `max`.
- Workspace mode: `copy`.
- Runner runtime: 9 minutes.
- Runner turns: 107.
- Runner model usage: 73,272 input tokens, 29,735 output tokens,
  5,051,264 cache-read input tokens.
- Runner reported cost: `$3.635367`.
- Result: initial implementation was directionally useful but incomplete;
  reviewer corrected the implementation and ran validation.

## Rollback

Revert the new helper functions, the orchestration check filtering change, and
the regression test. Affected projects would again need manual cleanup of
`sula-check` automation intents if the loop appears.

## Data Side-effects

The task and orchestration run records are updated under `docs/workflows/` and
`.sula/state/orchestration/`. No provider credentials or project-local executor
configuration are published.

## Follow-up

- Tighten the DeepSeek Flash executor runner prompt and permissions so delegated
  tasks can run validation without interactive Claude Code permission prompts.

## Architecture Boundary Check

- Highest rule impact: preserved. The fix changes Sula Core orchestration
  semantics and does not encode project-owned business truth.
- Sync impact: adopted projects inherit the corrected check behavior after
  syncing the release.
