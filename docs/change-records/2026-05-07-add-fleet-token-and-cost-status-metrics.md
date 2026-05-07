# Add Fleet Token And Cost Status Metrics

## Metadata

- date: 2026-05-07
- executor: Codex host with local Sula validation
- branch: main
- related commit(s): pending
- status: implemented

## Background

Sula 0.18.12 introduced fleet autopilot status, but the compact fleet status bar
did not show the token and cost metrics returned by executor wrappers. That left
the user without the cost visibility needed to evaluate whether planner/executor
routing is paying off.

## Analysis

- Shell fleet executors already return `metrics.token_count` and
  `metrics.cost_usd`.
- The fleet payload already stores each executor result.
- The missing piece was aggregation into the fleet summary and compact status
  line.
- Sula should report wrapper-provided metrics without trying to read provider
  bills or secrets directly.

## Chosen Plan

- Aggregate executor metrics across fleet project results.
- Store the aggregate in `summary.usage`.
- Add `Tokens` and `Cost` fields to the compact fleet status bar.
- Extend tests so the executor-delegation path asserts both payload and status
  line metrics.

## Execution

- Added `fleet_usage_metrics`.
- Updated `fleet_status_bar` to display token and cost fields.
- Updated fleet upgrade payload summaries to include aggregate usage.
- Updated README and the autopilot reference doc.
- Added test assertions for executor-reported token and cost display.

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_auto_upgrade_intent_delegates_project_upgrade_to_executor tests.test_sula.SulaCliTests.test_auto_upgrade_blocks_old_project_without_executor -v`
- `python3 scripts/sula.py auto --project-root . --intent "升级这个目录所有 Sula 项目" --scope /home/jing/Project/projectdev/sula/examples --target-version 0.18.13 --dry-run --json`

## Rollback

Revert the fleet usage aggregation, status bar formatting change, docs update,
and test assertions. Executor result storage remains backward compatible.

## Data Side-effects

Fleet runs still write `.sula/state/fleet/latest.json`. The new fields are
derived from already returned executor metrics and do not introduce credential
storage.

## Follow-up

- Measure real wrapper-reported token and cost values across non-dry-run project
  upgrades.

## Architecture Boundary Check

- highest rule impact: Preserved. The change remains in reusable Sula status and
  reporting logic and does not add project-specific business truth.
