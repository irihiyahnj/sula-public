# Upgrade Adopted Projects From The Published Git Release

## Purpose

Use this runbook when Sula has already been published as a tagged public Git release and you need to upgrade one or many adopted repositories from that canonical source.

This is the preferred rollout path for scattered project fleets because it removes dependence on one local Sula checkout and makes the release source explicit.

Current canonical public source:

- repository: `https://github.com/irihiyahnj/sula-public.git`
- stable tag: `v0.14.0`

## Standard Release Checkout

Clone the exact release you want to use into a local operator path:

```bash
git clone --branch v0.14.0 --depth 1 https://github.com/irihiyahnj/sula-public.git /opt/sula/v0.14.0
export SULA_ROOT=/opt/sula/v0.14.0
python3 "$SULA_ROOT/scripts/sula.py" --help
```

If you already keep a local Sula release checkout, refresh it explicitly instead of drifting on `main`:

```bash
git -C /opt/sula/v0.14.0 fetch --tags origin
git -C /opt/sula/v0.14.0 checkout v0.14.0
git -C /opt/sula/v0.14.0 reset --hard v0.14.0
export SULA_ROOT=/opt/sula/v0.14.0
```

The operator rule is simple: use a versioned checkout path and point all project upgrades at that exact tagged release.

## Single-project Upgrade

Run the following against each adopted repository:

```bash
export PROJECT_ROOT=/path/to/project

python3 "$SULA_ROOT/scripts/sula.py" sync --project-root "$PROJECT_ROOT" --dry-run
python3 "$SULA_ROOT/scripts/sula.py" sync --project-root "$PROJECT_ROOT"
python3 "$SULA_ROOT/scripts/sula.py" memory digest --project-root "$PROJECT_ROOT"
python3 "$SULA_ROOT/scripts/sula.py" doctor --project-root "$PROJECT_ROOT" --strict
python3 "$SULA_ROOT/scripts/sula.py" check --project-root "$PROJECT_ROOT"
```

If the project already has staged memory that needs review:

```bash
python3 "$SULA_ROOT/scripts/sula.py" memory review --project-root "$PROJECT_ROOT" --json
python3 "$SULA_ROOT/scripts/sula.py" memory promote --project-root "$PROJECT_ROOT" --capture-id <capture-id> --to rule
python3 "$SULA_ROOT/scripts/sula.py" memory clear --project-root "$PROJECT_ROOT" --reviewed-captures
python3 "$SULA_ROOT/scripts/sula.py" check --project-root "$PROJECT_ROOT"
```

## Fleet Upgrade

When repositories are scattered, keep the project list outside Sula and drive the rollout with a plain shell loop:

```bash
export SULA_ROOT=/opt/sula/v0.14.0

while IFS= read -r PROJECT_ROOT; do
  [ -z "$PROJECT_ROOT" ] && continue
  echo "==> upgrading $PROJECT_ROOT"
  python3 "$SULA_ROOT/scripts/sula.py" sync --project-root "$PROJECT_ROOT" --dry-run || break
  python3 "$SULA_ROOT/scripts/sula.py" sync --project-root "$PROJECT_ROOT" || break
  python3 "$SULA_ROOT/scripts/sula.py" memory digest --project-root "$PROJECT_ROOT" || break
  python3 "$SULA_ROOT/scripts/sula.py" doctor --project-root "$PROJECT_ROOT" --strict || break
  python3 "$SULA_ROOT/scripts/sula.py" check --project-root "$PROJECT_ROOT" || break
done < /path/to/adopted-projects.txt
```

`adopted-projects.txt` should contain one absolute project root per line.

## Upgrade Completion Criteria

Treat a project as upgraded only when all of the following are true:

- `.sula/version.lock` records `0.14.0`
- `.sula/state/session/` exists
- `.sula/state/jobs/` exists
- `docs/ops/session-promotions.md` exists when the project uses durable promotion
- `python3 "$SULA_ROOT/scripts/sula.py" doctor --project-root "$PROJECT_ROOT" --strict` passes
- `python3 "$SULA_ROOT/scripts/sula.py" check --project-root "$PROJECT_ROOT"` returns `SULA CHECK OK`

## Operational Notes

- Do not upgrade projects from an arbitrary mutable local checkout when a tagged public release exists.
- Do not point one project at `main` and another at `v0.14.0` unless you intentionally want mixed rollout state.
- Keep `SULA_ROOT` versioned so rollback is just switching the checkout path or tag.
- If a project fails because of stale captures, review or clear that memory before treating the rollout as complete.
- If a project has reusable managed-file drift, capture it as feedback instead of carrying silent divergence forever.
