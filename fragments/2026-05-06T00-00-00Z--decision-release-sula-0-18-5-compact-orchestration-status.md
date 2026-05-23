---
id: 2026-05-06T00-00-00Z--decision-release-sula-0-18-5-compact-orchestration-status
time: 2026-05-06T00:00:00Z
kind: decision
tags: [migrated-from-sula, change-record]
source_path: docs/change-records/2026-05-06-release-sula-0-18-5-compact-orchestration-status.md
---
# Release Sula 0.18.5 compact orchestration status

## Metadata

- date: 2026-05-06
- executor: Codex
- branch: main
- related commit(s): this release commit
- status: verified

## Background

MedFlow needed reusable Sula execution visibility instead of a project-local wrapper. The recurring operator need is a concise English tool line showing Sula run state, model/depth routing, executor effort, workspace mode, task progress, cost, and next action.

The compact status and effort-routing implementation already landed in Sula Core. This record promotes that implementation into a versioned Sula release so adopted projects can sync the behavior without depending on MedFlow-local scripts.

## Analysis

- Keeping the feature only in MedFlow would create project-local Sula drift and make other projects unable to upgrade to the same behavior.
- A patch release is appropriate because the change is backward-compatible and extends existing CLI/runtime surfaces.
- The public descriptor must move from `v0.18.4` to `v0.18.5` so external agents and adopted projects resolve the immutable release tag.
- Canary projects need to sync their version locks before release verification can pass against the new source version.

## Chosen Plan

- Bump `VERSION`, `.sula/version.lock`, `site/sula.json`, and `site/launch/bootstrap.py` to `0.18.5` / `v0.18.5`.
- Add `CHANGELOG.md` release notes with explicit sync impact.
- Add a release note under `docs/releases/`.
- Sync in-repo canaries to the new Sula version and refresh their status records.
- Verify with full unit tests, canary verification, `doctor --strict`, `check`, and `git diff --check`.

## Execution

- Added Sula 0.18.5 release metadata and changelog entries.
- Updated the public descriptor and bootstrap default source ref to `v0.18.5`.
- Updated release-facing tests and overview docs to the new version.
- Synchronized in-repo canary projects to the 0.18.5 version lock.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula -v`
  - result: pass, 121 tests

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/sula.py canary verify --project-root . --all`
  - result: pass, 4 canaries
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/sula.py doctor --project-root . --strict`
  - result: pass
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/sula.py check --project-root .`
  - result: pass, `SULA CHECK OK`
- `git diff --check`
  - result: pass

## Rollback

- Restore release metadata to `0.18.4` / `v0.18.4`.
- Revert the compact-status and effort-routing implementation commit if downstream runner behavior regresses.
- Resync affected canary projects back to the previous released Sula version if needed.

## Data Side-effects

- In-repo canary `.sula/version.lock` files are expected to move to `0.18.5`.
- Canary status and memory digest files are refreshed as part of release verification.
- No secrets, external provider credentials, or production project data are introduced.

## Follow-up

- After MedFlow syncs to this release, remove any project-local Sula wrapper that duplicates compact status behavior.
- Publish `v0.18.5` to the public Sula repository only after explicit push/publication approval.

## Architecture Boundary Check

- highest rule impact: preserves project-owned truth while moving reusable operating-kernel behavior upstream into Sula Core.
