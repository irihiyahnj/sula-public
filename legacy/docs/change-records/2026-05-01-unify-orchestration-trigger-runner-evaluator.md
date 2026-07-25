# Unify Orchestration Trigger Runner Evaluator

## Metadata

- date: 2026-05-01
- executor: Codex
- branch: main
- related commit(s): none
- status: completed

## Background

The orchestration mainline needed to move beyond local dry-run scheduling without accepting a minimal one-off loop. The completed-state design requires a unified task trigger surface, a real runner adapter, isolated workspace handling, machine-readable evidence, and review-required learning proposals.

## Analysis

- Any Sula-connected surface should be able to emit task intent without becoming a new task model.
- A first real runner should stay dependency-light and disabled by default, while proving the runner/evidence contract end-to-end.
- Shell execution must be blocked unless it has an explicit command and either an isolated workspace or an explicit project-root mutation opt-in.
- Closeout should persist machine evaluation fields, not only raw operator evidence.
- Reusable lessons should become review candidates instead of silently mutating durable memory.

## Chosen Plan

- Add `orchestration trigger` as the generic deduped intake surface for Sula commands, webhooks, provider task documents, and external connectors.
- Implement `runner = "shell-command"` with `runner_command`, workspace preparation, command evidence, touched-file summaries, and normalized runner events.
- Keep `dry-run` as the default and keep orchestration disabled by default.
- Add closeout evaluation payloads and review-required promotion candidate records.
- Preserve adapter boundaries for future Codex SDK/app-server runners.

## Execution

- Added manifest fields `runner_command` and `allow_project_root_runner`.
- Added trigger records under `.sula/state/orchestration/triggers.jsonl` and promotion candidates under `.sula/state/orchestration/promotion-candidates.jsonl`.
- Added `orchestration trigger` with stable `identity_key` dedupe and optional immediate dispatch.
- Added isolated copy-workspace preparation for shell-command runner execution.
- Added shell-command runner evidence with redacted stdout/stderr, return code, timeout status, runtime metrics, runner events, and touched-file summaries.
- Added closeout evaluation fields for verification evidence, acceptance evidence, touched files, links, and promotion candidates.
- Updated documentation, schema, example manifest, and tests.

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m json.tool schema/project.schema.json`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_orchestration_trigger_and_shell_command_runner_collect_evidence -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_orchestration_intake_and_closeout_require_evidence tests.test_sula.SulaCliTests.test_agent_behavior_policy_surfaces_in_status_and_orchestration_runs -v`
- `python3 -m unittest discover -s tests -v` passed 102 tests.
- `python3 scripts/sula.py doctor --project-root . --strict --json` passed.
- `python3 scripts/sula.py check --project-root . --json` passed.
- `python3 scripts/sula.py orchestration doctor --project-root . --json` passed with expected disabled-orchestration warnings.

## Rollback

- Remove `orchestration trigger`, trigger records, promotion candidate records, shell-command runner execution, and the new manifest fields.
- Revert schema/example/docs/test changes.
- Keep historical `.sula/state/orchestration/` records as audit history unless explicit cleanup is approved.

## Data Side-effects

- New manifests can include `runner_command` and `allow_project_root_runner` under `[orchestration]`.
- Trigger records append to `.sula/state/orchestration/triggers.jsonl`.
- Promotion candidates append to `.sula/state/orchestration/promotion-candidates.jsonl`.
- Shell-command runs may create isolated copies under `.sula/local/workspaces/` when `workspace_mode = "copy"`.

## Follow-up

- Add a non-local external task-source adapter that reads from a provider or issue tracker while still normalizing into the same task model.
- Add portfolio-level orchestration summaries for blocked/running/review states across adopted projects.
- Add Codex SDK or app-server runner as an optional adapter after the shell-command evidence contract remains stable.

## Architecture Boundary Check

- highest rule impact: preserved. Task intent stays project-owned, runner execution stays behind explicit manifest policy, and reusable lessons become review candidates instead of direct durable memory mutations.
