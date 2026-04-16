# Add daily Sula check workflow for state-sync verification

## Metadata

- date: 2026-04-15
- executor: Codex
- branch: codex/release-main
- related commit(s): pending
- status: completed

## Background

Sula already had durable state files and structural validation through `doctor --strict`, but it did not yet provide a single operator-facing gate for day-to-day status-sync work. That left a real failure mode: `STATUS.md` or change records could move forward while `.sula/state/current.md` and `.sula/memory-digest.md` stayed stale.

## Analysis

- The need is reusable across adopted projects, so it belongs in Sula Core rather than in one project's private script.
- The implementation must stay dependency-light and reuse the primary orchestration lane in `scripts/sula.py`.
- `doctor --strict` is still the broader health check, but a daily workflow needs a more explicit pass/fail surface and clearer remediation commands.

## Chosen Plan

- add a first-class `check` command to `scripts/sula.py`
- keep `check` read-only and make it fail when generated state drifts from current source documents
- normalize generated timestamps so daily checks do not fail only because the calendar date changed
- wire the new gate into Sula templates and operating docs so `SULA CHECK OK` becomes the default close-out rule for status-sync work

## Execution

- added `python3 scripts/sula.py check --project-root ...` with human-readable and JSON output
- made `check` reuse strict doctor validation, then add generated-state drift checks for `.sula/state/current.md` and `.sula/memory-digest.md`
- added remediation hints that point operators at `python3 scripts/sula.py memory digest --project-root ...` when generated state needs rebuilding
- updated repository instructions, operating docs, README examples, and scaffold templates to require `check` after status-memory changes
- added regression tests for fresh-pass, stale-fail, rebuild-recover, and template generation behavior

## Verification

- `python3 -m unittest tests.test_sula.SulaCliTests.test_init_creates_manifest_lock_and_templates tests.test_sula.SulaCliTests.test_check_passes_for_freshly_adopted_project tests.test_sula.SulaCliTests.test_check_detects_stale_generated_state_until_memory_digest_rebuilds_it -v`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py check --project-root .`

## Rollback

- revert the commit that introduced `check`, the template rules, and the new change record
- fall back to `doctor --strict` plus manual `memory digest` discipline until a revised workflow gate is available

## Data Side-effects

- no new external dependency or storage contract was introduced
- adopted projects gain one new CLI surface and stronger generated-state verification after sync
- stale generated state now becomes an explicit failure instead of a silent mismatch

## Follow-up

- decide whether future release automation should run `check` automatically before publishing
- evaluate whether `check` should later expose a machine-readable diff summary for changed generated state

## Architecture Boundary Check

- highest rule impact: preserved; the change strengthens the separation between source-of-truth documents and generated `.sula/*` state instead of blurring it
