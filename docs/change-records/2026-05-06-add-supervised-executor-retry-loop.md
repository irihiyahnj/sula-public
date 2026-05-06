# 2026-05-06 - Add Supervised Executor Retry Loop

## Metadata

- Date: 2026-05-06
- Executor: Codex
- Branch: main
- Related commits: pending
- Status: implemented

## Background

Sula can route a bounded task to a local executor model, but the previous
contract stopped at a single runner result. The desired operating model is that
the higher-capability session acts as planner, reviewer, and diagnostician,
while the lower-cost executor handles the long code-writing loop.

## Analysis

Automatic model escalation would spend the expensive model on the executor path.
The better default is supervised retry: classify the executor failure, let the
reviewer write a precise diagnosis, then pass that diagnosis back to the same
executor route with an incremented routing cycle and hard scope guards.

## Chosen Plan

- Add structured failure classification and per-run execution summaries.
- Add `orchestration review` for reviewer feedback.
- Add `orchestration run --from-run-id` so retries inherit the latest reviewer
  feedback.
- Pass review feedback through both shell-command environment variables and
  Codex runner request payloads.
- Expose descriptive runner health in `orchestration status --json`.

## Execution

- Added failure types for tests, Sula checks, permissions, dependencies, scope,
  diff quality, hallucinated files, timeouts, generic runner failures, and
  unknown failures.
- Added `SULA_REVIEW_FEEDBACK_JSON` and embedded retry feedback in the bounded
  execution packet.
- Recorded `failure_classification`, `execution_summary`, and `runner_score` on
  runner completion.
- Added reviewer feedback persistence and max-review-cycle enforcement.
- Added regression coverage for first-run failure, reviewer diagnosis, retry
  dispatch, and runner health aggregation.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_orchestration_review_feedback_feeds_executor_retry_and_health -v`
- `python3 -m py_compile scripts/sula.py tests/test_sula.py`

## Rollback

Revert the new orchestration review command, retry run option, runner feedback
payload fields, runner health payload, and version metadata back to `0.18.10`.

## Data Side-effects

Existing run records remain readable. New run records may include
`failure_classification`, `execution_summary`, `runner_score`,
`review_feedback`, `retry_of_run_id`, and `next_routing_cycle`.

## Follow-up

- Use real project data to tune failure classification patterns and runner
  health scoring weights.
- Consider wrapper scaffolding only after the feedback contract stabilizes
  across multiple local CLIs.

## Architecture Boundary Check

- Highest rule impact: preserved. Sula stores portable orchestration contracts
  and records, while provider calls, API keys, and local CLI behavior remain
  project-local.
- Sync impact: downstream projects gain the supervised retry protocol through
  normal versioned Sula sync.
