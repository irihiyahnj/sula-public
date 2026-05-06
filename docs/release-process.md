# Sula Release Process

This process exists to protect adopted projects from accidental Sula Core regressions.

For Sula Core, `release` means the intended repository state is published through the canonical Git history and is ready for downstream sync. It does not require a web-style production deployment.

## Release Inputs

Before any version bump or tag:

1. classify the change as patch, minor, or major under [versioning.md](versioning.md)
2. update [CHANGELOG.md](../CHANGELOG.md) with a `Sync Impact` section
3. review [../registry/feedback/catalog.json](../registry/feedback/catalog.json) and triage reusable feedback targeted for this release
4. run `python3 -m unittest discover -s tests -v`
5. run `python3 scripts/sula.py canary verify --project-root . --all`
6. review `python3 scripts/sula.py sync --project-root <project> --dry-run` against any additional external canary projects that are not addressable through `local_root`
7. regenerate any canary `memory digest` outputs that are committed by policy
8. if the release is intended to become the canonical public source, run `python3 scripts/sula.py release readiness --project-root .` and follow the recommended strategy

## Rollout Rules

- Every adopted project must appear in [../registry/adopted-projects.toml](../registry/adopted-projects.toml) before broad rollout.
- At least one canary project should receive each minor or major release first.
- Breaking manifest or projection/ownership contract changes require migration notes before release.
- If a managed template changes operational behavior, call that out explicitly in the changelog instead of hiding it inside wording updates.

## Recommended Release Sequence

1. finish implementation and tests on a working branch
2. update docs, changelog, and registry metadata
3. bump [../VERSION](../VERSION)
4. run `python3 scripts/sula.py canary verify --project-root . --all`
5. tag the release
6. sync canary repositories
7. mark shipped feedback items as `released`
8. expand rollout to the rest of the registry in controlled batches

## Public Repository Rule

- The default public-release path is `fresh-public-repo`, not in-place publication of this repository.
- When `release readiness` reports git-history lineage issues, export a clean tree with `release export-public` and create a new public repository from that export.
- Only update `site/sula.json`, `site/launch/bootstrap.py`, and any bootstrap-facing docs after the new public repository URL and ref are real.

## Non-release Changes

If a change is still exploratory and not ready for adopted projects, keep it off the release path until its sync impact is understood.
