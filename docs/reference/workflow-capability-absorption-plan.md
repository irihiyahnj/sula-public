# Workflow Capability Absorption Proposal

## Executive Summary

Sula should absorb reusable workflow-governance capabilities, but it should not bundle one external delivery doctrine as a mandatory methodology.

The durable opportunity is to extract a small set of cross-project operating capabilities that fit Sula's role as a project operating system:

- workflow capability registration
- first-class spec, plan, and review artifacts
- execution-mode policy
- workspace-isolation policy
- stronger verification and close-out policy

The correct product shape is "Sula governs which workflow capabilities a project enables" rather than "Sula hardcodes one agent plugin's behavior."

## Objectives And Scope

### Objectives

- define which workflow capabilities create long-term reusable value for Sula
- separate portable operating-system value from platform-specific skill mechanics
- propose a manifest, command, and rollout shape that preserves Sula's architecture boundaries
- estimate expected return from adoption so rollout can be prioritized rationally

### Scope

- reusable workflow and governance capabilities relevant to Sula
- Sula Core manifest and command surface implications
- rollout sequencing for Sula Core and future adopted projects

### Out Of Scope

- implementing a compatibility layer for any one external workflow system inside Sula
- making strict TDD or mandatory brainstorming a universal Sula rule
- changing the highest rule about managed operating-system files versus project-owned truth

## Current State And Constraints

### What The Workflow Pattern Contributes

The workflow pattern under review centers on:

- brainstorming before implementation
- explicit implementation plans
- isolated development branches and worktrees
- subagent-driven execution
- strict test-driven development
- recurring code review checkpoints
- explicit branch-finishing options

### What Sula Already Has

Sula already provides:

- project manifest contracts
- workflow-pack and projection concepts
- durable traceability through status, change records, releases, and incidents
- project memory and daily state-sync verification
- document-design bundles that already treat proposal, report, process, and training artifacts as first-class source documents

### Main Constraint

Sula is an operating system for many project types. A strong software-delivery methodology may be useful, but Sula should absorb the reusable governance layer, not the entire opinionated delivery doctrine.

## Proposed Approach

### Decision Rule

Adopt only the workflow capabilities that satisfy all of the following:

- reusable across more than one adopted project
- represent durable project truth instead of one agent runtime preference
- can be expressed as a manifest policy, a documented artifact, or a deterministic CLI contract
- do not require Sula to become a platform-specific plugin manager

### Capability Matrix

| Capability | Decision | Sula Shape | Expected Value | Notes |
| --- | --- | --- | --- | --- |
| Workflow capability registry | absorb | manifest + docs + CLI inspection | very high | turns agent habits into governed project policy |
| Spec / plan / review artifacts | absorb | source-first documents under durable paths | very high | strengthens traceability before code starts |
| Execution modes (`solo`, `review-heavy`, `subagent-parallel`) | absorb | manifest policy + recommended command flow | high | lets projects choose rigor without forked instructions |
| Workspace isolation (`none`, `branch`, `worktree`) | absorb | manifest policy + helper command | medium-high | strong for risky changes and multi-agent work |
| Verification policy | absorb | manifest policy + `check` integration | high | lowers "claimed done, not actually verified" failures |
| Finish / close-out protocol | absorb | close-out command + release-gate prompts | medium-high | gives a reusable ending contract |
| Universal mandatory brainstorming | reject as default | optional policy only | medium | too heavy for small fixes |
| Universal strict TDD | reject as default | optional policy only | medium | valuable, but not suitable for every repo or task |
| Skill precedence over project rules | reject | none | low | conflicts with Sula's governance hierarchy |
| Platform-specific plugin bootstrapping | reject | none | low | not operating-system truth |

### Estimated Return

These ranges are directional estimates, not measured production benchmarks.

| Adoption Slice | Expected Return |
| --- | --- |
| workflow capability registry + artifactized spec/plan/review | `20%` to `35%` better delivery consistency |
| execution-mode and verification policy | `15%` to `30%` less rework on multi-step tasks |
| isolation and close-out protocol | `10%` to `20%` less branch/worktree confusion and cleaner completion states |
| hard-importing one full external workflow doctrine as a default | only `5%` to `15%` likely net gain because friction rises on simple work |

### Manifest Delta

Sula should extend the optional `[workflow]` surface instead of inventing a source-specific section.

Proposed additions:

```toml
[workflow]
pack = "software-delivery"
stage = "active"
artifacts_root = "docs/workflows"
execution_mode = "review-heavy"
design_gate = "complex-only"
plan_gate = "multi-step"
review_policy = "task-checkpoints"
workspace_isolation = "branch"
testing_policy = "verify-first"
closeout_policy = "explicit"
```

Field intent:

- `execution_mode`: `solo-inline`, `review-heavy`, `subagent-parallel`
- `design_gate`: `never`, `complex-only`, `always`
- `plan_gate`: `never`, `multi-step`, `always`
- `review_policy`: `none`, `batch`, `task-checkpoints`, `strict`
- `workspace_isolation`: `none`, `branch`, `worktree`
- `testing_policy`: `inherit`, `verify-first`, `tdd`
- `closeout_policy`: `inherit`, `explicit`

This keeps the behavior portable and project-owned while leaving agent adapters free to implement the policy in different ways.

### Command Draft

Sula should add a narrow workflow command family instead of embedding agent prompts in core commands.

Recommended first-pass surfaces:

- `python3 scripts/sula.py workflow assess --project-root .`
  - reports recommended workflow mode from manifest and task shape
- `python3 scripts/sula.py workflow scaffold --project-root . --kind spec`
  - creates source-first workflow artifacts under `docs/workflows/`
- `python3 scripts/sula.py workflow scaffold --project-root . --kind plan`
  - creates a plan document using the project's document rules
- `python3 scripts/sula.py workflow scaffold --project-root . --kind review`
  - creates a review checklist or review report shell
- `python3 scripts/sula.py workflow branch --project-root .`
  - enforces the configured isolation policy and prints the resulting path or branch
- `python3 scripts/sula.py workflow close --project-root .`
  - applies close-out checks and presents structured end states such as merge, PR, keep, or discard

### File And Artifact Shape

Recommended source-first paths:

- `docs/workflows/specs/YYYY-MM-DD-<slug>.md`
- `docs/workflows/plans/YYYY-MM-DD-<slug>.md`
- `docs/workflows/reviews/YYYY-MM-DD-<slug>.md`

These should be treated as project-owned workflow truth, while any agent-specific prompts or plugin files remain optional projections or adapters.

## Milestones And Work Plan

### Phase 1: Contracts And Documentation

- document the capability model and decision boundaries
- extend the manifest schema and example files
- add workflow artifact path conventions

### Phase 2: Artifact Scaffolding

- add `workflow scaffold` for `spec`, `plan`, and `review`
- connect scaffolded artifacts to the formal document-design rules where relevant
- make `docs/README.md` and template packs aware of the new durable workflow surfaces

### Phase 3: Verification And Close-out

- add workflow policy checks to `check`
- add `workflow close` with structured completion options
- ensure close-out keeps traceability explicit

### Phase 4: Isolation And Parallel Execution

- add `workflow branch` with `branch` and `worktree` policy support
- treat subagent-parallel as a policy recommendation first, not a hard runtime dependency

### Phase 5: Adapter Rollout

- expose workflow policy to Codex, Claude, Cursor, and future adapters through managed instructions
- keep adapter behavior secondary to project manifest policy

## Responsibility Matrix

| Area | Owner | Notes |
| --- | --- | --- |
| capability contract | Sula Core maintainers | belongs in core docs and schema |
| manifest schema updates | Sula Core maintainers | must remain backward-compatible |
| CLI workflow commands | Sula Core maintainers | reuse `scripts/sula.py` |
| adapter-specific instruction projections | Sula Core maintainers | generated from core policy, not hand-diverged |
| canary validation | first adopted software-delivery projects | validate friction versus value on real work |

## Risks And Decisions

### Main Risks

- overfitting Sula to coding-agent workflows and weakening its generic-project posture
- introducing too many workflow knobs before one canary proves the right defaults
- confusing project truth with ephemeral agent prompts
- making small tasks slower by forcing heavyweight design rituals

### Decisions

- decide against importing one external workflow doctrine as a mandatory default
- decide for absorbing a smaller workflow capability model into Sula Core
- decide that strict brainstorming and strict TDD should remain opt-in policy levels, not core defaults
- decide that durable workflow artifacts are the highest-value near-term absorption target

## Recommended Next Step

The next practical step is not implementation of every workflow feature. It is a narrow contract release:

1. add workflow policy fields to the manifest and schema
2. add source-first `spec`, `plan`, and `review` scaffolds
3. validate the model on one real software-delivery canary before deeper worktree and adapter automation
