# Self-adopt Sula root under sula-core profile

## Metadata

- date: 2026-04-11
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): 901c67f
- status: completed

## Background

Promoted the Sula repository itself into a managed consumer so root governance, memory, and rollout checks use the same operating-system model.

## Analysis

- Sula Core had gained governance, memory, and rollout mechanisms, but the repository root was not yet consuming them as a project itself.
- Without root self-adoption, the in-repo canary proved consumer behavior only for the example profile, not for Sula Core's own operating shape.
- A dedicated `sula-core` profile is the cleanest way to manage the repository without pretending it is a React business project.

## Chosen Plan

- add a `sula-core` profile with architecture and runbook docs for operating-system repositories
- self-adopt the repository root with a dedicated manifest
- migrate root traceability into the new memory structure and add a root change record
- make CI and doctor treat the root repository as a strict self-managed consumer

## Execution

- added the `sula-core` profile under `templates/profiles/sula-core/`
- created `.sula/project.toml` for the repository root
- rendered managed and scaffold files into the root repository
- updated `STATUS.md`, `CHANGE-RECORDS.md`, and root memory assets to align with the new contract
- prepared the root repository to pass `sula doctor --project-root . --strict`

## Verification

- `python3 scripts/sula.py init --project-root .`
- `python3 scripts/sula.py record new --project-root . --title "Self-adopt Sula root under sula-core profile" --summary "Promoted the Sula repository itself into a managed consumer so root governance, memory, and rollout checks use the same operating-system model." --date 2026-04-11`
- `python3 scripts/sula.py memory digest --project-root .`
- `python3 scripts/sula.py doctor --project-root . --strict`

## Rollback

- remove the root `.sula/` files and generated self-adoption assets if the repository should stop self-consuming Sula
- keep the in-repo canary and reusable profiles intact if only root self-adoption proves unsuitable

## Data Side-effects

- no production data side-effects
- repository-only metadata and memory files were added for root self-management

## Follow-up

- keep the `sula-core` profile aligned with any future root operating changes
- onboard an external canary that also uses the `sula-core` profile if one emerges

## Architecture Boundary Check

- highest rule impact: preserved; self-adoption uses a dedicated operating-system profile rather than forcing Sula into a one-project business template
