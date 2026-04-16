# Sula Release And Rollout Runbook

Use this runbook when shipping Sula Core changes that may later sync into adopted repositories.

In this repository, `released` means the Git-backed source of truth has been synchronized to the canonical repository state for downstream consumers. It is not limited to web deployment.

## Pre-release

1. update `CHANGELOG.md`
2. review [registry/adopted-projects.toml](../../registry/adopted-projects.toml)
3. review [registry/feedback/catalog.json](../../registry/feedback/catalog.json) and triage any reusable feedback targeted for this release
4. run repository tests
5. verify the in-repo canary

## Rollout

1. run `python3 scripts/sula.py canary verify --project-root . --all`
2. review high-impact managed-file changes before writing them
3. run `doctor --strict` after sync
4. mark shipped feedback bundles as `released` when the rollout that absorbed them is complete
5. update the registry with the new Sula version

## Rollback

- revert or patch Sula Core on a working branch
- resync only the affected adopted projects
- record the rollback rationale in a change or release record
