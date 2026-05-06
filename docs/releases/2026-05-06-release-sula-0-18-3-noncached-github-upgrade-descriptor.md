# Release Sula 0.18.3 noncached GitHub upgrade descriptor

## Metadata

- date: 2026-05-06
- executor: Codex
- branch: main
- status: verified

## Scope

Version the current Sula source tree as `0.18.3` so external model-facing upgrade instructions read the live descriptor from:

`https://github.com/irihiyahnj/sula-public/raw/refs/heads/main/site/sula.json`

This replaces the `raw.githubusercontent.com/.../main/...` URL after verification showed that endpoint could temporarily return the previous descriptor after a force-updated public export.

## Risks

- The descriptor URL is intentionally a live channel on `main`; agents must use it only to discover `source_ref`, then clone the immutable tag.
- GitHub availability remains required for unattended upgrade discovery.

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
- Public tag target: `v0.18.3`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.18.3`.

## Rollback

- Restore `VERSION`, `.sula/version.lock`, `site/sula.json`, and `site/launch/bootstrap.py` to the previous published source ref.
- Revert descriptor URL changes if another live update channel is chosen.

## Follow-up

- Treat `sula.1stp.monster` and `raw.githubusercontent.com/.../main` as non-authoritative for upgrade discovery until they are explicitly verified current.
