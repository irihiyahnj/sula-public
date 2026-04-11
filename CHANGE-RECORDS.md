# Sula Change Records

This file is the index for non-trivial Sula Core changes.

## Purpose

Track why Sula changed, how sync impact was evaluated, what was verified, and how rollback should work.

## Rules

- keep this file short and index-oriented
- put detailed records in `docs/change-records/`
- mention sync impact explicitly in non-trivial records
- use release records when the rollout itself needs durable history

## Index

- 2026-04-11 - [Add adoption-agent flow for one-sentence onboarding](docs/change-records/2026-04-11-add-adoption-agent-flow-for-one-sentence-onboarding.md) - Added an inspect-report-approve onboarding flow so new repositories can adopt Sula through a single approval-based entrypoint.
- 2026-04-11 - [Self-adopt Sula root under sula-core profile](docs/change-records/2026-04-11-self-adopt-sula-root-under-sula-core-profile.md) - Promoted the Sula repository itself into a managed consumer so root governance, memory, and rollout checks use the same operating-system model.

## Detailed Records

- directory: `docs/change-records/`
- template: [docs/change-records/_template.md](docs/change-records/_template.md)
