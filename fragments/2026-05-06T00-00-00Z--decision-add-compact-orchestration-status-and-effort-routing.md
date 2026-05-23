---
id: 2026-05-06T00-00-00Z--decision-add-compact-orchestration-status-and-effort-routing
time: 2026-05-06T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-06-add-compact-orchestration-status-and-effort-routing.md
---
# 2026-05-06 - Add Compact Orchestration Status And Effort Routing

## Metadata

- Date: 2026-05-06
- Executor: Codex
- Branch: main
- Related commits: pending
- Status: implemented

## Background

An adopted project needed a compact, tool-like execution status line for
delegated Sula work. The local prototype also showed that executor reasoning
effort should be visible to the user, and that Claude-style runners need a
runner-native mapping where Sula `xhigh` corresponds to CLI `max`.

## Analysis

The feature is portable across adopted projects when implemented as a Sula Core
status surface rather than as a project-local script. The compact line should
not replace existing JSON or multiline status output; it should be an optional
human-readable surface. Runner adapters should receive both Sula's canonical
reasoning effort and a runner-native effort hint without requiring Sula Core to
own provider credentials.

## Chosen Plan

- Add `orchestration status --compact`.
- Add `--reasoning-effort` to `agent-routing configure`.
- Expose `SULA_MODEL_REASONING_EFFORT` and `SULA_RUNNER_EFFORT` to
  `shell-command` runners.
- Include `runner_effort` in `codex-sdk` and `codex-app-server` request
  payloads.
- Map Sula `xhigh` to runner effort `max` for Claude-style executor routes.

## Execution

- Updated `scripts/sula.py` CLI arguments, compact status rendering, shell
  runner environment, codex runner request payloads, and shell runner JSON
  response parsing.
- Updated `tests/test_sula.py` coverage for remembered reasoning effort,
  runner effort propagation, and compact status output.
- Updated `README.md` and the agent-routing visible execution spec.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_agent_routing_configure_remembers_executor_choice_until_replaced tests.test_sula.SulaCliTests.test_role_aware_runner_request_and_visible_active_state tests.test_sula.SulaCliTests.test_orchestration_trigger_and_shell_command_runner_collect_evidence tests.test_sula.SulaCliTests.test_shell_runner_receives_reasoning_effort_and_compact_status_line -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/sula.py doctor --project-root . --strict`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/sula.py orchestration status --project-root . --compact`

## Rollback

Revert the CLI additions, compact status helper functions, runner effort
environment fields, request-payload field, tests, and documentation changes.
Existing projects remain compatible because the feature is opt-in.

## Data Side-effects

Running status and doctor commands records normal local Sula operational events
under `.sula/`. No project-owned business files, provider credentials, or
external systems are touched.

## Follow-up

Before releasing, run the full Sula test suite and normal `report`/`check`
closeout. Downstream projects can then remove project-local status wrappers
after upgrading.

## Architecture Boundary Check

- Highest rule impact: preserved. The implementation is a reusable Sula
  operating-system surface and does not encode MedFlow-specific business truth.
- Sync impact: adopted projects receive an optional status command and optional
  routing metadata; existing manifests remain valid.
