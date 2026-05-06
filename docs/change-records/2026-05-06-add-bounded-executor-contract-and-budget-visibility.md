# 2026-05-06 - Add Bounded Executor Contract And Budget Visibility

## Metadata

- Date: 2026-05-06
- Executor: Codex
- Branch: main
- Related commits: pending
- Status: implemented

## Background

The first DeepSeek Flash executor run proved that Sula's routing direction is
sound, but the executor boundary was still too close to a full autonomous agent:
it spent excessive turns, time, cache reads, and cost while also getting stuck
on interactive permission prompts.

## Analysis

The expensive model should remain the planner and reviewer. The executor should
receive a bounded Sula-owned work packet and budget contract so local runner
adapters can treat the cheap model as a constrained patch worker.

## Chosen Plan

- Add reusable executor budget fields under `[agent_routing]`.
- Keep defaults dependency-light and compatible with existing manifests.
- Pass the bounded executor contract and minimal execution packet to shell and
  Codex-style runner boundaries.
- Show the executor budget in the existing compact Sula status line.
- Warn when cost-aware routing still uses executor `xhigh` by default.

## Execution

- Added executor contract defaults for context mode, output contract, default
  effort, max turns, max run minutes, and max cost cents.
- Added `SULA_EXECUTOR_CONTRACT_JSON` and `SULA_EXECUTION_PACKET_JSON` for
  shell-command runners.
- Added `executor_contract` and `execution_packet` to Codex/app-server runner
  request JSON while preserving existing request fields.
- Bounded runner timeout by the lower of the global orchestration timeout and
  executor contract timeout.
- Extended `orchestration status --compact` with `Budget: <turns>t/<minutes>m/$<cost>`.
- Added tests for shell runner contract env, compact budget display, default
  cost-aware executor effort, and Codex request compatibility.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_shell_runner_receives_bounded_executor_contract_and_compact_budget tests.test_sula.SulaCliTests.test_shell_runner_receives_reasoning_effort_and_compact_status_line tests.test_sula.SulaCliTests.test_role_aware_runner_request_and_visible_active_state -v`

## Runner Metrics

- This implementation intentionally did not delegate to the current DeepSeek
  Flash runner because the previous run showed the runner boundary itself was
  the cost problem being fixed.
- The previous delegated sample remains the baseline: 107 turns, 9 minutes,
  73,272 input tokens, 29,735 output tokens, 5,051,264 cache-read input tokens,
  and reported cost `$3.635367`.
- Expected effect: future executor routes receive a 5 minute, 8 turn, `$0.30`
  default budget contract unless the project config changes it.

## Rollback

Revert the executor contract fields, runner request/env additions, compact
status budget label, and related tests/docs. Existing projects would continue
to route executors as before but would lose Sula-owned budget visibility.

## Data Side-effects

Project-local provider credentials remain outside committed truth. Runtime
events and runner outputs remain under `.sula/state/` and `.sula/local/`.

## Follow-up

- Update local executor wrapper prompts to consume `SULA_EXECUTOR_CONTRACT_JSON`
  and stop early when the budget or output contract cannot be satisfied.
- Add streaming cost checkpoints if a future runner can report token/cost
  progress before process exit.

## Architecture Boundary Check

- Highest rule impact: preserved. The contract is reusable Sula operating
  structure, not project-owned business truth.
- Sync impact: adopted projects inherit safe defaults without requiring provider
  SDKs or credential storage changes.
