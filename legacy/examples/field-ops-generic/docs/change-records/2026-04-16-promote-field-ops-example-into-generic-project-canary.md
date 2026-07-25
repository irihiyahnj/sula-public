# Promote field ops example into generic-project canary

## Metadata

- date: 2026-04-16
- executor: Codex
- branch: main
- related commit(s): pending
- status: completed

## Background

Use this example as a local generic-project rollout canary.

## Analysis

- The example already carried a valid generic-project adoption, but it was not yet treated as a formal rollout canary.
- A local canary is useful because generic-project changes should be verified somewhere smaller than a live client repository.

## Chosen Plan

- promote the example into the registry as a canary
- keep the example small and source-first so `sync`, `doctor --strict`, and `check` remain easy to verify

## Execution

- updated the example status so it reflects a real maintained canary
- added the example to the rollout registry with a resolvable `local_root`
- regenerated the memory digest after the status and record changes

## Verification

- `python3 scripts/sula.py memory digest --project-root examples/field-ops-generic`
- `python3 scripts/sula.py check --project-root examples/field-ops-generic`

## Rollback

- remove the canary registry entry and keep the example as a non-canary fixture if generic-project rollout verification moves elsewhere

## Data Side-effects

- the example now participates in local canary verification runs

## Follow-up

- keep the canary synchronized with future generic-project managed-template changes

## Architecture Boundary Check

- highest rule impact: preserved; the example remains project-owned while Sula-managed surfaces are verified through normal sync rules
