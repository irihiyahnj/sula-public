# Agent Execution Quality Policy

Sula absorbs Karpathy-style coding guidance as a reusable agent behavior policy, not as a Claude/Cursor-specific plugin.

## Source Reviewed

- `forrestchang/andrej-karpathy-skills` README and Chinese README
- `skills/karpathy-guidelines/SKILL.md`
- `.cursor/rules/karpathy-guidelines.mdc`
- `EXAMPLES.md`
- `.claude-plugin/plugin.json`

The upstream material is instruction-first: it defines how an agent should think, scope changes, simplify, and verify. It does not provide runtime code that Sula should vendor.

## Decision

Sula absorbs the reusable behavior contract:

- surface uncertain assumptions before non-trivial work
- prefer the simplest durable design that satisfies the task
- keep diffs surgical and avoid drive-by refactors
- preserve or define acceptance criteria
- require verification evidence before accepted closeout
- keep the behavior portable across adopted projects and agent providers

Sula does not absorb the upstream repository as a dependency, because that would couple a reusable project operating system to one assistant ecosystem and duplicate policy already controlled by Sula manifests.

## Manifest Contract

Projects may declare:

```toml
[agent_behavior]
quality_policy = "sula-karpathy-inspired"
clarification_policy = "non-trivial-only"
diff_scope_policy = "surgical"
success_criteria_policy = "required"
assumption_policy = "surface-when-uncertain"
complexity_policy = "simplicity-first"
require_verification = true
forbid_drive_by_refactors = true
```

The default policy is intentionally strict because it protects Sula's highest rule: centrally managed operating-system files must stay separate from project-owned business truth.

## Orchestration Integration

`orchestration run` writes the resolved agent behavior and a quality checklist into every run record. This gives future real runner adapters a machine-readable contract before they mutate files.

`orchestration close --accept` enforces policy evidence when configured:

- verification evidence is required when `require_verification = true`
- acceptance or success-criteria evidence is required when `success_criteria_policy = "required"`

Dry-run scheduling evidence alone is not enough to accept a run.

## Boundary

This policy is advisory and gating infrastructure. It does not replace project-specific rules, the repository highest rule, workflow gates, tests, or human approval for high-risk actions.
