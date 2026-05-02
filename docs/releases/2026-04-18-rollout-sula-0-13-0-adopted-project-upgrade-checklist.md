# Roll out Sula 0.13.0 to adopted projects

## Metadata

- date: 2026-04-18
- executor: Codex
- branch: main
- status: active rollout guidance

## Scope

Use this checklist when upgrading already-adopted projects to Sula `0.13.0`. This rollout raises the normal operating bar around staged memory hygiene, durable promotion, rule discovery, and project checks, and it defines the per-project sequence teams should use to bring existing repositories onto the stable operator workflow.

Key release changes that matter downstream:

- staged session memory is now first-class under `.sula/state/session/captures.jsonl`
- durable promotions now land in `docs/ops/session-promotions.md` by default
- `memory capture`, `memory review`, `memory promote`, `memory clear`, and `memory jobs` are now part of the stable operator surface
- `status`, `onboard`, and `adopt` now expose memory state directly
- `doctor --strict` and `check` now validate stale staged captures and promotion-file integrity

Before upgrading any adopted project:

1. confirm the project is already adopted and has `.sula/project.toml`
2. confirm the project has no unreviewed local managed-file drift that should become feedback first
3. review whether the project has old temporary notes that should become durable rules, decisions, tasks, risks, or state updates
4. communicate that `check` may fail after upgrade until memory state is reviewed and regenerated

Canonical Git release source for this rollout:

- repository: `https://github.com/irihiyahnj/sula-public.git`
- tag: `v0.13.0`

Standard release checkout:

```bash
git clone --branch v0.13.0 --depth 1 https://github.com/irihiyahnj/sula-public.git /opt/sula/v0.13.0
export SULA_ROOT=/opt/sula/v0.13.0
```

Per-project upgrade sequence:

```bash
export PROJECT_ROOT=/path/to/project

python3 "$SULA_ROOT/scripts/sula.py" sync --project-root "$PROJECT_ROOT" --dry-run
python3 "$SULA_ROOT/scripts/sula.py" sync --project-root "$PROJECT_ROOT"
python3 "$SULA_ROOT/scripts/sula.py" memory digest --project-root "$PROJECT_ROOT"
python3 "$SULA_ROOT/scripts/sula.py" doctor --project-root "$PROJECT_ROOT" --strict
python3 "$SULA_ROOT/scripts/sula.py" check --project-root "$PROJECT_ROOT"
```

If the project already has temporary memory to review, continue with:

```bash
python3 "$SULA_ROOT/scripts/sula.py" memory review --project-root "$PROJECT_ROOT" --json
python3 "$SULA_ROOT/scripts/sula.py" memory promote --project-root "$PROJECT_ROOT" --capture-id <capture-id> --to rule
python3 "$SULA_ROOT/scripts/sula.py" memory clear --project-root "$PROJECT_ROOT" --reviewed-captures
python3 "$SULA_ROOT/scripts/sula.py" check --project-root "$PROJECT_ROOT"
```

Required post-upgrade outcomes:

- `.sula/version.lock` records `0.13.0`
- `.sula/state/session/` exists
- `.sula/state/jobs/` exists
- `docs/ops/session-promotions.md` exists when the project uses promotion
- `python3 scripts/sula.py doctor --project-root . --strict` passes in that project
- `python3 scripts/sula.py check --project-root .` returns `SULA CHECK OK`

## Risks

- projects that accumulated private scratch notes or informal temporary memory may fail `check` until they explicitly review, promote, or clear that state
- teams may over-promote low-signal notes if they do not keep the promotion bar narrow to durable rules, state, decisions, risks, or workflow-artifact expectations
- reusable local managed-file drift can be lost as one-off divergence if operators skip `feedback capture` during rollout

Promotion should stay narrow. Promote only when the captured item has become stable operating knowledge, for example a repeated project rule, a stable current-state update, a durable decision or risk, or a workflow-artifact expectation that should survive beyond one session. Do not promote low-signal scratch notes or one-off chat fragments.

## Verification

Treat a project as fully upgraded only when all of the following are true:

- sync completed
- memory digest was regenerated
- `doctor --strict` passed
- `check` passed
- the team knows whether that project will actively use the staged-memory loop

The stable operator loop after rollout is:

1. `memory capture`
2. `memory review`
3. `memory promote`
4. `query`
5. `memory clear --reviewed-captures`
6. `check`

For a quick manual audit across known local canaries:

```bash
python3 "$SULA_ROOT/scripts/sula.py" canary verify --project-root "$SULA_ROOT" --all
```

For other adopted repositories not listed as in-repo canaries, run the per-project upgrade sequence above against each repository root.

## Rollback

- if a downstream project upgrade fails, repair malformed managed or generated state, rerun `memory digest`, then rerun `doctor --strict` and `check`
- if `check` fails because of stale staged captures, run `memory review`, then either promote reviewed captures or clear them before retrying
- if a project has reusable local managed-file drift, capture it with `feedback capture` before continuing rollout so the divergence can be reviewed in Sula Core instead of becoming silent permanent drift

## Follow-up

- validate the first external upgraded projects and confirm the staged-memory workflow is understandable outside the Sula source repository
- watch for projects that need `docs/ops/session-promotions.md` materialized earlier in their adoption lifecycle
- keep using this rollout record as the canonical per-project upgrade checklist until a later release supersedes `0.13.0`
