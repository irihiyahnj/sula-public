# Sula Release And Rollout Runbook

Use this runbook when shipping Sula Core changes that may later sync into adopted repositories.

## Pre-release

1. update `CHANGELOG.md`
2. review [registry/adopted-projects.toml](../../registry/adopted-projects.toml)
3. run repository tests
4. verify the in-repo canary

## Rollout

1. use `sync --dry-run` against canary projects first
2. review high-impact managed-file changes before writing them
3. run `doctor --strict` after sync
4. update the registry with the new Sula version

## Rollback

- revert or patch Sula Core on a working branch
- resync only the affected adopted projects
- record the rollback rationale in a change or release record
