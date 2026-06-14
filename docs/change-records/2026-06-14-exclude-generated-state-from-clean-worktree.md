# Exclude generated kernel state from clean-worktree assertion (finish self-invalidation fix)

## Metadata

- date: 2026-06-14
- executor: Kiro
- branch: main
- related commit(s): pending
- status: implemented

## Background

A reported and previously "root-cause fixed" defect (2026-06-06,
`...make-legacy-check-read-only-wrt-worktree-root-fix`) still reproduced on an
adopted project (`aoif`) that tracks `.sula/` in git: `sula check` could never
hold a stable `SULA CHECK OK`. Every run reported

```
STATUS.md: `## Handoff` git working tree is clean, but the repo is dirty
```

even immediately after committing, forcing an endless rebuild→check→commit loop.

## Analysis

`is_clean_git_worktree()` runs `git status --short` with a telemetry-excluding
pathspec, `EPHEMERAL_TELEMETRY_PATHSPEC_EXCLUDES`. The 2026-06-06 fix populated
that list with only two paths:

```
.sula/state/automation
.sula/state/orchestration
```

But `sula check` / `memory digest` also re-stamp four other git-tracked
generated files on every run:

```
.sula/events/log.jsonl
.sula/indexes/catalog.json
.sula/state/jobs/history.jsonl
.sula/state/jobs/latest.json
```

Because those were not excluded, the cleanliness probe kept seeing the worktree
as dirty, so the STATUS `## Handoff` `git working tree: clean` field never
matched the live worktree. This is a coverage gap in the prior fix, not a new
mechanism: the check still mutated state it then asserted on.

Confirmed empirically on `aoif`: excluding the four paths makes the worktree
read clean and `SULA CHECK OK` stable across repeated runs.

Note: the 2026-06-06 root-cause change (the `EPHEMERAL_TELEMETRY_PATHSPEC_EXCLUDES`
constant itself plus its two call sites) was never committed in the canonical
repo; it sat as an uncommitted working-tree change. This change finishes and
commits that fix line.

## Chosen Plan

- Extend `EPHEMERAL_TELEMETRY_PATHSPEC_EXCLUDES` with the four additional
  generated-state paths, reusing the existing mechanism (no new code path).
- Keep the exclusion narrow and explicit (named files, not whole dirs) so real,
  non-generated changes still register as dirty.

## Execution

- `scripts/sula.py`: added the four paths to
  `EPHEMERAL_TELEMETRY_PATHSPEC_EXCLUDES` with an explanatory comment block.
- `tests/test_sula.py`:
  - `test_clean_worktree_ignores_ephemeral_telemetry_writes` now also creates
    `events/log.jsonl`, `indexes/catalog.json`, `state/jobs/history.jsonl`,
    `state/jobs/latest.json` and asserts the worktree still reads clean, while a
    real source edit still reads dirty.
  - `test_check_is_idempotent_and_stable_despite_telemetry_writes` helper
    `non_telemetry_dirty()` updated to the full exclude set.

## Verification

- Targeted: `test_clean_worktree_ignores_ephemeral_telemetry_writes`,
  `test_check_is_idempotent_and_stable_despite_telemetry_writes`,
  `test_check_fails_when_handoff_git_state_mismatches_repo` — 3/3 PASS.
- Broader check/worktree/digest/handoff subset — 29/29 PASS (253s).
- End-to-end on `aoif`: `SULA CHECK OK` stable across 3 consecutive runs with no
  intervening rebuild.

## Rollback

Revert the constant additions in `scripts/sula.py` and the test changes. The
self-invalidation loop would return for git-tracked-`.sula/` projects.

## Data Side-effects

None. The change only widens which paths the cleanliness probe treats as
ephemeral; it writes no data and does not alter generated content. Real
(non-telemetry) changes still register as dirty, preserving handoff/release
meaning.

## Follow-up

- The fix reaches all thin-wrapper adopted projects via the shared canonical
  runtime immediately; projects with a vendored `scripts/sula.py` copy pick it
  up on next sync.
- Consider whether these generated files should additionally be gitignored in
  adopted projects (separate decision; not required for the loop fix).

## Architecture Boundary Check

- highest rule impact: preserved. The change keeps the cleanliness check
  read-only with respect to state it can itself mutate; it encodes no
  project-owned business truth.
