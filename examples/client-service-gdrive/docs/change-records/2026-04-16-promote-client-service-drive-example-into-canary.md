# Promote client service drive example into canary

## Metadata

- date: 2026-04-16
- executor: Codex
- branch: main
- related commit(s): pending
- status: completed

## Background

Use this example as a local client-service rollout canary.

## Analysis

- The example already expressed the `client-service` workflow pack and Google Drive adapter metadata, but it was not yet wired into formal rollout verification.
- Keeping a local provider-aware canary reduces the chance that workflow-pack or storage-contract changes ship without a quick validation target.

## Chosen Plan

- promote the example into the registry as a local canary
- keep the example provider-aware without requiring live Google access

## Execution

- updated the example status so it reflects a maintained rollout canary
- added the example to the rollout registry with a resolvable `local_root`
- regenerated the memory digest after the status and record changes

## Verification

- `python3 scripts/sula.py memory digest --project-root examples/client-service-gdrive`
- `python3 scripts/sula.py check --project-root examples/client-service-gdrive`

## Rollback

- remove the canary registry entry and fall back to manual local verification if this example stops representing the client-service workflow safely

## Data Side-effects

- the example now participates in local canary verification runs for provider-aware workflow changes

## Follow-up

- keep the canary aligned with future Google Drive adapter and client-service workflow changes

## Architecture Boundary Check

- highest rule impact: preserved; the example remains a project-owned fixture while Sula validates managed behavior through normal rollout checks
