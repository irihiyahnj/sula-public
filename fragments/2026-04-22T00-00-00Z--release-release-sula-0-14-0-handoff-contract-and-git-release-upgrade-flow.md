---
id: 2026-04-22T00-00-00Z--release-release-sula-0-14-0-handoff-contract-and-git-release-upgrade-flow
time: 2026-04-22T00:00:00Z
kind: release
tags: [migrated-from-sula, release]
source_path: docs/releases/2026-04-22-release-sula-0-14-0-handoff-contract-and-git-release-upgrade-flow.md
---
# Release Sula 0.14.0 handoff contract and Git release upgrade flow

## Metadata

- date: 2026-04-22
- executor: Codex
- branch: main
- status: released

## Scope

Published the handoff-based closeout contract, current-state archiving, and canonical Git-release upgrade path as the new stable downstream rollout baseline.

## Risks

- adopted projects that still treat `STATUS.md` as a loose narrative will fail `doctor --strict` and `check` until they add a valid `## Handoff` section and keep current-state sections within the configured limits
- projects that have older managed-file drift may need one explicit sync and memory-digest rebuild before the new Git-release upgrade flow reads as a no-drama routine upgrade
- public release communication should point at the published Git release and tag, not this private source repository `main`, or teams will end up with mixed rollout baselines

## Verification

- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py sync --project-root .`
- `python3 scripts/sula.py sync --project-root examples/okoktoto`
- `python3 scripts/sula.py sync --project-root examples/field-ops-generic`
- `python3 scripts/sula.py sync --project-root examples/client-service-gdrive`
- `python3 scripts/sula.py memory digest --project-root .`
- `python3 scripts/sula.py memory digest --project-root examples/okoktoto`
- `python3 scripts/sula.py memory digest --project-root examples/field-ops-generic`
- `python3 scripts/sula.py memory digest --project-root examples/client-service-gdrive`
- `python3 scripts/sula.py canary verify --project-root . --all`

## Rollback

- revert the `0.14.0` release batch from Git if the handoff contract or Git-release rollout path should not become the canonical downstream standard
- point external canaries or adopted projects back to the previous public tag if rollout must pause while teams clean up old status pages or managed-file drift

## Follow-up

- publish the clean `0.14.0` export into `irihiyahnj/sula-public`, tag `v0.14.0`, and make that tag the canonical upgrade baseline for downstream projects
- update `site/sula.json` and any launch-facing metadata so the public source ref points at the published `v0.14.0` tag instead of a mutable branch
- send the fleet-facing upgrade notice telling already-adopted projects to upgrade from the published Git release, rerun `memory digest`, and only treat the rollout as complete when `doctor --strict` and `check` both pass
