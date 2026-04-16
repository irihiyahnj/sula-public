# Adopted Project Registry

Sula Core tracks rollout scope in [../../registry/adopted-projects.toml](../../registry/adopted-projects.toml).

## Why This Exists

Without a registry, Sula maintainers cannot answer basic release questions:

- which repositories are actually adopted
- which profile each repository uses
- which repository should act as the canary
- which Sula version each repository is currently locked to

## Registry Fields

Each `[[project]]` entry should record:

- `slug`
- `name`
- `profile`
- `repository`
- `primary_branch`
- `deployment_branch`
- `current_sula_version`
- `sync_status`
- `canary`
- `local_root`
- `owner`
- `notes`

## Operating Rules

- Add a project to the registry before its first production sync from Sula Core.
- Mark at least one project per active profile as `canary = true`.
- If no external canary exists yet, an in-repo example can act as a temporary canary, but it should be labeled clearly in `notes`.
- Set `local_root` whenever Sula Core should be able to run automated canary verification commands against a local checkout.
- Update `current_sula_version` after every successful sync batch.
- Use `sync_status` to distinguish planned, canary, active, paused, or retired projects.
