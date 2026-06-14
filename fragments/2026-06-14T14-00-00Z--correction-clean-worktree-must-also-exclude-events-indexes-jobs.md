---
id: 2026-06-14T14-00-00Z--correction-clean-worktree-must-also-exclude-events-indexes-jobs
time: 2026-06-14T14:00:00Z
kind: correction
refs: [2026-06-06T09-50-58Z--decision-make-legacy-check-read-only-wrt-worktree-root-fix, 2026-06-06T07-46-12Z--decision-migrator-ignores-legacy-telemetry-to-end-check-self-invalidation]
tags: [bug-fix, root-cause, sula-check, worktree, self-invalidation, coverage-gap]
---
# Clean-worktree pathspec must also exclude events/indexes/jobs generated state

## What the 2026-06-06 root-cause fix missed

The 2026-06-06 fix made `is_clean_git_worktree()` read-only with respect to
ephemeral runtime state by excluding `.sula/state/automation` and
`.sula/state/orchestration` via `EPHEMERAL_TELEMETRY_PATHSPEC_EXCLUDES`. But
`sula check` / `memory digest` also re-stamp four other git-tracked generated
files on every run:

```
.sula/events/log.jsonl
.sula/indexes/catalog.json
.sula/state/jobs/history.jsonl
.sula/state/jobs/latest.json
```

Those were not in the exclude list, so on any project that tracks `.sula/` in
git (e.g. `aoif`), the cleanliness probe kept reporting dirty and the STATUS
`## Handoff` `git working tree: clean` field never matched the live worktree —
`SULA CHECK OK` was unreachable as a stable fixed point. The 2026-06-06 change
also turned out to be uncommitted in the canonical repo.

## Fix

Added the four paths to `EPHEMERAL_TELEMETRY_PATHSPEC_EXCLUDES` (named files, so
real changes still read dirty). Extended the existing clean-worktree test to
create all four and assert clean, plus updated the idempotency test helper.

## Verification

- Targeted + 29 check/worktree/digest/handoff tests PASS.
- End-to-end on `aoif`: `SULA CHECK OK` stable across 3 consecutive runs with no
  intervening rebuild.

## Scope discipline

Committed only this fix line (`scripts/sula.py`, `tests/test_sula.py`, the new
change record, this fragment). Other unrelated uncommitted working-tree changes
in the canonical repo (README, migrate.py, examples) were intentionally left
untouched.
