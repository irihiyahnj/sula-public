# Strengthen Orchestration Closeout Evaluator

## Metadata

- date: 2026-05-01
- executor: Codex
- branch: main
- related commit(s): none
- status: completed

## Background

Sula orchestration already required closeout evidence, agent behavior verification, and acceptance/success-criteria evidence. The next completed-state gap was that accepted closeout still relied too heavily on summary text. The evaluator needed to inspect task validation requirements, touched-file references, links, and Sula check evidence.

## Analysis

- Runner success and operator prose are not enough to prove completed work.
- Task-specific validation requirements should be checked against closeout evidence.
- Touched files should resolve in the runner workspace or project root.
- Links should resolve as URLs, artifact ids, artifact paths, or project-local files.
- When `sula check` is declared as validation evidence, Sula should actually run `check` before accepting.

## Chosen Plan

- Expand closeout evaluation with structured validation requirement matching.
- Add touched-file and link resolution checks.
- Run `daily_check` when closeout evidence or task validation requests `sula check`.
- Block accepted closeout when required validation evidence, touched files, links, or requested Sula checks fail.
- Preserve the full evaluation payload in the run record for auditability.

## Execution

- Extended `evaluate_orchestration_closeout` to include validation requirement matching, touched-file checks, link checks, and conditional `sula check` execution.
- Updated `orchestration close --accept` to enforce missing validation requirements, missing touched files, unresolved links, and failed requested checks.
- Added negative unit coverage for unresolved required evidence.
- Adjusted existing closeout tests to use resolvable links.

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_orchestration_intake_and_closeout_require_evidence -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_orchestration_trigger_and_shell_command_runner_collect_evidence -v`
- `python3 -m unittest tests.test_sula.SulaCliTests.test_orchestration_closeout_evaluator_blocks_unresolved_required_evidence -v`
- `python3 -m unittest discover -s tests -v` passed, 104 tests in 950.721s.
- `python3 scripts/sula.py memory digest --project-root .`
- `python3 scripts/sula.py doctor --project-root . --strict --json`
- `python3 scripts/sula.py check --project-root . --json`
- `python3 scripts/sula.py orchestration doctor --project-root . --json`

## Rollback

- Remove validation requirement matching, touched-file checks, link checks, and conditional `sula check` execution from closeout evaluation.
- Keep historical closeout evaluation payloads in run records as audit history.

## Data Side-effects

- New closeout records include richer `closeout_evaluation` fields.
- Accepted closeout can now fail if evidence references missing touched files, unresolved links, unmet validation requirements, or a failing requested Sula check.

## Follow-up

- Add PR-specific verification once a GitHub or provider PR adapter exists.
- Add provider-native artifact verification once direct provider task APIs are enabled.
- Add Codex SDK/app-server runner adapters behind optional adapter boundaries.

## Architecture Boundary Check

- highest rule impact: preserved. Sula validates operating evidence and references without turning task summaries, runner prompts, or external tracker fields into managed business truth.
