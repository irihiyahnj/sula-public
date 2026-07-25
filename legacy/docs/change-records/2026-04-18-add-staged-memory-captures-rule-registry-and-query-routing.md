# Add staged memory captures, rule registry, and query routing

## Metadata

- date: 2026-04-18
- executor: Codex
- branch: codex/release-main
- related commit(s): pending
- status: completed

## Background

Sula already had durable state snapshots, change records, queryable kernel objects, and generated memory digests, but it still lacked an explicit bridge between temporary session findings and promoted durable operating knowledge. That gap made cross-session continuity weaker than the surrounding kernel architecture.

## Analysis

- Temporary operator context needed a first-class staged store instead of being implied by chat history or left in ad hoc notes.
- Project rules such as `AGENTS.md` and promoted workflow constraints needed to be queryable as first-class rule objects.
- Query quality could improve through deterministic route selection before any optional semantic cache existed.
- The daily `check` workflow needed to detect stale staged captures so temporary memory would not silently rot.

## Chosen Plan

- add staged session capture storage under `.sula/state/session/captures.jsonl`
- add `memory capture`, `memory review`, `memory promote`, `memory clear`, and `memory jobs`
- add a durable promotion path through `docs/ops/session-promotions.md`
- index rule objects, session captures, promotions, and memory jobs into the kernel
- add deterministic query routing and expose the chosen route in query output
- make `check` and `doctor` validate stale staged captures and malformed memory-job state

## Execution

- extended the optional `[memory]` manifest surface with capture, promotion, routing, retention, and promotion-file settings
- implemented staged memory capture, review, promotion, clear, and job-inspection commands in `scripts/sula.py`
- added first-class kernel object extraction for rules, session captures, promotions, and memory jobs
- extended query scoring with deterministic route selection such as `rules`, `state`, `record`, `execution`, and `freshness`
- updated the README and project-memory reference so the new memory lifecycle is documented
- added regression tests for capture/review, promotion/query, stale staged-capture checks, and derived-cache clearing

## Verification

- `python3 -m unittest tests.test_sula.SulaCliTests.test_check_passes_for_freshly_adopted_project tests.test_sula.SulaCliTests.test_check_detects_stale_generated_state_until_memory_digest_rebuilds_it tests.test_sula.SulaCliTests.test_memory_digest_generates_summary_file tests.test_sula.SulaCliTests.test_memory_capture_and_review_store_staged_session_context tests.test_sula.SulaCliTests.test_memory_promote_creates_rule_object_and_query_route tests.test_sula.SulaCliTests.test_check_fails_on_stale_staged_memory_capture tests.test_sula.SulaCliTests.test_memory_jobs_and_clear_derived_state -v`

## Rollback

- remove the new memory command variants and their kernel-object extraction
- remove the staged capture store and memory job tracking
- remove the promotion-file integration and route-aware query scoring

## Data Side-effects

- Sula projects now persist staged session captures and memory job history under `.sula/state/`
- promoted captures now write durable operating knowledge into `docs/ops/session-promotions.md` by default
- query results now report the deterministic route used to rank results

## Follow-up

- decide whether `memory promote` should support more durable targets beyond rules, tasks, decisions, and risks
- validate the route-selection heuristics on additional canary projects before introducing any optional semantic cache

## Architecture Boundary Check

- highest rule impact: preserved; Sula still keeps project-owned truth in source documents, keeps derived memory disposable, and treats staged captures as temporary until explicit promotion
