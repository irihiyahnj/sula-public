# Sula Versioning

Sula uses semantic versioning for its reusable operating system.

## Rules

- patch: wording improvements, typo fixes, low-risk managed-file changes
- minor: new managed files, new profile docs, new doctor checks, backward-compatible script improvements
- major: manifest schema breakage, managed/scaffold contract changes, or migration-required sync behavior

## Project Locking

Adopted repositories keep `.sula/version.lock`.

That file records:

- the Sula version last synced into the project
- the active profile

It allows projects to upgrade intentionally instead of drifting accidentally.

## Upgrade Discipline

Before bumping Sula in a project:

1. review release notes or git diff
2. run `sula sync`
3. run `sula doctor`
4. review the generated diff
5. commit the upgrade as its own change batch
