# 2026-05-06 - Fix Orchestration Status Terminal Active Display

## Metadata

- Date: 2026-05-06
- Executor: Codex
- Branch: main
- Related commits: pending
- Status: implemented

## Background

The orchestration status surface was still treating the most recent terminal
run as an active execution. That made `session start` and compact status output
look like Sula was still running a finished smoke task, even after closeout had
been accepted.

## Analysis

The visible execution surface needs to distinguish between a live run and the
most recent completed run. Terminal states such as `accepted`, `failed`,
`blocked`, and `cancelled` belong in history, not in the active execution slot.
The fix needs to preserve run history while making the current state obvious to
users of every CLI.

## Chosen Plan

- Hide terminal runs from the active execution slot.
- Preserve the last run in history for compact status and audit output.
- Keep `session start` and `orchestration status` aligned on the same state
  model.

## Execution

- Added a visible-active state filter in `scripts/sula.py`.
- Updated `session start` and `orchestration status` to surface terminal runs
  only as `last_active`.
- Adjusted compact status output so idle state is explicit and `Next` resolves
  to `none` when nothing is active.
- Added regression coverage in `tests/test_sula.py`.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_session_start_surfaces_visible_execution_and_unknown_host_model tests.test_sula.SulaCliTests.test_session_start_does_not_show_terminal_run_as_active -v`
- `python3 scripts/sula.py session start --project-root .`
- `python3 scripts/sula.py orchestration status --project-root . --compact`

## Rollback

Revert the active-state filter, the status payload split between `active` and
`last_active`, the compact status change, and the added regression test.

## Data Side-effects

Status records continue to be written under `.sula/state/orchestration/`.
Terminal runs now remain visible as history without being presented as live
execution.

## Follow-up

If needed, extend the same visible-active filter to any future watch or poll
surface so the UI stays consistent across long-running execution views.

## Architecture Boundary Check

- Highest rule impact: preserved. This is a reusable Sula status-surface fix,
  not project-owned business logic.
- Sync impact: adopted projects will inherit the corrected status semantics
  when they upgrade Sula.
