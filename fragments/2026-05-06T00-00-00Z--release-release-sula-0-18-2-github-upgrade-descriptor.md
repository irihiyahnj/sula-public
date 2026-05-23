---
id: 2026-05-06T00-00-00Z--release-release-sula-0-18-2-github-upgrade-descriptor
time: 2026-05-06T00:00:00Z
kind: release
tags: [migrated-from-sula, release]
source_path: docs/releases/2026-05-06-release-sula-0-18-2-github-upgrade-descriptor.md
---
# Release Sula 0.18.2 GitHub upgrade descriptor

## Metadata

- date: 2026-05-06
- executor: Codex
- branch: main
- status: verified

## Scope

Version the current Sula source tree as `0.18.2` so Git release upgrade instructions resolve the live current descriptor from the public GitHub repository rather than from the older hosted `sula.1stp.monster` descriptor.

This keeps one current-version truth for external models:

- live channel: `https://raw.githubusercontent.com/irihiyahnj/sula-public/main/site/sula.json`
- immutable upgrade baseline: the `source_ref` tag declared by that descriptor

## Risks

- The GitHub raw descriptor is mutable by design because it is the update channel; agents must use it only to discover `source_ref`, then upgrade from the immutable tag.
- Operators in restricted networks need direct GitHub access for the descriptor and public source clone.

## Verification

- Final gate passed on 2026-05-06:
  - `python3 -m py_compile scripts/sula.py tests/test_sula.py`
  - `python3 -m unittest tests.test_sula.SulaCliTests.test_site_descriptor_points_to_published_public_repo -v`
  - `python3 scripts/sula.py check --project-root . --json`
  - `python3 scripts/sula.py doctor --project-root . --strict --json`
  - `git diff --check`

## Publication

- Public repository: `https://github.com/irihiyahnj/sula-public.git`
- Public branch: `main`
- Public tag target: `v0.18.2`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.18.2`.

## Rollback

- Restore `VERSION`, `.sula/version.lock`, `site/sula.json`, and `site/launch/bootstrap.py` to the previous published source ref.
- Revert upgrade docs to a previous descriptor source if GitHub raw delivery proves unsuitable.

## Follow-up

- Decide separately whether to retire or redeploy `sula.1stp.monster`; do not use it as the upgrade truth until it is verified current.
