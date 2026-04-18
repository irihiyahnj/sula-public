# Sula 0.13.0 adopted-project upgrade checklist

## Purpose

Use this checklist when upgrading already-adopted projects to Sula `0.13.0`.

This release adds the stable staged-memory workflow and raises the normal operating bar around memory hygiene, rule discovery, and project checks.

## What Changed

- staged session memory is now first-class under `.sula/state/session/captures.jsonl`
- durable promotions now land in `docs/ops/session-promotions.md` by default
- `memory capture`, `memory review`, `memory promote`, `memory clear`, and `memory jobs` are now part of the stable operator surface
- `status`, `onboard`, and `adopt` now expose memory state directly
- `doctor --strict` and `check` now validate stale staged captures and promotion-file integrity

## Release Preflight

Before upgrading any adopted project:

1. confirm the project is already adopted and has `.sula/project.toml`
2. confirm the project has no unreviewed local managed-file drift that should become feedback first
3. review whether the project has old temporary notes that should become durable rules, decisions, tasks, risks, or state updates
4. communicate that `check` may fail after upgrade until memory state is reviewed and regenerated

## Per-project Upgrade Sequence

Run the following in each adopted project:

```bash
python3 /path/to/sula/scripts/sula.py sync --project-root /path/to/project --dry-run
python3 /path/to/sula/scripts/sula.py sync --project-root /path/to/project
python3 /path/to/sula/scripts/sula.py memory digest --project-root /path/to/project
python3 /path/to/sula/scripts/sula.py doctor --project-root /path/to/project --strict
python3 /path/to/sula/scripts/sula.py check --project-root /path/to/project
```

If the project already has temporary memory to review, continue with:

```bash
python3 /path/to/sula/scripts/sula.py memory review --project-root /path/to/project --json
python3 /path/to/sula/scripts/sula.py memory promote --project-root /path/to/project --capture-id <capture-id> --to rule
python3 /path/to/sula/scripts/sula.py memory clear --project-root /path/to/project --reviewed-captures
python3 /path/to/sula/scripts/sula.py check --project-root /path/to/project
```

## Required Project Outcomes

After upgrade, each adopted project should satisfy all of the following:

- `.sula/version.lock` records `0.13.0`
- `.sula/state/session/` exists
- `.sula/state/jobs/` exists
- `docs/ops/session-promotions.md` exists when the project uses promotion
- `python3 scripts/sula.py doctor --project-root . --strict` passes in that project
- `python3 scripts/sula.py check --project-root .` returns `SULA CHECK OK`

## Promotion Rules

Projects should use promotion narrowly.

Promote only when the captured item has become stable operating knowledge, for example:

- a project rule that should be followed repeatedly
- a stable current-state update that future sessions must recover quickly
- a durable decision or risk that should be queryable
- a workflow-artifact expectation that should survive beyond one session

Do not promote low-signal scratch notes or one-off chat fragments.

## Team Operator Model

The stable operator loop is now:

1. `memory capture`
2. `memory review`
3. `memory promote`
4. `query`
5. `memory clear --reviewed-captures`
6. `check`

Teams should treat this as the default close-out path whenever session context created reusable operating knowledge.

## Fleet Audit Commands

For a quick manual audit across known local canaries:

```bash
python3 /path/to/sula/scripts/sula.py canary verify --project-root /path/to/sula --all
```

For other adopted repositories not listed as in-repo canaries, run the per-project upgrade sequence above against each repository root.

## Failure Handling

If `doctor --strict` fails:

- fix malformed managed or generated state first
- rerun `memory digest`
- rerun `doctor --strict`

If `check` fails because of stale staged captures:

- run `memory review`
- either promote reviewed captures or clear them
- rerun `check`

If a project has reusable local managed-file drift:

- capture it with `feedback capture` before broad rollout
- review it in Sula Core instead of silently carrying one-off divergence forever

## Sign-off Gate

Treat a project as fully upgraded only when:

- sync completed
- memory digest was regenerated
- `doctor --strict` passed
- `check` passed
- the team knows whether that project will actively use the staged-memory loop
