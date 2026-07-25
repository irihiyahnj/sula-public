# Add feedback bundles and Sula Core review workflow

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: main
- related commit(s): pending local commit
- status: released

## Background

Sula already had a strong downstream model: managed files sync into adopted projects, projects keep project-owned truth local, and version locks plus canary rollout protect shared changes. What was missing was the upstream half of the loop.

Real adopted projects may discover a reusable Sula issue while working locally and may need to patch a managed file immediately to stay productive. Without a formal intake flow, those fixes either stay trapped as undocumented drift or pressure maintainers to treat one project's local patch as if it were already an upstream change.

## Analysis

- Leaving reusable fixes as local drift breaks the whole promise that Sula improves once and benefits many projects.
- Letting adopted projects write directly into Sula Core would break the boundary between local consumption and upstream governance.
- A commercial-grade workflow needs both sides:
  - project-side capture that packages evidence, diffs, and context
  - core-side intake, review, and release discipline before rollout

## Chosen Plan

- add `feedback capture` for adopted projects
- add `feedback ingest`, `feedback list`, `feedback show`, and `feedback decide` for Sula Core
- store project-side bundles under `.sula/feedback/outbox/`
- store core-side inbox state under `registry/feedback/`
- document the lifecycle, release discipline, and AI/operator responsibilities

## Execution

- implemented the feedback command family in `scripts/sula.py`
- generated portable feedback bundles with `bundle.json`, `doctor.json`, `sync-plan.json`, diffs, snapshots, and zip archives
- added a Sula Core feedback catalog and inbox structure
- updated templates, README, release docs, AGENTS guidance, and changelog
- added automated tests for capture, ingest, show, list, and decision flows

## Verification

- `python3 -m unittest tests.test_sula.SulaCliTests.test_feedback_capture_creates_bundle_and_archive_for_managed_drift tests.test_sula.SulaCliTests.test_feedback_ingest_show_list_and_decide_track_core_review_state -v`
- `python3 -m py_compile scripts/sula.py tests/test_sula.py`

## Rollback

- remove the `feedback` command family from `scripts/sula.py`
- remove `registry/feedback/` and `.sula/feedback/` outputs if the lifecycle is rejected
- revert the template and documentation changes so Sula returns to a downstream-only rollout model

## Data Side-effects

- adopted projects may now create `.sula/feedback/outbox/bundles/*` and `.sula/feedback/outbox/archives/*`
- Sula Core may now persist `registry/feedback/catalog.json` and `registry/feedback/inbox/*`
- export catalogs now expose feedback outbox and inbox paths

## Follow-up

- add stronger Sula Core doctor checks for malformed feedback registry entries if operational usage reveals drift or manual edits
- connect future remote transport or automation only after the local bundle contract proves durable in real adopted projects
- decide when accepted feedback items should be marked `released` automatically versus manually during release rollout

## Architecture Boundary Check

- highest rule impact: preserved; local projects still own their own business truth, local Sula drift is explicitly separated from Sula Core, and reusable upstream changes still require central review plus versioned rollout
