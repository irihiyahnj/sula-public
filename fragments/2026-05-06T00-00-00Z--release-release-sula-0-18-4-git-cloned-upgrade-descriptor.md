---
id: 2026-05-06T00-00-00Z--release-release-sula-0-18-4-git-cloned-upgrade-descriptor
time: 2026-05-06T00:00:00Z
kind: release
tags: [migrated-from-sula, release]
source_path: docs/releases/2026-05-06-release-sula-0-18-4-git-cloned-upgrade-descriptor.md
---
# Release Sula 0.18.4 Git-cloned upgrade descriptor

## Metadata

- date: 2026-05-06
- executor: Codex
- branch: main
- status: verified

## Scope

Version the current Sula source tree as `0.18.4` so upgrade command examples discover the current published `source_ref` by cloning the public Git repository and reading `site/sula.json` locally.

This avoids relying on hosted or raw HTTP descriptor endpoints for automation. The release keeps the same core rule: use `main` only as the live descriptor channel, then upgrade from the immutable tag declared by `source_ref`.

## Risks

- Upgrade discovery requires Git access to `https://github.com/irihiyahnj/sula-public.git`.
- Agents must not upgrade directly from the descriptor clone's mutable `main`; they must clone the tag declared by `source_ref`.

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
- Public tag target: `v0.18.4`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.18.4`.

## Rollback

- Restore `VERSION`, `.sula/version.lock`, `site/sula.json`, and `site/launch/bootstrap.py` to the previous published source ref.
- Revert command examples if a better descriptor discovery channel is chosen.

## Follow-up

- Keep model-facing upgrade instructions focused on `docs/runbooks/git-release-upgrade.md` and `docs/reference/model-upgrade-prompts.md`.
