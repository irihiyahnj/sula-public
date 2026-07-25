# Commit 0.15.0 and Fix Self-referencing Validation

## Metadata

- date: 2026-05-02
- executor: Claude Code (deepseek-v4-pro)
- branch: main
- related commit(s): 281c964..7872d97 (12 commits)
- status: completed

## Background

The 0.15.0 release (orchestration control plane, automation kernel, verification adapters, runner boundaries, agent behavior policy) existed entirely in the working tree — 83 files, +7732/-1038 lines — but was never committed. Git HEAD was at `f3db8f2 Release 0.14.0`. A `git clone` would get 0.14.0 while all project state claimed 0.15.0.

Additionally, `doctor` and `check` validation contained a self-reference cycle: the `git commit` field in STATUS.md Handoff was compared against HEAD, but updating that field requires a commit which moves HEAD, making the field permanently one commit behind.

## Analysis

- The working tree had 83 modified files representing the complete 0.15.0 release. Committing them was the highest priority fix.
- The `git commit` self-reference problem has no fix within the existing validation logic: any commit that updates the field moves HEAD, creating a new mismatch. The least-invasive fix is a sentinel value that opts out of strict comparison.
- Runtime automation/orchestration state was being tracked in git, causing every sula command to dirty the working tree. This should be gitignored like `.sula/cache/` and `.sula/local/`.
- All 4 example canary STATUS.md files were stale (handoff dated 2026-04-22, commit ref at `f3db8f2`, working tree marked dirty). These needed to be synced for release readiness to pass.

## Chosen Plan

1. Commit the full 0.15.0 working tree as a single release commit.
2. Add `**/.sula/state/automation/*` and `**/.sula/state/orchestration/*` to `.gitignore` and remove previously tracked runtime state files from git.
3. Add `or git_commit_value == "any"` to the doctor handoff validation condition in `scripts/sula.py`, and set all STATUS.md files to use `- git commit: any`.
4. Sync all example STATUS.md handoff fields (date, commit ref, working tree) and regenerate their `.sula/state/current.md` files.
5. Verify all 4 canaries pass release readiness.

## Execution

- Committed 118 files (+9742/-1038) as `281c964 Release Sula 0.15.0...`
- Updated `.gitignore` and removed 20 tracked runtime state files from git in `d4f6d82`.
- Added single-line sentinel check in `scripts/sula.py` line ~7137 and updated 4 STATUS.md files in `0859e54`.
- Synced all example handoff fields, regenerated `.sula/state/current.md` for all projects, regenerated `.sula/memory-digest.md`.
- Created this change record and updated STATUS.md Summary with date-grouped 2026-05-02 entries.

## Verification

- `python3 -m unittest discover -s tests -v`: all observed tests pass.
- `sula check --project-root . --json`: passes (with `git commit: any` sentinel).
- `sula doctor --project-root . --strict --json`: passes.
- `sula memory digest --project-root .`: generates cleanly.
- `sula release readiness --project-root . --json`: all 4 canaries pass with 0 issues. Only remaining issue is pre-existing git history metadata (`@MacBook-Pro.local`), which requires the `fresh-public-repo` export path as documented.

## Rollback

- Revert the 12 commits from `281c964` through `7872d97` to return to the pre-0.15.0-commit state.
- Remove `or git_commit_value == "any"` from `scripts/sula.py` line ~7137 and restore hardcoded commit hashes in all STATUS.md files.
- Remove the two `.gitignore` lines and restore tracked runtime state files from the previous commit.

## Data Side-effects

- 20 runtime state files removed from git tracking (not deleted from disk). They continue to exist at `.sula/state/automation/` and `.sula/state/orchestration/` but are now ignored.
- 1 new change record created: this file.
- STATUS.md Summary now uses date-grouped sub-sections (`### 2026-05-02`, `### 0.15.0 and earlier`).
- All 4 projects' `.sula/state/current.md` and `.sula/memory-digest.md` were regenerated.

## Follow-up

- Design and implement `sula report` command (target 0.15.1) to automate the session-summary write-back into STATUS.md.
- Evaluate whether `memory-digest.md` should be removed from `.gitignore` so new AI windows can read it immediately after clone.
- Add Summary freshness check to `sula check` so it can detect when git commits exist that are not reflected in STATUS.md Summary.

## Architecture Boundary Check

- highest rule impact: none — all changes preserve the split between centrally managed operating-system files and project-owned business truth. The `git commit: any` sentinel is a validation behavior change in managed code; the `.gitignore` addition is a kernel artifact boundary adjustment; STATUS.md updates are project-owned truth maintenance.
