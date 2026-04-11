# Sula Versioning

Sula uses semantic versioning for its reusable operating system.

## Rules

- patch: wording improvements, typo fixes, low-risk managed-file changes
- minor: new managed files, new profile docs, new doctor checks, backward-compatible script improvements, new memory tooling, new adoption automation
- major: manifest schema breakage, managed/scaffold contract changes, memory contract breakage, or migration-required sync behavior

## Project Locking

Adopted repositories keep `.sula/version.lock`.

That file records:

- the Sula version last synced into the project
- the active profile

It allows projects to upgrade intentionally instead of drifting accidentally.

## Upgrade Discipline

Before bumping Sula in a project:

1. review release notes or git diff
2. run `sula sync --dry-run`
3. run `sula sync`
4. run `sula doctor --strict`
5. review the generated diff
6. commit the upgrade as its own change batch

## Release Discipline

Before tagging a new Sula version:

1. update [../CHANGELOG.md](../CHANGELOG.md) with explicit sync impact
2. follow [release-process.md](release-process.md)
3. verify canary rollout order through [../registry/adopted-projects.toml](../registry/adopted-projects.toml)
