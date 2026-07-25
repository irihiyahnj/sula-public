# Release Sula 0.18.1 current upgrade descriptor

## Metadata

- date: 2026-05-06
- executor: Codex
- branch: main
- status: verified

## Scope

Version the current Sula source tree as `0.18.1` so adopted projects and external coding agents can resolve the current published upgrade baseline from the launch descriptor instead of from hard-coded prose.

This is a documentation and release-contract patch. It keeps machine-readable version fields authoritative while removing duplicate current-version claims from Git upgrade runbooks and model-facing upgrade prompts.

## Risks

- Upgrade flows now depend on the hosted or checked-out `site/sula.json` descriptor being reachable and current.
- Operators with no network access must read `site/sula.json` from a checked-out published release instead of fetching the hosted descriptor.

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
- Public tag target: `v0.18.1`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.18.1`.

## Rollback

- Restore `VERSION`, `.sula/version.lock`, `site/sula.json`, and `site/launch/bootstrap.py` to the previous published `v0.18.0` source ref.
- Revert the upgrade docs and prompts to the previous text if descriptor-based resolution proves unsuitable.

## Follow-up

- Keep future model-facing upgrade instructions descriptor-based so release notes and launch metadata remain the only current-version source of truth.
