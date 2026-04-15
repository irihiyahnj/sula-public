# Sula Versioning

Sula uses semantic versioning for its reusable operating system.

## Rules

- patch: wording improvements, typo fixes, low-risk managed-file changes
- minor: new managed files, new profile docs, new doctor checks, backward-compatible script improvements, new memory tooling, new adoption automation
- major: manifest schema breakage, projection or ownership contract changes, memory contract breakage, or migration-required sync behavior

## Project Locking

Adopted repositories keep `.sula/version.lock`.

That file records:

- the Sula version last synced into the project
- the active profile

It allows projects to upgrade intentionally instead of drifting accidentally.

## Upgrade Discipline

Before bumping Sula in a project:

1. review release notes or git diff
2. if the project had reusable local managed-file fixes, capture them first with `sula feedback capture`
3. run `sula sync --dry-run`
4. run `sula sync`
5. run `sula doctor --strict`
6. review the generated diff
7. commit the upgrade as its own change batch

## Release Discipline

Before tagging a new Sula version:

1. update [../CHANGELOG.md](../CHANGELOG.md) with explicit sync impact
2. review [../registry/feedback/catalog.json](../registry/feedback/catalog.json) and decide which accepted feedback items land in the release
3. follow [release-process.md](release-process.md)
4. verify canary rollout order through [../registry/adopted-projects.toml](../registry/adopted-projects.toml)

For Sula Core, a release is the published Git/tagged repository state that adopted projects should sync against, not a web-app deployment event.
