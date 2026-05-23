---
id: 2026-05-07T00-00-00Z--decision-add-deterministic-fleet-upgrade-executor
time: 2026-05-07T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-07-add-deterministic-fleet-upgrade-executor.md
---
# Add Deterministic Fleet Upgrade Executor

## Metadata

- date: 2026-05-07
- executor: Codex host with local Sula validation
- branch: main
- related commit(s): pending
- status: implemented

## Background

The first real fleet upgrade test showed that most active projects were still
blocked because their local Sula manifests used `runner = "dry-run"`. One
project with a DeepSeek-backed shell runner entered the model route, but the
wrapper did not understand the fleet upgrade packet and returned a human-review
status without upgrading.

This exposed a design issue: Sula upgrades are deterministic maintenance work
and should not require a model runner at all.

## Analysis

- Sula upgrade work has a known command sequence: `sync`, `doctor --strict`,
  `memory digest`, and `check`.
- Running that sequence directly is cheaper than using DeepSeek Flash and more
  reliable than relying on each project to implement a compatible wrapper.
- The host model should supervise and review evidence, not execute the commands
  manually.
- Shell/model executors remain useful for code-changing tasks and may still be
  tried when a project has a real configured runner.

## Chosen Plan

- Add a deterministic fleet upgrade executor inside Sula Core.
- Use it automatically when a target project has no real executor.
- If a configured shell executor runs but does not complete the version upgrade,
  fall back to deterministic execution and preserve the shell result for review.
- Keep token and cost metrics at zero for deterministic execution.
- Record the chosen executor kind in each project result.

## Execution

- Added `run_fleet_deterministic_executor`.
- Updated `fleet_upgrade_payload` to avoid blocking old projects only because
  their runner is `dry-run`.
- Added shell-executor fallback when the shell result is not accepted or the
  version lock does not reach the target.
- Updated tests so no-runner Sula upgrades are accepted through
  `sula-deterministic`.
- Updated README, reference docs, changelog, and release metadata.

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py site/launch/bootstrap.py`
- `python3 -m json.tool site/sula.json >/dev/null`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_auto_upgrade_intent_delegates_project_upgrade_to_executor tests.test_sula.SulaCliTests.test_auto_upgrade_uses_deterministic_executor_without_model_runner -v`

## Rollback

Revert the deterministic executor function and fleet payload routing change,
then restore version metadata to the previous release.

## Data Side-effects

Fleet upgrades can now modify target projects by running Sula's normal managed
sync and state-regeneration commands. The executor does not read secrets and
reports zero model tokens/cost.

## Follow-up

- Add a separate executor contract for code-changing tasks so deterministic
  maintenance remains separate from model-backed implementation.
- Continue measuring real fleet runs after the next published release.

## Architecture Boundary Check

- highest rule impact: Preserved. The change keeps Sula upgrades in the reusable
  operating-system layer and does not modify project-owned business truth except
  through normal managed sync behavior.
