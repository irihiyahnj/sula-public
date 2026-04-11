# Sula Release Process

This process exists to protect adopted projects from accidental Sula Core regressions.

## Release Inputs

Before any version bump or tag:

1. classify the change as patch, minor, or major under [versioning.md](versioning.md)
2. update [CHANGELOG.md](../CHANGELOG.md) with a `Sync Impact` section
3. run `python3 -m unittest discover -s tests -v`
4. review `python3 scripts/sula.py sync --project-root <project> --dry-run` against each canary project
5. run `python3 scripts/sula.py doctor --project-root <project> --strict` on each canary project after sync
6. regenerate any canary `memory digest` outputs that are committed by policy

## Rollout Rules

- Every adopted project must appear in [../registry/adopted-projects.toml](../registry/adopted-projects.toml) before broad rollout.
- At least one canary project should receive each minor or major release first.
- Breaking manifest or managed/scaffold contract changes require migration notes before release.
- If a managed template changes operational behavior, call that out explicitly in the changelog instead of hiding it inside wording updates.

## Recommended Release Sequence

1. finish implementation and tests on a working branch
2. update docs, changelog, and registry metadata
3. bump [../VERSION](../VERSION)
4. run canary dry-runs and canary doctor checks
5. tag the release
6. sync canary repositories
7. expand rollout to the rest of the registry in controlled batches

## Non-release Changes

If a change is still exploratory and not ready for adopted projects, keep it off the release path until its sync impact is understood.
