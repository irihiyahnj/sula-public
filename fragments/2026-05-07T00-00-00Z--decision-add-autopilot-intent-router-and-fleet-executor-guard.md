---
id: 2026-05-07T00-00-00Z--decision-add-autopilot-intent-router-and-fleet-executor-guard
time: 2026-05-07T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-07-add-autopilot-intent-router-and-fleet-executor-guard.md
---
# Add Autopilot Intent Router And Fleet Executor Guard

## Metadata

- date: 2026-05-07
- executor: Codex host with local Sula validation
- branch: main
- related commit(s): pending
- status: implemented

## Background

The user goal is that high-end host models should plan, supervise, diagnose, and
accept work while cheaper or local executor routes perform repetitive project
work. Before this change, Sula could display role routing and executor
contracts, but a plain instruction such as "upgrade all Sula projects" still
depended on the host agent remembering to delegate manually.

## Analysis

- Sula already had role routing and local executor-wrapper contracts.
- The missing layer was a commandless route that every AI CLI can call from the
  user's natural-language goal.
- Fleet Sula upgrades are the right first slice because they are repetitive,
  easy to validate, and expensive when performed directly by a supervisor model.
- Unknown goals should remain blocked until Sula has a portable workflow for
  them.

## Chosen Plan

- Add `auto` as the natural-language entrypoint.
- Route recognized Sula upgrade/update/sync goals to `fleet.upgrade`.
- Add `fleet upgrade` and `fleet status`.
- Make fleet upgrades executor-required by default.
- Support real execution first through project-local `shell-command` wrappers.
- Update managed AI instructions so downstream CLIs call `auto` before doing
  mechanical maintenance work themselves.

## Execution

- Added CLI parser and dispatcher support for `auto`, `fleet upgrade`, and
  `fleet status`.
- Added adopted-project discovery under a filesystem scope with backup, archive,
  workspace, and deployment-release classification.
- Added executor readiness checks and a fleet task packet exposed as
  `SULA_FLEET_TASK_JSON`.
- Added shell-command fleet executor dispatch with Sula model-routing
  environment variables and structured JSON response parsing.
- Added `.sula/state/fleet/latest.json` and compact fleet status output.
- Updated root and template AI instruction files, README, docs map, changelog,
  and release metadata.
- Added tests covering successful executor delegation and missing-executor
  blocking.

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m py_compile scripts/sula.py tests/test_sula.py site/launch/bootstrap.py`
- `python3 -m json.tool site/sula.json >/dev/null`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_auto_upgrade_intent_delegates_project_upgrade_to_executor tests.test_sula.SulaCliTests.test_auto_upgrade_blocks_old_project_without_executor tests.test_sula.SulaCliTests.test_orchestration_review_feedback_feeds_executor_retry_and_health -v`

## Rollback

Revert the `auto` and `fleet` command additions, the managed instruction
template updates, and the 0.18.12 docs/metadata. Existing project manifests do
not require schema rollback.

## Data Side-effects

- Fleet runs write `.sula/state/fleet/latest.json`.
- `sync` regenerates normal managed `.sula/*` indexes and memory projections.
- No secrets are stored by the new fleet packet; wrappers receive provider/model
  hints and must keep API-key handling local.

## Follow-up

- Add more `auto` classifiers only when a portable Sula workflow exists.
- Consider SDK/app-server fleet adapters after shell-command wrappers prove
  stable.
- Continue measuring token/cost metrics from executor responses.

## Architecture Boundary Check

- highest rule impact: Preserved. The change stays in Sula's reusable operating
  layer and does not add project-specific business truth.
