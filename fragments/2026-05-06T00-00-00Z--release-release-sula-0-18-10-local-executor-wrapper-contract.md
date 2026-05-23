---
id: 2026-05-06T00-00-00Z--release-release-sula-0-18-10-local-executor-wrapper-contract
time: 2026-05-06T00:00:00Z
kind: release
tags: [migrated-from-sula, release]
source_path: docs/releases/2026-05-06-release-sula-0-18-10-local-executor-wrapper-contract.md
---
# Release Sula 0.18.10 local executor wrapper contract

## Metadata

- date: 2026-05-06
- executor: Codex
- branch: main
- status: verified

## Scope

Version the current Sula source tree as `0.18.10` so adopted projects receive a
discoverable contract for updating project-local executor wrappers.

## Risks

- The release documents the wrapper boundary but does not centrally install or
  overwrite project-local `.sula/local/` scripts.
- Projects still need to adapt their local wrapper command to their chosen CLI
  and provider credentials.

## Verification

- Local wrapper smoke test with fake `claude` command.
- `python3 -m json.tool site/sula.json >/dev/null`
- `python3 -m py_compile scripts/sula.py tests/test_sula.py site/launch/bootstrap.py`

## Publication

- Public repository: `https://github.com/irihiyahnj/sula-public.git`
- Public branch: `main`
- Public tag target: `v0.18.10`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.18.10`.

## Rollback

- Restore `VERSION`, `.sula/version.lock`, `.sula/kernel.toml`,
  `site/sula.json`, `site/launch/bootstrap.py`, changelog, and release notes to
  `0.18.9` / `v0.18.9`.
- Remove the wrapper contract reference if the documented shape changes before
  downstream adoption.

## Follow-up

- Add a wrapper scaffold only after multiple real projects confirm the
  documented contract is stable enough to generate.
